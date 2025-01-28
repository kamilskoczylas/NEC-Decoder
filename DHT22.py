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


class Measure:
	Temperature = 0
	Humidity = 0
	DateTime = 0

	def __init__(self, temperature, humidity, dateTime):
		self.Temperature = temperature
		self.Humidity = humidity
		self.DateTime = dateTime


class BasicMeasure:
	value = 0
	DateTime = 0

	def __init__(self, value, dateTime):
		self.value = value
		self.DateTime = dateTime


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
		self.value = 0
		pulseLengthDifference = 0
		if self.pulseLength >= self.PULSE_POSITIVE_LENGTH and self.pulseLength <= self.PULSE_POSITIVE_LENGTH + self.PULSE_ERROR_MAX_RANGE:
			self.value = 1
			pulseLengthDifference = self.pulseLength - self.PULSE_POSITIVE_LENGTH
		else:
			pulseLengthDifference = self.pulseLength - self.PULSE_NEGATIVE_LENGTH

		self.stability = self.factor * (1 - min(abs(pulseLengthDifference), self.PULSE_ERROR_MAX_RANGE) / self.PULSE_ERROR_MAX_RANGE)
		return self.value


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
		self.value = 0
		pulseLengthDifference = 0
  
		if self.pulseLength >= self.PULSE_POSITIVE_LENGTH and self.pulseLength <= self.PULSE_POSITIVE_LENGTH + self.PULSE_ERROR_MAX_RANGE:
			self.value = 1
			pulseLengthDifference = self.pulseLength - self.PULSE_POSITIVE_LENGTH
		else:
			if self.pulseLength <= self.PULSE_NEGATIVE_LENGTH + self.PULSE_ERROR_MAX_RANGE / 2:
				self.value = -1
				pulseLengthDifference = self.pulseLength - self.PULSE_NEGATIVE_LENGTH
			else:
				pulseLengthDifference = self.PULSE_ERROR_MAX_RANGE

		self.stability = self.factor * (1 - min(abs(pulseLengthDifference), self.PULSE_ERROR_MAX_RANGE) / self.PULSE_ERROR_MAX_RANGE)
		return self.value


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
		self.value = input_value
		self.factor = factor

	def calculate(self):
  
		self.stability = 1
		return self.value

	def load(self, pulseLengthArray):
		for i in range(0, 8):
			pulseLength = pulseLengthArray[i]
   
			neuralFactors = [
				DHT22PulseLength(pulseLength, 1)
			]
			self.neuralBits[i].load(neuralFactors)


class NeuralReading(NeuralValue):
	value_hi = 0
	value_low = 0
	
	def __init__(self, name, averageValue: BasicMeasure):
		super(NeuralReading, self).__init__(name, 16, True, 10, True)
		self.averageValue = averageValue

	def load(self, pulseLengthArray):
		for i in range(0, 16):
			pulseLength = pulseLengthArray[i]
			if int(self.averageValue.value * 10) & (1 << (16 - i)) > 0:
				averageBitValue = 1
			else:
				averageBitValue = 0


			# Starting settings. Every execution, the values will be initialized
			# If the result will not pass the checksum, the factor values will be rewarded
			neuralFactors = [
				DHT22PulseLength(pulseLength, 1),
				DHT22AverageValue(averageBitValue, 0),
				DHT22Checksum(0, 0)
			]
			self.neuralBits[i].load(neuralFactors)

	def calculate(self):
		result = super().calculate()
		self.value_hi = result >> 8
		self.value_low = result & 255
  
		return result

	def reward(self, value: BasicMeasure):
		# super().
		pass


class NeuralChecksum(NeuralValue):
	
	def __init__(self):
		super(NeuralChecksum, self).__init__("Checksum", 8, False)

	def load(self, pulseLengthArray):
		for i in range(0, 8):
			pulseLength = pulseLengthArray[i]
			neuralFactors = [
				DHT22PulseLength(pulseLength, 1),
				# DHT22PulseLengthLeft(pulseLengthLeft, 1)
			]
			self.neuralBits[i].load(neuralFactors)


class NeuralTemperature(NeuralReading):
	
	def __init__(self, linkedAverageMeasure):
		super(NeuralTemperature, self).__init__("Temperature", linkedAverageMeasure)
		pass

	def calculate(self):
		self.temperature = float(super().calculate()) / 10


class NeuralHumidity(NeuralReading):
	
	def __init__(self, linkedAverageMeasure):
		super(NeuralHumidity, self).__init__("Humidity", linkedAverageMeasure)
		pass

	def calculate(self):
		self.humidity = float(super().calculate()) / 10

    
