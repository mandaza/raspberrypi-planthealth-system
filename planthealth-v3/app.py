import cv2
import os
import numpy as np
from fastiecm import fastiecm
from picamera2 import Picamera2
from PIL import Image
import adafruit_dht
import telepot
from telepot.loop import MessageLoop
import board

# Inital dht device
sensor = adafruit_dht.DHT11(board.D26)

# Telegram Bot Token from BotFather
TELEGRAM_BOT_TOKEN = '8038657874:AAHsc6_5FgFqz27pfCkaHmmOG9Fpov8wFjg'

# Ensure the 'images' directory exists
if not os.path.exists('images'):
    os.makedirs('images')
    print("'images' directory created")

# Function for contrast stretching
def contrast_stretch(im):
    in_min = np.percentile(im, 5)
    in_maxe = np.percentile(im, 95)
    
    out_min = 0.0
    out_max = 255.0
    
    out = im - in_min
    out *= ((out_max - out_min) / (in_maxe - in_min))
    out += out_min
    
    return out.astype(np.uint8)

# Function to calculate NDVI
def calc_ndvi(image):
    print("Calculating NDVI...")
    b, g, r = cv2.split(image)  # Split image into blue, green, and red channels
    bottom = (r.astype(float) + b.astype(float))
    bottom[bottom == 0] = 0.01  # Avoid division by zero
    ndvi = (b.astype(float) - r) / bottom  # NDVI calculation (NIR approximation as blue)
    print("NDVI calculated.")
    return ndvi

# Function to classify plant health based on NDVI values
def classify_plant_health(ndvi_image):
    ndvi_flat = ndvi_image.flatten()
    avg_ndvi = np.mean(ndvi_flat)
    print(f"Average NDVI: {avg_ndvi}")

    if avg_ndvi >= 0.6:
        return "Healthy"
    elif 0.2 <= avg_ndvi < 0.6:
        return "Stressed"
    else:
        return "Dead or Bare Soil"

# Function to save the processed image as PNG
def save_image_as_png(ndvi_image, filename):
    try:
        print(f"Saving image as {filename}...")
        image_pillow = Image.fromarray(ndvi_image)
        image_pillow.save(filename, "PNG")
        print(f"Image successfully saved as {filename}.")
    except Exception as e:
        print(f"Error saving image: {e}")

# Function to capture the image and process it
def capture_and_process():
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
    contrasted = contrast_stretch(original)

    # Calculate NDVI from the contrasted image
    ndvi = calc_ndvi(contrasted)
    
    # Contrast stretch the NDVI image
    ndvi_contrasted = contrast_stretch(ndvi)
    
    # Apply color mapping using fastiecm
    color_mapped_prep = ndvi_contrasted.astype(np.uint8)
    color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm)
    
    # Save the NDVI image to the 'images' directory as PNG
    image_dir = os.path.abspath('images')
    image_count = len(os.listdir(image_dir))
    image_filename = os.path.join(image_dir, f'ndvi_image_{image_count + 1}.png')
    save_image_as_png(color_mapped_image, image_filename)

    # Classify plant health based on NDVI values
    health_status = classify_plant_health(ndvi_contrasted)
    
    # Stop the camera after processing
    cam.stop()

    return health_status, image_filename

# ReadTemperature
def read_temp():
    temp = sensor.temperature
    print(f'Temperature {temp:.1f}C')
    return temp

# ReadHumidity
def read_Humid():
    humid = sensor.humidity
    print(f'Humidity: {humid:.1f}%')
    return humid

# Function to handle messages from Telegram
def handle_message(msg):
    chat_id = msg['chat']['id']
    command = msg['text']

    if command == '/start':
        bot.sendMessage(chat_id, "Welcome to Plant Health Bot! \n Use /NDVI to capture the plant and get its NDVI health status.\n Use /temperature to read temperature. \n Use /humidity to read humidity.")
    
    elif command == '/NDVI':
        # Capture the plant's image, process it, and get the NDVI health status
        health_status, image_path = capture_and_process()

        # Send the plant health status to the user
        bot.sendMessage(chat_id, f"Plant Health Status: {health_status}")

        # Send the NDVI image back to the user
        bot.sendPhoto(chat_id, open(image_path, 'rb'))
    elif command == '/temperature':
        # Get temperature
        temperature = read_temp()
        if temperature is not None:
            bot.sendMessage(chat_id, f"Current Temperature: {temperature}C")
        else:
            bot.sendMessage(chat_id, 'Error reading temperature!')
    elif command == '/humidity':
        # Get humidity
        humidity = read_Humid()
        if humidity is not None:
            bot.sendMessage(chat_id,f"Current Humidity: {humidity}%")
        else:
            bot.sendMessage(chat_id,'Error reading humidity!')

# Initialize the Telegram bot
bot = telepot.Bot(TELEGRAM_BOT_TOKEN)
MessageLoop(bot, handle_message).run_as_thread()

print('Listening for commands...')

# Keep the program running
while True:
    pass

