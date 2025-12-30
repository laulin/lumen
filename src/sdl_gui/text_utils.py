import re
from typing import List, Tuple, Optional

class TextSegment:
    def __init__(self, text: str, bold: bool = False, color: Optional[Tuple[int, int, int, int]] = None, link_target: Optional[str] = None):
        self.text = text
        self.bold = bold
        self.color = color
        self.link_target = link_target

    def __repr__(self):
        return f"TextSegment(text='{self.text}', bold={self.bold}, color={self.color}, link={self.link_target})"

    def __eq__(self, other):
        if not isinstance(other, TextSegment):
            return False
        return (self.text == other.text and 
                self.bold == other.bold and 
                self.color == other.color and 
                self.link_target == other.link_target)

def parse_color(color_str: str) -> Optional[Tuple[int, int, int, int]]:
    """Parse hex color string (#RRGGBB or #RRGGBBAA) to tuple."""
    if not color_str.startswith("#"):
        return None
    
    hex_str = color_str[1:]
    if len(hex_str) == 6:
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return (r, g, b, 255)
        except ValueError:
            return None
    elif len(hex_str) == 8:
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            a = int(hex_str[6:8], 16)
            return (r, g, b, a)
        except ValueError:
            return None
    return None

def parse_rich_text(text: str, default_color: Tuple[int, int, int, int] = (0, 0, 0, 255)) -> List[TextSegment]:
    """
    Parse text with tags <b>, <color=#...>, <link=...>.
    Returns a list of TextSegments.
    """
    segments: List[TextSegment] = []
    
    # State
    is_bold = False
    current_color = default_color
    current_link = None
    
    # Stack for handling nested tags (simplified: we process linearly but keeping track of state)
    # Actually, regex splitting is easier if tags are non-overlapping or perfectly nested.
    # Let's iterate through the string and find tags.
    
    # Regex to find tags: <tag> or </tag>
    # Supported: <b>, </b>, <color=...>, </color>, <link=...>, </link>
    tag_pattern = re.compile(r'(</?b>|</?color(?:=[^>]+)?>|</?link(?:=[^>]+)?>)')
    
    parts = tag_pattern.split(text)
    
    # Stack to restore previous state?
    # For simplicity, we assume robust simple nesting or just toggle.
    # Color stack, Link stack.
    color_stack = [default_color]
    link_stack = [None] 
    
    for part in parts:
        if not part:
            continue
            
        if part == "<b>":
            is_bold = True
        elif part == "</b>":
            is_bold = False
        elif part.startswith("<color="):
            val = part[7:-1]
            c = parse_color(val)
            if c:
                color_stack.append(c)
                current_color = c
        elif part == "</color>":
            if len(color_stack) > 1:
                color_stack.pop()
                current_color = color_stack[-1]
        elif part.startswith("<link="):
            val = part[6:-1]
            link_stack.append(val)
            current_link = val
        elif part == "</link>":
            if len(link_stack) > 1:
                link_stack.pop()
                current_link = link_stack[-1]
        elif part.startswith("<") and part.endswith(">"):
            # Unknown tag, treat as text? or ignore?
            # treating as text might be confusing if regex caught it.
            # But regex specific for our tags.
            # Only if user typed something looking like a tag matched by regex but logic didn't handle.
            # The regex is specific.
            pass
        else:
            # Text content
            # Add segment
            if part:
                segments.append(TextSegment(part, is_bold, current_color, current_link))
                
    return segments
