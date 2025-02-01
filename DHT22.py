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

	PULSE_ERROR_MAX_RANGE = 0.000044
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

	PULSE_ERROR_MAX_RANGE = 0.000044
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

class DHT22DifferenceFromAverageValueValidator(SingleNeuralFactor):

	def __init__(self, input_value, factor) -> None:
		self.name = "DifferenceFromAverage"
		self.input_value = input_value
		self.factor = factor

	def calculate(self):
		self.stability = 1
		return self.input_value


class DHT22DifferenceChecksumValidator(SingleNeuralFactor):

	def __init__(self, input_value, factor) -> None:
		self.name = "DifferenceChecksum"
		self.input_value = input_value
		self.factor = factor

	def calculate(self):
		self.stability = 1
		return self.input_value


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


class NeuralValidator():
	
	def __init__(self, name, DEBUG = False):
		self.correcting_value_mask = [0] * 16
		self.value = 0
		self.name = name
		self.DEBUG = DEBUG
		pass

	def calculate(self, average_measure, last_reading, checksum_calculated, checksum_read, stability_bits_array):
     
		average_measure_minus_last_reading = average_measure - last_reading
		checksum_read_minus_checksum_calculated = checksum_read - checksum_calculated
		checksum_calculated_minus_checksum = checksum_calculated - checksum_read

		if self.DEBUG:
			print("Checksum read: {0}".format(checksum_read))
			print("Calculated checksum = {0}".format(checksum_calculated))
			print("checksum_read_minus_checksum_calculated = {0}".format(checksum_read_minus_checksum_calculated))
			print("checksum_calculated_minus_checksum = {0}".format(checksum_calculated_minus_checksum))
			print("")
			print("Checksum read: {0}".format(bin(checksum_read)))
			print("Calculated checksum bin= {0}".format(bin(checksum_calculated)))
			print("checksum_read_minus_checksum_calculated bin= {0}".format(bin(checksum_read_minus_checksum_calculated)))
			print("checksum_calculated_minus_checksum bin= {0}".format(bin(checksum_calculated_minus_checksum)))

		# Calculate probability that the difference in checksum is result of the difference in average reading
		int_last_reading = 0
		if last_reading >= 0:
			int_last_reading = int(last_reading * 10)
		else:
			int_last_reading = int(-last_reading * 10) | (1 << 16)

		calculated_value = 0

		
		# Experimental parameter / 10 might be Machine Learning in the future
		average_measure_covering = abs(average_measure_minus_last_reading) / 10
  
		for i in range(0, 16):
			if (i < 10 or i == 15) and (abs(checksum_read_minus_checksum_calculated) & (1 << (i % 8))):
				calculated_value = calculated_value + pow((100 - min(stability_bits_array[i], 100)) / 50, 3)
				self.correcting_value_mask[i] = pow((100 - min(stability_bits_array[i], 100)) / 50, 3)
			else:
				self.correcting_value_mask[i] = 0
		#else:
			# some bits read might be set too high
		#	for i in range(0, 10):
		#		if not checksum_calculated_minus_checksum & (1 << (i % 8)) and (int_last_reading & (1 << i)):
		#			calculated_value = calculated_value + ((100 - min(stability_bits_array[i], 100)) / 100)
		#			self.correcting_value_mask[i] = 1


		if self.DEBUG:
			print(self.name)
			print("Value: {0}".format(self.value))
			print("Calculated by stability: {0}".format(calculated_value))
			print("Difference from average Measure: = {0}".format(average_measure_covering))
   
		self.value = calculated_value * average_measure_covering
		return self.value

   


