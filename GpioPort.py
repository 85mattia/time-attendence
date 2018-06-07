# -*- coding: UTF-8 -*-
#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
from threading import Timer


class Sound():

    n = 1
    
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(35, GPIO.OUT)
        GPIO.output(35, GPIO.LOW)
        
    def bip(self, nBip=1):
        self.n = nBip
        self.startSound()

        
    def stopSound(self):
        GPIO.output(35, GPIO.LOW)
        self.n -= 1
        if self.n != 0:
            print(str(self.n))
            self.timer = Timer(0.05, self.startSound)
            self.timer.start()

    def startSound(self):
        GPIO.output(35, GPIO.HIGH)
        self.timer = Timer(0.14, self.stopSound)
        self.timer.start()

if __name__ == "__main__":
    s = Sound()
    s.bip(4)
