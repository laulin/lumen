"""
Dashboard demo with vector graphics charts.

This example demonstrates how to create a dashboard with various chart types
using the VectorGraphics primitive: bar charts, pie charts, and line charts.
All displayed with a dark theme aesthetic.

Usage:
    python examples/dashboard_charts_demo.py
"""
import sys
import os
import math
from typing import List, Tuple

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import sdl2.ext
from sdl_gui import core
from sdl_gui.window.window import Window
from sdl_gui.layouts.flexbox import FlexBox
from sdl_gui.primitives.rectangle import Rectangle
from sdl_gui.primitives.responsive_text import ResponsiveText
from sdl_gui.primitives.vector_graphics import VectorGraphics


# =============================================================================
# Dark Theme Color Palette
# =============================================================================
COLOR_BG = (15, 15, 20, 255)
COLOR_CARD_BG = (25, 25, 32, 255)
COLOR_CARD_BORDER = (45, 45, 55, 255)

COLOR_TEXT_PRIMARY = (240, 240, 240, 255)
COLOR_TEXT_SECONDARY = (150, 150, 160, 255)
COLOR_TEXT_MUTED = (100, 100, 110, 255)

# Chart Colors - Vibrant yet dark-theme friendly
COLOR_CHART_BLUE = (66, 133, 244, 255)
COLOR_CHART_GREEN = (52, 211, 153, 255)
COLOR_CHART_ORANGE = (251, 146, 60, 255)
COLOR_CHART_PURPLE = (167, 139, 250, 255)
COLOR_CHART_PINK = (244, 114, 182, 255)
COLOR_CHART_CYAN = (34, 211, 238, 255)
COLOR_CHART_RED = (248, 113, 113, 255)

COLOR_GRID = (45, 45, 55, 255)
COLOR_AXIS = (80, 80, 90, 255)


# =============================================================================
# Chart Drawing Functions
# =============================================================================

def draw_bar_chart(
    vg: VectorGraphics,
    data: List[Tuple[str, float]],
    colors: List[Tuple[int, int, int, int]],
    show_grid: bool = True
) -> None:
    """
    Draw a bar chart in the VectorGraphics canvas.
    
    Args:
        vg: The VectorGraphics primitive to draw on.
        data: List of (label, value) tuples.
        colors: List of colors for each bar.
        show_grid: Whether to show grid lines.
    """
    vg.clear()
    
    if not data:
        return
    
    # Chart area (using percentages for responsive layout)
    margin_left = 10
    margin_right = 5
    margin_top = 10
    margin_bottom = 15
    
    chart_width = 100 - margin_left - margin_right
    chart_height = 100 - margin_top - margin_bottom
    
    max_value = max(v for _, v in data)
    bar_count = len(data)
    bar_width = chart_width / bar_count * 0.7
    bar_gap = chart_width / bar_count * 0.3
    
    # Draw grid lines
    if show_grid:
        vg.stroke(COLOR_GRID, width=1)
        for i in range(5):
            y_pct = margin_top + chart_height * (1 - i / 4)
            vg.move_to(f"{margin_left}%", f"{y_pct}%")
            vg.line_to(f"{100 - margin_right}%", f"{y_pct}%")
    
    # Draw axis
    vg.stroke(COLOR_AXIS, width=2)
    vg.move_to(f"{margin_left}%", f"{margin_top}%")
    vg.line_to(f"{margin_left}%", f"{100 - margin_bottom}%")
    vg.line_to(f"{100 - margin_right}%", f"{100 - margin_bottom}%")
    
    # Draw bars
    for i, (label, value) in enumerate(data):
        color = colors[i % len(colors)]
        
        # Calculate bar dimensions
        x_start = margin_left + (i * (chart_width / bar_count)) + (bar_gap / 2)
        bar_height_pct = (value / max_value) * chart_height if max_value > 0 else 0
        y_start = margin_top + chart_height - bar_height_pct
        
        # Draw filled bar with rounded corners
        vg.fill(color)
        vg.stroke(color, width=0)
        vg.rect(
            f"{x_start}%", f"{y_start}%",
            f"{bar_width}%", f"{bar_height_pct}%",
            r=4
        )


