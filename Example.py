# Program start
import NecDecoder

# Example
IReader = IRdecoder()

while True:
    sleep(0.1)
    
    if IReader.hasDetected():
        cmd = IReader.getCommand()
        print(cmd)
