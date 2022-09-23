#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 15:17:27 2022

@author: lindamegner

Functions used in analysis images and calibration development but NOT for operational processing.
"""

#############################################################################
#   Plotting Functions                                                      #
#############################################################################

def plotCCDitem(CCDitem, fig, axis, title="", clim=999, aspect="auto"):
    image = CCDitem["IMAGE"]
    sp = plot_CCDimage(image, fig, axis, title, clim, aspect)
    return sp


def plot_CCDimage(image, fig, axis, title="", clim=999, aspect="auto"):
    sp = axis.imshow(image, cmap="viridis", origin="lower", interpolation="none")
    # sp=axis.pcolormesh(image, , cmap='viridis')
    if clim == 999:
        mean = image.mean()
        std = image.std()
        sp.set_clim([mean - 2 * std, mean + 2 * std])
    else:
        sp.set_clim(clim)
    fig.colorbar(sp, ax=axis)
    axis.set_title(title)
    axis.set_aspect(aspect)
    return sp


def plot_CCDimage_hmean(fig, axis, image, title="", clim=999):
    yax = range(0, image.shape[0])
    sp = axis.plot(image.mean(axis=1), yax)
    axis.set_title(title)
    return sp


def plot_simple(filename, clim=999):
    import numpy as np
    from PIL import Image
    import matplotlib.pyplot as plt

    pic = np.float64(Image.open(filename))  # read image
    plt.imshow(pic)
    if clim == 999:
        mean = pic.mean()
        std = pic.std()
        plt.clim([mean - 2 * std, mean + 2 * std])
    else:
        plt.clim(clim)
    plt.colorbar()


def diffplot(image1, image2, title1, title2, clim=999, climdiff=999):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(3, 1)
    diffimg = image1 - image2
    if clim == 999:
        plot_CCDimage(image1, fig, ax[0], title=title1)
        plot_CCDimage(image2, fig, ax[1], title=title2)
    else:
        plot_CCDimage(image1, fig, ax[0], title=title1, clim=clim)
        plot_CCDimage(image2, fig, ax[1], title=title2, clim=clim)
    if climdiff == 999:
        plot_CCDimage(diffimg, fig, ax[2], title="pic 1-pic2")
    else:
        plot_CCDimage(diffimg, fig, ax[2], title="pic 1-pic2", clim=climdiff)
    return fig




def plot_full_temperature_info(temperaturedata, relativetimedata):
    import matplotlib.pyplot as plt
    HTR1A = temperaturedata[:, 0]
    HTR1B = temperaturedata[:, 1]
    HTR2A = temperaturedata[:, 2]
    HTR2B = temperaturedata[:, 3]
    HTR8A = temperaturedata[:, 4]
    HTR8B = temperaturedata[:, 5]

    plt.plot(relativetimedata / 60.0, HTR1A,
             label="splitter plate, regulation")
    plt.plot(relativetimedata / 60.0, HTR1B, label="splitter plate, measuring")
    plt.plot(relativetimedata / 60.0, HTR2A, label="limb house, regulation")
    plt.plot(relativetimedata / 60.0, HTR2B, label="limb house, measuring")
    plt.plot(relativetimedata / 60.0, HTR8A, label="UV2 CCDn")
    plt.plot(relativetimedata / 60.0, HTR8B, label="UV1 CCDn")
    plt.xlabel("Time since start of instrument [min]")
    plt.ylabel("Temperature [C]")
    plt.legend()
    plt.show()
    plt.savefig("HTRmeasurements.jpg")
    

#############################################################################
#   Protocol reading functiions                                             # 
#############################################################################

def read_all_files_in_protocol(df, read_from, root_directory):
    from database_generation.read_in_imgview_functions import read_CCDitem_from_imgview
    from mats_l1_processing.read_in_functions import read_CCDitem_image, find_CCDitem_matching_PicID, add_and_rename_CCDitem_info
    from .get_temperature import add_rac_temp_data
    import pandas as pd 
    CCDitems = []
    for PicID in list(df["PicID"]):
        if read_from == "rac":
            racdf = pd.read_csv(root_directory + "RacFiles_out/CCD.csv", skiprows=[0]) #Read in full CCD.csv to panda data frame
            CCD_image_data = racdf.to_dict("records") #Comvert full data frame to list of dicts
            CCDitem=find_CCDitem_matching_PicID(CCD_image_data, PicID) #select the dict that corresponds to the wanted PiCID (as given by protocol) and name that dict CCDitem 
            errorflag=read_CCDitem_image(CCDitem, root_directory + "RacFiles_out/") # read in the image that corresponds to the PicID and add that to the CCDitem
            if errorflag:
                raise Exception("Image"+CCDitem['Image File Name'] +"not found") 

                
        elif read_from == "imgview":    
            CCDitem = read_CCDitem_from_imgview(root_directory + "PayloadImages/", PicID)
        else:
            raise Exception("read_from must be rac or imgview")    
        if CCDitem != -999:
            CCDitems.append(CCDitem)
            
    for CCDitem in CCDitems:        
            add_and_rename_CCDitem_info(CCDitem)
            CCDitem["DarkBright"] = df.DarkBright[df.PicID == PicID].iloc[0]
            CCDitem["Shutter"] = df.Shutter[df.PicID == PicID].iloc[0]
            CCDitem["Comment"] = df.Comment[df.PicID == PicID].iloc[0]
            
            #Add temperature data from rac files   
            add_rac_temp_data(root_directory + "RacFiles_out/HTR.csv", CCDitem, labtemp=999)

    return CCDitems

def readprotocol(filename):
    import pandas as pd

    df = pd.read_csv(filename, sep=" ", comment="#",
                     skipinitialspace=True, skiprows=())  
    return df


#############################################################################
#   Miscellaneous                                                           # 
#############################################################################


def filter_on_time(CCDitems, starttime=None, stoptime=None):
    I = []
    for i in range(len(CCDitems)):
        image_time = pd.to_datetime(
            CCDitems[i]["EXP Date"], format="%Y-%m-%dT%H:%M:%S.%fZ"
        )
        if (starttime != None) and (stoptime != None):
            if (image_time > starttime) and (image_time < endtime):
                I.append(i)
        elif (starttime != None) and (stoptime == None):
            if image_time > starttime:
                I.append(i)
        elif (starttime == None) and (stoptime != None):
            if image_time < starttime:
                I.append(i)
        else:
            Warning("Start or end time invalid")

    CCDitems = [CCDitems[i] for i in I]
    return CCDitems

