import cv2
import os
import numpy as np
from fastiecm import fastiecm
from picamera2 import Picamera2
from gpiozero import Button
from PIL import Image
from RPLCD.i2c import CharLCD

lcd = CharLCD(i2c_expander='PCF8574', address= 0x27, port=1, cols=16, rows=2, dotsize=8)
lcd.clear()

# Ensure the 'images' directory exists
if not os.path.exists('images'):
    os.makedirs('images')
    
# Function for contrast stretching
def contrast_stretch(im):
    in_min = np.percentile(im, 5)
    in_max = np.percentile(im, 95)
    
    out_min = 0.0
    out_max = 255.0
    
    out = im - in_min
    out *= ((out_max - out_min) / (in_max - in_min))
    out += out_min
    
    return out.astype(np.uint8)

# Function to calculate NDVI
def calc_ndvi(image):
    b, g, r = cv2.split(image)  # Split image into blue, green, and red channels
    bottom = (r.astype(float) + b.astype(float))
    bottom[bottom == 0] = 0.01  # Avoid division by zero
    ndvi = (b.astype(float) - r) / bottom  # NDVI calculation (NIR approximation as blue)
    return ndvi

def classify_plant_health(ndvi_image):
    ndvi_flat = ndvi_image.flatten()
    
    avg_ndvi = np.mean(ndvi_flat)
    print(f'Average NDVI:{avg_ndvi}')
    
    if avg_ndvi >= 0.6:
        return 'Healthy'
    elif 0.2 <= avg_ndvi < 0.6:
        return 'Stressed'
    else:
        return 'Dead'
    
    

# Function to save the processed image
def save_image(ndvi_image, filename):
    try:
        print(f'Saving image as {filename}...')
        image_pillow = Image.fromarray(ndvi_image)
        image_pillow.save(filename, 'PNG')
        print(f'Image successfully saved as {filename}.')
    except Exception as e:
        print(f'Error while saving image: {e}')

# Function to capture the image and process it
def capture_and_process(cam):
    lcd.clear()
    lcd.write_string('Capturing image..')
    print("Capturing image...")
    
    # Capture the original image
    original = cam.capture_array()
    
    # Contrast stretch the captured image
    contrasted = contrast_stretch(original)

    # Calculate NDVI from the contrasted image
    ndvi = calc_ndvi(contrasted)
    
    # Contrast stretch the NDVI image
    ndvi_contrasted = contrast_stretch(ndvi)
    
    # Apply color mapping using fastiecm
    color_mapped_prep = ndvi_contrasted.astype(np.uint8)
    
    color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm)
    
    # Save the NDVI image to the 'images' directory
    image_dir = os.path.abspath('images')
    image_count = len(os.listdir(image_dir))
    image_filename = os.path.join(image_dir, f'ndvi_image_{image_count + 1}.png')
    save_image(color_mapped_image, image_filename)
    
    health_status = classify_plant_health(color_mapped_image)
    lcd.clear()
    lcd.write_string(f'Status: {health_status}')
    print(f'Plant Health Status: {health_status}')
    
    

# Main function to initialize the camera and button, and handle the process
def main():
    # Initialize camera and button
    cam = Picamera2()
    button = Button(16)
    config = cam.create_still_configuration()
    cam.configure(config)
    cam.start()

    # Bind button press to capture and process image
    button.when_pressed = lambda: capture_and_process(cam)

    # Keep the program running to listen for button presses
    lcd.write_string('Waiting for button press.....')
    print("Waiting for button press...")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        cam.stop()
        print("Camera stopped.")

# Run the main function
if __name__ == "__main__":
    main()
