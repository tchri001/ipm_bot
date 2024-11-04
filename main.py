import autopy
import pyautogui
import pytesseract
import easyocr
import time
from mss.windows import MSS as mss
import os
import threading
import keyboard

def hello_world():
    autopy.alert.alert("Hello, world")

def move_mouse():
    autopy.mouse.smooth_move(1, 1)

def type_words():
    autopy.key.type_string("Hello, world!", wpm=100)

def type_letters():
    autopy.key.tap(autopy.key.Code.TAB, [autopy.key.Modifier.META])
    autopy.key.tap("w", [autopy.key.Modifier.META])

#Polling function to exit program on 'q' key press
def exit_program():
    while True:
        if keyboard.is_pressed('q'):
            #self.logger.debug('EXITING PROGRAM')
            os._exit(1)

if __name__ == '__main__':
    #hello_world()
    #move_mouse()
    #type_words()
    #type_letters()
    exit_program = threading.Thread(target=exit_program, args=())
    exit_program.start()

    # while True:
    #     print("Greetings")
    #     time.sleep(0.5)
    
    reader = easyocr.Reader(['en'], gpu = False) # this needs to run only once to load the model into memory
    result = reader.readtext('./images/app.png', detail = 0)
    print(result)



    #Need to find coords of the bluestacks game to put into mss.sct()
    # with mss.mss() as sct:
    # # The screen part to capture
    # monitor = {"top": 160, "left": 160, "width": 160, "height": 135}
    # output = "sct-{top}x{left}_{width}x{height}.png".format(**monitor)

    # # Grab the data
    # sct_img = sct.grab(monitor)

    # # Save to the picture file
    # mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
    # print(output)