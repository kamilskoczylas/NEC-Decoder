# NEC-Decoder

Designed and tested on Raspberry PI Zero
Version 0.1
Python 3 required

The idea of this module is to retrieve, translate and fill in missing InfraRed signal for Raspberry PI 

This module try to guess missing signal phrases.

Before using with Raspberry Zero make sure your Raspberry PI has
- appropriate power adapter
- good cooling

Additionally, follow IR Receiver documentation to use appropriate resistors to eliminate unnecessary noises

Use case example:

    
    # Only for value of GPIO.BCM
    import RPi.GPIO as GPIO 
    # Sleeping allows CPU to increase performance for other applications on Raspberry
    # CPU goes down from 100% to 5-15% on NECDecoder
    from time import sleep 
    
    from NECDecoder import IRdecoder

    GPIO_Mode = GPIO.BCM
    GPIO_PIN = 16

    # Initialization of the class. Sets thread deamon
    # Default values are GPIO.BCM and PIN 16
    IReader = IRdecoder(GPIO_Mode, GPIO_PIN)

    while True:
        sleep(0.1)

        if IReader.hasDetected():
            cmd = IReader.getCommand()
            print(cmd)
