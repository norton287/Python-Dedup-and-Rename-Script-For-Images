# Image Deduplication and Renaming Script

This script is designed to identify and remove duplicate images in a specified directory based on content similarity, and then rename the remaining images to a standardized format. It uses OpenCV for image processing and the `scikit-image` library to compare image similarity.

## Features
- Traverse a specified directory and list all image files.
- Compare images based on both filename and pixel-wise content.
- Handle different image orientations.
- Remove the lower resolution duplicate when duplicates are found.
- Rename all images to the format `image-%timestamp%.%OriginalImageExtension%`.
- Perform a sanity check to ensure all images follow the naming convention.
- Log each step of the process to `/var/log/dedupe.log`.

## Requirements
- Python 3.x
- OpenCV
- `scikit-image`

## Setup

1. **Install the required libraries:**

    ```bash
    pip install opencv-python-headless scikit-image
    ```

2. **Download the script:**

    Save the script to a file, for example, `dedupe_and_rename.py`.

3. **Place the script in `/usr/bin` directory:**

    ```bash
    sudo mv dedupe_and_rename.py /usr/bin/dedupe_and_rename
    ```

4. **Make the script executable:**

    ```bash
    sudo chmod +x /usr/bin/dedupe_and_rename
    ```

## Usage

Once the script is set up, you can run it from anywhere on your system by calling `dedupe_and_rename`.

dedupe_and_rename
Ensure you update the directory variable in the script with the path to your image directory before running the script.

## Logging
** The script logs all its operations to /var/log/dedupe.log. You can check this log file for detailed information about the script's actions and any errors encountered.

### Detailed Explanation
## list_images(directory, extensions):
** Traverses the directory and lists all image files with the given extensions.

## load_image(path):
** Loads an image from the specified file path using OpenCV.

## rotate_image(image, angle):
** Rotates an image by the specified angle (0, 90, 180, 270 degrees).

## image_similarity(img1, img2):
** Computes the structural similarity index between two images to determine how similar they are.

## compare_images_with_orientations(img1, img2):
** Compares images in all orientations to find the highest similarity.

## compare_and_remove_duplicates(images):
** Compares each image with every other image in the list, and removes the lower resolution duplicate if they are similar.

## generate_unique_filename(directory, file_extension):
** Generates a unique filename using the current timestamp and checks for collisions.

## rename_images(directory, extensions):
** Renames all images in the directory to the format image-%timestamp%.%originalImageExtension%.

## sanity_check(directory, extensions):
** Ensures all filenames follow the naming convention and handles renaming again if necessary.

### Example
## Modify the main function in the script to specify your directory:

```python
def main():
    directory = "path/to/your/image/directory"
    extensions = (".png", ".jpg", ".jpeg", ".bmp")
    logging.info(f"Starting duplicate removal in directory: {directory}")
    images = list_images(directory, extensions)
    logging.info(f"Found {len(images)} images to process")
    compare_and_remove_duplicates(images)
    logging.info("Duplicate removal process completed")
    logging.info("Starting renaming process")
    rename_images(directory, extensions)
    logging.info("Renaming process completed")
    logging.info("Starting sanity check process")
    sanity_check(directory, extensions)
    logging.info("Sanity check process completed")

if __name__ == "__main__":
    main()
```

## Replace "path/to/your/image/directory" with the actual path to your directory containing images.