def draw_pie_chart(
    vg: VectorGraphics,
    data: List[Tuple[str, float]],
    colors: List[Tuple[int, int, int, int]],
    donut: bool = True
) -> None:
    """
    Draw a pie/donut chart in the VectorGraphics canvas.
    
    Args:
        vg: The VectorGraphics primitive to draw on.
        data: List of (label, value) tuples.
        colors: List of colors for each slice.
        donut: If True, draw as donut chart with hollow center.
    """
    vg.clear()
    
    if not data:
        return
    
    total = sum(v for _, v in data)
    if total == 0:
        return
    
    # Center and radius (using percentage)
    center_x, center_y = 50, 50
    outer_radius = 40
    inner_radius = 25 if donut else 0
    
    # Draw slices
    current_angle = -90  # Start from top
    
    for i, (label, value) in enumerate(data):
        color = colors[i % len(colors)]
        slice_angle = (value / total) * 360
        
        end_angle = current_angle + slice_angle
        
        # Draw pie slice
        vg.fill(color)
        vg.stroke((0, 0, 0, 0), width=0)
        vg.pie(f"{center_x}%", f"{center_y}%", f"{outer_radius}%",
               int(current_angle), int(end_angle))
        
        current_angle = end_angle
    
    # Draw center hole for donut effect
    if donut:
        vg.fill(COLOR_CARD_BG)
        vg.stroke((0, 0, 0, 0), width=0)
        vg.circle(f"{center_x}%", f"{center_y}%", f"{inner_radius}%")


def draw_line_chart(
    vg: VectorGraphics,
    data: List[float],
    color: Tuple[int, int, int, int],
    show_grid: bool = True,
    show_dots: bool = True
) -> None:
    """
    Draw a line chart in the VectorGraphics canvas.
    
    Args:
        vg: The VectorGraphics primitive to draw on.
        data: List of values.
        color: Line color.
        show_grid: Whether to show grid lines.
        show_dots: Whether to show data points.
    """
    vg.clear()
    
    if not data:
        return
    
    margin_left = 10
    margin_right = 5
    margin_top = 10
    margin_bottom = 15
    
    chart_width = 100 - margin_left - margin_right
    chart_height = 100 - margin_top - margin_bottom
    
    min_val = min(data)
    max_val = max(data)
    value_range = max_val - min_val if max_val != min_val else 1
    
    # Draw grid lines
    if show_grid:
        vg.stroke(COLOR_GRID, width=1)
        for i in range(5):
            y_pct = margin_top + chart_height * (1 - i / 4)
            vg.move_to(f"{margin_left}%", f"{y_pct}%")
            vg.line_to(f"{100 - margin_right}%", f"{y_pct}%")
    
    # Draw axis
    vg.stroke(COLOR_AXIS, width=2)
    vg.move_to(f"{margin_left}%", f"{margin_top}%")
    vg.line_to(f"{margin_left}%", f"{100 - margin_bottom}%")
    vg.line_to(f"{100 - margin_right}%", f"{100 - margin_bottom}%")
    
    # Calculate points
    points = []
    for i, value in enumerate(data):
        x_pct = margin_left + (i / (len(data) - 1)) * chart_width if len(data) > 1 else margin_left + chart_width / 2
        y_pct = margin_top + chart_height * (1 - (value - min_val) / value_range)
        points.append((x_pct, y_pct))
    
    # Draw line
    vg.stroke(color, width=3)
    if points:
        vg.move_to(f"{points[0][0]}%", f"{points[0][1]}%")
        for x, y in points[1:]:
            vg.line_to(f"{x}%", f"{y}%")
    
    # Draw dots
    if show_dots:
        for x, y in points:
            vg.fill(color)
            vg.stroke((0, 0, 0, 0), width=0)
            vg.circle(f"{x}%", f"{y}%", 6)
            # Inner white dot
            vg.fill(COLOR_CARD_BG)
            vg.circle(f"{x}%", f"{y}%", 3)


