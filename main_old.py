import autopy
import threading
import time
import os
import keyboard
from pynput.mouse import Listener
import pyautogui
import logging
from utils import Utils
import tkinter as tk
import cv2
import numpy as np

def hello_world():
    autopy.alert.alert("Hello, world")

def move_mouse():
    autopy.mouse.smooth_move(1, 1)

def type_words():
    autopy.key.type_string("Hello, world!", wpm=100)

def type_letters():
    autopy.key.tap(autopy.key.Code.TAB, [autopy.key.Modifier.META])
    autopy.key.tap("w", [autopy.key.Modifier.META])

def exit_program():
    while True:
        if keyboard.is_pressed('q'):
            os._exit(1)

if __name__ == '__main__':
    # logging.basicConfig(filename="gc_bot.log", format='%(asctime)s %(message)s', filemode='w', level=logging.DEBUG)
    # logger = logging.getLogger()
    # utils = Utils(logger)

    # exit_program = threading.Thread(exit_program, args=())
    # exit_program.start()

    # print(pyautogui.size())
    # counter = 0
    # while True:
    #     if keyboard.is_pressed('b'):
    #         print(pyautogui.position())
    #         time.sleep(1)

