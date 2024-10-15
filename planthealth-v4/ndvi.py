import cv2
import os
import numpy as np
from fastiecm import fastiecm
from picamera2 import Picamera2
from PIL import Image

class NDVI:
    def __init__(self):
        # Ensure the 'images' directory exists
        if not os.path.exists('images'):
            os.makedirs('images')

    def contrast_stretch(self, im):
        in_min = np.percentile(im, 5)
        in_maxe = np.percentile(im, 95)

        out_min = 0.0
        out_max = 255.0

        out = im - in_min
        out *= ((out_max - out_min) / (in_maxe - in_min))
        out += out_min

        return out.astype(np.uint8)

    def calc_ndvi(self, image):
        print("Calculating NDVI...")
        b, g, r = cv2.split(image)  # Split image into blue, green, and red channels
        bottom = (r.astype(float) + b.astype(float))
        bottom[bottom == 0] = 0.01  # Avoid division by zero
        ndvi = (b.astype(float) - r) / bottom  # NDVI calculation (NIR approximation as blue)
        print("NDVI calculated.")
        return ndvi

    def classify_plant_health(self, ndvi_image):
        ndvi_flat = ndvi_image.flatten()
        avg_ndvi = np.mean(ndvi_flat)
        print(f"Average NDVI: {avg_ndvi}")

        if avg_ndvi >= 0.6:
            return "Healthy"
        elif 0.2 <= avg_ndvi < 0.6:
            return "Stressed"
        else:
            return "Dead or Bare Soil"

    def capture_and_process(self):
        print("Capturing image...")

        # Initialize camera
        cam = Picamera2()
        config = cam.create_still_configuration()
        cam.configure(config)
        cam.start()

        # Capture the original image
        original = cam.capture_array()
        print("Image captured.")

        # Contrast stretch the captured image
        contrasted = self.contrast_stretch(original)

        # Calculate NDVI from the contrasted image
        ndvi = self.calc_ndvi(contrasted)

        # Contrast stretch the NDVI image
        ndvi_contrasted = self.contrast_stretch(ndvi)

        # Apply color mapping using fastiecm
        color_mapped_prep = ndvi_contrasted.astype(np.uint8)
        color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm)

        # Save the NDVI image to the 'images' directory as PNG
        image_dir = os.path.abspath('images')
        image_count = len(os.listdir(image_dir))
        image_filename = os.path.join(image_dir, f'ndvi_image_{image_count + 1}.png')
        self.save_image_as_png(color_mapped_image, image_filename)

        # Classify plant health based on NDVI values
        health_status = self.classify_plant_health(ndvi_contrasted)

        # Stop the camera after processing
        cam.stop()

        return health_status, image_filename

    def save_image_as_png(self, ndvi_image, filename):
        try:
            print(f"Saving image as {filename}...")
            image_pillow = Image.fromarray(ndvi_image)
            image_pillow.save(filename, "PNG")
            print(f"Image successfully saved as {filename}.")
        except Exception as e:
            print(f"Error saving image: {e}")
