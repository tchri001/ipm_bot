import easyocr
import time
import os
import threading
import keyboard

#Polling function to exit program on 'q' key press
def exit_program():
    while True:
        if keyboard.is_pressed('q'):
            #self.logger.debug('EXITING PROGRAM')
            os._exit(1)

if __name__ == '__main__':
    exit_program = threading.Thread(target=exit_program, args=())
    exit_program.start()

    
    reader = easyocr.Reader(['en'], gpu = False) # this needs to run only once to load the model into memory
    result = reader.readtext('./images/app.png', detail = 0)
    print(result)
