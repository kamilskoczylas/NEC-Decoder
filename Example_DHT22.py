from time import sleep 

import TemperatureSensor

GPIO_PIN = 12

# DHT22 connected to PIN 12 of Raspberry (BCM), class refresh every 4 seconds
Sensor = TemperatureSensor.TemperatureSensor(GPIO_PIN, 4)

while True:
    print("Temperature = {temperature}°C, Humidity = {humidity}%".format(temperature=Sensor.Temperature, humidity=Sensor.Humidity))
    print("Avg. Temperature = {temperature}°C, Avg. Humidity = {humidity}%".format(temperature=Sensor.AvgTemperature, humidity=Sensor.AvgHumidity))
    sleep(2)
