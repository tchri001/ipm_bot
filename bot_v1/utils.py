import os
import pyautogui
import keyboard
import mss

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

    def capture_region(self, x, y, width, height, output_file):
        self.logger.debug("Taking a screenshot")
        """
        Captures a screenshot of a defined region of the screen.

        Parameters:
            x (int): The x-coordinate of the top-left corner.
            y (int): The y-coordinate of the top-left corner.
            width (int): The width of the region.
            height (int): The height of the region.
            output_file (str): The file name to save the screenshot.
        """
        with mss.mss() as sct:
            # Define the region to capture
            region = {"top": y, "left": x, "width": width, "height": height}
            # Capture the region
            screenshot = sct.grab(region)
            # Save the screenshot to a file
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=output_file)
            self.logger.debug(f"Screenshot saved as {output_file}")