class NeuralSignalRecognizer(NeuralCalculation):
	
	def __init__(self, debug = True):
		self.DEBUG = debug
		self.averageTemperature = AverageValue(180, 1)
		self.averageHumidity = AverageValue(180, 1)
		self.NeuralTemperature = NeuralTemperature(self.averageTemperature.measure)
		self.NeuralHumidity = NeuralHumidity(self.averageHumidity.measure)
		self.NeuralChecksum = NeuralChecksum()
		pass

	def __str__(self):
		return "{0}\n{1}\n{2}".format(str(self.NeuralHumidity), str(self.NeuralTemperature), str(self.NeuralChecksum))

	def load(self, inputTimeBuffer, timeStarted):
		self.firstReadingDateTime = timeStarted
		if len(inputTimeBuffer) != 40:
			print("Invalid length")
			return

		
		self.NeuralHumidity.load(inputTimeBuffer[0:16])
		self.NeuralTemperature.load(inputTimeBuffer[16:32])
		self.NeuralChecksum.load(inputTimeBuffer[32:40])

	def reward(self, value: BasicMeasure):
		self.NeuralHumidity.reward(value)
		pass

	def finalize(self):
		self.averageTemperature.remove()
		self.averageHumidity.remove()
		pass

	def succeed(self, iteration = 1):
		self.averageTemperature.append(BasicMeasure(self.NeuralTemperature.temperature, self.firstReadingDateTime))
		self.averageHumidity.append(BasicMeasure(self.NeuralHumidity.humidity, self.firstReadingDateTime))
		if self.DEBUG:
			print("Attempt: {0}: SUCCESS: {1}°C, {2}%".format(iteration, self.averageTemperature.getValue(), self.averageHumidity.getValue()))
		pass

	def get_checksum_bit_differences_value(self):
		calculated_checksum = (self.NeuralHumidity.value_low + self.NeuralHumidity.value_hi + self.NeuralTemperature.value_low + self.NeuralTemperature.value_hi) & 255
		return calculated_checksum ^ self.NeuralChecksum.value

	def validate(self):
		calculated_checksum = (self.NeuralHumidity.value_low + self.NeuralHumidity.value_hi + self.NeuralTemperature.value_low + self.NeuralTemperature.value_hi) & 255
		if self.DEBUG:
			print("Calculated checksum = {0}".format(calculated_checksum))
			print("Calculated checksum bin= {0}".format(bin(calculated_checksum)))
		return calculated_checksum == self.NeuralChecksum.value

	def mask_values(self, array, bit_mask):
		# return the same array only if all bits of bit_mask are set to 1
		return [value if bit_mask & (1 >> index % 8) > 0 else 0 for index, value in enumerate(array)]

	def calculate_all_values(self, iteration = 1):
		self.NeuralHumidity.calculate()
		self.NeuralTemperature.calculate()
		self.NeuralChecksum.calculate()

		self.finalize()
		if self.validate():
			self.succeed(iteration)
			return True
		return False

	def calculate(self):
		# First level - just calculate the data from DHT22, if it match checksum, fine
		# TODO: check  and stability > 90%
  
		success = self.calculate_all_values()
  
		if not success:

			bit_stabilities_humidity = self.NeuralHumidity.getStabilityBitArray()
			bit_stabilities_temperature = self.NeuralTemperature.getStabilityBitArray()
			bit_stabilities_checksum = self.NeuralChecksum.getStabilityBitArray()

			# Correcting loop. Insted of typical Neural Network, date will not be pre-trained
			# We'll check various combination of factors that could impact the reading quality:
			# Checksum might indicate wrong bytes, average values might help to detect more probable results

			for iteration in range (1, 5):

				proportion_humidity = iteration / 4
				proportion_temperature = 1 - proportion_humidity

				checksum_factors_humidity = [proportion_humidity * (1 - value) for value in bit_stabilities_humidity]
				checksum_factors_temperature = [proportion_temperature * (1 - value) for value in bit_stabilities_temperature]

				checksum_difference_bit_value = self.get_checksum_bit_differences_value()
				checksum_bit_masked_values = [round(self.NeuralChecksum.getBit(i % 8).value) if checksum_difference_bit_value & (1 >> (i % 8)) > 0 else 0 for i in range (0, 16)]

				masked_checksum_factors_humidity = self.mask_values(checksum_factors_humidity, checksum_difference_bit_value)
				masked_checksum_factors_temperature = self.mask_values(checksum_factors_temperature, checksum_difference_bit_value)

				avg_readings_factors_temperature = [proportion_temperature * (1 - value) for value in bit_stabilities_temperature]
				avg_readings_factors_humidity = [proportion_humidity * (1 - value) for value in bit_stabilities_humidity]

				masked_temperature = self.mask_values(avg_readings_factors_temperature, checksum_difference_bit_value)
				masked_humidity = self.mask_values(avg_readings_factors_humidity, checksum_difference_bit_value)

    
				if self.DEBUG:
					print("ATTEMPT: {0}".format(iteration))
					print(self)
					print("Checksum: {0}".format(bin(self.NeuralChecksum.value)))
					print("Different bits: {0}".format(bin(checksum_difference_bit_value)))
					print(checksum_bit_masked_values)
					print("Humidity different values")
					print(masked_checksum_factors_humidity)
					print("Temperature different values")
					print(masked_checksum_factors_temperature)

					print("Masked temperature")
					print(masked_temperature)
					print("Masked humidity")
					print(masked_humidity)
					
				"""
				self.NeuralHumidity.updateFactorsFactor(DHT22Checksum, masked_checksum_factors_humidity)
				self.NeuralTemperature.updateFactorsFactor(DHT22Checksum, masked_checksum_factors_temperature)
	
				self.NeuralHumidity.updateFactorsValue(DHT22Checksum, checksum_bit_masked_values)
				self.NeuralTemperature.updateFactorsValue(DHT22Checksum, checksum_bit_masked_values)
				"""

				
	
				self.NeuralHumidity.updateFactorsFactor(DHT22AverageValue, masked_humidity)
				self.NeuralTemperature.updateFactorsFactor(DHT22AverageValue, masked_temperature)

				success = self.calculate_all_values(iteration)
				if success:
					break
		
		return success


