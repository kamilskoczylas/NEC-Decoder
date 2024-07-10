from time import sleep 
from threading import Thread

import RPi.GPIO as GPIO 
import DHT22
import SignalDecoder
import GPIODataProvider

class TemperatureSensor:

  GPIO_Mode = GPIO.BCM
  GPIO_PIN = 12

  Temperature = 0
  Humidity = 0
  MeasureFrequencyInSeconds = 8
  
  def __init__(self, GPIO_BCM_PIN, MeasureFrequencyInSeconds = 8):
    assert MeasureFrequencyInSeconds>=2, "DHT22 requires that measures must be 2 seconds at minimum"
    self.GPIO_PIN = GPIO_BCM_PIN

    DHT22Reader = SignalDecoder.SignalDecoder(
        GPIODataProvider.EdgeDetected(
            GPIO_Mode,
            GPIO_PIN
        ),
        DHT22.DHT22Decoder(),
        True
        )

    self.MeasureFrequencyInSeconds = MeasureFrequencyInSeconds
    worker = Thread(target=self.QueueConsumer)
    worker.daemon = True
    worker.start()
    pass

    
  def QueueConsumer(self):
    # Keep positive signal for a while
    GPIO.setup(self.GPIO_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
    sleep(self.MeasureFrequencyInSeconds)
    
    # You have to set negative signal for at least 1 ms to request data from DHT22
    GPIO.setup(GPIO_PIN, GPIO.OUT)
    GPIO.output(GPIO_PIN, GPIO.LOW)
    sleep(0.005)
    
    GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
    sleep(0.1)
    measure = IReader.getCommand()

    if type(measure) is dict and "result" in measure:
      if measure['result'] == "OK":
        self.Temperature = measure['temperature']
        self.Humidity = measure['humidity']
        
    pass
    




