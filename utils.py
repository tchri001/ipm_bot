import os
import pyautogui
import keyboard

class Utils:
    def __init__(self, logger):
        self.logger = logger

    #Find an image with optional screen region constraint
    def find_image(self, image, type, confidence=0.8, region=None):
        image_path = 'images/'+type+'/'+image+'.png'

        if region is None:
            x,y = pyautogui.locateCenterOnScreen(image=image_path, confidence=confidence)
        else:
            x,y = pyautogui.locateCenterOnScreen(image=image_path, confidence=confidence, region=region)
        
        return x,y
    
    #Click on passed in coordinates (more reliable than pyautogui.click())
    def mouse_click(self, x, y):
        self.logger.debug(f'Clicking: {x},{y}')
        pyautogui.moveTo(x, y)
        pyautogui.mouseDown()
        pyautogui.mouseUp()

    #Chain find and click together
    def click_image(self, image, region=None, confidence=0.8):
        x,y = self.find_image(image, confidence, region)
        pyautogui.click(x,y+10)
        #self.mouse_click(x,y)

    #Polling function to exit program on 'q' key press
    def exit_program(self):
        while True:
            if keyboard.is_pressed('q'):
                self.logger.debug('EXITING PROGRAM')
                os._exit(1)