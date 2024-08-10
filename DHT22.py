#
#   DHT22: Temperature & Humidity values decoder
#   Designed for Raspberry Pi, Python 3
#
#   2024 Kamil Skoczylas
#   MIT Licence
#

from time import sleep
from queue import Empty
from timeit import default_timer
from collections import deque
from NeuralNetwork import SingleNeuralFactor, NeuralBoolean, NeuralValue, NeuralCalculation


class DHT22PulseLength(SingleNeuralFactor):

	PULSE_ERROR_MAX_RANGE = 0.000060
	PULSE_POSITIVE_LENGTH = 0.000120
	PULSE_NEGATIVE_LENGTH = 0.000076

	pulseLength = 0

	def __init__(self, input_value, factor) -> None:
		self.name = "Pulse Length"
		self.pulseLength = input_value
		self.factor = factor
		pass

	def calculate(self):
		ValueBasedOnPulseLength = 0
		pulseLengthDifference = 0
		if self.pulseLength >= self.PULSE_POSITIVE_LENGTH and self.pulseLength <= self.PULSE_POSITIVE_LENGTH + self.PULSE_ERROR_MAX_RANGE:
			self.ValueBasedOnPulseLength = 1
			pulseLengthDifference = self.pulseLength - self.PULSE_POSITIVE_LENGTH
		else:
			pulseLengthDifference = self.pulseLength - self.PULSE_NEGATIVE_LENGTH

		self.stability = self.factor * (1 - min(abs(pulseLengthDifference), self.PULSE_ERROR_MAX_RANGE) / self.PULSE_ERROR_MAX_RANGE)
		return ValueBasedOnPulseLength


class DHT22PulseLengthLeft(SingleNeuralFactor):

	PULSE_ERROR_MAX_RANGE = 0.000060
	PULSE_POSITIVE_LENGTH = 0.000120
	PULSE_NEGATIVE_LENGTH = 0.000076

	pulseLength = 0

	def __init__(self, input_value, factor) -> None:
		self.name = "Pulse Length + Left from previous"
		self.pulseLength = input_value
		self.factor = factor

	def calculate(self):
		ValueBasedOnPulseLength = 0
		pulseLengthDifference = 0
  
		if self.pulseLength >= self.PULSE_POSITIVE_LENGTH and self.pulseLength <= self.PULSE_POSITIVE_LENGTH + self.PULSE_ERROR_MAX_RANGE:
			self.ValueBasedOnPulseLength = 1
			pulseLengthDifference = self.pulseLength - self.PULSE_POSITIVE_LENGTH
		else:
			pulseLengthDifference = self.pulseLength - self.PULSE_NEGATIVE_LENGTH

		self.stability = self.factor * (1 - min(abs(pulseLengthDifference), self.PULSE_ERROR_MAX_RANGE) / self.PULSE_ERROR_MAX_RANGE)
		return ValueBasedOnPulseLength


class DHT22AverageValue(SingleNeuralFactor):

	def __init__(self, input_value, factor) -> None:
		self.name = "Average"
		self.input_value = input_value
		self.factor = factor

	def calculate(self):
  
		self.stability = 1
		return self.input_value


class DHT22Checksum(SingleNeuralFactor):

	def __init__(self, input_value, factor) -> None:
		self.name = "Checksum"
		self.input_value = input_value
		self.factor = factor

	def calculate(self):
  
		self.stability = 1
		return self.input_value


class DHT22Bit(NeuralBoolean):

	def load(self, bitNumber, pulseLength, pulseLengthLeft, averageBitValue):
		self.bitNumber = bitNumber
		self.neuralFactors = [
			DHT22PulseLength(pulseLength, 1),
			DHT22AverageValue(averageBitValue, 1),
			DHT22PulseLengthLeft(pulseLengthLeft, 1)
		]

