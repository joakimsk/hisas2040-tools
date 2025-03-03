import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk
from pathlib import Path
import csv

class ImageApp:
    def __init__(self, root, image_path):
        self.root = root
        self.root.title("Click and crop image")

        self.no_roi = 1
        self.x = 0
        self.y = 0
        self.image_path = Path(image_path)

        self.csv_filename = f"roi_{self.image_path.stem}.csv"

        self.square_sizes = [50, 100, 150, 200, 250, 300, 500, 1000]  # List of square sizes
        self.square_size_index = 1  # Initial index
        self.square_size = self.square_sizes[self.square_size_index]  # Initial square size

        self.target_description = ""  # Initialize target description

        # Load the image using OpenCV
        self.img = cv2.imread(self.image_path)
        if self.img is None:
            raise ValueError("Image not found or path is incorrect")

        self.display_img = self.img.copy()

        # Convert image to PIL format
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)))

        # Create a Canvas
        self.canvas = tk.Canvas(root, width=self.img.shape[1], height=self.img.shape[0])
        self.canvas.pack()

        # Add image to canvas
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Bind mouse click event
        self.canvas.bind("<Button-1>", self.draw_target)
        self.canvas.bind("<Motion>", self.show_crop_box)
        self.canvas.bind("<MouseWheel>", self.change_box_size)
        self.initialize_csv()

    def change_box_size(self, event):
        if event.delta > 0:
            self.square_size_index = (self.square_size_index + 1) % len(self.square_sizes)
        elif event.delta < 0:
            self.square_size_index = (self.square_size_index - 1) % len(self.square_sizes)

        self.square_size = self.square_sizes[self.square_size_index]
        print(f"Square size changed to: {self.square_size}")
        self.show_crop_box(event)

    def show_crop_box(self, event):
        x, y = event.x, event.y

        # Copy the original image to display image
        self.display_img = self.img.copy()

        self.top_left = (max(x - self.square_size // 2, 0), max(y - self.square_size // 2, 0))
        self.bottom_right = (min(x + self.square_size // 2, self.img.shape[1]), min(y + self.square_size // 2, self.img.shape[0]))

        # Draw a rectangle representing the cropping box
        cv2.rectangle(self.display_img, self.top_left, self.bottom_right, (255, 0, 0), 2)

        cm_per_pixel = 2*0.9030351932265315 # *2 for halfed aspect ratio
        print(self.img.shape[0])
        label = f"{self.square_size}x{self.square_size} - c{x},{y} - {cm_per_pixel*x/100:.2f}m"
        cv2.putText(self.display_img, label, (self.top_left[0], self.top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Update the image on the canvas
        self.update_image()

    def draw_target(self, event):
        # Get the coordinates of the mouse click
        self.x, self.y = event.x, event.y
        # Draw a circle on the OpenCV image

        # Calculate the top-left and bottom-right points of the square
        self.top_left = (max(self.x - self.square_size // 2, 0), max(self.y - self.square_size // 2, 0))
        self.bottom_right = (min(self.x + self.square_size // 2, self.img.shape[1]), min(self.y + self.square_size // 2, self.img.shape[0]))

        # Draw a rectangle around the selected region
        cv2.rectangle(self.img, self.top_left, self.bottom_right, (0, 0, 255), 2)
        label = f"{self.no_roi}"

        cv2.putText(self.img, label, (self.top_left[0], self.top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        roi = None
        roi = self.img[self.top_left[1]:self.bottom_right[1], self.top_left[0]:self.bottom_right[0]]

        print("Saving roi", self.no_roi)

        self.target_description = simpledialog.askstring("Target Description", "Enter target description:")

        output_folder = Path("roi")
        output_folder.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(output_folder / f"roi_{self.no_roi}.tiff", roi)
        self.no_roi = self.no_roi + 1
        
        self.write_to_csv()
        # Update the image on the canvas
        self.update_image()

    def initialize_csv(self):
        # Create or append to the CSV file with headers if it doesn't exist
        with open(self.csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            if file.tell() == 0:  # Check if file is empty
                writer.writerow(['filename', 'no_roi', 'center', 'topleft', 'bottomright', 'Description'])

    def update_image(self):
        # Convert the updated OpenCV image to PIL format
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(self.display_img, cv2.COLOR_BGR2RGB)))
        # Update the canvas image
        self.canvas.itemconfig(self.image_on_canvas, image=self.photo)

    def write_to_csv(self):
        # Append data to CSV file
        with open(self.csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self.image_path, self.no_roi, f"{self.x}_{self.y}", self.top_left, self.bottom_right, self.target_description])

def main():
    root = tk.Tk()

    # Open a file dialog to choose an image file
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.tiff"), ("All files", "*.*")]
    )
    if not file_path:
        print("No file selected. Exiting.")
        return

    app = ImageApp(root, file_path)
    root.mainloop()

if __name__ == "__main__":
    main()
