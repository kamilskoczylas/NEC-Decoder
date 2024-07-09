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
  
  PULSE_POSITIVE_LENGTH = 0.000110
  PULSE_NEGATIVE_LENGTH = 0.000076

  MAX_DHT22_SIGNAL_LENGTH = 0.005

  currentSignalStartTime = 0
  
  temperature = 0
  humidity = 0
  checksum = 0
  calculated_checksum = 0

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
  
  def formatBinary(self, signal):
      ending = ""
      if len(signal) > 40:
          ending = " " + signal[40:len(signal)]
      return signal[0:8] + " " + signal[8:16] + " " + signal[16:24] + " " + signal[24:32] + " " + signal[32:40] + ending
    
  def getCommand(self):
      
      signalTime = self.waitForSignal()
      pulseArray = self.getBurst(40, self.currentSignalStartTime, self.currentSignalStartTime + self.MAX_DHT22_SIGNAL_LENGTH)    
      decodedSignal = self.translateSignal(pulseArray)

      if self.validateSignal(decodedSignal):
          return { "binary": self.formatBinary(decodedSignal),
                   "result": "OK",
                   "temperature": self.temperature,
                   "humidity": self.humidity
                   }
      else:
          return { "binary": self.formatBinary(decodedSignal),
                   "result": "ERROR",
                   "checksum": self.checksum,
                   "calculated_checksum": self.calculated_checksum,
                   "temperature": self.temperature,
                   "humidity": self.humidity
                   }
      pass
      
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
      decodedSignal = ''
      i = 0
      humidity = 0
      temperature = 0
      checksum = 0
      sign = 1
      
      for pulseLength in timeArray:
        
          if pulseLength >= self.PULSE_POSITIVE_LENGTH and pulseLength <= self.PULSE_POSITIVE_LENGTH + self.PulseErrorRange:
              decodedSignal += '1'
  
              # it makes no sense if humidity exceed 100%, therefore no need to calculate it
              if i in range (5, 16):
                  humidity += (1 << (15 - i))

              # i = 17 is only sign digit: +/-
              if i == 16:
                  sign = -1
                
              if i in range (17, 32):
                  temperature += (1 << (31 - i))
    
              if i in range (32, 40):
                  checksum += (1 << (39 - i))
                  
          elif pulseLength > self.PULSE_NEGATIVE_LENGTH - self.PulseErrorRange and pulseLength < self.PULSE_POSITIVE_LENGTH:
              decodedSignal += '0'

          i+= 1

      # Raspberry reads incorrectly beginning of the signal. But it must be 5 times 0
      correctSignal = "00000" + decodedSignal[5:len(decodedSignal)]
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

      self.calculated_checksum = 0
      for i in range (0, 32):
          if signalString[i] == '1':
              self.calculated_checksum += 1 << (7 - (i % 8))

      self.calculated_checksum = self.calculated_checksum & 255
      return self.calculated_checksum == self.checksum
      
