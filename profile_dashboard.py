"""
Profiling script for dashboard_charts_demo.py

Runs the demo for 3 seconds with cProfile and outputs analysis.
"""
import cProfile
import pstats
import io
import sys
import os
import time

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import sdl2.ext
from sdl_gui import core

# Import the demo class
from examples.dashboard_charts_demo import DashboardDemo


def run_profile(duration_seconds: float = 3.0) -> None:
    """
    Run the dashboard demo for a specified duration and profile it.
    
    Args:
        duration_seconds: How long to run the demo before stopping.
    """
    demo = DashboardDemo()
    demo.show()
    
    start_time = time.time()
    frame_count = 0
    
    while True:
        elapsed = time.time() - start_time
        if elapsed >= duration_seconds:
            break
        
        events = demo.get_ui_events()
        for event in events:
            if event.get("type") == core.EVENT_QUIT:
                break
            if event.get("type") == core.EVENT_KEY_DOWN:
                if event.get("key_sym") == sdl2.SDLK_ESCAPE:
                    break
        
        display_list = demo.get_root_display_list()
        demo.render(display_list)
        frame_count += 1
    
    sdl2.ext.quit()
    
    # Print frame statistics
    print(f"\n{'='*60}")
    print(f"PROFILING RESULTS")
    print(f"{'='*60}")
    print(f"Duration: {elapsed:.2f} seconds")
    print(f"Frames rendered: {frame_count}")
    print(f"Average FPS: {frame_count / elapsed:.1f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Create profiler
    profiler = cProfile.Profile()
    
    # Run profiled code
    profiler.enable()
    run_profile(3.0)
    profiler.disable()
    
    # Analyze results
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    
    print("\n" + "="*60)
    print("TOP 50 FUNCTIONS BY CUMULATIVE TIME")
    print("="*60)
    stats.print_stats(50)
    print(s.getvalue())
    
    # Also print by total time
    s2 = io.StringIO()
    stats2 = pstats.Stats(profiler, stream=s2)
    stats2.strip_dirs()
    stats2.sort_stats('tottime')
    
    print("\n" + "="*60)
    print("TOP 50 FUNCTIONS BY TOTAL TIME")
    print("="*60)
    stats2.print_stats(50)
    print(s2.getvalue())
    
    # Print callers for top functions
    s3 = io.StringIO()
    stats3 = pstats.Stats(profiler, stream=s3)
    stats3.strip_dirs()
    stats3.sort_stats('cumulative')
    
    print("\n" + "="*60)
    print("CALLERS - Who calls the top functions?")
    print("="*60)
    stats3.print_callers(20)
    print(s3.getvalue())
