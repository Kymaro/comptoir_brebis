import numpy as np

import struct
import pyaudio
import sys
import time
from scipy.fftpack import fft
from neopixel import *

# LED strip configuration:
LED_COUNT = 100  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 127  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

FPS = 60
list_indice = []
current_min = 1000000
current_max = 0


def moy_FFT(list_fft, list_indice):
    average_fft = []
    for i in range(len(list_indice)):
        upper = list_indice[i][1]
        lower = list_indice[i][0]
        sum = 0
        n = upper - lower
        for j in range(n):
            sum += list_fft[lower + j]
        average_fft.append(sum / n)
    return average_fft


def moyfft_To_Led(current_max, current_min, average_fft):
    nb_led = []
    # print(average_fft)
    maximum = max(average_fft)
    minimum = min(average_fft)
    # print(maximum)
    # print(minimum)
    if (current_max < maximum):
        current_max = maximum
    if (current_min > minimum):
        current_min = minimum
    range_led = np.linspace(current_min, current_max, 12)
    for i in range(len(average_fft)):
        for j in range(11):
            if (average_fft[i] >= range_led[j] and average_fft[i] <= range_led[j + 1]):
                nb_led.append(j)
                break
    current_max *= 0.99
    current_min *= 1.01
    return nb_led


def set_indice(start_freq):
    A = [start_freq]
    for i in range(7):
        A.append(A[-1] * 2)
    B = []
    for i in range(len(A)):
        B.append([(int((A[i] / np.sqrt(2)) / 43) + 1), (int((A[i] * np.sqrt(2)) / 43) + 1)])
    return B


class AudioStream(object):
    def __init__(self):

        # pyaudio
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024 * 4
        self.frames_per_buffers = int(1024)

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.frames_per_buffers,
        )

    def update(self, strip):
        y = np.fromstring(self.stream.read(self.frames_per_buffers, exception_on_overflow=False), dtype=np.int16)
        y = y.astype(np.float32)
        self.stream.read(self.stream.get_read_available(), exception_on_overflow=False)  # 735 elements (pas de 60Hz)

        sp_data = fft(y)

        sp_data = np.abs(sp_data[0:int(self.CHUNK / 2)]
                         ) * 2 / (128 * self.CHUNK)

        # print(sp_data)
        sp_amp = []
        for i in range(len(sp_data)):
            sp_amp.append(np.sqrt(np.power(np.real(sp_data[i]), 2) + np.power(np.imag(sp_data[i]), 2)))

        list_average = moy_FFT(sp_amp, list_indice)
        list_led = moyfft_To_Led(current_max, current_min, list_average)

        for i in range(len(list_led)):
            for j in range(10):
                if j <= list_led[i]:
                    if j <= 5:
                        strip.setPixelColor((10 * i) + j, Color(255, 0, 0))
                    elif j > 5 and j <= 8:
                        strip.setPixelColor((10 * i) + j, Color(140, 255, 0))
                    else:
                        strip.setPixelColor((10 * i) + j, Color(0, 255, 0))
                else:
                    strip.setPixelColor((10 * i) + j, Color(0, 0, 0))
        strip.show()


if __name__ == '__main__':
    audio_app = AudioStream()
    list_indice = set_indice(60)
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    while True:
        audio_app.update(strip)
# time.sleep(0.02)
