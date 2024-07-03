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

  DEBUG = False
  
  def initialize(self, timeQueue, DebugMode = False):
      self.IRTimeQueue = timeQueue
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
              edgeTimeDetected = self.IRTimeQueue.get_nowait()
              self.IRTimeQueue.task_done()
              signalTime = edgeTimeDetected - previousPulseStart
                  #min(maxTime - previousPulseStart, edgeTimeDetected - previousPulseStart)
          
          except Empty:
              #if default_timer() >= maxTime:
              #edgeTimeDetected = maxTime
              #signalTime = maxTime - previousPulseStart
              
              #if self.DEBUG:
              print("Empty: {0}".format(len(resultArray)))
              
              if (maxTime - previousPulseStart < self.REPEAT_BURST_ERROR_RANGE):
                  break
              
              print (resultArray)
              print("Left: {0}".format(maxTime - previousPulseStart))
              edgeTimeDetected = self.IRTimeQueue.get()
              self.IRTimeQueue.task_done()
              signalTime = edgeTimeDetected - previousPulseStart
              
          resultArray.append(signalTime)
          previousPulseStart = edgeTimeDetected
          if self.DEBUG:
              print ("{0} {1}".format(i, signalTime))
      
      self.timeFromNextPhase = edgeTimeDetected - maxTime
      #print ("{0} {1}".format(i, self.timeFromNextPhase))
      #resultArray.append(self.timeFromNextPhase)
      
      # To future calculation of breakTime
      self.ir_pulseStart = edgeTimeDetected
      return resultArray
  
      
  def getCommand(self):
      
      signalTime = self.waitForSignal()
      repeatCode = False
      self.timeFromNextPhase = 0
      
      if self.DEBUG:
          print("Break: {0}".format(self.breakTime))
      
      
      new_signalStart = self.ir_pulseStart + self.AddressLengthSeconds + self.PulseErrorRange
      pulseArray = self.getBurst(32, self.ir_pulseStart, self.ir_pulseStart + self.AddressLengthSeconds + self.CommandLengthSeconds)    
      
      addressArray = self.getFirst16bitsOr27ms(pulseArray)
      address = self.fillInKnownValues(addressArray)
      
      commandArray = pulseArray
      command = self.fillInKnownValues(commandArray)
      
      if self.DEBUG:
          print("Address: {0}".format(address))
          print("Command: {0}".format(command))
      
      if type(address) != str or type(command) != str:
          return False
      
      return { "hex": self.ConvertString16ToHex(address[:8] + command[:8]),
               "address": address,
               "command": command
               }
      
  def waitForSignal(self):
      self.breakTime = 0
      while True:
          # Try to find start 
          edgeTimeDetected = self.IRTimeQueue.get()
          #self.IRTimeQueue.task_done()
          
          # Let Raspberry read whole signal before
          # we use max CPU for decoding
          signalTime = edgeTimeDetected - self.ir_pulseStart
          self.ir_pulseStart = edgeTimeDetected
          
          # If signal starts 13,5ms
          if signalTime > 0.0035 and signalTime < 0.015:
              # Need to wait for the rest of the signal
              if self.IRTimeQueue.qsize() < 32:
                  sleep(0.054)
              else:
                  if self.DEBUG:
                      print(self.IRTimeQueue.qsize())
              
              return signalTime
          else:
              self.breakTime = signalTime
              
              if self.DEBUG:
                  print("Wrong start signal", signalTime)
          
          if self.IRTimeQueue.empty():
              sleep(0.01)
          
      
  def validateSignal(self, signalString):
      if type(signalString) != str:
          return False
      
      if len(signalString) != 16:
          if self.DEBUG:
              print("Invalid length")
          return False
      
      difference = 0
      for i in range(0, 8):
          if signalString[i] != signalString[i + 8]:
              difference += 1
              
      if difference > 0 and difference < 8:        
          if self.DEBUG:
              print("Invalid reflection")
          return False
          
      return True
      
