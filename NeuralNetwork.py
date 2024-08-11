#
#   Neural Network basic abstract structure
#
#   2024 Kamil Skoczylas
#   MIT Licence
#

from typing import List
from abc import ABC, abstractmethod


class SingleNeuralFactor():

	value = 0
	stability = 1

	def __init__(self, name: str, input_value: float, factor: float) -> None:
		self.name = name
		self.input_value = input_value
		self.factor = factor
		pass

	def __str__(self):
		return "Name: {0}, stability: {1}, value {2}, factor {3}\n".format(self.name, self.stability, self.value, self.factor)

	def calculate(self):
		return self.value * self.factor

	def reward(self):
		self.factor += 1
		pass

   
class NeuralBoolean():
        
	stability = 0
	value = 0
	pulseLength = 0
	previousPulseLengthLeft = 0
	bitNumber = 0

	neuralFactors = []

	def __init__(self, bitNumber):
		print(self)
		self.bitNumber = bitNumber

	# def __str__(self):
	# 	result = "BIT: {0}\n".format(self.bitNumber)
	# 	result += "value: {0}, stability: {1}\n".format(self.value, self.stability)
	# 	for neuralFactor in self.neuralFactors:
	# 		result += str(neuralFactor)
   
	# 	return result

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

		if factorSum > 0:
			self.value = round(valueSum / factorSum)
			self.stability = stabilitySum / factorSum
		pass

	def reward(self, value):
		for neuralFactor in self.neuralFactors:
			if neuralFactor.value == value:
				neuralFactor.reward()


class NeuralValue():
	
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
				NeuralBoolean(max_bits - i - 1)
			)
   
		print("{0}: {1}".format(name, max_bits))
		print(self.neuralBits)

	def __str__(self):
		result = "{0}\n".format(self.name)
		result += "{0}\n".format(self.value)	
		line1 = "------"
		line2 = "| bit |"
		line3 = "| val |"
		for neuralBit in self.neuralBits:
			# result += str(neuralBit)
			line1 += "----"
			line2 += " {:2}|".format(neuralBit.bitNumber)
			line3 += "{:3.1f}|".format(neuralBit.value)
		return result + line1 + "\n" + line2 + "\n" + line3 + "\n" + line1 + "\n"

	def load(self, neuralFactorsList):
		for i in range(0, self.max_bits):
			self.neuralBits[i].load(neuralFactorsList[i])
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
