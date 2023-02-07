import pandas as pd
import numpy as np
import requests
from requests import HTTPError
import json
import spotipy
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from sqlalchemy import create_engine
import time
import os
import ast
import itertools

class api_handling:
    def __init__(self, save_location, client_id = None, client_secret = None):
        self.client_id = "bf7981913014450c8a984eb79eaad419"
        self.client_secret = 'a763340271dd406c89f230459f4abfff'
        self.save_location = save_location
        self.source = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(client_id=self.client_id,client_secret=self.client_secret)
            )
        self.frames = {}
        self.offset_counts = {}
        self.errors = {}

        session = requests.Session()
        session.timeout = 15  # set timeout to 10 seconds
        


    def error_note(self, frame_key, note_tuple):
        if frame_key in self.errors.keys():
            self.errors[frame_key].append(note_tuple)
        else:
            self.errors[frame_key] = []

    def search(self,query:str,t:str,framekey:str,apply_offset = False):
        #calls spotipy search method
        if not apply_offset:
            return self.source.search(q=query,limit=50,offset=0,type=t)
        if framekey in self.offset_counts.keys():
            return self.source.search(q=query,limit=50,offset=self.offset_counts[framekey],type=t)
        else:
            return self.source.search(q=query,limit=50,offset=0,type=t)


    def new_main_df(self,frame_key, pull, overwrite=False):
        #adds frame to class instance with safety built in to prevent overwriting accidentally
        if overwrite:

            if type(pull) == pd.DataFrame:
                self.frames[frame_key] = pull
                self.offset_counts[frame_key] = 0

            elif type(pull) == list:
                pull = self.dict_transform(pull)
                self.frames[frame_key] = pd.DataFrame(pull, index='id')
                self.offset_counts[frame_key] = 0

            else:
                assert type(pull) == dict, 'send a dict if not a list of dictionaries, sent type: {}'.format(type(pull))
                pull = self.dict_transform([pull])
                self.frames[frame_key] = pd.DataFrame(pull) 
                self.offset_counts[frame_key] = 0

        else:
            assert not frame_key in self.frames.keys(), 'Dataframe already exists. Either overwrite or choose new name.'
            self.frames[frame_key] = pd.DataFrame(pull)
            self.offset_counts[frame_key] = 0


    def append_to_frame(self, frame_key, pull):
        assert self.frame_exists(frame_key), 'create frame first'
        assert type(pull) == list or type(pull) == pd.DataFrame, 'Pull parameter must be pd.DataFrame or list of Dataframes'

        if type(pull) == list:
            pull = self.dict_transform(pull)
            self.frames[frame_key] = pd.concat([self.frames[frame_key],pd.DataFrame(pull)])#, ignore_index=True

        if type(pull) == pd.DataFrame:
            self.frames[frame_key] = pd.concat([self.frames[frame_key],pull])
            self.offset_counts[frame_key] = self.frames[frame_key].shape[0]


    def frame_exists(self,frame_key):
        if frame_key in self.frames.keys():
            return True
        else:
            return False

    def pull_set(self, query, pull_count, frame_key, t, apply_offset=True):
        '''
        PURPOSE: Call the 'search' spotipy method more than once, with safeguards for not calling the API too often
        PARAMETERS:
        query is language passed to the spotipy method
        pull_count is the quantity of pulls (50 each)
        frames_key is the key for what is stored in the dictionary full of each dataframe pulled using this class 
        t is the type parameter in the spotipy method
        '''
        #artists
        sleep_count = 25
        #pulls between rests

        while pull_count > 0:
            
            pull = self.search(query = query,framekey=frame_key,t = t,apply_offset=apply_offset)
            
            pull = pd.DataFrame(pull[str(t)+'s']['items'])
            
            if self.frame_exists(frame_key):
                self.append_to_frame(frame_key,pull)    

            else:
                self.new_main_df(frame_key,pull)

            if sleep_count == 0:
                time.sleep(15)
                sleep_count = 15
            else:
                sleep_count -= 1

            pull_count -= 1
            

    def pull_artists(self,genre,pull_count):
        #pull artists by genre
        self.pull_set(query='genre:{}'.format(genre),frame_key='artists',pull_count=pull_count,t='artist')


    def pull_tracks(self, pull_count:int):
        #pull tracks by artists located in self.frames
        assert self.frame_exists('artists'), 'No artist data in class instance'
        assert self.frame_exists('song_data'), 'No song_data found in self.frames'

        for artist in self.frames['artists'].name.unique():
            if artist in self.frames['song_data'].name:
                pass
            else:
                self.pull_set(query='artist:{}'.format(artist),frame_key='song_data',pull_count=1,t='track',apply_offset=False)
                time.sleep(0.5)
        self.frames['song_data'].dropna(inplace=True)


    def pull_track_features(self):
        # pull all spotify characteristics from the .features method
        hundred_list=[[]]
        #group of 100 (or less) artists at a time
        for track_key in self.frames['song_data'].index:
            if type(track_key) == str:
                if len(hundred_list[-1]) == 100:
                    hundred_list.append([track_key])
                else:
                    hundred_list[-1].append(track_key)

        flattened_bucket = []
        #return flattened_bucket
        for song_keys in hundred_list:
            # pull in bunches of 100
            pull = self.source.audio_features(song_keys)
            for row in pull:
                # flatten list of lists consisting of 100 or less rows each, to just a single list of rows, named flattened_bucket
                flattened_bucket.append(row)

            if not self.frame_exists('track_features'):
                self.new_main_df(frame_key='track_features',pull=pull, overwrite=True)
            else:
                self.append_to_frame(frame_key='track_features',pull=pull)


    def pull_track_analysis(self, max_iterations=10_000):
        track_pulls = []
        save_when_zero = 2000
        rest_when_zero = 500
        iter_count = 0

        if self.frame_exists('track_analysis'):
            data_needed = [str(x) for x in list(self.frames['song_data'].index.unique()) if not x in list(self.frames['track_analysis'].id.unique())]
        else:
            data_needed = [str(x) for x in self.frames['song_data'].index]

        for track_key in data_needed:
            #these are the unique spotify song ids being used for the query

            if iter_count > max_iterations:
                break

            if rest_when_zero == 0:
                time.sleep(2)
                rest_when_zero = 500

            if save_when_zero == 0:
                if self.frame_exists('track_analysis'):
                    self.append_to_frame('track_analysis',pull=track_pulls)
                    track_pulls = []
                else:
                    self.new_main_df(frame_key='track_analysis',pull=track_pulls, overwrite=True)
                    track_pulls = []
                save_when_zero = 2000

            rest_when_zero -= 1
            save_when_zero -= 1
            iter_count += 1

            try:
                pull = self.source.audio_analysis(track_id=track_key)
                pull['id'] = track_key
                track_pulls.append(pull)

            except:
                continue
            
        if self.frame_exists('track_analysis'):
            self.append_to_frame('track_analysis',pull=track_pulls)
        else:
            self.new_main_df(frame_key='track_analysis',pull=track_pulls, overwrite=True)
            

    def csv_pull(self,overwrite=False):
        for file in os.listdir(self.save_location):
            if file[-3:] == 'csv':
                self.new_main_df(file[:-4],pd.read_csv(self.save_location + file,index_col=0),overwrite=overwrite)


    def remove_substring_cols(self,col_substring:str,frame_key:str):
        # removes columns from a frame that has a substring in the column name
        # rename eventually
        remove_list = []
        for col in self.frames[frame_key].columns.values:
            if col_substring in col:
                remove_list.append(col)
        self.frames[frame_key].drop(columns=remove_list,inplace=True)


    def convert_literals(self, frame_key:str, column_names:list):
        # some of the initial data pulled from spotipy returns dictionaries as column values,
        # some of these column subdictionaries store the dictionaries in a string format
        # in order to clean these strings must be converted into their native type
        assert type(column_names) == list or type(column_names) == str, 'col parameter must be str or list'
        assert self.frame_exists(frame_key), 'called frame that does not exist'

        for column in column_names:
            assert column in self.frames[frame_key].columns, 'column name does not exist: {}'.format(column)
            self.frames[frame_key][column] = [ast.literal_eval(x) for x in self.frames[frame_key][column]]


    def save(self,frame_key):
        assert self.frame_exists(frame_key), 'called frame that does not exist'
        self.frames[frame_key].to_csv(self.save_location + frame_key + '.csv')


    @staticmethod
    def dict_transform(pull):
        '''
        PARAMETER: list of dictionaries
        FUNCTION: pandas prefers a single dictionary, with each key as a column name and corresponding value as an array of each value in the entire column
        '''
        assert type(pull) == list, 'send list. if single item, send encased within a list'
        output = {}
        for entry in pull:
            for key in entry.keys():
                if key in output.keys():
                    output[key].append(entry[key])
                else:
                    output[key] = [entry[key]]

        return output