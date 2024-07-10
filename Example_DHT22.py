from time import sleep 

import TemperatureSensor

GPIO_PIN = 12

# DHT22 connected to PIN 12 of Raspberry (BCM), class refresh every 2 seconds
Sensor = TemperatureSensor.TemperatureSensor(GPIO_PIN, 2)

while True:
    print("Temperature = {temperature}°C, Humidity = {humidity}%".format(temperature=Sensor.Temperature, humidity=Sensor.Humidity))
    sleep(2)
