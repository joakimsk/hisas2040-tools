import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
import argparse
import logging

from pyxtf import xtf_read, concatenate_channel, XTFHeaderType, XTFChannelType

def convert_xtf_tiff(file_path: str, output_folder_path: str, output_bitdepth: int, resize_half_width: bool, histogram_equalization: bool, column_threshold: int):
    filename = file_path.name # full filename
    file_stem = file_path.stem # only filename
    file_suffix = file_path.suffix # only extension

    starboard = False
    port = False

    # Read file header and packets
    (fh, p) = xtf_read(file_path)
    logging.info(fh)

    n_channels = fh.channel_count(verbose=True)
    #print('Number of data channels: {}\n'.format(n_channels))
    actual_chan_info = [fh.ChanInfo[i] for i in range(0, n_channels)]
    logging.info(actual_chan_info)

    if n_channels != 1:
        exit("Converting only implemented for single channel XTF, you have", n_channels)

    logging.info(f'Channels found in file: {n_channels}')

    packets_in_file = str([key.name + ':{}'.format(len(v)) for key, v in p.items()])
    print(f'Packets found in file: {packets_in_file}')

    chan_type = fh.ChanInfo[0].TypeOfChannel
    if chan_type == XTFChannelType.stbd:
        print("XTF Channel is Starboard")
        starboard = True
    elif chan_type == XTFChannelType.port:
        print("XTF Channel is Port")
        port = True
    else:
        exit("Unknown XTF channel type")

    # Get sonar if present
    if XTFHeaderType.sonar in p:
        upper_limit = 2 ** 16

        logging.info(f"Concatenating pings in channel")
        np_chan = concatenate_channel(p[XTFHeaderType.sonar], file_header=fh, channel=0, weighted=True)

        #for ping in p[XTFHeaderType.sonar]:
            #print(ping)
            #print(ping.ping_chan_headers[0])
            #print(ping.SlantRange, ping.GroundRange)
        #    primary_altitude = ping.SensorPrimaryAltitude
        #    calculated_altitude = np.sqrt(np.square(ping.ping_chan_headers[0].SlantRange) - np.square(ping.ping_chan_headers[0].GroundRange))
        #    #print("Detaalt", primary_altitude-calculated_altitude)
            #print(ping.XTFPingChanHeader)
        #    print(ping.SensorYcoordinate, ping.SensorXcoordinate, ping.PingNumber, ping.SoundVelocity)
        #print(fh.NavUnits, fh.NavigationLatency)
        #print("VoltScale", fh.ChanInfo[0].VoltScale, "Frequency", fh.ChanInfo[0].Frequency, "SampleFormat", fh.ChanInfo[0].SampleFormat)
        #print()
     
        #exit()
        np.set_printoptions(threshold=np.inf, linewidth=200, precision=3, formatter={'float': '{:,.0f}'.format}, suppress=True)  # Ensure entire array is displayed
        
        print("Columns before cleanup:", np_chan.shape[1])

        # Start cutting columns where average value is below column_threshold, used to remove black sides
        average_along_columns = np.mean(np_chan, axis=0)
        empty_columns = np.where(average_along_columns < column_threshold)[0]

        logging.info(f"Removing {len(empty_columns)} columns with value below column_threshold={column_threshold}")
        np_chan = np.delete(np_chan, empty_columns, axis=1)
        
        print("Columns after cleanup:", np_chan.shape[1])

        # Clip to range (max cannot be used due to outliers)
        # More robust methods are possible (through histograms / statistical outlier removal)
        np_chan.clip(0, upper_limit - 1, out=np_chan)
        
        # The sonar data is logarithmic (dB), add small value to avoid log10(0)
        np_chan = np.log10(np_chan + 1, dtype=np.float32)

        # Need to find minimum and maximum value for scaling
        vmin = np_chan.min()
        vmax = np_chan.max()

        print("Values before scaling; min, vmax", vmin, vmax)
        
        # Scaling values to fit datatype uint16
        np_chan = ((np_chan - vmin) / (vmax - vmin)) * 65535
        np_chan = np.clip(np_chan, 0, 65535)

        if histogram_equalization:
            #np_chan = cv2.equalizeHist(np_chan)
            hist, bins = np.histogram(np_chan.flatten(), bins=65536, range=(0, 65536))
            cdf = hist.cumsum()
            cdf_normalized = cdf / cdf.max()  # Normalize CDF
            equalized_img = np.interp(np_chan.flatten(), bins[:-1], cdf_normalized * 65535).astype(np.uint16)
            np_chan = equalized_img.reshape(np_chan.shape)

        # Resample as necessary after histogram equalization, it is already in uin16

        vmin = np_chan.min()
        vmax = np_chan.max()

        print("Values before saving; min, vmax", vmin, vmax)

        img = None

        if output_bitdepth == 8: # Scaling values to fit datatype uint8
            np_chan = ((np_chan - vmin) / (vmax - vmin)) * 255
            np_chan = np.clip(np_chan, 0, 255)
            img = Image.fromarray(np_chan.astype(np.uint8))

        elif output_bitdepth == 16: # Scaling values to fit datatype uint16
            #np_chan = ((np_chan - vmin) / (vmax - vmin)) * 65535
            #np_chan = np.clip(np_chan, 0, 65535)
            img = Image.fromarray(np_chan.astype(np.uint16))

        else:
            exit("Invalid requested bit depth")

        print("resize_half_width", resize_half_width)
        if resize_half_width:
            print("Half width resize")
            img = img.resize((int(img.size[0]/2), img.size[1]), Image.Resampling.LANCZOS)

        output_filename = f'{file_stem}.tiff'
        output_folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Saving file {output_folder_path / output_filename}, width {img.size[0]}, height {img.size[1]}")
        img.save(output_folder_path / output_filename)

