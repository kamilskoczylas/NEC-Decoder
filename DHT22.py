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
from timeit import default_timer
from collections import deque


class Measure:
  Temperature = 0
  Humidity = 0
  DateTime = 0

  def __init__(self, temperature, humidity, dateTime):
      self.Temperature = temperature
      self.Humidity = humidity
      self.DateTime = dateTime


class AverageMeasure:

  sum = Measure(0, 0, 0)
  lastMeasureDateTime = 0
  counter = 0

  ALLOW_TEMPERATURE_DIFFERENCE = 2
  ALLOW_HUMIDITY_DIFFERENCE = 4

  def __init__(self, maximum_length = 3):
      self.results = deque(maxlen = maximum_length)


  def append(self, measure: Measure):
      temp = 0
    
      if self.counter >= self.results.maxlen:
          first = self.results.popleft()
          self.sum.Temperature -= first.Temperature
          self.sum.Humidity -= first.Humidity
          temp = first.Temperature
    
      self.results.append(measure)
      self.sum.Temperature += measure.Temperature
      self.sum.Humidity += measure.Humidity
      self.sum.DateTime = measure.DateTime
      self.lastMeasureDateTime = measure.DateTime
      self.counter += 1
      divider = min(self.counter, self.results.maxlen)
      result = 0
      if divider > 0:
        result = self.sum.Temperature / divider  

      print("{0} + {1} - {2} / {3} = {4}".format(self.sum.Temperature, measure.Temperature, temp, divider, result))
      pass

  def canAddMeasure(self, measure: Measure):
      average = self.getAvegareMeasure()
      print(abs(measure.Temperature - average.Temperature))
      print(abs(measure.Humidity - average.Humidity))
    
      return self.counter < self.results.maxlen or (abs(measure.Temperature - average.Temperature) <= self.ALLOW_TEMPERATURE_DIFFERENCE and abs(measure.Humidity - average.Humidity) <= self.ALLOW_HUMIDITY_DIFFERENCE)

  def getAvegareMeasure(self):
      divider = min(self.counter, self.results.maxlen)
      if divider > 0:
          return Measure(temperature = round(self.sum.Temperature / divider, 1), humidity = round(self.sum.Humidity / divider, 1), dateTime = self.lastMeasureDateTime)
      else:
          return Measure(0, 0, 0)


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
  averageMeasure = AverageMeasure()

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

      if self.DEBUG:
          print("Queue length: {0}".format(self.signalEdgeDetectedTimeQueue.qsize()))

      while self.signalEdgeDetectedTimeQueue.qsize() > 40:
          i += 1
          edgeTimeDetected = self.signalEdgeDetectedTimeQueue.get_nowait()
          signalTime = edgeTimeDetected - previousPulseStart
          previousPulseStart = edgeTimeDetected

      i = 0
      while self.signalEdgeDetectedTimeQueue.qsize() > 0:
          i += 1
  
          try:
              edgeTimeDetected = self.signalEdgeDetectedTimeQueue.get_nowait()
              signalTime = edgeTimeDetected - previousPulseStart
          
          except Empty:
              if self.DEBUG:
                print("Empty: {0}".format(len(resultArray)))
                print (resultArray)
              
              print("Left: {0}".format(maxTime - previousPulseStart))
              signalTime = default_timer() - previousPulseStart

          self.signalEdgeDetectedTimeQueue.task_done()
          resultArray.append(signalTime)
          previousPulseStart = edgeTimeDetected
          if self.DEBUG:
              print ("{:0>2} {:.6f}".format(i, signalTime))
      
      self.timeFromNextPhase = edgeTimeDetected - maxTime
      if self.DEBUG:
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
          measure = Measure(temperature = self.temperature, humidity = self.humidity, dateTime = self.currentSignalStartTime)
          self.averageMeasure.append(measure)
          average = self.averageMeasure.getAvegareMeasure()

          if self.averageMeasure.canAddMeasure(measure):
              return { "binary": self.formatBinary(decodedSignal),
                       "result": "OK",
                       "temperature": self.temperature,
                       "humidity": self.humidity,
                       "avg_temperature": average.Temperature,
                       "avg_humidity": average.Humidity
                       }
      
      return { "binary": self.formatBinary(decodedSignal),
               "result": "ERROR",
               "checksum": self.checksum,
               "calculated_checksum": self.calculated_checksum,
               "temperature": self.temperature,
               "humidity": self.humidity
               }
      
  def waitForSignal(self):
      self.breakTime = 0
      while True:

          if self.signalEdgeDetectedTimeQueue.qsize() > 0:
            edgeTimeDetected = self.signalEdgeDetectedTimeQueue.get()
          
            # Let Raspberry read whole signal before
            # we use max CPU for decoding
            signalTime = edgeTimeDetected - self.currentSignalStartTime
            self.currentSignalStartTime = edgeTimeDetected
  
            if self.DEBUG:
              print(signalTime)
            
            # If signal starts 13,5ms
            if signalTime > 0.002 and signalTime < 0.008:
                # Need to wait for the rest of the signal
                if self.signalEdgeDetectedTimeQueue.qsize() < 40:
                    #sleep(0.005) - for quarantee that signal has been read increased
                    sleep(0.01)
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
      
