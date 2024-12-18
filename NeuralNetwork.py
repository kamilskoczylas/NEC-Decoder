#
#   Neural Network basic abstract structure
#
#   2024 Kamil Skoczylas
#   MIT Licence
#

from typing import List
from abc import ABC, abstractmethod


class SingleNeuralFactor(ABC):

	value = 0
	stability = 1

	def __init__(self, name: str, input_value: float, factor: float) -> None:
		self.name = name
		self.input_value = input_value
		self.factor = factor
		pass

	def __str__(self):
		print("value: {0}, stability: {1}, length {2}, previous pulse length left {3}".format(self.value, self.stability, self.pulseLength, self.previousPulseLengthLeft))
		print("Factors: pulse length {2}, previous pulse length left {3}".format(self.pulseLengthFactor, self.previousPulseLengthLeftFactor))
		pass

	def calculate(self):
		return self.value * self.factor

	def reward(self):
		self.factor += 1
		pass

   
class NeuralBoolean(ABC):
        
	stability = 0
	value = 0
	pulseLength = 0
	previousPulseLengthLeft = 0
	bitNumber = 0

	def __init__(self, bitNumber):
		self.bitNumber = bitNumber
		self.neuralFactors = []

	def __str__(self):
		print("BIT: {0}".format(self.bitNumber))
		print("value: {0}, stability: {1}".format(self.value, self.stability))
		for neuralFactor in self.neuralFactors:
			print(neuralFactor)

	def load(self, neuralFactors):
		self.neuralFactors = neuralFactors

	def addFactor(self, neuralFactor: SingleNeuralFactor):
		self.neuralFactors.append(neuralFactor)
		return self.calculate()

	def getFactor(self, number: int):
		return self.neuralFactors[number]

	def calculate(self):
		factorSum = 0
		valueSum = 0
		stabilitySum = 0
  
		for neuralFactor in self.neuralFactors:
			factorSum += neuralFactor.factor
			valueSum += neuralFactor.calculate()
			stabilitySum += neuralFactor.stability

		self.value = valueSum / factorSum
		self.stability = stabilitySum / factorSum
		pass

	def reward(self, value):
		for neuralFactor in self.neuralFactors:
			if neuralFactor.value == value:
				neuralFactor.reward()


class NeuralValue(ABC):
	name = "NeuralValue"
	max_bits = 0
	is_signed = False
	value = 0

	def __init__(self, name, max_bits, is_signed):
		self.name = name
		self.max_bits = max_bits
		self.is_signed = is_signed
		self.neuralBits = []
  
		for i in range(0, max_bits):
			self.neuralBits.append(
				NeuralBoolean(max_bits - i)
			)

	def __str__(self):
		print("{0}".format(self.name))
		for neuralBit in self.neuralBits:
			print(neuralBit)

	def load(self, pulseLengthArray):
		for i in range(0, self.max_bits):
			self.neuralBits[i].load(pulseLengthArray[i])
		pass

	def getBit(self, number: int):
		return self.neuralBits[(self.max_bits - 1) - number]

	def calculate(self):
		self.value = 0
		multiply_by = 1
		for i in range(0, self.max_bits):
			self.neuralBits[i].calculate()	
		for i in range(0, self.max_bits):
			if round(self.neuralBits[i].value) == 1:
				if i == 0 and self.is_signed:
					multiply_by = -1
				else:
					self.value += 1 << (self.max_bits - 1 - i)
		self.value = multiply_by * self.value
		return self.value

		
class NeuralCalculation(ABC):

	@abstractmethod
	def load(self):
		pass

	@abstractmethod
	def calculate(self):
		pass

	@abstractmethod
	def reward(self, value):
		pass
