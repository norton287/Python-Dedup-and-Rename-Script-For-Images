#!/usr/bin/python3
import os
import cv2
import logging
import time
import gzip
import shutil
from datetime import datetime, timedelta
from skimage.metrics import structural_similarity as ssim

# Configure logging
log_file = "/var/log/dedupe.log"
logging.basicConfig(filename=log_file, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def list_images(directory, extensions):
    """List all images in the directory with given extensions."""
    images = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(extensions):
                images.append(os.path.join(root, file))
    return images

def load_image(path):
    """Load an image from a file path."""
    try:
        return cv2.imread(path)
    except Exception as e:
        logging.error(f"Error loading image {path}: {e}")
        return None

def rotate_image(image, angle):
    """Rotate an image by the given angle."""
    if angle == 0:
        return image
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1)
    return cv2.warpAffine(image, matrix, (width, height))

def image_similarity(img1, img2):
    """Compute the structural similarity between two images."""
    if img1.shape != img2.shape:
        return 0
    gray_img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray_img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    similarity, _ = ssim(gray_img1, gray_img2, full=True)
    return similarity

def compare_images_with_orientations(img1, img2):
    """Compare images in all orientations to find the highest similarity."""
    angles = [0, 90, 180, 270]
    max_similarity = 0
    for angle in angles:
        rotated_img2 = rotate_image(img2, angle)
        similarity = image_similarity(img1, rotated_img2)
        max_similarity = max(max_similarity, similarity)
    return max_similarity

def compare_and_remove_duplicates(images):
    """Compare images and remove the lower resolution duplicates."""
    checked = set()
    for i in range(len(images)):
        img1_path = images[i]
        if img1_path in checked:
            continue
        img1 = load_image(img1_path)
        if img1 is None:
            continue
        for j in range(i + 1, len(images)):
            img2_path = images[j]
            if img2_path in checked:
                continue
            img2 = load_image(img2_path)
            if img2 is None:
                continue
            similarity = compare_images_with_orientations(img1, img2)
            if similarity > 0.95:  # Assuming a high similarity threshold
                resolution1 = img1.shape[0] * img1.shape[1]
                resolution2 = img2.shape[0] * img2.shape[1]
                if resolution1 >= resolution2:
                    logging.info(f"Deleting {img2_path} (resolution: {resolution2}) as duplicate of {img1_path} (resolution: {resolution1})")
                    try:
                        os.remove(img2_path)
                    except Exception as e:
                        logging.error(f"Error deleting file {img2_path}: {e}")
                    checked.add(img2_path)
                else:
                    logging.info(f"Deleting {img1_path} (resolution: {resolution1}) as duplicate of {img2_path} (resolution: {resolution2})")
                    try:
                        os.remove(img1_path)
                    except Exception as e:
                        logging.error(f"Error deleting file {img1_path}: {e}")
                    checked.add(img1_path)
                    break  # img1 is deleted, no need to compare further
        checked.add(img1_path)

def generate_unique_filename(directory, file_extension):
    """Generate a unique filename using the current timestamp."""
    while True:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        new_filename = f"image-{timestamp}.{file_extension}"
        new_path = os.path.join(directory, new_filename)
        if not os.path.exists(new_path):
            return new_path
        # Sleep a bit to avoid timestamp collision
        time.sleep(0.1)

def rename_images(directory, extensions):
    """Rename all images in the directory to the format 'image-%timestamp%.%originalImageExtension%'."""
    images = list_images(directory, extensions)
    for image_path in images:
        dir_path, filename = os.path.split(image_path)
        file_extension = filename.split('.')[-1]
        try:
            new_path = generate_unique_filename(dir_path, file_extension)
            os.rename(image_path, new_path)
            logging.info(f"Renamed {image_path} to {new_path}")
        except Exception as e:
            logging.error(f"Error renaming file {image_path} to {new_path}: {e}")

def sanity_check(directory, extensions):
    """Sanity check to ensure all filenames follow the naming convention."""
    images = list_images(directory, extensions)
    for image_path in images:
        filename = os.path.basename(image_path)
        if not filename.startswith("image-") or not filename.endswith(tuple(extensions)):
            logging.warning(f"File {image_path} does not follow naming convention")
            # Handle renaming again
            dir_path, file_extension = os.path.split(image_path)
            try:
                new_path = generate_unique_filename(dir_path, file_extension)
                os.rename(image_path, new_path)
                logging.info(f"Renamed {image_path} to {new_path} during sanity check")
            except Exception as e:
                logging.error(f"Error renaming file {image_path} during sanity check: {e}")

def handle_log_file():
    """Check the log file size and compress if over 1MB, also clean up old gzipped logs."""
    if os.path.exists(log_file) and os.path.getsize(log_file) > 1 * 1024 * 1024:  # 1MB
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        gzip_filename = f"/var/log/dedupe-{timestamp}.gz"
        with open(log_file, 'rb') as f_in, gzip.open(gzip_filename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(log_file)
        open(log_file, 'a').close()
        os.chmod(log_file, 0o644)
        logging.info(f"Compressed log file to {gzip_filename}")

    cutoff_date = datetime.now() - timedelta(days=10)
    for root, _, files in os.walk('/var/log'):
        for file in files:
            if file.startswith('dedupe-') and file.endswith('.gz'):
                file_path = os.path.join(root, file)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    logging.info(f"Removed old log file {file_path}")

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
    logging.info("Handling log file")
    handle_log_file()

if __name__ == "__main__":
    main()
