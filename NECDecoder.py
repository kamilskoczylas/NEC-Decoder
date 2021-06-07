#
#   IR Receiver
#   NEC Protocol
#   Designed for Raspberry Pi
#   Tested on Raspberry Pi Zero
#   2021 Kamil Skoczylas
#

import RPi.GPIO as GPIO
from time import sleep
from timeit import default_timer
from Queue import Queue
from Queue import Empty
from threading import Thread


class IRdecoder:

    startIRTimeQueue = 0
    MAX_QUEUE_SIZE = 512
    MAX_COMMANDS = 10
    DEBUG = True
    
    GPIO_Mode = GPIO.BCM
    GPIO_PIN = 16
    
    class NECDecoder:
        AddressLengthSeconds = 0.027
        CommandLengthSeconds = 0.027
        
        # Maximum value is half of the difference between
        # positive and negative signal length: 0.00055125
        PulseErrorRange = 0.00055125
        
        PULSE_POSITIVE_LENGTH = 0.00225
        PULSE_NEGATIVE_LENGTH = 0.001125
        
        REPEAT_BURST_SHORT_LENGTH = 0.045
        REPEAT_BURST_LONG_LENGTH = 0.097
        REPEAT_BURST_ERROR_RANGE = 0.01
        
        breakTime = 0
        ir_pulseStart = 0
        timeFromNextPhase = 0
        
        REMOTE_CONTROLLER_COMMANDS = {
            "00001100": "ON",
            "00011010": "OK",
            "01011010": "RIGHT"
            }
        
        REMOTE_CONTROLLERS = {
            "10110100": "DVD",
            "00000000": "Custom"
            }
        
        DEBUG = False
        
        def __init__(self, timeQueue, DebugMode = False):
            
            self.IRTimeQueue = timeQueue
            self.DEBUG = DebugMode
            
        def getBurst(self, pulseCount, burstStartTime, maxTime):
            resultArray = []
            edgeTimeDetected = burstStartTime
            previousPulseStart = burstStartTime
            i = 0
            
            while i < pulseCount and edgeTimeDetected <= maxTime:
                i += 1

                try:
                    edgeTimeDetected = self.IRTimeQueue.get_nowait()
                    self.IRTimeQueue.task_done()
                    signalTime = edgeTimeDetected - previousPulseStart
                        #min(maxTime - previousPulseStart, edgeTimeDetected - previousPulseStart)
                
                except Empty:
                    #if default_timer() >= maxTime:
                    #edgeTimeDetected = maxTime
                    #signalTime = maxTime - previousPulseStart
                    
                    #if self.DEBUG:
                    print("Empty: {0}".format(len(resultArray)))
                    
                    if (maxTime - previousPulseStart < self.REPEAT_BURST_ERROR_RANGE):
                        break
                    
                    print (resultArray)
                    print("Left: {0}".format(maxTime - previousPulseStart))
                    edgeTimeDetected = self.IRTimeQueue.get()
                    self.IRTimeQueue.task_done()
                    signalTime = edgeTimeDetected - previousPulseStart
                    
                resultArray.append(signalTime)
                previousPulseStart = edgeTimeDetected
                if self.DEBUG:
                    print ("{0} {1}".format(i, signalTime))
            
            self.timeFromNextPhase = edgeTimeDetected - maxTime
            #print ("{0} {1}".format(i, self.timeFromNextPhase))
            #resultArray.append(self.timeFromNextPhase)
            
            # To future calculation of breakTime
            self.ir_pulseStart = edgeTimeDetected
            return resultArray
        
        def getFirst16bitsOr27ms(self, arrayOfPulses):
            first16or27ms = []
            i = 0
            totalTime = 0
            
            while i < 16 and totalTime <= self.AddressLengthSeconds and len(arrayOfPulses) > 0:
                i += 1
                signalTime = arrayOfPulses.pop(0)
                first16or27ms.append(signalTime)
                totalTime += signalTime
            
            return first16or27ms
            
        def getCommand(self):
            
            signalTime = self.waitForSignal()
            repeatCode = False
            self.timeFromNextPhase = 0
            
            if self.DEBUG:
                print("Break: {0}".format(self.breakTime))
            
            if self.breakTime > self.REPEAT_BURST_SHORT_LENGTH - self.REPEAT_BURST_ERROR_RANGE and self.breakTime < self.REPEAT_BURST_SHORT_LENGTH + self.REPEAT_BURST_ERROR_RANGE:
                repeatCode = True
            if self.breakTime > self.REPEAT_BURST_LONG_LENGTH - self.REPEAT_BURST_ERROR_RANGE and self.breakTime < self.REPEAT_BURST_LONG_LENGTH + self.REPEAT_BURST_ERROR_RANGE:
                repeatCode = True
            
            if repeatCode:
                return 'REPEAT'
            
            new_signalStart = self.ir_pulseStart + self.AddressLengthSeconds + self.PulseErrorRange
            pulseArray = self.getBurst(32, self.ir_pulseStart, self.ir_pulseStart + self.AddressLengthSeconds + self.CommandLengthSeconds)    
            
            addressArray = self.getFirst16bitsOr27ms(pulseArray)
            address = self.fillInKnownValues(addressArray)
            
            commandArray = pulseArray
            command = self.fillInKnownValues(commandArray)
            
            if self.DEBUG:
                print("Address: {0}".format(address))
                print("Command: {0}".format(command))
            
            if type(address) != str or type(command) != str:
                return False
            
            return { "hex": self.ConvertString16ToHex(address[:8] + command[:8]),
                     "address": address,
                     "command": command,
                     "bestCommand": self.bestCommand(command),
                     "bestAddress": self.bestAddress(address)
                     }
        
        def calculateSimilarity(self, string1, string2, string3):
            i = 0
            score = 0
            for character in string1:
                if len(string2) >= i and string2[i:1] != '_':
                    if character == string2[i:1]:
                        score += 1
                    else:
                        score -= 1
                    
                if len(string3) >= i and string3[i:1] != '_':
                    if character != string3[i:1]:
                        score += 1
                    else:
                        score -= 1
                    
            return score
                
            
        
        def bestMatch(self, command, arrayOfMatches):
            bestValue = ''
            bestScore = 0
            i = 0
            
            for key in arrayOfMatches:
                score = self.calculateSimilarity(key, command[:8], command[8:16])
                if bestScore < score:
                    bestScore = score
                    bestValue = arrayOfMatches[key]
            
            return {
                "score": bestScore,
                "value": bestValue
                }
        
        def bestAddress(self, command):
            return self.bestMatch(command, self.REMOTE_CONTROLLERS)
        
        def bestCommand(self, command):
            return self.bestMatch(command, self.REMOTE_CONTROLLER_COMMANDS)
        
        def ConvertString16ToHex(self, binaryStringValue):
            result = 0
            i = 0
            if len(binaryStringValue) != 16:
                return hex(0)
            
            for character in binaryStringValue:
                i += 1
                if character == '1':
                    result |= 1 << (16 - i)
                    
                if character == '_':
                    return hex(0)
                    
            return hex(result)
            
        def waitForSignal(self):
            self.breakTime = 0
            while True:
                # Try to find start 
                edgeTimeDetected = self.IRTimeQueue.get()
                #self.IRTimeQueue.task_done()
                
                # Let Raspberry read whole signal before
                # we use max CPU for decoding
                signalTime = edgeTimeDetected - self.ir_pulseStart
                self.ir_pulseStart = edgeTimeDetected
                
                # If signal starts 13,5ms
                if signalTime > 0.0035 and signalTime < 0.015:
                    sleep(0.2)
                    #new_time = default_timer()
                    #while new_time < edgeTimeDetected + 0.054:
                    #    sleep(0.01)
                    #    new_time = default_timer()
                    
                    return signalTime
                else:
                    self.breakTime = signalTime
                    
                    if self.DEBUG:
                        print("Wrong start signal", signalTime)
                    
                sleep(0.01)
                
        def enhanceArray(self, timeArray):
            newArray = []
            
            correctSignal = ''
            correctChunks = []
            timeToCorrectArray = []
            chunk = ''
            wrongLength = 0
            
            for pulseLength in timeArray:
                
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
                
                if self.DEBUG:
                    print ("error {0}".format(errorTime))
                
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
                
                if self.DEBUG:
                    print ("{0} result: {1}".format(testedSignal, validated))
                    
                if validated:
                    result = testedSignal
                    break
                
            if not result:
                result = self.getCorrectPattern(correctSignal, correctChunks)
                
            return result
        
        def getCorrectPattern(self, correctSignal, correctChunks):
            if len(correctSignal) < 10:
                return False
            
            correctS = ''
            connector = ''
            if correctSignal[0] == '0':
                connector = "__"
                
            for correct in correctChunks:
                correctS += connector + correct
                connector = "__"
                
            return correctS
        
        def connectSignalParts(self, correctSignal, correctChunks, combinationToTest):
            concatenated = ''
            i_correct = 0
            i_wrong = 0
            lastCharacter = ''
            
            if len(correctSignal) < 10:
                # print ("Too many errors")
                return False
            
            if self.DEBUG:
                correctS = self.getCorrectPattern()
                print ("For {0} testing:".format(correctSignal))
                
                for combination in combinationToTest:
                    print (combination)
                
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
                return ['011', '110', '101', '1000', '0100', '0010', '0001'] #, '0101', '1100', '0110', '0011', '1010'
            
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
                #    # print(element)
                # print("---")
            
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
            
            # print("Combination Mix")
            # self.printCombination(combinationMix)
            
            while not finished:
                combinationArray = []
                
                for i in range(0, max_key):
                    # print ("Combination: i={0} value = {1}".format(i, indexes[i]))
                    combinationArray.append(combinationMix[i][indexes[i]])
                
                finished = not self.incrementIndexes(indexes, max_values, 0, max_key)
                    
                allCombinations.append(combinationArray)
                # self.printCombination(combinationArray)
                
            return allCombinations
            
        def validateCombinationSignal(self, signalString):
            if type(signalString) != str:
                return False
            
            if len(signalString) != 16:
                if self.DEBUG:
                    print("Invalid length")
                return False
            
            difference = 0
            for i in range(0, 8):
                if signalString[i] != signalString[i + 8]:
                    difference += 1
                    
            if difference > 0 and difference < 8:        
                if self.DEBUG:
                    print("Invalid reflection")
                return False
                
            return True
            
            
                
        def fillInKnownValues(self, timeArray):
            commandDecoded = ''
            #finalSignalString =
            return self.enhanceArray(timeArray)
            #return (finalSignalString)
            
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
    
    def __init__(self, GPIO_Mode = None, GPIO_PIN = None):
        
        self.IRTimeQueue = Queue(self.MAX_QUEUE_SIZE)
        self.Commands = Queue(self.MAX_COMMANDS)
        
        if not GPIO_Mode is None:
            self.GPIO_Mode = GPIO_Mode
            
        if not GPIO_PIN is None:    
            self.GPIO_PIN = GPIO_PIN
        
        worker = Thread(target=self.QueueConsumer)
        worker.daemon = True
        worker.start()
        
        GPIO.setmode(self.GPIO_Mode)
        GPIO.setup(self.GPIO_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP) 
        GPIO.add_event_detect(self.GPIO_PIN, GPIO.RISING, callback = self.SignalEdgeDetected) #, bouncetime = 70)

    
    def QueueConsumer(self):
        
        nec = self.NECDecoder(self.IRTimeQueue, self.DEBUG)
        while True:
            
            currentCommand = nec.getCommand()
            self.Commands.put_nowait(currentCommand)
            
            # Minimum time for next IR command
            sleep(0.07)
            
    def DecodeIRTimeQueue(self):
        self.ConvertArray(self.IRTimeQueue)
        self.Reset()
    
    def hasDetected(self):
        return not self.Commands.empty()
    
    def getCommand(self):
        command = self.Commands.get_nowait()
        self.Commands.task_done()
        return command
            
    # Too many errors
    def SignalEdgeDetected(self, PinNumber):
        self.IRTimeQueue.put_nowait(default_timer())
        
    def WaitUntilEndOfSignal(self, Zero_One, PinNumber):
        input_value = Zero_One
        i = 0
        while input_value == Zero_One and i < 1000:
                input_value = GPIO.input(PinNumber)
                i += 1
                
    # New approach
    def SignalDetected(self, PinNumber):
        
        currentTime = default_timer()
        self.IRTimeQueue.put_nowait(currentTime)
        
        # Wait until end of beginning signal, aprox. 9ms and 4.5 ms
        self.WaitUntilEndOfSignal(1, PinNumber)
        self.WaitUntilEndOfSignal(0, PinNumber)
        
        currentTime = default_timer()
        self.IRTimeQueue.put_nowait(currentTime)
        
        # Maximum time when we need to keep reading, 54ms
        maxTime = currentTime + 0.054
        
        # After detecting a signal, try to catch remaining pulses in loop
        pulsesCount = 0
        while currentTime < maxTime and pulsesCount < 32:
            
            self.WaitUntilEndOfSignal(1, PinNumber)
            currentTime = default_timer()
            self.IRTimeQueue.put_nowait(currentTime)
            pulsesCount += 1
            
            self.WaitUntilEndOfSignal(0, PinNumber)
                
             
                
            
        
    def __del__(self):
        GPIO.cleanup(self.GPIO_PIN)

    
# Program start
# Example
IReader = IRdecoder()

while True:
    sleep(0.1)
    
    if IReader.hasDetected():
        cmd = IReader.getCommand()
        print(cmd)