def main(args):

    arg_input = args.input
    arg_output = args.output
    arg_bitdepth = args.bitdepth
    arg_column_threshold = args.column_threshold

    arg_resize_half_width = None

    if args.resize_half_width:
        arg_resize_half_width = True
    else:
        arg_resize_half_width = False
    
    arg_histogram_equalization = None
    if args.histogram_equalization:
        arg_histogram_equalization = True
    else:
        arg_histogram_equalization = False
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)  # Set the logging level to DEBUG

    input_folder = Path(arg_input)
    output_folder = Path(arg_output)

    if not input_folder.is_dir():
        print(f"The provided path {input_folder} is not a directory.")
        return

    for file_path in input_folder.iterdir():
        #logging.info(f"Processing file: {file_path}")
        if file_path.is_file():
            print(f"Processing file: {file_path}")
            convert_xtf_tiff(file_path=file_path, output_folder_path=output_folder, output_bitdepth=arg_bitdepth, resize_half_width=arg_resize_half_width, histogram_equalization=arg_histogram_equalization, column_threshold=arg_column_threshold)
            print("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert all .xtf files to .tiff in a specified folder.')
    parser.add_argument('-i', '--input', default="xtfs", type=str, help='Input folder.')
    parser.add_argument('-o', '--output', default="tiffs", type=str, help='Output folder.')
    parser.add_argument('-b', '--bitdepth', choices=[8,16], default=8, type=int, help='Bitdepth of output image, must be of the allowed values: 8 (default), 16.')
    parser.add_argument('-rhw', '--resize_half_width', default=True, action='store_true', help='Resize to half width. (default True)')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose mode.')
    parser.add_argument('-heq', '--histogram_equalization', default=False, action='store_true', help='Histogram equalization. (default False)')
    parser.add_argument('-cth', '--column_threshold', default=7, type=int, help='Column threshold, avg col val to cut from data. Typical 0 to 7 (default). Set to -1 to disable')
    args = parser.parse_args()
    
    main(args)