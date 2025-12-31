try:
    from sdl2 import sdlgfx
    print("sdlgfx available")
except ImportError:
    print("sdlgfx NOT available")
