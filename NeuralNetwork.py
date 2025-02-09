#
#   Neural Network basic abstract structure
#
#   2024 Kamil Skoczylas
#   MIT Licence
#

from typing import List
from abc import ABC, abstractmethod
import math

class SingleNeuralFactor():

	value = 0
	stability = 1

	def __init__(self, name: str, input_value: float, factor: float) -> None:
		self.name = name
		self.input_value = input_value
		self.factor = factor
		pass

	def __str__(self):
		line1 = "{:4.1f}|".format(self.value)
		line2 = "{:4.1f}|".format(self.factor)
		#line3 = "{:4.0f}|".format(self.stability * 100)
		return  line1 + "\n" + line2

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

	def __init__(self):
		self.neuralFactors = []

	def __str__(self):
		line1 = "{:4.1f}|".format(self.value)
		line2 = ""
  
		for neuralFactor in self.neuralFactors:
			line2 += str(neuralFactor)
   
		line3 = "{:4.0f}|".format(self.stability * 100)
  
		return line1 + "\n" + line2 + "\n" + line3


	def load(self, neuralFactors):
		self.neuralFactors = neuralFactors

	def addFactor(self, neuralFactor: SingleNeuralFactor):
		self.neuralFactors.append(neuralFactor)
		return self.calculate()

	def getFactor(self, number: int):
		return self.neuralFactors[number]

	def getFactorByClass(self, factor_class_type):
		for obj in self.neuralFactors:
			if isinstance(obj, factor_class_type) and hasattr(obj, "value") and hasattr(obj, "factor"):
				return obj
		return

	def getValueFactorByClass(self, factor_class_type):
		for obj in self.neuralFactors:
			if isinstance(obj, factor_class_type) and hasattr(obj, "value") and hasattr(obj, "factor"):
				return (obj.value, obj.factor)
		return (0, 0)

	def updateFactorFactor(self, factor_class_type, value: float):
		property_name = "factor"
		for obj in self.neuralFactors:
			if isinstance(obj, factor_class_type) and hasattr(obj, property_name):
				setattr(obj, property_name, value)
		pass

	def updateFactorValue(self, factor_class_type, value: float):
		property_name = "value"
		for obj in self.neuralFactors:
			if isinstance(obj, factor_class_type) and hasattr(obj, property_name):
				setattr(obj, property_name, value)
		pass

	def sigmoid(x):
		return 1 / (1 + math.exp(-x))

	def calculate(self):
		valueSum = 0
		max_stability = 0
  
		for neuralFactor in self.neuralFactors:
			if neuralFactor.factor > 0:
				valueSum += neuralFactor.calculate()
				max_stability = max(max_stability, neuralFactor.stability * neuralFactor.factor)

		sigmoid_value = self.sigmoid(valueSum)
		self.value = 1 if sigmoid_value > 0 else 0
		self.stability = max(abs(sigmoid_value), max_stability)
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
	value_bits = 0
	minus_negative = False

	def __init__(self, name, max_bits, is_signed, value_bits = 0, minus_negative = True):
		self.name = name
		self.max_bits = max_bits
		self.value_bits = value_bits if value_bits > 0 else max_bits
		self.is_signed = is_signed
		self.neuralBits = []
		self.minus_negative = minus_negative
  
		for i in range(0, max_bits):
			self.neuralBits.append(
				NeuralBoolean()
			)

	def __str__(self):
		result = "{0}\n".format(self.name)
		result += "{0}, HI: {1}, LOW: {2}\n".format(self.value, self.value >> 8, self.value & 255)	
		line1 = "---------"
		line2 = "| bit   |"
		line3 = "| value |"
		line4 = "| OK..% |"

		lines = []
		for neuralFactor in self.neuralBits[0].neuralFactors:
			lines.append("|" + neuralFactor.name[:6] + "V|")
			lines.append("|" + neuralFactor.name[:6] + "F|")
  
		for i in range(self.max_bits - 1, -1, -1):
			neuralBit = self.neuralBits[self.max_bits -1 - i]
			line1 += "-----"
			line2 += " {:3}|".format(i)
			line3 += "{:4.1f}|".format(neuralBit.value)
			line4 += "{:4.0f}|".format(neuralBit.stability * 100)
   
			for j, neuralFactor in enumerate(self.neuralBits[i].neuralFactors):
				lines[j * 2] += "{:4.1f}|".format(neuralFactor.value)
				lines[j * 2 + 1] += "{:4.1f}|".format(neuralFactor.factor)

		return result + line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 + "\n" + ("\n".join(lines)) + "\n" + line1 + "\n"

	def load(self, neuralFactorsList):
		for i in range(0, self.max_bits):
			self.neuralBits[i].load(neuralFactorsList[i])
		pass

	def getBit(self, number: int):
		return self.neuralBits[number]

	def getStabilityBitArray(self):
		stability = [0] * self.max_bits
		for i in range(0, self.max_bits):
			stability[i] = self.neuralBits[i].stability
		return stability

	def getStability(self):
		stability = 1
		for i in range(0, self.max_bits):
			if i < self.value_bits or (i == self.max_bits - 1 and self.is_signed):
				stability = stability * self.neuralBits[i].stability
		return stability


	def updateFactorsFactor(self, factor_class_type, values):
		assert len(values) == self.max_bits, "You must pass the same number of factors ({0}) as the number of value has bits ({1})".format(len(values), self.max_bits)
		for i in range(0, self.max_bits):
			self.neuralBits[i].updateFactorFactor(factor_class_type, values[i])
		pass

	def updateFactorsValue(self, factor_class_type, values):
		assert len(values) == self.max_bits, "You must pass the same number of factors ({0}) as the number of value has bits ({1})".format(len(values), self.max_bits)
		for i in range(0, self.max_bits):
			self.neuralBits[i].updateFactorValue(factor_class_type, values[i])
		pass

	def calculate(self):
		self.value = 0
		multiply_by = 1
		for i in range(0, self.max_bits):
			self.neuralBits[i].calculate()	
		for i in range(0, self.max_bits):
			if i < self.value_bits or ((i == (self.max_bits - 1)) and self.is_signed):
				if round(self.neuralBits[i].value) == 1:
					if (i == (self.max_bits - 1)) and self.is_signed:
						multiply_by = -1
					else:
						self.value += 1 << i
		if self.minus_negative and multiply_by == -1:
			self.value = multiply_by * ((1 << self.value_bits) - self.value)
		else:
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
