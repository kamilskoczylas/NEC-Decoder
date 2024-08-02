#
#   GPIOEdgeDetectedDataProvider.py
#   Designed for Raspberry Pi, Python 3
#
#   2021-2024 Kamil Skoczylas
#   MIT Licence
#

from abc import ABC, abstractmethod
from timeit import default_timer
from queue import Queue
from queue import Empty
from queue import Full
import RPi.GPIO as GPIO
import sys 


class EdgeDetected(ABC):
    
    def __init__(self, GPIO_Mode=None, GPIO_PIN=None):
        
        if not GPIO_Mode is None:
            self.GPIO_Mode = GPIO_Mode

        if not GPIO_PIN is None: 
            self.GPIO_PIN = GPIO_PIN
            
        GPIO.setmode(self.GPIO_Mode)
        GPIO.setup(self.GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
        pass
    
    def SignalEdgeDetected(self, PinNumber):
        try:
            self.Queue.put_nowait(default_timer())
          
        except Full:
            sys.exit()
        pass
        
    def InitDataQueue(self, queue):
        self.Queue = queue
        GPIO.add_event_detect(self.GPIO_PIN, GPIO.FALLING, callback=self.SignalEdgeDetected)
        pass

    def __del__(self):
        GPIO.cleanup(self.GPIO_PIN)
