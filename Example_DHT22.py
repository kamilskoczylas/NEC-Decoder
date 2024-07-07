# Only for value of GPIO.BCM
import RPi.GPIO as GPIO 
from time import sleep 

import DHT22
import SignalDecoder
import GPIODataProvider

GPIO_Mode = GPIO.BCM
GPIO_PIN = 12

IReader = SignalDecoder.SignalDecoder(
    GPIODataProvider.EdgeDetected(
        GPIO_Mode,
        GPIO_PIN
    ),
    DHT22.DHT22Decoder()
    )

# Keep positive signal for a while
GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
sleep(2)

# You have to set negative signal for at least 1 ms to request data from DHT22
GPIO.setup(GPIO_PIN, GPIO.OUT)
GPIO.output(GPIO_PIN, GPIO.LOW)
sleep(0.005)

cmd = IReader.getCommand()
print(cmd)

GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP) 

