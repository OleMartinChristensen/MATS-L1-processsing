import mats_l1_processing
import numpy as np
from PIL import Image
from mats_l1_processing.L1_calibration_functions import read_flatfield
from mats_l1_processing.instrument import CCD
from mats_l1_processing.experimental_utils import (
    plot_CCDimage,
    read_all_files_in_protocol,
)
from mats_l1_processing.read_in_functions import readprotocol
import matplotlib.pyplot as plt

# from scipy import signal
from scipy import ndimage, io
from scipy.signal import spline_filter
from pathlib import Path
import toml


def make_flatfield(channel, signalmode, calibration_file, plot=True):
    # makes flatfield using both a cold flatfield without baffle and a room temp flatfield with baffle.



    CCDunit=CCD(channel,calibration_file)

    calibration_data=toml.load(calibration_file)

    if signalmode == "HSM":
        flatfield_wo_baffle = read_flatfield(
            CCDunit, 0, calibration_data["flatfield"]["flatfieldfolder_cold_unprocessed"]
        )
    elif signalmode == "LSM":
        flatfield_wo_baffle = read_flatfield(
            CCDunit, 1, calibration_data["flatfield"]["flatfieldfolder_cold_unprocessed"]
        )

    directory = calibration_data["flatfield"][
        "baffle_flatfield"
    ]  #'/Users/lindamegner/MATS/retrieval/Calibration/Final_AIT_2021/LimbFlatfield/Flatfield20210421/PayloadImages/'

    # Read in flatfields taken in April 2021 with baffle Snippet frpm protocol1.txt below
    # TODO: add filename to calibration_file or autoread
    if channel == "IR1":
        filelist = [
            "1303052462743530240_1",
            "1303052550753753600_1",
            "1303052736716888320_1",
            "1303052669289184512_1",
        ]
    elif channel == "IR2":
        filelist = [
            "1303052978547042816_4",
            "1303053042442397952_4",
            "1303053108130874624_4",
            "1303053177900405760_4",
        ]
    elif channel == "IR3":
        filelist = [
            "1303053542163925248_3",
            "1303053614869430528_3",
            "1303053680075119104_3",
            "1303053754744018432_3",
        ]
    elif channel == "IR4":
        filelist = [
            "1303053854620956416_2",
            "1303053921036712704_2",
            "1303053986963058432_2",
            "1303054064460723968_2",
        ]
    elif channel == "UV1":
        filelist = [
            "1303054184923202560_6",
            "1303054301145446656_6",
            "1303054436714050304_6",
            "1303054566244445696_6",
        ]
    elif channel == "UV2":
        filelist = [
            "1303054749741714432_5",
            "1303055407319107072_5",
            "1303055745598846464_5",
            "1303056141568969728_5",
        ]
    elif channel == "NADIR":
        filelist = [""]

    pfile = filelist[1]
    dfile = filelist[3]

    # read_from='imgview'
    # df_protocol=readprotocol(directory+'protocol1.txt')
    # df_bright=df_protocol[df_protocol.DarkBright=='B']
    # CCDitems=read_all_files_in_protocol(df_bright, read_from,directory)

    pic = np.float64(Image.open(directory + pfile + ".pnm"))  # read image
    picd = np.float64(Image.open(directory + dfile + ".pnm"))  # read image

    flatfield_w_baffle = pic - picd
    
    #Save these files to give to Jörg:
    #io.savemat('flatfield_wo_baffle_'+channel+'.mat', {'data': flatfield_wo_baffle})
    #io.savemat('flatfield_w_baffle_'+channel+'.mat', {'data': flatfield_w_baffle})
    

    # Scale flatfield without baffle so that the group of pixels that
    # are close to the main axis of the instrument gets the mean value of 1.
    # Since the poining axis has not yet been determined we for now scale
    # so that the avarage value of the entire flatfield is 1.

    flatfield_wo_baffle_scaled = flatfield_wo_baffle / np.mean(flatfield_wo_baffle)

    fig, ax = plt.subplots(8, 1, figsize=(5, 22))

    # Now scale the average of the middle part of the flatfield with baffle
    # to be the same as the average of flatfield_wo_baffle_scaled .

    # The values of the below shall be given by Jörgs lego analysis
    FirstRow = 100
    LastRow = 400
    FirstCol = 200
    LastCol = 1850

    # scale factor for making the mean of the baffle flatfield (in area) same as for the one without
    scale_fact = (
        flatfield_w_baffle[FirstRow:LastRow, FirstCol + 1 : LastCol + 1].mean()
        / flatfield_wo_baffle_scaled[
            FirstRow:LastRow, FirstCol + 1 : LastCol + 1
        ].mean()
    )
    flatfield_w_baffle_scaled = 1 / scale_fact * flatfield_w_baffle

    diff_field = flatfield_wo_baffle_scaled - flatfield_w_baffle_scaled
    diff_field_smooth = ndimage.gaussian_filter(
        diff_field, sigma=4
    )  # sigma = 4 pixels for gaussan smoothing kernel?

    # add baffle effects to flatfield without baffle except where the baffle has no impact (TBD)
    flatfield_morphed = flatfield_wo_baffle_scaled - diff_field_smooth
    flatfield_morphed[
        FirstRow:LastRow, FirstCol + 1 : LastCol + 1
    ] = flatfield_wo_baffle_scaled[FirstRow:LastRow, FirstCol + 1 : LastCol + 1]

    #
    flatfield_morphed_minus_wo_scaled = flatfield_morphed - flatfield_wo_baffle_scaled

    if plot:

        # Plotting limits
        fullpic = True
        if fullpic:
            xpmin = 0
            xpmax = flatfield_w_baffle.shape[1]
            ypmin = 0
            ypmax = flatfield_w_baffle.shape[0]
        else:
            xpmin = 1000
            xpmax = 1100
            ypmin = 300
            ypmax = 400

        plot_CCDimage(
            flatfield_wo_baffle[ypmin:ypmax, xpmin:xpmax],
            fig,
            ax[0],
            title="flatfield_wo_baffle",
        )
        plot_CCDimage(
            flatfield_wo_baffle_scaled[ypmin:ypmax, xpmin:xpmax],
            fig,
            ax[1],
            title="flatfield_wo_baffle_scaled",
        )
        plot_CCDimage(
            flatfield_w_baffle[ypmin:ypmax, xpmin:xpmax],
            fig,
            ax[2],
            title="flatfield_w_baffle",
        )
        plot_CCDimage(
            flatfield_w_baffle_scaled[ypmin:ypmax, xpmin:xpmax],
            fig,
            ax[3],
            title="flatfield_w_baffle_scaled",
        )
        plot_CCDimage(
            diff_field[ypmin:ypmax, xpmin:xpmax],
            fig,
            ax[4],
            clim=[-0.1, 0.1],
            title="difference in scaled flatf without and with baffle",
        )

        # diff_field_smooth= spline_filter(diff_field, lmbda=4.)
        plot_CCDimage(
            diff_field_smooth[ypmin:ypmax, xpmin:xpmax],
            fig,
            ax[5],
            clim=[-0.1, 0.1],
            title="smooth difference in scaled flatf without and with baffle",
        )

        plot_CCDimage(
            flatfield_morphed[ypmin:ypmax, xpmin:xpmax],
            fig,
            ax[6],
            title="morphed flatfield",
        )

        plot_CCDimage(
            flatfield_morphed_minus_wo_scaled[ypmin:ypmax, xpmin:xpmax],
            fig,
            ax[7],
            title="flatfield_morphed-flatfield_w_baffle_scaled",
        )

        # for myax in ax:

        #    myax.set_ylim((300,400))
        #    myax.set_xlim((1000,1100))
        #    myax.set_aspect('auto')

        fig.suptitle(channel+' '+signalmode)
        Path("output").mkdir(parents=True, exist_ok=True)
        fig.savefig("output/MorphedFlatfield_" + channel + ".jpg")

    return flatfield_morphed
