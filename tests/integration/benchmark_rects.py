import unittest
import sdl2
import sdl2.ext
from sdl2 import sdlgfx
import time
import os
import ctypes
import random

def to_sdlgfx_color(color):
    r, g, b, a = color
    return (a << 24) | (b << 16) | (g << 8) | r

class TestBenchmarkRects(unittest.TestCase):
    def test_benchmark_rects(self):
        """Benchmark rendering of 5000 rectangles."""
        # Force dummy driver
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        
        sdl2.ext.init()
        window = sdl2.ext.Window("Benchmark", size=(800, 600))
        # Software renderer for dummy
        renderer = sdl2.ext.Renderer(window, flags=sdl2.SDL_RENDERER_SOFTWARE)
        
        sdl_renderer = renderer.sdlrenderer
        
        count = 5000
        rects = []
        for _ in range(count):
            x = random.randint(0, 700)
            y = random.randint(0, 500)
            w = random.randint(20, 100)
            h = random.randint(20, 100)
            r = 10
            c = (255, 0, 0, 255)
            rects.append((x,y,w,h,r,c))
            
        print(f"\nBenchmarking {count} rectangles...")

        # 1. Alias (Standard sdlgfx)
        start = time.time()
        for x,y,w,h,r,c in rects:
            col = to_sdlgfx_color(c)
            sdlgfx.roundedBoxColor(sdl_renderer, x, y, x+w-1, y+h-1, r, col)
        renderer.present()
        end = time.time()
        old_time = end - start
        print(f"Aliased (Old): {old_time:.4f}s")
        
        renderer.clear()
        
        def draw_aa(x, y, w, h, r, c):
            gfx_color = to_sdlgfx_color(c)
            sdlgfx.roundedBoxColor(sdl_renderer, x, y, x+w-1, y+h-1, r, gfx_color)
            
            sdlgfx.aalineColor(sdl_renderer, x + r, y, x + w - 1 - r, y, gfx_color)
            sdlgfx.aalineColor(sdl_renderer, x + r, y + h - 1, x + w - 1 - r, y + h - 1, gfx_color)
            sdlgfx.aalineColor(sdl_renderer, x, y + r, x, y + h - 1 - r, gfx_color)
            sdlgfx.aalineColor(sdl_renderer, x + w - 1, y + r, x + w - 1, y + h - 1 - r, gfx_color)
            
            def set_clip(cx, cy, cw, ch):
                 clip = sdl2.SDL_Rect(cx, cy, cw, ch)
                 sdl2.SDL_RenderSetClipRect(sdl_renderer, ctypes.byref(clip))

            set_clip(x, y, r, r)
            sdlgfx.aacircleColor(sdl_renderer, x + r, y + r, r, gfx_color)
            
            set_clip(x + w - r, y, r, r)
            sdlgfx.aacircleColor(sdl_renderer, x + w - 1 - r, y + r, r, gfx_color)
            
            set_clip(x + w - r, y + h - r, r, r)
            sdlgfx.aacircleColor(sdl_renderer, x + w - 1 - r, y + h - 1 - r, r, gfx_color)
            
            set_clip(x, y + h - r, r, r)
            sdlgfx.aacircleColor(sdl_renderer, x + r, y + h - 1 - r, r, gfx_color)
            
            sdl2.SDL_RenderSetClipRect(sdl_renderer, None)

        start = time.time()
        for x,y,w,h,r,c in rects:
            draw_aa(x,y,w,h,r,c)
        renderer.present()
        end = time.time()
        new_time = end - start
        print(f"Anti-Aliased (New): {new_time:.4f}s")
        
        if old_time > 0:
            print(f"Overhead: {new_time/old_time:.2f}x")
            
        sdl2.ext.quit()

if __name__ == "__main__":
    unittest.main()