class AverageValue:

	sum = 0
	lastMeasureDateTime = 0
	measure = BasicMeasure(0, 0)
	DEBUG = False
	digit_numbers = 2

	def __init__(self, maximum_length_seconds=120, digit_numbers = 2):
		self.results = deque()
		self.maximum_length_seconds = maximum_length_seconds
		self.digit_numbers = digit_numbers
		pass

	def remove(self):
		while len(self.results) > 0 and default_timer() - self.results[0].DateTime > self.maximum_length_seconds:
			first = self.results.popleft()
			self.sum -= first.value
		self.update()
		pass

	def update(self):
		results_count = len(self.results)
		if results_count > 0:
			self.measure.DateTime = self.results[0].DateTime
			self.measure.value = self.sum / results_count 
		else:
			self.measure.DateTime = 0
			self.measure.value = 0
		pass
    
	def append(self, measure: BasicMeasure):
    
		self.results.append(measure)
		self.sum += measure.value
		self.update() 

		if self.DEBUG:
			print("+ {0} = {1} / {2} = {3}".format(measure.value, self.sum, len(self.results), self.measure.value))
		pass

	def getValue(self):
		divider = len(self.results)
		if divider > 0:
			return round(self.sum / divider, self.digit_numbers)
		else:
			return 0


class AverageMeasure:

	ALLOW_TEMPERATURE_DIFFERENCE = 2
	ALLOW_HUMIDITY_DIFFERENCE = 10

	def __init__(self, maximum_length_seconds = 180):
		self.sum = Measure(0, 0, 0)
		self.results = deque()
		self.maximum_length_seconds = maximum_length_seconds
		self.lastMeasureDateTime = 0

	def remove(self):
		while len(self.results) > 0 and default_timer() - self.results[0].DateTime > self.maximum_length_seconds:
			first = self.results.popleft()
			print("removing first measure after {0} seconds: {1}C".format(default_timer() - first.DateTime, first.Temperature))
			self.sum.Temperature -= first.Temperature
			self.sum.Humidity -= first.Humidity
    
	def append(self, measure: Measure):

    
		self.results.append(measure)
		print(self.results)
		i = 0
		for result in self.results:
			i += 1
			print("{0}. = {1}".format(i, result.Temperature))

      
		self.sum.Temperature += measure.Temperature
		self.sum.Humidity += measure.Humidity
		self.sum.DateTime = measure.DateTime
		self.lastMeasureDateTime = measure.DateTime
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
		self.neuralSignalRecognizer.load(pulseArray, self.currentSignalStartTime)
		result = self.neuralSignalRecognizer.calculate()
		print(self.neuralSignalRecognizer)

		self.temperature = self.neuralSignalRecognizer.averageTemperature.getValue()
		self.humidity = self.neuralSignalRecognizer.averageHumidity.getValue()

		return  { "binary": "TESTING NEURAL",
				"result": "OK" if result else "ERROR",
				"checksum": self.checksum,
				"calculated_checksum": self.calculated_checksum,
				"temperature": self.temperature,
				"humidity": self.humidity,
    			"avg_temperature": self.temperature,
				"avg_humidity": self.humidity
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