class NeuralChecksumValidator():
	def calculate(self, checksum_read, checksum_calculated, checksum_stability):
		self.value = checksum_stability * min((8 - bin(256 - (checksum_calculated - checksum_read)).count('1')), (8 - bin(checksum_calculated - checksum_read).count('1')))
		return checksum_stability > 0.8

	


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

		self.NeuralTemperatureValidator = NeuralValidator("Temperature", self.DEBUG)
		self.NeuralHumidityValidator = NeuralValidator("Humidity", self.DEBUG)
		self.NeuralChecksumValidator = NeuralChecksumValidator()
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
		differences_should_be_lower = calculated_checksum ^ self.NeuralChecksum.value & self.NeuralChecksum.value
		differences_should_be_higher = ~calculated_checksum ^ self.NeuralChecksum.value & calculated_checksum
  
		
		return differences_should_be_lower, differences_should_be_higher

	def validate(self):
		calculated_checksum = (self.NeuralHumidity.value_low + self.NeuralHumidity.value_hi + self.NeuralTemperature.value_low + self.NeuralTemperature.value_hi) & 255
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
		else:
			calculated_checksum = (self.NeuralHumidity.value_low + self.NeuralHumidity.value_hi + self.NeuralTemperature.value_low + self.NeuralTemperature.value_hi) & 255
			self.NeuralTemperatureValidator.calculate(self.averageTemperature.getValue(), self.NeuralTemperature.temperature, calculated_checksum, self.NeuralChecksum.value, self.NeuralTemperature.getStabilityBitArray())
			self.NeuralHumidityValidator.calculate(self.averageHumidity.getValue(), self.NeuralHumidity.humidity, calculated_checksum, self.NeuralChecksum.value, self.NeuralHumidity.getStabilityBitArray())
			self.NeuralChecksumValidator.calculate(self.NeuralChecksum.value, calculated_checksum, self.NeuralChecksum.getStability())

		return False

	def calculate(self):
		# First level - just calculate the data from DHT22, if it match checksum, fine
		# TODO: check  and stability > 90%
  
		success = self.calculate_all_values()
  
		if not success:

			# Correcting loop. Insted of typical Neural Network, date will not be pre-trained
			# We'll check various combination of factors that could impact the reading quality:
			# Checksum might indicate wrong bytes, average values might help to detect more probable results

			for iteration in range (1, 2):
				if self.NeuralChecksumValidator.value < 0.2:
					if self.DEBUG:
						print("Checksum Stability {0} too low to recover.".format(self.NeuralChecksumValidator.value))
					break

				if self.DEBUG:
					print("ATTEMPT: {0}".format(iteration))
					print("Checksum stability: {0}".format(self.NeuralChecksumValidator.value))
					print(self)

				if self.NeuralTemperatureValidator.value > self.NeuralHumidityValidator.value and self.NeuralTemperatureValidator.value > 0:
					self.NeuralTemperature.updateFactorsFactor(DHT22AverageValue, self.NeuralTemperatureValidator.correcting_value_mask)
     
					if self.DEBUG:
						print("Correcting temperature")
						print(self.NeuralTemperatureValidator.correcting_value_mask)
						

				else:
					self.NeuralHumidity.updateFactorsFactor(DHT22AverageValue, self.NeuralHumidityValidator.correcting_value_mask)
					if self.DEBUG:
						print("Correcting humidity")
						print(self.NeuralHumidityValidator.correcting_value_mask)


				success = self.calculate_all_values(iteration)
				if success:
					break
		
		return success


class AverageValue:

	sum = 0
	lastMeasureDateTime = 0
	DEBUG = False
	digit_numbers = 2

	def __init__(self, maximum_length_seconds=120, digit_numbers = 2):
		self.measure = BasicMeasure(0, 0)
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


class DHT22Decoder:

	MAX_DHT22_SIGNAL_LENGTH = 0.0048
 
	currentSignalStartTime = 0
	temperature = 0
	humidity = 0
	checksum = 0

	average_temperature = 0
	average_humidity = 0

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

		if result:
			self.humidity = self.neuralSignalRecognizer.NeuralHumidity.value
			self.temperature = self.neuralSignalRecognizer.NeuralTemperature.value
			self.checksum = self.neuralSignalRecognizer.NeuralChecksum.value
   
		self.average_temperature = self.neuralSignalRecognizer.averageTemperature.getValue()
		self.average_humidity = self.neuralSignalRecognizer.averageHumidity.getValue()

		return  { "binary": "{0} {1} {2}".format(bin(int(self.neuralSignalRecognizer.NeuralHumidity.value * 10)), bin(int(self.neuralSignalRecognizer.NeuralTemperature.value * 10)), bin(self.neuralSignalRecognizer.NeuralChecksum.value)),
				"result": "OK" if result else "ERROR",
				"checksum": self.checksum,
				"temperature": self.temperature,
				"humidity": self.humidity,
    			"avg_temperature": self.average_temperature,
				"avg_humidity": self.average_humidity
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
