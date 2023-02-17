# Music Generative Adversarial Networks

## Problem Statement

Since about the turn of the century, music production became democratized through the release of Digital Audio Workstations. Powerful software systems like Ableton Live and Logic Pro have allowed almost anyone with a laptop to have the tools that were once limited to those with access to physical studio access. One issue that many musicians, including myself face is the explosion of optionality in starting a song. With so many options for plug-in software, there is continually an issue of being falling under choice-paralysis.

One common solution often proposed is to limit your optionality. Perhaps force yourself to select a few tools to work with and go from there. I wanted to see if I could use data science to create a product to facilitate the process of starting a new song. Because I love house music, I decided to start with that genre, while keeping in mind how I could apply this to another genre of music.

My goal in this project has been to create a minimum viable product to see what I could create to help begin the process of music production.

## Project Notebook Structure Overview

I worked on this Project Across several Notebooks. To quickly summarize the structure and contents of each, please see below.
- **Spotify_Data_Pull.ipynb:** I deploy a class to pull and save data in a structured an organized manner.
- **EDA.ipynb:** Contains some simple interesting analysis of the broader Spotify dataset.
- **Data_Setting.ipynb:** I structure my data to prepare it for training within the GAN.
- **Vanilla_Model.ipynb:** I construct a tensorflow subclass to train a generator and discriminator network simultaneously, and train the network.
- **MVP output.ipynb:** Contains my method to take generated rythm tensors and create midi files.

## Executive Summary

To build a tool that can help begin a catchy song, it would need to be very effective in capturing the important factors associated with whatever genre that you are working within. This lead to me realizing that there is probably no better way to get a catchy beat than from songs that were confidently sent into the marketplace. Thus, after researching what data was publically available and chose Spotify as my source of data, and began my data pulling.

I queried the Spotify dataset utilizing the Spotipy python wrapper because of its nicely handled process of keeping authentication handled, so that I could focus on querying. I first pulled a substantial quantity of artists within the house and techno genres. Next I pulled the 50 or fewer songs from each artist, as well as the Spotify comprehensive analysis data for each song. This process was handled by my api_handling class found on my Spotify_Data_Pull workbook.

Fortunately after some analysis of the data that I pulled from spotify, there was time series analyses on each of the songs. I realized at this point that I would have access to pleanty of data to help create a tool to assist with music production. Ultimately one concern was the fact of potentially copying an artist's work if I directly based my product off of the data of these songs. This lead me to Generative Adversarial Networks, and learning how to create data that is influenced, but not directly sourced from my dataset.

Ultimately, I synthesized the Spotify data into a data representation that could be essentially convolved on by a discriminator portion of a GAN, and created a one after conducting research on the production of tabular data. Once my generator was strong enough, I created a method that takes its outputs and produced a midi file that can be fed straight into a Digital Audio Workstation. This is conducted on MVP Output.

## Conclusions & Next Steps:
General Adversarial Network archetecture can be very challenging to construct if constrained by hardware. I trained my GAN on an RTX 3070Ti, and configured my system environment to train locally on my PC, but nonetheless, training two networks that influence each other can add substantially more constraints to the archetecture of my model than I first thought it would. I was able to maintain 1,343,201 parameters on my generator, and 976,377 parameters on my discriminator, so just more than 2.3 million parameters. Though it is much more common in practice to have a more complex discriminator than generator, when limited by hardware in my situation, this was the solution that was able to keep my generator from falling into mode collapse and / or vanishing gradients. Ultimately I will be adding to the complexity of this product looking forward, but I am still facinated by what the GAN was able to create. It clearly has learned rythm, but by my last epoch, it started to fall into mode collapse.

Please see below for how I will improve this looking forward.

1. Deploy a more complex Loss function to avoid Vanishing Gradients. There are a few interesting options such as Wasserstein loss and modified minimax loss.

2. Work on a system with more graphics processing capacity.

3. Continue to toggle with GAN archetecture
