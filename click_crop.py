import argparse
import numpy as np
from pathlib import Path
import cv2

square_size = 100 # pixels square
no_roi = 1
image = None
input_file = None
output_folder = None

def click_and_crop(event, x, y, flags, param):
    global image, square_size, no_roi, clone, input_file, output_folder
    print(x,y)
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"ROI trigger")
        # Calculate the top-left and bottom-right points of the square
        top_left = (max(x - square_size // 2, 0), max(y - square_size // 2, 0))
        bottom_right = (min(x + square_size // 2, image.shape[1]), min(y + square_size // 2, image.shape[0]))

        # Draw a rectangle around the selected region
        cv2.rectangle(image, top_left, bottom_right, (0, 0, 255), 2)
        label = f"{no_roi}"
        cv2.putText(image, label, (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.imshow(f'{input_file}', image)

        # Extract the region of interest
        roi = None
        roi = clone[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        #cv2.imshow("ROI", roi)
        print("saving roi", no_roi)

        output_folder.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(output_folder / f"roi_{no_roi}.tiff", roi)
        no_roi = no_roi + 1

def main(args):
    global image, clone, input_file, output_folder

    arg_input = args.input_image
    arg_output = args.output_folder

    input_file = Path(arg_input)
    if not input_file.is_file():
        print(f"The provided file {arg_input} is not an image.")
        return

    output_folder = Path(arg_output)

    file_name = input_file.stem
    file_extension = input_file.suffix

    # Load the image, clone it, and setup the mouse callback function
    image = cv2.imread(input_file)
    
    height, width, channels = image.shape
    datatype = image.dtype

    print(f"Loaded image {input_file}, height x width = {height}x{width} datatype {datatype}, {channels} channel(s)")

    # If we resize the image, we lose fidelity. We should use the coordinates from the scaled image, to get the full resolution image.
    # Work to do.
    #image = cv2.resize(image, (int(width/3), int(height/3) ))
    clone = image.copy()
    cv2.namedWindow(f'{input_file}')
    cv2.setMouseCallback(f'{input_file}', click_and_crop)

    while True: # Display image and wait for Q
        cv2.imshow(f'{input_file}', image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Open image (.tiff/.png) for region of interest cropping.')
    parser.add_argument('-i', '--input_image', default="tiffs/sasi-P-upper-20240314-110520-wrk_l1.tiff",required=False, type=str, help='Input file.')
    parser.add_argument('-o', '--output_folder', default="roi", type=str, help='Output folder.')
    args = parser.parse_args()
    print("Press keyboard q to quit.")
    main(args)