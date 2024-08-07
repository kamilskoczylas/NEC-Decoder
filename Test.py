# Tests using text file data

from time import sleep 
from timeit import default_timer
from abc import ABC
from unittest import TestCase
import SignalDecoder
import datetime
import NEC
import DHT22

class TestDataProvider(ABC):

    expectedResult = []
    
    def InitDataQueue(self, queue):
        self.Queue = queue
        pass

    def ReadFile(self, filename, addZeroTime = False):
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



class NECTesting(TestCase):
    
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
        

class DHT22Testing(TestCase):
    
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
        
