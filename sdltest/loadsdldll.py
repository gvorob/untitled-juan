import os
os.environ["PYSDL2_DLL_PATH"] = r"D:\Program Files\bin"

import sys
from sdl2 import *

SDL_Init(0)
window = SDL_CreateWindow(b"asd", 20,20,50,50,0)
