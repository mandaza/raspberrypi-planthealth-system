import BlynkLib
import time
from ndvi import NDVI
from weather import Weather
from BlynkTimer import BlynkTimer

# Blynk Auth Token (replace with your own token)
BLYNK_AUTH = 'U5t0cS_zkxitwY-n_tZUl1fc66fG76XM'


# Initialize Blynk
blynk = BlynkLib.Blynk(BLYNK_AUTH)

timer = BlynkTimer()

# Initialize NDVI and Weather classes
ndvi_processor = NDVI()
weather_monitor = Weather()

# Virtual Pins

VIRTUAL_PIN_HUMID = 0 # Blynk Virtual Pin for Humidity
VIRTUAL_PIN_TEMP = 1  # Blynk Virtual Pin for Temperature
VIRTUAL_PIN_STATUS = 2 # Blynk Virtual Pin for Health Status
VIRTUAL_PIN_BUTTON = 4

# Capture NDVI and send to Blynk
def send_ndvi_to_blynk():
    health_status, _ = ndvi_processor.capture_and_process()
    
    # Update Blynk virtual pins with NDVI and Health status
    #blynk.virtual_write(VIRTUAL_PIN_NDVI, health_status)
    blynk.virtual_write(VIRTUAL_PIN_STATUS, health_status)
    

@blynk.on('V4')
def blynk_button(value):
    if int(value[0]) == 1:
        send_ndvi_to_blynk()
        

# Send temperature and humidity to Blynk
def send_temp_and_humidity():
    temperature = weather_monitor.read_temperature()
    print(f'Temp: {temperature}C')
    humidity = weather_monitor.read_humidity()
    print(f'Humidity: {humidity}%')
    
    blynk.virtual_write(VIRTUAL_PIN_TEMP, temperature)
    blynk.virtual_write(VIRTUAL_PIN_HUMID, humidity)
  
   

# Blynk timer to periodically send data
def update_blynk():
    timer.set_interval(2,send_temp_and_humidity)
    while True:
        #send_ndvi_to_blynk()
        #send_temp_and_humidity_to_blynk()
        blynk.run()
        timer.run()
       

if __name__ == '__main__':
    print("Blynk integration running...")
    update_blynk()