def draw_multi_line_chart(
    vg: VectorGraphics,
    datasets: List[Tuple[str, List[float], Tuple[int, int, int, int]]],
    show_grid: bool = True
) -> None:
    """
    Draw a multi-line chart in the VectorGraphics canvas.
    
    Args:
        vg: The VectorGraphics primitive to draw on.
        datasets: List of (label, data, color) tuples.
        show_grid: Whether to show grid lines.
    """
    vg.clear()
    
    if not datasets:
        return
    
    margin_left = 10
    margin_right = 5
    margin_top = 10
    margin_bottom = 15
    
    chart_width = 100 - margin_left - margin_right
    chart_height = 100 - margin_top - margin_bottom
    
    # Find global min/max
    all_values = [v for _, data, _ in datasets for v in data]
    if not all_values:
        return
    
    min_val = min(all_values)
    max_val = max(all_values)
    value_range = max_val - min_val if max_val != min_val else 1
    
    # Draw grid lines
    if show_grid:
        vg.stroke(COLOR_GRID, width=1)
        for i in range(5):
            y_pct = margin_top + chart_height * (1 - i / 4)
            vg.move_to(f"{margin_left}%", f"{y_pct}%")
            vg.line_to(f"{100 - margin_right}%", f"{y_pct}%")
    
    # Draw axis
    vg.stroke(COLOR_AXIS, width=2)
    vg.move_to(f"{margin_left}%", f"{margin_top}%")
    vg.line_to(f"{margin_left}%", f"{100 - margin_bottom}%")
    vg.line_to(f"{100 - margin_right}%", f"{100 - margin_bottom}%")
    
    # Draw each line
    for label, data, color in datasets:
        if not data:
            continue
        
        points = []
        for i, value in enumerate(data):
            x_pct = margin_left + (i / (len(data) - 1)) * chart_width if len(data) > 1 else margin_left + chart_width / 2
            y_pct = margin_top + chart_height * (1 - (value - min_val) / value_range)
            points.append((x_pct, y_pct))
        
        vg.stroke(color, width=2)
        if points:
            vg.move_to(f"{points[0][0]}%", f"{points[0][1]}%")
            for x, y in points[1:]:
                vg.line_to(f"{x}%", f"{y}%")


def draw_gauge_chart(
    vg: VectorGraphics,
    value: float,
    max_value: float,
    color: Tuple[int, int, int, int],
    label: str = ""
) -> None:
    """
    Draw a semi-circular gauge chart.
    
    Args:
        vg: The VectorGraphics primitive to draw on.
        value: Current value.
        max_value: Maximum value.
        color: Gauge color.
        label: Optional label.
    """
    vg.clear()
    
    center_x, center_y = 50, 60
    radius = 35
    thickness = 8
    
    # Background arc (gray)
    vg.stroke(COLOR_GRID, width=int(thickness))
    vg.arc(f"{center_x}%", f"{center_y}%", f"{radius}%", 180, 360)
    
    # Value arc
    percentage = min(value / max_value, 1.0) if max_value > 0 else 0
    end_angle = 180 + (percentage * 180)
    
    vg.stroke(color, width=int(thickness))
    vg.arc(f"{center_x}%", f"{center_y}%", f"{radius}%", 180, int(end_angle))


# =============================================================================
# Dashboard Window Class
# =============================================================================

