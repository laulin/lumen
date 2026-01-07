#!/usr/bin/env python3
"""
Benchmark script to validate spatial index performance improvements.

This script renders a large number of elements in a scrollable container
and measures the performance with spatial indexing enabled.
"""

import sys
import time

import sdl2
import sdl2.ext

from sdl_gui import core
from sdl_gui.window.window import Window
from sdl_gui.layers.layer import Layer
from sdl_gui.primitives.rectangle import Rectangle


def create_many_items(count: int):
    """Create a layer with many child rectangles."""
    layer = Layer(0, 0, "100%", "100%")
    
    for i in range(count):
        row = i // 10
        col = i % 10
        color = (
            (i * 37) % 256,
            (i * 73) % 256,
            (i * 101) % 256,
            255
        )
        rect = Rectangle(
            col * 80 + 10,
            row * 50 + 10,
            70,
            40,
            color=color
        )
        layer.add_child(rect)
    
    return layer


def run_benchmark(item_count: int = 500, frames: int = 100):
    """Run the benchmark and return results."""
    sdl2.ext.init()
    
    try:
        window = Window("Spatial Index Benchmark", 800, 600)
        
        # Enable profiling
        window.renderer.enable_profiling(True)
        window.renderer._spatial_index.reset_stats()
        
        layer = create_many_items(item_count)
        display_list = [layer.to_data()]
        
        print(f"\n{'='*60}")
        print(f"Spatial Index Benchmark")
        print(f"{'='*60}")
        print(f"Items: {item_count}")
        print(f"Frames: {frames}")
        print(f"{'='*60}\n")
        
        # Warmup
        for _ in range(10):
            window.renderer.clear()
            window.renderer.render_list(display_list)
            window.renderer.present()
        
        # Reset stats after warmup
        window.renderer.enable_profiling(True)
        window.renderer._spatial_index.reset_stats()
        
        # Benchmark
        start_time = time.perf_counter()
        
        for i in range(frames):
            window.renderer.clear()
            window.renderer.render_list(display_list)
            window.renderer.present()
        
        elapsed = time.perf_counter() - start_time
        
        # Get stats
        perf_stats = window.renderer.get_perf_stats()
        spatial_stats = window.renderer.get_spatial_stats()
        
        fps = frames / elapsed
        avg_frame_ms = (elapsed / frames) * 1000
        
        print(f"Results:")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Average FPS: {fps:.1f}")
        print(f"  Avg frame time: {avg_frame_ms:.2f}ms")
        print()
        print(f"Spatial Index Stats:")
        print(f"  Total items indexed: {spatial_stats['total_items']}")
        print(f"  Total inserts: {spatial_stats['inserts']}")
        print(f"  Total queries: {spatial_stats['queries']}")
        print()
        print(f"Performance Stats:")
        print(f"  Draw calls: {perf_stats['draw_calls']}")
        print(f"  Batched rects: {perf_stats['batch_stats']['batched_rects']}")
        print(f"  Saved calls: {perf_stats['batch_stats']['saved_calls']}")
        print()
        print(f"Culling Stats:")
        print(f"  Rendered: {perf_stats['culling_stats']['rendered']}")
        print(f"  Skipped: {perf_stats['culling_stats']['skipped']}")
        
        if 'timings' in perf_stats and perf_stats['timings']:
            print(f"\nTimings:")
            for name, timing in perf_stats['timings'].items():
                avg_ms = (timing / frames) * 1000
                print(f"  {name}: {avg_ms:.3f}ms/frame")
        
        print(f"\n{'='*60}")
        print("Benchmark complete!")
        print(f"{'='*60}\n")
        
        return {
            "fps": fps,
            "avg_frame_ms": avg_frame_ms,
            "spatial_stats": spatial_stats,
            "perf_stats": perf_stats,
        }
        
    finally:
        sdl2.ext.quit()


def main():
    """Main entry point."""
    item_count = 500
    frames = 100
    
    if len(sys.argv) > 1:
        try:
            item_count = int(sys.argv[1])
        except ValueError:
            pass
    
    if len(sys.argv) > 2:
        try:
            frames = int(sys.argv[2])
        except ValueError:
            pass
    
    run_benchmark(item_count, frames)


if __name__ == "__main__":
    main()
