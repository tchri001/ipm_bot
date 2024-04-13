import autopy

def hello_world():
    autopy.alert.alert("Hello, world")

def move_mouse():
    autopy.mouse.smooth_move(1, 1)

def type_words():
    autopy.key.type_string("Hello, world!", wpm=100)

def type_letters():
    autopy.key.tap(autopy.key.Code.TAB, [autopy.key.Modifier.META])
    autopy.key.tap("w", [autopy.key.Modifier.META])

if __name__ == '__main__':
    #hello_world()
    move_mouse()
    #type_words()
    #type_letters()