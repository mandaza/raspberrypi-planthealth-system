import adafruit_dht
import board

class Weather:
    def __init__(self):
        # Initialize the DHT sensor
        self.sensor = adafruit_dht.DHT11(board.D26)

    def read_temperature(self):
        try:
            temp = self.sensor.temperature
            
            return temp
        except RuntimeError as error:
        
            return None

    def read_humidity(self):
        try:
            humidity = self.sensor.humidity
            
            return humidity
        except RuntimeError as error:
       
            return None
