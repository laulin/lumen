import unittest
from sdl_gui.markdown import MarkdownParser, TextSegment

class TestMarkdownParser(unittest.TestCase):
    def setUp(self):
        self.parser = MarkdownParser()
        
    def test_plain_text(self):
        segments = self.parser.parse("Hello World")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "Hello World")
        
    def test_bold(self):
        segments = self.parser.parse("Hello **Bold** World")
        # "Hello ", "Bold", " World"
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0].text, "Hello ")
        self.assertFalse(segments[0].bold)
        self.assertEqual(segments[1].text, "Bold")
        self.assertTrue(segments[1].bold)
        self.assertEqual(segments[2].text, " World")
        
    def test_link(self):
        segments = self.parser.parse("[Click Me](target)")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "Click Me")
        self.assertEqual(segments[0].link_target, "target")
        
    def test_color(self):
        segments = self.parser.parse("[Red Text]{#FF0000}")
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].text, "Red Text")
        self.assertEqual(segments[0].color, (255, 0, 0, 255))
        
    def test_nested_bold_in_link(self):
        segments = self.parser.parse("[Link **Bold**](target)")
        # Expected: "Link ", "Bold" -> both have link_target="target"
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].text, "Link ")
        self.assertEqual(segments[0].link_target, "target")
        self.assertFalse(segments[0].bold)
        
        self.assertEqual(segments[1].text, "Bold")
        self.assertEqual(segments[1].link_target, "target")
        self.assertTrue(segments[1].bold)
        
    def test_mixed(self):
        segments = self.parser.parse("**Start** [Link]{#00FF00} End")
        # "Start" (bold), " ", "Link" (color=#00FF00), " End"
        self.assertEqual(len(segments), 4) # "Start", " ", "Link", " End"
        self.assertTrue(segments[0].bold)
        self.assertEqual(segments[2].color, (0, 255, 0, 255))

    def test_broken_syntax(self):
        segments = self.parser.parse("Hello [Broken")
        # Should behave safely
        self.assertEqual(segments[0].text, "Hello ")
        self.assertEqual(segments[1].text, "[")
        self.assertEqual(segments[2].text, "Broken")