"""class NeuralTemperature(ABC):
	neuralBits = []
	name = "NeuralTemperature"
	max_bits = 16
	is_signed = True

	def __init__(self):
		for i in range(0, self.max_bits):
			self.neuralBits.append(
				NeuralBoolean(self.max_bits - i)
			)

	def __str__(self):
		print("{0}".format(self.name))
		for neuralBit in self.neuralBits:
			print(neuralBit)

	def load(self, pulseLengthArray):
		for i in range(0, 16):
			
			self.neuralBits[i].load(pulseLengthArray[i])
"""

    
class NeuralSignalRecognizer(NeuralCalculation):
	
	def __init__(self):
		self.NeuralTemperature = NeuralValue("Temperature", 16, True)
		self.NeuralHumidity = NeuralValue("Humidity", 16, True)
		self.NeuralChecksum = NeuralValue("Checksum", 8, False)
		self.averageTemperature = AverageMeasure()
		self.averageHumidity = AverageMeasure()
		pass

	def __str__(self):
		print(self.NeuralHumidity)
		print(self.NeuralTemperature)
		print(self.NeuralChecksum)

	def load(self, inputTimeBuffer):
		if len(inputTimeBuffer) != 40:
			print("Invalid length")
			return

		self.NeuralHumidity.load(inputTimeBuffer[0:16])
		self.NeuralTemperature.load(inputTimeBuffer[16:32])
		self.NeuralChecksum.load(inputTimeBuffer[32:40])

	def reward(self, value: Measure):
		self.NeuralHumidity.reward()
		pass

	def calculate(self):
		self.NeuralHumidity.calculate()
		self.NeuralTemperature.calculate()
		pass

  
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
	ALLOW_HUMIDITY_DIFFERENCE = 10

	def __init__(self, maximum_length_seconds=120):
		self.results = deque()
		self.maximum_length_seconds = maximum_length_seconds

	def remove(self):
		while len(self.results) > 0 and default_timer() - self.results[0].DateTime > self.maximum_length_seconds:
			first = self.results.popleft()
			print("removing first measure after {0} seconds: {1}C".format(default_timer() - first.DateTime, first.Temperature))
			self.sum.Temperature -= first.Temperature
			self.sum.Humidity -= first.Humidity
    
	def append(self, measure: Measure):
    
		self.results.append(measure)
		self.sum.Temperature += measure.Temperature
		self.sum.Humidity += measure.Humidity
		self.sum.DateTime = measure.DateTime
		self.lastMeasureDateTime = measure.DateTime
		self.counter += 1
		divider = len(self.results)
    
		result = 0
		if divider > 0:
			result = self.sum.Temperature / divider  

		print("+ {0} = {1} / {2} = {3}".format(measure.Temperature, self.sum.Temperature, divider, result))
		pass

	def canAddMeasure(self, measure: Measure):
		average = self.getAvegareMeasure()
		print(abs(measure.Temperature - average.Temperature))
		print(abs(measure.Humidity - average.Humidity))
    
		return len(self.results) < 2 or (abs(measure.Temperature - average.Temperature) <= self.ALLOW_TEMPERATURE_DIFFERENCE and abs(measure.Humidity - average.Humidity) <= self.ALLOW_HUMIDITY_DIFFERENCE)

	def isStableAverage(self):
		return len(self.results) >= 3
    
	def getAvegareMeasure(self):
		divider = len(self.results)
		if divider > 0:
			return Measure(temperature=round(self.sum.Temperature / divider, 1), humidity=round(self.sum.Humidity / divider, 1), dateTime=self.lastMeasureDateTime)
		else:
			return Measure(0, 0, 0)


