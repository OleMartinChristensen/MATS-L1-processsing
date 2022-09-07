#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 11:41:36 2020

@author: lindamegner
"""

import numpy as np
from mats_l1_processing.L1_calibration_functions import (
    get_true_image,
    desmear_true_image,
    CCD,
    subtract_dark,
    compensate_flatfield,
    get_linearized_image,
    get_linearized_image_parallelized,
)

# from L1_calibration_functions import get_true_image_old, desmear_true_image_old
#################################################
#       L1 calibration routine                  #
#################################################


def calibrate_all_items(CCDitems, instrument, plot=False):
    import matplotlib.pyplot as plt
    from LindasCalibrationFunctions import plot_CCDimage

    for CCDitem in CCDitems:
        (
            image_lsb,
            image_bias_sub,
            image_desmeared,
            image_dark_sub,
            image_flatf_comp,
        ) = L1_calibrate(CCDitem, instrument)

        if plot == True:
            fig, ax = plt.subplots(5, 1)
            plot_CCDimage(image_lsb, fig, ax[0], "Original LSB")
            plot_CCDimage(image_bias_sub, fig, ax[1], "Bias subtracted")
            plot_CCDimage(image_desmeared, fig, ax[2], " Desmeared LSB")
            plot_CCDimage(image_dark_sub, fig, ax[3], " Dark current subtracted LSB")
            plot_CCDimage(image_flatf_comp, fig, ax[4], " Flat field compensated LSB")
            fig.suptitle(CCDitem["channel"])


def L1_calibrate(CCDitem, instrument): #This used to take in a calibration_file instread of instrument object 

    CCDitem["CCDunit"] =instrument.get_CCD(CCDitem["channel"])

    #  Hack to have no compensation for bad colums at the time. TODO later.
    if not (CCDitem["NBC"] == 0):
        CCDitem["NBC"] = 0
        CCDitem["BC"] = np.array([])
        error_bad_column = np.ones(CCDitem["IMAGE"].shape)
        


    image_lsb = CCDitem["IMAGE"]
    
    # Step 1 and 2: Remove bias and compensate for bad columns, image still in LSB
    image_bias_sub,error_flags_bias = get_true_image(CCDitem)
    #    image_bias_sub = get_true_image(CCDitem)

    # step 3: correct for non-linearity (image is converted into float??)
    image_linear,error_flags_linearity = get_linearized_image(CCDitem, image_bias_sub)
    #image_linear = image_bias_sub

    # Step 4: Desmear
    image_desmeared, error_flags_desmear= desmear_true_image(CCDitem, image_linear)
    #    image_desmeared = desmear_true_image(CCDitem)

    # Step 5 Remove dark current
    # TBD: Decide on threshold fro when to use pixel correction (little dark current) and when to use average image correction (large dark current).

    image_dark_sub, error_flags_dark = subtract_dark(CCDitem, image_desmeared)

    # Step 6 Remove flat field of the particular CCD.

    image_flatf_comp, error_flags_flatfield = compensate_flatfield(CCDitem, image_dark_sub)
    CCDitem["image_calibrated"] = image_flatf_comp

    # Step 7 Remove ghost imaging. TBD.

    # Step 8 Transform from LSB to electrons and then to photons. TBD.

    return image_lsb, image_bias_sub, image_desmeared, image_dark_sub, image_flatf_comp
