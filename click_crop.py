import cv2
import numpy as np

square_size = 100 # pixels square
no_roi = 1

def click_and_crop(event, x, y, flags, param):
    global image, square_size, no_roi

    if event == cv2.EVENT_LBUTTONDOWN:
        # Calculate the top-left and bottom-right points of the square
        top_left = (max(x - square_size // 2, 0), max(y - square_size // 2, 0))
        bottom_right = (min(x + square_size // 2, image.shape[1]), min(y + square_size // 2, image.shape[0]))

        # Draw a rectangle around the selected region
        cv2.rectangle(image, top_left, bottom_right, (0, 0, 255), 2)
        label = f"{no_roi}"
        cv2.putText(image, label, (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.imshow("image", image)

        # Extract the region of interest
        roi = None
        roi = clone[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        #cv2.imshow("ROI", roi)
        print("saving roi", no_roi)
        cv2.imwrite(f"roi_{no_roi}.png", roi)
        no_roi += 1
        

# Load the image, clone it, and setup the mouse callback function
image = cv2.imread('tiffs\sasi-P-upper-20240314-110550-wrk_l1.tiff')
height, width, channels = image.shape

# If we resize the image, we lose fidelity. We should use the coordinates from the scaled image, to get the full resolution image.
# Work to do.
#image = cv2.resize(image, (int(width/3), int(height/3) ))
clone = image.copy()
cv2.namedWindow("image")
cv2.setMouseCallback("image", click_and_crop)

print("Press keyboard q to quit.")

while True:
    # Display the image and wait for a key press
    cv2.imshow("image", image)
    key = cv2.waitKey(1) & 0xFF

    # Press 'q' to break from the loop
    if key == ord("q"):
        break

# Close all open windows
cv2.destroyAllWindows()