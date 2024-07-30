#
#   Digital Signal Decoder
#   Designed for Raspberry Pi, Python 3
#
#   2021-2024 Kamil Skoczylas
#   MIT Licence
#


from time import sleep
from queue import Queue
from queue import Empty
from threading import Thread
from abc import ABC, abstractmethod

class SignalDataProvider(ABC):
    @abstractmethod
    def InitDataQueue(self, queue):
        pass

class SignalAdapter(ABC):
    DEBUG = False

    @abstractmethod
    def initialize(self, timeQueue, debug):
        self.timeQueue = timeQueue
        self.DEBUG = debug
        pass

    @abstractmethod
    def getCommand(self):
        pass

class SignalDecoder:

    startIRTimeQueue = 0
    MAX_QUEUE_SIZE = 1024
    MAX_COMMANDS = 20
    
    def __init__(self, dataProvider: SignalDataProvider, decoder: SignalAdapter, DEBUG = False):
        
        self.DEBUG = DEBUG

        self.timeQueue = Queue(self.MAX_QUEUE_SIZE)
        self.Commands = Queue(self.MAX_COMMANDS)
        self.decoder = decoder

        dataProvider.InitDataQueue(self.timeQueue)

        worker = Thread(target=self.QueueConsumer)
        worker.daemon = True
        worker.start()
        pass

    
    def QueueConsumer(self):
        self.decoder.initialize(self.timeQueue, self.DEBUG)
        
        while True:
            
            currentCommand = self.decoder.getCommand()
            self.Commands.put_nowait(currentCommand)
            
            # Minimum time for next IR command
            sleep(0.01)
        pass
    
    def hasDetected(self):
        return not self.Commands.empty()

    def clear(self, number_of_elements_to_leave = 0):
        with self.Commands.mutex:
            while self.Commands.qsize() > number_of_elements_to_leave:
                try:
                    self.Commands.get(block=False)
                except Empty:
                    continue
                self.Commands.task_done()
        pass
    
    def getCommand(self, wait_for_result = False):
        command = self.Commands.get(wait_for_result)
        self.Commands.task_done()
        return command
        

    
    
    
