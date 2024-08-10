# Tests using text file data

from time import sleep 
from timeit import default_timer
from abc import ABC
import unittest
import SignalDecoder
import datetime
import NEC
import DHT22
from NeuralNetwork import SingleNeuralFactor, NeuralValue, NeuralCalculation


class TestDataProvider(ABC):

    expectedResult = []
    
    def InitDataQueue(self, queue):
        self.Queue = queue
        pass

    def ReadFile(self, filename, addZeroTime=False):
        with open("Tests/" + filename, "r") as file:
            lines = file.readlines()
            
        timeline = False
        result = False
        previous_signal = 0
        
        edge_number = 0
        for line in lines:
            if timeline:
                words = line.split()
                edge_number += 1
                if len(words) == 2 and int(words[0]) == edge_number:
                    previous_signal += float(words[1])
                    self.Queue.put_nowait(previous_signal)
                else:
                    timeline = False
            else:
                print(line)
                
            if 'Timeline' in line:
                timeline = True
                edge_number = 0
                previous_signal = default_timer()
                if addZeroTime:
                    self.Queue.put_nowait(previous_signal)

            if result:
                self.expectedResult.append(line)
            if 'Returns' in line:
                result = True
            else:
                result = False
            
        pass


class NECTesting(unittest.TestCase):
    
    def test_001(self):
        self.testProvider = TestDataProvider()
        self.IReader = SignalDecoder.SignalDecoder(self.testProvider, NEC.NECDecoder())
        self.testProvider.ReadFile("test-001.txt")
        sleep(0.1)
        for result in self.testProvider.expectedResult:
            cmd = self.IReader.getCommand()
            print(cmd)
            print("Expected:" + result)
            self.assertTrue(type(cmd) is dict and "hex" in cmd and cmd['hex'] in result)
            sleep(0.1)
        pass
        

class DHT22Testing(unittest.TestCase):
    
    def dht_test_001(self):
        self.dhtTestProvider = TestDataProvider()
        self.DHT22Reader = SignalDecoder.SignalDecoder(self.testProvider, DHT22.DHT22Decoder(), True)
        self.testProvider.ReadFile("test-dht22-01.txt", True)
        sleep(0.1)
        
        for result in self.testProvider.expectedResult:
            cmd = self.DHT22Reader.getCommand()
            print(cmd)
            print("Expected:" + result)
            self.assertTrue(result == "Result = {0}, Temperature = {1}°C, Humidity = {2}%. Avg. Temperature = {3}°C, Avg. Humidity = {4}%".format(cmd['result'], cmd['temperature'], cmd['humidity'], cmd['avg_temperature'], cmd['avg_humidity']))
            sleep(0.1)
        pass

        
class NeuralNetworkTesting(unittest.TestCase):
    
    def basic_concepts(self):
        neuralValue = NeuralValue("value", 2, False)
        neuralValue.load()
        
        oneFactor = SingleNeuralFactor("one", 1, 1)
        self.assertTrue(oneFactor.calculate() == 1)

        zeroFactor = SingleNeuralFactor("zero", 0, 1)
        self.assertTrue(zeroFactor.calculate() == 0)

        neuralBit0 = neuralValue.getBit(0)
        neuralBit0.addFactor(zeroFactor)
        self.assertTrue(neuralBit0.calculate() == 0)

        neuralBit1 = neuralValue.getBit(1)
        neuralBit1.addFactor(oneFactor)
        self.assertTrue(neuralBit1.calculate() == 1)

        print(neuralValue)
        self.assertTrue(neuralValue.calculate() == 2)
        pass


if __name__ == '__main__':
    unittest.main()
