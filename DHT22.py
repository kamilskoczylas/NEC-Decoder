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
  PulseErrorRange = 0.00006
  
  PULSE_POSITIVE_LENGTH = 0.000120
  PULSE_NEGATIVE_LENGTH = 0.000076

  MAX_DHT22_SIGNAL_LENGTH = 0.005

  currentSignalStartTime = 0
  
  temperature = 0
  humidity = 0
  checksum = 0

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

      while self.signalEdgeDetectedTimeQueue.qsize() > 40:
          i += 1
          try:
              edgeTimeDetected = self.signalEdgeDetectedTimeQueue.get_nowait()
              self.signalEdgeDetectedTimeQueue.task_done()
              signalTime = edgeTimeDetected - previousPulseStart
              previousPulseStart = edgeTimeDetected

      i = 0
      while self.signalEdgeDetectedTimeQueue.qsize() > 0:
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
              print ("{:0>2} {:.6f}".format(i, signalTime))
      
      self.timeFromNextPhase = edgeTimeDetected - maxTime
      print ("{:0>2} {:.6f}".format(i, self.timeFromNextPhase))
      
      return resultArray
  
      
  def getCommand(self):
      
      signalTime = self.waitForSignal()
      pulseArray = self.getBurst(40, self.currentSignalStartTime, self.currentSignalStartTime + self.MAX_DHT22_SIGNAL_LENGTH)    
      decodedSignal = self.translateSignal(pulseArray)

      
      return { "binary": decodedSignal,
               "temperature": self.temperature,
               "humidity": self.humidity
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
          if signalTime > 0.002 and signalTime < 0.008:
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
      

  def translateSignal(self, timeArray):
      correctSignal = ''
      i = 0
      humidity = 0
      temperature = 0
      checksum = 0
      sign = 1
      
      for pulseLength in timeArray:
          i+= 1
        
          if pulseLength >= self.PULSE_POSITIVE_LENGTH and pulseLength <= self.PULSE_POSITIVE_LENGTH + self.PulseErrorRange:
              correctSignal += '1'

              # it makes no sense if humidity exceed 100%, therefore no need to calculate it
              if i in range (6, 16):
                  humidity += (1 << (16 - i))

              # i = 17 is only sign digit: +/-
              if i == 17:
                  sign = -1
                
              if i in range (18, 32):
                  temperature += (1 << (32 - i))
    
              if i in range (33, 40):
                  checksum += (1 << (i - 33))
                  
          elif pulseLength > self.PULSE_NEGATIVE_LENGTH - self.PulseErrorRange and pulseLength < self.PULSE_POSITIVE_LENGTH:
              correctSignal += '0'

      self.temperature = sign * temperature / 10
      self.humidity = humidity / 10
      self.checksum = checksum
          
      return correctSignal 
      
  def validateSignal(self, signalString):
      if type(signalString) != str:
          return False
      
      if len(signalString) != 40:
          if self.DEBUG:
              print("Invalid length")
          return False
          
      return True
      
