#
#    IR Circular buffer decoder
#

import RPi.GPIO as GPIO
from time import sleep
from timeit import default_timer
from Queue import Queue
from threading import Thread


class IRdecoder:

    startIRTimeQueue = 0
    MAX_QUEUE_SIZE = 512
    MAX_COMMANDS = 10
    
    class NECDecoder:
        AddressLengthSeconds = 0.027
        CommandLengthSeconds = 0.027
        PulseErrorRange = 0.0008
        
        PULSE_POSITIVE_LENGTH = 0.00225
        PULSE_NEGATIVE_LENGTH = 0.001125
        
        REPEAT_BURST_SHORT_LENGTH = 0.04
        REPEAT_BURST_LONG_LENGTH = 0.097
        REPEAT_BURST_ERROR_RANGE = 0.01
        
        AddressString = ''
        AddressInvertedString = ''
        CommandString = ''
        CommandInvertedString = ''
        breakTime = 0
        ir_pulseStart = 0
        timeFromNextPhase = 0
        accurracyArray = []
        
        def __init__(self, timeQueue):
            
            self.IRTimeQueue = timeQueue
            
        def getBurst(self, pulseCount, burstStartTime, maxTime):
            resultArray = []
            edgeTimeDetected = burstStartTime
            previousPulseStart = burstStartTime
            i = 0
            
            while i < 16 and edgeTimeDetected <= maxTime:
                i += 1
                
                if self.IRTimeQueue.empty():
                    edgeTimeDetected = maxTime
                    signalTime = maxTime - previousPulseStart
                else:
                    edgeTimeDetected = self.IRTimeQueue.get()
                    self.IRTimeQueue.task_done()
                    signalTime = edgeTimeDetected - previousPulseStart
                    
                resultArray.append(signalTime)
                previousPulseStart = edgeTimeDetected
                print ("{0} {1}".format(i, signalTime))
            
            self.timeFromNextPhase = edgeTimeDetected - maxTime
            
            # To future calculation of breakTime
            self.ir_pulseStart = edgeTimeDetected
            return resultArray
            
        def getCommand(self):
            
            signalTime = self.waitForSignal()
            print("Break: {0}".format(self.breakTime))
            repeatCode = False
            self.timeFromNextPhase = 0
            
            if self.breakTime > self.REPEAT_BURST_SHORT_LENGTH - self.REPEAT_BURST_ERROR_RANGE and self.breakTime < self.REPEAT_BURST_SHORT_LENGTH + self.REPEAT_BURST_ERROR_RANGE:
                repeatCode = True
            if self.breakTime > self.REPEAT_BURST_LONG_LENGTH - self.REPEAT_BURST_ERROR_RANGE and self.breakTime < self.REPEAT_BURST_LONG_LENGTH + self.REPEAT_BURST_ERROR_RANGE:
                repeatCode = True
            
            if repeatCode:
                #print ("Repeat")
                #edgeTimeDetected = self.IRTimeQueue.get()
                #self.IRTimeQueue.task_done()
                #signalTime = edgeTimeDetected - self.ir_pulseStart
                
                print ("Break: {0} Repeat time: {1}".format(self.breakTime, signalTime))
                return 'REPEAT'
            
            ir_addressStart = self.ir_pulseStart
            edgeTimeDetected = ir_addressStart
            
            addressArray = self.getBurst(16, edgeTimeDetected, self.ir_pulseStart + self.AddressLengthSeconds + self.PulseErrorRange)    
            address = self.fillInKnownValues(addressArray)
            print("Address: {0}".format(address))
            
            ir_commandStart = self.ir_pulseStart
            commandArray = self.getBurst(16, self.ir_pulseStart, ir_commandStart - self.timeFromNextPhase + self.CommandLengthSeconds + self.PulseErrorRange)    
            command = self.fillInKnownValues(commandArray)
            print("Command: {0}".format(command))
            
            if not address or not command:
                return False
            
            return self.ConvertString16ToHex(address[:8] + command[:8])
        
        def ConvertString16ToHex(self, binaryStringValue):
            result = 0
            i = 0
            for character in binaryStringValue:
                i += 1
                if character == '1':
                    result |= 1 << (16 - i)
                    
            return hex(result)
            
        def waitForSignal(self):
            self.breakTime = 0
            while True:
                # Try to find start 
                edgeTimeDetected = self.IRTimeQueue.get()
                self.IRTimeQueue.task_done()
                
                signalTime = edgeTimeDetected - self.ir_pulseStart
                self.ir_pulseStart = edgeTimeDetected
                
                # If signal starts 13,5ms
                if signalTime > 0.008 and signalTime < 0.015:   
                    # Let Raspberry read whole signal before
                    # we use max CPU for decoding
                    sleep(0.54)
                    return signalTime
                else:
                    self.breakTime = signalTime
                    print("Wrong start signal", signalTime)
                    
                sleep(0.1)
                
        def enhanceArray(self, timeArray):
            newArray = []
            
            #timeArray[0] += self.timeFromNextPhase
            correctSignal = ''
            correctChunks = []
            timeToCorrectArray = []
            chunk = ''
            wrongLength = 0
            
            for pulseLength in timeArray:
                #newArray.append(pulseLength)
                
                if pulseLength > self.PULSE_POSITIVE_LENGTH - self.PulseErrorRange / 2 and pulseLength < self.PULSE_POSITIVE_LENGTH + self.PulseErrorRange / 2:
                    correctSignal += '1'
                    chunk += '1'
                    
                    # next correct pulse found, so we end the wrong period if it was
                    if wrongLength > 0:
                            timeToCorrectArray.append(wrongLength)
                            wrongLength = 0
                        
                elif pulseLength > self.PULSE_NEGATIVE_LENGTH - self.PulseErrorRange / 2 and pulseLength < self.PULSE_NEGATIVE_LENGTH + self.PulseErrorRange / 2:
                        correctSignal += '1'
                        chunk += '0'
                        
                        # next correct pulse found, so we end the wrong period if it was
                        if wrongLength > 0:
                            timeToCorrectArray.append(wrongLength)
                            wrongLength = 0
                else:
                    # Wrong pulse length found
                    # Need to notice wrong time for later bug recovery
                    
                    # 1. save partial correct signal
                    if len(chunk) > 0:
                        correctChunks.append(chunk)
                        
                    # 2. reset next partial correct signal
                    chunk = ''
                    
                    # 3. Add information about wrong signal found
                    if pulseLength > 0 and wrongLength == 0:
                        correctSignal += '0'
                        
                    # 4. As we cannot rely on length read by RaspBerry,
                    #    better to concatenate incorrect signal and try to
                    #    check all possibilities
                    wrongLength += pulseLength
                    
                    
            if wrongLength > 0:
                timeToCorrectArray.append(wrongLength)
                
            if len(chunk) > 0:
                correctChunks.append(chunk)
                    
            combinationsMix = []
            for errorTime in timeToCorrectArray:
                
                print ("error {0}".format( errorTime))
                
                possibleCombinations = self.getCombinationsForTime(errorTime)
                if not possibleCombinations:
                    return False
                
                combinationsMix.append(possibleCombinations)
            
            result = False
            if correctSignal == '1111111111111111':
                result = chunk
            
            for combinationToTest in self.getAllCombinations(combinationsMix):
                testedSignal = self.connectSignalParts(correctSignal, correctChunks, combinationToTest)
                validated = self.validateCombinationSignal(testedSignal)
                print ("{0} result: {1}".format(testedSignal, validated))
                if validated:
                    result = testedSignal
                    break
                
            return result
        
        def connectSignalParts(self, correctSignal, correctChunks, combinationToTest):
            concatenated = ''
            i_correct = 0
            i_wrong = 0
            lastCharacter = ''
            
            if len(correctSignal) < 10:
                print ("Too many errors")
                return False
            
            print ("For {0} testing:".format(correctSignal))
            for combination in combinationToTest:
                print (combination)
                
            correctS = ''
            connector = ''
            if correctSignal[0] == '0':
                connector = "__"
                
            for correct in correctChunks:
                correctS += connector + correct
                connector = "__"
                
            print (correctS)
            
            for character in correctSignal:
                if character == '1':
                    if lastCharacter != character:
                        concatenated += correctChunks[i_correct]
                        i_correct += 1
                else:
                    concatenated += combinationToTest[i_wrong]
                    i_wrong += 1
                    
                lastCharacter = character
                    
            return concatenated

        
        def getCombinationsForTime(self, pulseLengthDetected):
            if pulseLengthDetected > 3 * self.PULSE_POSITIVE_LENGTH - self.PulseErrorRange / 2:
                return False
            
            if pulseLengthDetected > self.PULSE_NEGATIVE_LENGTH + 2 * self.PULSE_POSITIVE_LENGTH - self.PulseErrorRange / 2:
                return ['011', '110', '101', '1000', '0100', '0010', '0001', '0101', '1100', '0110', '0011', '1010']
            
            if pulseLengthDetected > 2 * self.PULSE_POSITIVE_LENGTH - self.PulseErrorRange:
                return ['11', '100', '010', '001', '000', '0000']
            
            if pulseLengthDetected > self.PULSE_NEGATIVE_LENGTH + self.PULSE_POSITIVE_LENGTH - self.PulseErrorRange:
                return ['10', '01', '000']
            
            if pulseLengthDetected > self.PULSE_POSITIVE_LENGTH - self.PulseErrorRange / 2:
                return ['1', '00']
            
            return ['0', '1']
            
        def printCombination(self, combination):
            for elements in combination:
                print(elements)
                
                #for element in elements:
                #    print(element)
                print("---")
            
        def incrementIndexes(self, indexes, max_values, key, max_key):
            if key >= max_key:
                return False
            
            if (max_values[key] > indexes[key]):
                indexes[key] += 1
                return True
            else:
                indexes[key] = 0
                return self.incrementIndexes(indexes, max_values, key + 1, max_key)
            
            
        def getAllCombinations(self, combinationMix):
            allCombinations = []
            max_key = len(combinationMix)
            indexes = [0] * max_key
            max_values = [0] * max_key
            
            for i in range(0, max_key):
                max_values[i] = len(combinationMix[i]) - 1
                
            finished = False
            
            print("Combination Mix")
            self.printCombination(combinationMix)
            
            while not finished:
                combinationArray = []
                
                for i in range(0, max_key):
                    print ("Combination: i={0} value = {1}".format(i, indexes[i]))
                    combinationArray.append(combinationMix[i][indexes[i]])
                
                finished = not self.incrementIndexes(indexes, max_values, 0, max_key)
                    
                allCombinations.append(combinationArray)
                self.printCombination(combinationArray)
                
            return allCombinations
            
        def validateCombinationSignal(self, signalString):
            if type(signalString) != str:
                return False
            
            if len(signalString) != 16:
                print("Invalid length")
                return False
            
            #ones = 0
            #for pulse in signalString:
            #    if pulse == '1':
            #        ones += 1
                    
            #if ones != 8:
            #    print("Invalid 1 count")
            #    return False
            
            difference = 0
            for i in range(0, 8):
                if signalString[i] != signalString[i + 8]:
                    difference += 1
                    
            if difference > 0 and difference < 8:        
                print("Invalid reflection")
                return False
                
            return True
            
            
                
        def fillInKnownValues(self, timeArray):
            commandDecoded = ''
            finalSignalString = self.enhanceArray(timeArray) 
            
            if not finalSignalString:
                return False
            
            if len(finalSignalString) != 16:
                return False
            
            differences = 0
            
            for i in range(0, 8):
                if finalSignalString[i] == finalSignalString[i + 8]:
                    differences += 1
                    
            if differences > 0 and differences < 8:
                return False
            
            commandDecoded = finalSignalString  
            return commandDecoded
    
    def __init__(self):
        self.IRTimeQueue = Queue(self.MAX_QUEUE_SIZE)
        self.Commands = Queue(self.MAX_COMMANDS)
        
        worker = Thread(target=self.QueueConsumer)
        worker.daemon = True
        worker.start()
    
    def QueueConsumer(self):
        
        nec = self.NECDecoder(self.IRTimeQueue)
        while True:
            
            currentCommand = nec.getCommand()
            
            if currentCommand != '':
                self.Commands.put_nowait(currentCommand)
                
            sleep(0.1)
            
    def DecodeIRTimeQueue(self):
        self.ConvertArray(self.IRTimeQueue)
        self.Reset()
    
    def isDetected(self):
        return not self.Commands.empty()
    
    def getCommand(self):
        command = self.Commands.get_nowait()
        self.Commands.task_done()
        return command
            
    def SignalEdgeDetected(self, PinNumber):
        self.IRTimeQueue.put_nowait(default_timer())
        

    
IReader = IRdecoder()
old = 0    
detect = False
i = 1
lastIRTimeQueue = ""
repeat = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
GPIO.add_event_detect(16, GPIO.FALLING, callback = IReader.SignalEdgeDetected)

command = 0
lastCommand = 0

while True:
    sleep(0.002)
    
    if IReader.isDetected():
        cmd = IReader.getCommand()
        print(cmd)
        #print("{0} {1} {2} {3}".format(cmd[0:8], cmd[8:16], cmd[16:24], cmd[24:32]))
    

GPIO.cleanup(16)