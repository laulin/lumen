from typing import List, Optional, Tuple


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

class MarkdownParser:
    def __init__(self, default_color: Tuple[int, int, int, int] = (0, 0, 0, 255)):
        self.default_color = default_color

    def parse(self, text: str) -> List[TextSegment]:
        """
        Parse text with markdown-like syntax:
        - **Bold**
        - [Link](target)
        - [Color]{#RRGGBB}
        """
        # We use a recursive descent approach or a simple stack-based parser isn't quite right for mixed inline.
        # Given the simplicity requirements, let's use a tokenizer + linear scan with a stack for bold?
        # Links and Colors are "blocks" that wrap text.

        # Regex for high-level structures
        # 1. Bold: \*\*(.*?)\*\*
        # 2. Block: \[(.*?)\]([({].*?[})]) -> detects [Content](target) or [Content]{#Color}
        # But we need to handle nesting? e.g. [**Bold**](Link)

        # Strategy:
        # Define a recursive parse function that processes a string and returns segments.
        # It finds the first occurrence of any marker, processes the "before", processes the "inner", and processes the "after".

        return self._parse_recursive(text, bold=False, color=self.default_color, link=None)

    def _parse_recursive(self, text: str, bold: bool, color: Tuple[int, int, int, int], link: Optional[str]) -> List[TextSegment]:
        segments = []

        # Patterns
        # We need to find the *first* match of any of these.

        # Bold: **...**
        # Link/Color: [...]...

        # We can't just regex distinct patterns because they might overlap or be nested incorrectly if we are not careful.
        # But for valid input:
        # [ ... ] is a distinct start.
        # ** is a distinct start.

        # Let's search for next special char: '[' or '*'

        i = 0
        while i < len(text):
            # scan for next marker
            next_bold = text.find("**", i)
            next_bracket = text.find("[", i)

            # Determine which comes first
            candidates = []
            if next_bold != -1: candidates.append((next_bold, "bold"))
            if next_bracket != -1: candidates.append((next_bracket, "bracket"))

            if not candidates:
                # No more markers
                remaining = text[i:]
                if remaining:
                    segments.append(TextSegment(remaining, bold, color, link))
                break

            candidates.sort(key=lambda x: x[0])
            first_idx, type_ = candidates[0]

            # Add text before marker
            if first_idx > i:
                segments.append(TextSegment(text[i:first_idx], bold, color, link))

            if type_ == "bold":
                # Find closing **
                end_bold = text.find("**", first_idx + 2)
                if end_bold != -1:
                    # Found bold block
                    inner_text = text[first_idx+2 : end_bold]
                    # Recurse for inner text with bold=True
                    inner_segments = self._parse_recursive(inner_text, not bold, color, link) # Toggle bold? typically force True.
                    # Markdown ** toggles? Usually enables. Nested **? **a **b** c** -> a b c (bold).
                    # Let's assume ** sets bold=True.
                    # Actually standard markdown: **a** is bold. **a **b** c** is ambiguous or valid.
                    # Let's simple toggle approach or sets to True.
                    # "Text **Bold** Text" -> Regular, Bold, Regular.
                    # "Text **Bold **Nested** Bold**" -> usually parsing fails or unbolds?
                    # Let's just set bold=True for inner.

                    segments.extend(self._parse_recursive(inner_text, True, color, link))
                    i = end_bold + 2
                else:
                    # No closing **, treat as literal **
                    segments.append(TextSegment("**", bold, color, link))
                    i = first_idx + 2

            elif type_ == "bracket":
                # Found [, look for closing ] to capture content
                # This needs to handle nested brackets if we support them?
                # Simple balanced bracket finder.
                bracket_depth = 0
                close_bracket = -1
                for j in range(first_idx, len(text)):
                    if text[j] == "[":
                        bracket_depth += 1
                    elif text[j] == "]":
                        bracket_depth -= 1
                        if bracket_depth == 0:
                            close_bracket = j
                            break

                if close_bracket != -1:
                    inner_content = text[first_idx+1 : close_bracket]
                    # Check what follows: (url) or {color}
                    next_char_idx = close_bracket + 1

                    processed = False

                    if next_char_idx < len(text):
                        suffix_char = text[next_char_idx]
                        if suffix_char == "(":
                            # Link: find closing )
                            close_paren = text.find(")", next_char_idx)
                            if close_paren != -1:
                                target = text[next_char_idx+1 : close_paren]
                                # Recurse inner content with link target
                                # (Inner content can have formatting, but links usually don't nest links)
                                segments.extend(self._parse_recursive(inner_content, bold, color, target))
                                i = close_paren + 1
                                processed = True

                        elif suffix_char == "{":
                            # Color: find closing }
                            close_brace = text.find("}", next_char_idx)
                            if close_brace != -1:
                                attr = text[next_char_idx+1 : close_brace]
                                # Expect #RRGGBB
                                new_color = parse_color(attr)
                                if new_color:
                                    segments.extend(self._parse_recursive(inner_content, bold, new_color, link))
                                else:
                                    # Invalid color, treat as text or fallback?
                                    # Fallback: just recurse with old color?
                                    segments.extend(self._parse_recursive(inner_content, bold, color, link))

                                i = close_brace + 1
                                processed = True

                    if not processed:
                        # Just brackets [], treat as literal text or recurse inner?
                        # [Text] -> just "Text" or "[Text]"?
                        # Markdown: [Text] is text if not followed by link.
                        # We return "[", recurse inner, "]"?
                        # Or just treats as text.
                        # Simple approach: It's text.
                        segments.append(TextSegment("[", bold, color, link))
                        segments.extend(self._parse_recursive(inner_content, bold, color, link))
                        segments.append(TextSegment("]", bold, color, link))
                        i = close_bracket + 1
                else:
                    # No closing bracket
                    segments.append(TextSegment("[", bold, color, link))
                    i = first_idx + 1

        return segments
