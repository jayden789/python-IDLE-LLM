import unittest
import tkinter as tk
from idlelib.llm import LLM_explanation

class DummyEditwin:
    def __init__(self, text):
        self.text = text
        self.explanation_panel = tk.Text()
        self._panel_visible = False

    def show_explanation_panel(self):
        self._panel_visible = True

    @property
    def code_explanation_visible(self):
        return self._panel_visible

class CodeExplanationVisibleTest(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.text = tk.Text(self.root)
        self.editwin = DummyEditwin(self.text)
        self.llm = LLM_explanation(self.editwin)

    def tearDown(self):
        self.root.destroy()

    def test_code_explanation_visible(self):
        # Simulate triggering the explanation panel
        self.llm.editwin.show_explanation_panel()
        self.assertTrue(self.llm.editwin.code_explanation_visible)

if __name__ == '__main__':
    unittest.main(verbosity=2)