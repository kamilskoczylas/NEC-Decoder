#
#   DHT22: Temperature & Humidity values decoder
#   Designed for Raspberry Pi, Python 3
#
#   2024 Kamil Skoczylas
#   MIT Licence
#

from time import sleep
from queue import Queue
from queue import Empty

class DHT22Decoder:

  # Maximum value is half of the difference between
  # positive and negative signal length
  PulseErrorRange = 0.000022
  
  PULSE_POSITIVE_LENGTH = 0.000120
  PULSE_NEGATIVE_LENGTH = 0.000076

  MAX_DHT22_SIGNAL_LENGTH = 0.005

  currentSignalStartTime = 0

  DEBUG = False
  
  def initialize(self, timeQueue, DebugMode = False):
      self.signalEdgeDetectedTimeQueue = timeQueue
      self.DEBUG = DebugMode
      pass
      
  def getBurst(self, pulseCount, burstStartTime, maxTime):
      resultArray = []
      edgeTimeDetected = burstStartTime
      previousPulseStart = burstStartTime
      i = 0
      
      while i < pulseCount and edgeTimeDetected <= maxTime:
          i += 1
  
          try:
              edgeTimeDetected = self.signalEdgeDetectedTimeQueue.get_nowait()
              self.signalEdgeDetectedTimeQueue.task_done()
              signalTime = edgeTimeDetected - previousPulseStart
          
          except Empty:
              if self.DEBUG:
                print("Empty: {0}".format(len(resultArray)))
              
              print (resultArray)
              print("Left: {0}".format(maxTime - previousPulseStart))
              edgeTimeDetected = self.signalEdgeDetectedTimeQueue.get()
              self.signalEdgeDetectedTimeQueue.task_done()
              signalTime = edgeTimeDetected - previousPulseStart
              
          resultArray.append(signalTime)
          previousPulseStart = edgeTimeDetected
          if self.DEBUG:
              print ("{0} {1}".format(i, signalTime))
      
      self.timeFromNextPhase = edgeTimeDetected - maxTime
      print ("{0} {1}".format(i, self.timeFromNextPhase))
      
      return resultArray
  
      
  def getCommand(self):
      
      signalTime = self.waitForSignal()
      pulseArray = self.getBurst(40, self.currentSignalStartTime, self.currentSignalStartTime + self.MAX_DHT22_SIGNAL_LENGTH)    

      temperature = 0
      humidity = 0
      
      return { "hex": "",
               "temperature": temperature,
               "humidity": humidity
               }
      
  def waitForSignal(self):
      self.breakTime = 0
      while True:
          
          edgeTimeDetected = self.signalEdgeDetectedTimeQueue.get()
          
          # Let Raspberry read whole signal before
          # we use max CPU for decoding
          signalTime = edgeTimeDetected - self.currentSignalStartTime
          self.currentSignalStartTime = edgeTimeDetected

          print(signalTime)
          
          # If signal starts 13,5ms
          if signalTime > 0.0002 and signalTime < 0.0005:
              # Need to wait for the rest of the signal
              if self.signalEdgeDetectedTimeQueue.qsize() < 40:
                  sleep(0.005)
              else:
                  if self.DEBUG:
                      print(self.signalEdgeDetectedTimeQueue.qsize())
              
              return signalTime
          else:
              self.breakTime = signalTime
              
              if self.DEBUG:
                  print("Wrong start signal", signalTime)
          
          if self.signalEdgeDetectedTimeQueue.empty():
              sleep(0.01)
          
      
  def validateSignal(self, signalString):
      if type(signalString) != str:
          return False
      
      if len(signalString) != 40:
          if self.DEBUG:
              print("Invalid length")
          return False
          
      return True
      
