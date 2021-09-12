# Program start
import NECDecoder

GPIO_Mode = GPIO.BCM
GPIO_PIN = 16

# Example
IReader = IRdecoder(GPIO_Mode, GPIO_PIN)

while True:
    sleep(0.1)
    
    if IReader.hasDetected():
        cmd = IReader.getCommand()
        print(cmd)
