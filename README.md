# NEC-Decoder

Designed and tested on Raspberry PI Zero
Version 0.1
Python 3 required

The idea of this module is to retrieve, translate and fill in missing InfraRed signal for Raspberry PI 

IR Signal recorded by a sound card using Line-in looks like this one:
![Recorded IR Signal](https://github.com/kamilskoczylas/NEC-Decoder/blob/main/Tests/RecordedIRsignal.jpg?raw=true)
- 9 miliseconds of positive signal
- 4.5 miliseconds of negative
- 27 miliseconds 8-bit Address and 8-bit of inversed address
- 27 miliseconds 8-bit Command and 8-bit inversed command

Example from the recording:
- Address: 00000000 11111111
- Command: 10100010 01011101

---
Requirements
-

Before using with Raspberry Zero make sure your Raspberry PI has
- appropriate power adapter
- good cooling
- use Python 3

Additionally, follow IR Receiver documentation to use appropriate resistors to eliminate unnecessary noises

---
NEC Decoder Example 
-

```
# Only for value of GPIO.BCM
import RPi.GPIO as GPIO 
from time import sleep 

import NEC
import SignalDecoder
import GPIODataProvider

GPIO_Mode = GPIO.BCM
GPIO_PIN = 16


IReader = SignalDecoder.SignalDecoder(
    GPIODataProvider.EdgeDetected(
        GPIO_Mode,
        GPIO_PIN
    ),
    NEC.NECDecoder()
    )

while True:
    sleep(0.1)

    if IReader.hasDetected():
        cmd = IReader.getCommand()
        print(cmd)
```


---

# DHT22 Signal Decoder: Humidity and temperature

Designed and tested on Raspberry PI 3A+
Version 0.1
Python 3 required

Recorded DHT22 signal (using sound card line-in)
![Recorded DHT22 Signal](https://github.com/kamilskoczylas/NEC-Decoder/blob/main/Tests/DHT22-Recorded-signal.png?raw=true)

Chart created from the data collected by the DHT22 class. Two DHT22 devices have been connected to single raspberryPI 3A+. One measures temperature and humidity inside, another one outside.
![2 DHT22 connected: inside and outside](https://github.com/kamilskoczylas/NEC-Decoder/blob/main/Tests/TemperatureInsideOutside.png?raw=true)

---
Requirements
-

- Raspberry 3 or better 
- use Python 3

---
DHT22 Sensor Example
-

```

from time import sleep 

import TemperatureSensor

GPIO_PIN = 12

# DHT22 connected to PIN 12 of Raspberry (BCM), class refresh every 2 seconds
Sensor = TemperatureSensor.TemperatureSensor(GPIO_PIN, 2)

while True:
    print("Temperature = {temperature}°C, Humidity = {humidity}%".format(temperature=Sensor.Temperature, humidity=Sensor.Humidity))
    sleep(2)


```
