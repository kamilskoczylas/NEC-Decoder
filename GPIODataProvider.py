#
#   GPIOEdgeDetectedDataProvider.py
#   Designed for Raspberry Pi, Python 3
#
#   2021-2024 Kamil Skoczylas
#   MIT Licence
#

from timeit import default_timer
from queue import Queue
from queue import Empty
from queue import Full
from SignalDecoder import SignalDataProvider
import RPi.GPIO as GPIO
import sys 


class EdgeDetected(SignalDataProvider):

	number_of_elements_to_leave = 0
 
	def __init__(self, GPIO_Mode=None, GPIO_PIN=None):

		if not GPIO_Mode is None:
			self.GPIO_Mode = GPIO_Mode

		if not GPIO_PIN is None: 
			self.GPIO_PIN = GPIO_PIN
			
		GPIO.setmode(self.GPIO_Mode)
		GPIO.setup(self.GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
		pass


	def Stop(self):
		GPIO.remove_event_detect(self.GPIO_PIN)
		pass

	def Start(self):
		GPIO.add_event_detect(self.GPIO_PIN, GPIO.FALLING, callback=self.SignalEdgeDetected)
		pass
    
	def SignalEdgeDetected(self, PinNumber):
		try:
			self.Queue.put_nowait(default_timer())

		except Full:
			print("Full")
			with self.Queue.mutex:
				while self.Queue.qsize() > self.number_of_elements_to_leave:
					try:
						self.Queue.get(block=False)
					except Empty:
						continue
					self.Queue.task_done()
                
		pass
        
	def InitDataQueue(self, queue):
		self.Queue = queue
		GPIO.add_event_detect(self.GPIO_PIN, GPIO.FALLING, callback=self.SignalEdgeDetected)
		pass

	def __del__(self):
		GPIO.cleanup(self.GPIO_PIN)