class DHT22Decoder:

	# Maximum value is half of the difference between
	# positive and negative signal length
	PulseErrorRange = 0.00006
	
	PULSE_POSITIVE_LENGTH = 0.000107
	PULSE_NEGATIVE_LENGTH = 0.000076

	MAX_DHT22_SIGNAL_LENGTH = 0.0048

	REMOVE_READING_WHEN_TEMPERATURE_DIFFERENT_FROM_AVG = 20
	REMOVE_READING_WHEN_HUMIDITY_DIFFERENT_FROM_AVG = 20

	currentSignalStartTime = 0
	
	temperature = 0
	humidity = 0
	checksum = 0
	calculated_checksum = 0
	averageMeasure = AverageMeasure()

	lastAverageTemperature = 0
	lastAverageHumidity = 0

	DEBUG = False
  
	def initialize(self, timeQueue, DebugMode=False):
		self.signalEdgeDetectedTimeQueue = timeQueue
		self.neuralSignalRecognizer = NeuralSignalRecognizer()
		self.DEBUG = DebugMode
		pass
		
	def getBurst(self, pulseCount, burstStartTime, maxTime):
		resultArray = []
		edgeTimeDetected = burstStartTime
		previousPulseStart = burstStartTime
		i = 0
		signalTime = 0

		if self.DEBUG:
			print("Queue length: {0}".format(self.signalEdgeDetectedTimeQueue.qsize()))

		while self.signalEdgeDetectedTimeQueue.qsize() > 40:
			i += 1
			edgeTimeDetected = self.signalEdgeDetectedTimeQueue.get_nowait()
			signalTime = edgeTimeDetected - previousPulseStart
			previousPulseStart = edgeTimeDetected

		i = 0
		while self.signalEdgeDetectedTimeQueue.qsize() > 0 and i < pulseCount and edgeTimeDetected <= maxTime:
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
		pulseArray = self.getBurst(40, self.currentSignalStartTime, self.currentSignalStartTime + signalTime + self.MAX_DHT22_SIGNAL_LENGTH)   
		self.neuralSignalRecognizer.load(pulseArray)
		self.neuralSignalRecognizer.calculate()
		print(self.neuralSignalRecognizer)

		# decodedSignal = self.translateSignal(pulseArray)

		# if not self.validateSignal(decodedSignal):
		#    decodedSignal = self.correctSignal(decodedSignal)
		
		# self.averageMeasure.remove()

		# if self.validateSignal(decodedSignal):
		"""
		measure = Measure(temperature=self.temperature, humidity=self.humidity, dateTime=self.currentSignalStartTime)
			
			if self.averageMeasure.canAddMeasure(measure):
				self.averageMeasure.append(measure)
				average = self.averageMeasure.getAvegareMeasure()

				if self.averageMeasure.isStableAverage():
					self.lastAverageTemperature = average.Temperature
					self.lastAverageHumidity = average.Humidity
			
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
				"""

		return  { "binary": "TESTING NEURAL",
				"result": "ERROR",
				"checksum": self.checksum,
				"calculated_checksum": self.calculated_checksum,
				"temperature": self.temperature,
				"humidity": self.humidity
				}

	def correctSignal(self, decodedSignal):
		if len(decodedSignal) != 40:
			return decodedSignal
		
		correctedSignal = decodedSignal
		print("Correcting {0}".format(self.formatBinary(decodedSignal)))
		print("Checksum read {0} == {1} calculated".format(self.checksum, self.calculated_checksum))

		difference_too_high = (256 - self.checksum) & self.calculated_checksum
		difference_too_low = (256 - self.calculated_checksum) & self.checksum

		counts_too_high = 0
		counts_too_low = 0
		for i in range(0, 8):
			if difference_too_high & (1 << i) > 0:
				counts_too_high += 1
			if difference_too_low & (1 << i) > 0:
				counts_too_low += 1
		
		print("Bitwise difference HI {0}, LOW {1}".format(difference_too_high, difference_too_low))
		print("Bits different HI {0}, LOW {1}".format(counts_too_high, counts_too_low))

		temperatureDifference = self.lastAverageTemperature - self.temperature
		humidityDifference = self.lastAverageHumidity - self.humidity

		print("Temperature difference {0} = {1} (avg) - {2} (last)".format(temperatureDifference, self.lastAverageTemperature, self.temperature))
		print("Humidity difference {0} = {1} (avg) - {2} (last)".format(humidityDifference, self.lastAverageHumidity, self.humidity))

		return correctedSignal
		
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
						# sleep(0.005) - for quarantee that signal has been read increased
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

				# skipping 17-21 bits, because temperature cannot be as high but it detects errors
				if i in range (22, 32):
					temperature += (1 << (31 - i))
		
				if i in range (32, 40):
					checksum += (1 << (39 - i))
					
			elif pulseLength > self.PULSE_NEGATIVE_LENGTH - self.PulseErrorRange and pulseLength < self.PULSE_POSITIVE_LENGTH:
				decodedSignal += '0'

			i += 1

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

		temperatureDifference = abs(self.lastAverageTemperature - self.temperature)
		humidityDifference = abs(self.lastAverageHumidity - self.humidity)
		if self.lastAverageTemperature != 0 and self.lastAverageHumidity != 0 and (temperatureDifference > self.REMOVE_READING_WHEN_TEMPERATURE_DIFFERENT_FROM_AVG or humidityDifference > self.REMOVE_READING_WHEN_HUMIDITY_DIFFERENT_FROM_AVG):
			return False

		self.calculated_checksum = 0
		for i in range (0, 32):
			if signalString[i] == '1':
				self.calculated_checksum += 1 << (7 - (i % 8))

		self.calculated_checksum = self.calculated_checksum & 255
		return self.calculated_checksum == self.checksum
		