class DashboardDemo(Window):
    """
    A beautiful dark-themed dashboard showcasing vector graphics charts.
    """
    
    def __init__(self):
        super().__init__("Lumen Dashboard - Vector Charts", 1200, 800, debug=True)
        self.root_children = self._build_ui()
    
    def _build_ui(self) -> List:
        """Build the complete dashboard UI."""
        # Root container
        root = FlexBox(
            x=0, y=0, width="100%", height="100%",
            flex_direction="column",
            padding=(20, 20, 20, 20),
            gap=20,
            id="root"
        )
        
        # Header
        header = self._create_header()
        root.add_child(header)
        
        # Stats cards row
        stats_row = self._create_stats_row()
        root.add_child(stats_row)
        
        # Main charts row (Bar + Pie)
        charts_row_1 = self._create_charts_row_1()
        root.add_child(charts_row_1)
        
        # Second charts row (Line + Multi-line)
        charts_row_2 = self._create_charts_row_2()
        root.add_child(charts_row_2)
        
        # Background
        bg = Rectangle(x=0, y=0, width="100%", height="100%", color=COLOR_BG)
        
        return [bg, root]
    
    def _create_header(self) -> FlexBox:
        """Create the dashboard header."""
        header = FlexBox(
            x=0, y=0, width="100%", height="auto",
            flex_direction="row",
            justify_content="space_between",
            align_items="center",
            padding=(0, 0, 10, 0)
        )
        
        # Title section
        title_box = FlexBox(
            x=0, y=0, width="auto", height="auto",
            flex_direction="column",
            gap=5
        )
        
        title = ResponsiveText(
            x=0, y=0, width="auto", height="auto",
            text="Analytics Dashboard",
            size=28, color=COLOR_TEXT_PRIMARY
        )
        
        subtitle = ResponsiveText(
            x=0, y=0, width="auto", height="auto",
            text="Vector Graphics Demo • Real-time Data Visualization",
            size=14, color=COLOR_TEXT_SECONDARY
        )
        
        title_box.add_child(title)
        title_box.add_child(subtitle)
        
        # Date badge
        date_badge = FlexBox(
            x=0, y=0, width="auto", height="auto",
            padding=(8, 16, 8, 16)
        )
        date_badge.set_color((35, 35, 45, 255))
        date_badge.set_radius(20)
        
        date_text = ResponsiveText(
            x=0, y=0, width="auto", height="auto",
            text="January 2026",
            size=13, color=COLOR_TEXT_SECONDARY
        )
        date_badge.add_child(date_text)
        
        header.add_child(title_box)
        header.add_child(date_badge)
        
        return header
    
    def _create_stats_row(self) -> FlexBox:
        """Create the stats cards row with gauge charts."""
        row = FlexBox(
            x=0, y=0, width="100%", height=120,
            flex_direction="row",
            gap=20
        )
        
        stats = [
            ("Revenue", "$124,500", 82, COLOR_CHART_GREEN, "+12.5%"),
            ("Users", "45,231", 68, COLOR_CHART_BLUE, "+8.3%"),
            ("Conversion", "3.2%", 45, COLOR_CHART_ORANGE, "-2.1%"),
            ("Sessions", "98,547", 91, COLOR_CHART_PURPLE, "+15.7%"),
        ]
        
        for label, value, gauge_val, color, change in stats:
            card = self._create_stat_card(label, value, gauge_val, color, change)
            card.set_flex_grow(1)
            card.set_flex_basis(0)
            row.add_child(card)
        
        return row
    
    def _create_stat_card(
        self, label: str, value: str, gauge_val: int,
        color: Tuple[int, int, int, int], change: str
    ) -> FlexBox:
        """Create a single stat card with mini gauge."""
        card = FlexBox(
            x=0, y=0, width="auto", height="100%",
            flex_direction="row",
            align_items="center",
            padding=(15, 20, 15, 20),
            gap=15
        )
        card.set_color(COLOR_CARD_BG)
        card.set_radius(12)
        card.set_border_width(1)
        card.set_border_color(COLOR_CARD_BORDER)
        
        # Left: Text content
        text_box = FlexBox(
            x=0, y=0, width="auto", height="auto",
            flex_direction="column",
            gap=4
        )
        text_box.set_flex_grow(1)
        
        label_text = ResponsiveText(
            x=0, y=0, width="auto", height="auto",
            text=label.upper(),
            size=11, color=COLOR_TEXT_MUTED
        )
        
        value_text = ResponsiveText(
            x=0, y=0, width="auto", height="auto",
            text=value,
            size=24, color=COLOR_TEXT_PRIMARY
        )
        
        # Change indicator
        change_color = COLOR_CHART_GREEN if change.startswith("+") else COLOR_CHART_RED
        change_text = ResponsiveText(
            x=0, y=0, width="auto", height="auto",
            text=change,
            size=12, color=change_color
        )
        
        text_box.add_child(label_text)
        text_box.add_child(value_text)
        text_box.add_child(change_text)
        
        # Right: Mini gauge
        gauge = VectorGraphics(0, 0, 60, 60, id=f"gauge_{label.lower()}")
        draw_gauge_chart(gauge, gauge_val, 100, color)
        
        card.add_child(text_box)
        card.add_child(gauge)
        
        return card
    
    def _create_charts_row_1(self) -> FlexBox:
        """Create first row of charts: Bar and Pie."""
        row = FlexBox(
            x=0, y=0, width="100%", height=280,
            flex_direction="row",
            gap=20
        )
        
        # Bar chart card (2/3 width)
        bar_card = self._create_chart_card(
            "Monthly Revenue",
            "Revenue breakdown by month"
        )
        bar_card.set_flex_grow(2)
        bar_card.set_flex_basis(0)
        
        bar_chart = VectorGraphics(
            0, 0, "100%", "100%",
            padding=(10, 10, 10, 10),
            id="bar_chart"
        )
        
        bar_data = [
            ("Jan", 4500),
            ("Feb", 5200),
            ("Mar", 4800),
            ("Apr", 6100),
            ("May", 7200),
            ("Jun", 6800),
            ("Jul", 8100),
            ("Aug", 7500),
        ]
        bar_colors = [
            COLOR_CHART_BLUE, COLOR_CHART_GREEN, COLOR_CHART_ORANGE,
            COLOR_CHART_PURPLE, COLOR_CHART_CYAN, COLOR_CHART_PINK,
            COLOR_CHART_BLUE, COLOR_CHART_GREEN
        ]
        draw_bar_chart(bar_chart, bar_data, bar_colors)
        
        bar_card.add_child(bar_chart)
        
        # Pie chart card (1/3 width)
        pie_card = self._create_chart_card(
            "Traffic Sources",
            "Where visitors come from"
        )
        pie_card.set_flex_grow(1)
        pie_card.set_flex_basis(0)
        
        pie_chart = VectorGraphics(
            0, 0, "100%", "100%",
            padding=(10, 10, 10, 10),
            id="pie_chart"
        )
        
        pie_data = [
            ("Organic", 45),
            ("Direct", 25),
            ("Social", 15),
            ("Referral", 10),
            ("Email", 5),
        ]
        pie_colors = [
            COLOR_CHART_BLUE, COLOR_CHART_GREEN, COLOR_CHART_ORANGE,
            COLOR_CHART_PURPLE, COLOR_CHART_PINK
        ]
        draw_pie_chart(pie_chart, pie_data, pie_colors, donut=True)
        
        pie_card.add_child(pie_chart)
        
        row.add_child(bar_card)
        row.add_child(pie_card)
        
        return row
    
    def _create_charts_row_2(self) -> FlexBox:
        """Create second row of charts: Line charts."""
        row = FlexBox(
            x=0, y=0, width="100%", height=250,
            flex_direction="row",
            gap=20
        )
        
        # Single line chart
        line_card = self._create_chart_card(
            "User Growth",
            "New user registrations over time"
        )
        line_card.set_flex_grow(1)
        line_card.set_flex_basis(0)
        
        line_chart = VectorGraphics(
            0, 0, "100%", "100%",
            padding=(10, 10, 10, 10),
            id="line_chart"
        )
        
        line_data = [120, 150, 180, 165, 210, 250, 280, 310, 340, 380, 420, 450]
        draw_line_chart(line_chart, line_data, COLOR_CHART_CYAN, show_dots=True)
        
        line_card.add_child(line_chart)
        
        # Multi-line chart
        multi_line_card = self._create_chart_card(
            "Performance Metrics",
            "Comparing multiple KPIs"
        )
        multi_line_card.set_flex_grow(1)
        multi_line_card.set_flex_basis(0)
        
        multi_line_chart = VectorGraphics(
            0, 0, "100%", "100%",
            padding=(10, 10, 10, 10),
            id="multi_line_chart"
        )
        
        multi_datasets = [
            ("Sales", [30, 45, 55, 60, 48, 70, 85, 90], COLOR_CHART_BLUE),
            ("Leads", [50, 55, 45, 70, 60, 65, 75, 80], COLOR_CHART_GREEN),
            ("Conversion", [20, 25, 35, 30, 40, 45, 55, 60], COLOR_CHART_ORANGE),
        ]
        draw_multi_line_chart(multi_line_chart, multi_datasets)
        
        multi_line_card.add_child(multi_line_chart)
        
        row.add_child(line_card)
        row.add_child(multi_line_card)
        
        return row
    
    def _create_chart_card(self, title: str, subtitle: str) -> FlexBox:
        """Create a card container for charts."""
        card = FlexBox(
            x=0, y=0, width="auto", height="100%",
            flex_direction="column",
            padding=(15, 15, 15, 15),
            gap=10
        )
        card.set_color(COLOR_CARD_BG)
        card.set_radius(12)
        card.set_border_width(1)
        card.set_border_color(COLOR_CARD_BORDER)
        
        # Header
        header_box = FlexBox(
            x=0, y=0, width="100%", height="auto",
            flex_direction="column",
            gap=2
        )
        
        title_text = ResponsiveText(
            x=0, y=0, width="100%", height="auto",
            text=title,
            size=16, color=COLOR_TEXT_PRIMARY
        )
        
        subtitle_text = ResponsiveText(
            x=0, y=0, width="100%", height="auto",
            text=subtitle,
            size=12, color=COLOR_TEXT_MUTED
        )
        
        header_box.add_child(title_text)
        header_box.add_child(subtitle_text)
        
        card.add_child(header_box)
        
        return card
    
    def run(self):
        """Run the dashboard demo."""
        self.show()
        running = True
        
        while running:
            events = self.get_ui_events()
            for event in events:
                if event.get("type") == core.EVENT_QUIT:
                    running = False
                if event.get("type") == core.EVENT_KEY_DOWN:
                    if event.get("key_sym") == sdl2.SDLK_ESCAPE:
                        running = False
            
            display_list = self.get_root_display_list()
            self.render(display_list)
        
        sdl2.ext.quit()


if __name__ == "__main__":
    demo = DashboardDemo()
    demo.run()
