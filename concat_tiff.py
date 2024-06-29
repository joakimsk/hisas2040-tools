from PIL import Image
from pathlib import Path
import argparse

def concat_tiff(tiff_path):
    folder = Path(tiff_path)
    if not folder.is_dir():
        print(f"The provided path {tiff_path} is not a directory.")
        return

    #tiff_files = []

    tiff_files = sorted([file for file in folder.glob('*.tiff')], reverse=True)

    print(tiff_files)

    images = [Image.open(img) for img in tiff_files]
    print(images)
    
    total_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)
    concatenated_image = Image.new('RGB', (total_width, total_height))
    offset = 0

    for img in images:
        concatenated_image.paste(img, (0, offset))
        offset += img.height

    concatenated_image.save("concatenated.tiff")

def main(folder_path):
    folder = Path(folder_path)
    if not folder.is_dir():
        print(f"The provided path {folder_path} is not a directory.")
        return

    concat_tiff(folder_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process all files in a specified folder.')
    parser.add_argument('folder_path', default="tiffs", nargs='?', type=str, help='Path to the folder containing files to process.')
    args = parser.parse_args()
    
    main(args.folder_path)