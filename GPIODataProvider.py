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
	Maximum_milliseconds_signal_length = 100
 
 
	def __init__(self, GPIO_Mode=None, GPIO_PIN=None, Maximum_milliseconds_signal_length = 100):

		if not GPIO_Mode is None:
			self.GPIO_Mode = GPIO_Mode

		if not GPIO_PIN is None: 
			self.GPIO_PIN = GPIO_PIN

		self.Maximum_milliseconds_signal_length = Maximum_milliseconds_signal_length
			
		GPIO.setmode(self.GPIO_Mode)
		GPIO.setup(self.GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
		pass


	def Stop(self):
		try:
			GPIO.remove_event_detect(self.GPIO_PIN)
		except:
			print("Can't remove the event detection from PIN {0}".format(self.GPIO_PIN))
		pass

	def Start(self):
		self.Stop()
		try:
			GPIO.add_event_detect(self.GPIO_PIN, GPIO.FALLING, callback=self.SignalEdgeDetected)
		except:
			print("This pin {0} has been already used. Ignoring".format(self.GPIO_PIN))
		pass
    
	def SignalEdgeDetected(self, PinNumber):
		try:
			
			self.Queue.put(default_timer())
   
			"""
					Unfortunately too slow solution using GPIO
					reaches maximum 0.00015 seconds while 0.000076 needed

						detected_beginning_of_signal_time = default_timer()
      					self.Stop()

						self.Queue.put(detected_beginning_of_signal_time)

						signal_state = GPIO.LOW

						last_signal_state = signal_state
						reading_time = detected_beginning_of_signal_time
						last_reading_time = detected_beginning_of_signal_time
						i = 0
			
						# Reading the signal until its end, or end of time it should end
						while reading_time - detected_beginning_of_signal_time < self.Maximum_milliseconds_signal_length / 1000:
							i += 1
							# To speed up reading from GPIO, not check time every time when checking the GPIO
							if i == 100:
								reading_time = default_timer()
								i = 0
				
							signal_state = GPIO.input(self.GPIO_PIN)
							if last_signal_state != signal_state and signal_state == GPIO.LOW:
								if i != 0:
									reading_time = default_timer()
								print("{:.5f}".format(reading_time - last_reading_time))
								self.Queue.put(reading_time)
								last_reading_time = reading_time
				
							last_signal_state = signal_state
				
						self.Start()

			"""
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
		self.Start()
		pass

	def __del__(self):
		GPIO.cleanup(self.GPIO_PIN)
