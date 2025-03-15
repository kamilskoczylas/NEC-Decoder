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
	AvgTemperature = 0
	AvgHumidity = 0
	MeasureFrequencyInSeconds = 8
	isStopped = False
	
  
	def __init__(self, GPIO_BCM_PIN, MeasureFrequencyInSeconds = 8):
		assert MeasureFrequencyInSeconds>=2, "DHT22 requires that measures must be 2 seconds at minimum"
		self.GPIO_PIN = GPIO_BCM_PIN

		self.edgeDetectionMethod = GPIODataProvider.EdgeDetected(
				self.GPIO_Mode,
				self.GPIO_PIN,
				90 # 90 milliseconds should be enough to read whole signal
			)

		self.DHT22Reader = SignalDecoder.SignalDecoder(
			self.edgeDetectionMethod,
			DHT22.DHT22Decoder(),
			False
			)

		self.MeasureFrequencyInSeconds = MeasureFrequencyInSeconds
		self.Start()
	pass

	def Stop(self):
		self.edgeDetectionMethod.Stop()
		self.DHT22Reader.Stop()
		self.isStopped = True

	def Start(self):
		self.edgeDetectionMethod.Start()
		self.DHT22Reader.Start()
  
		self.isStopped = False

		self.worker = Thread(target=self.QueueConsumer)
		self.worker.daemon = True
		self.worker.start()


	def QueueConsumer(self):
		while not self.isStopped:
			# Keep positive signal for a while
			GPIO.setup(self.GPIO_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
			sleep(self.MeasureFrequencyInSeconds)
			
			# You have to set negative signal for at least 1 ms to request data from DHT22
			GPIO.setup(self.GPIO_PIN, GPIO.OUT)
			GPIO.output(self.GPIO_PIN, GPIO.LOW)
			sleep(0.002)
			
			GPIO.setup(self.GPIO_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
			sleep(0.05)

			if self.DHT22Reader.hasDetected():
				measure = self.DHT22Reader.getCommand()

				if type(measure) is dict and "result" in measure:
					if measure['result'] == "OK":
						self.Temperature = measure['temperature']
						self.Humidity = measure['humidity']
						self.AvgTemperature = measure['avg_temperature']
						self.AvgHumidity = measure['avg_humidity']
		
	pass
    





