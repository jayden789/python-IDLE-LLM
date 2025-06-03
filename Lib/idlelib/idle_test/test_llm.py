import tkinter as tk
import unittest
from unittest.mock import Mock, patch
from idlelib.llm import LLM_explanation

class LLMText:
    def __init__(self):
        self.content = "print('hello')\n"
        self.tags = {}
        self.insert_calls = []
        self.tag_configure_calls = []
        self.deleted = False

    def tag_ranges(self, tag):
        return self.tags.get(tag, ())

    def get(self, start, end):
        if start == "sel.first" and end == "sel.last" and self.tags.get("sel"):
            return "selected code"
        if start == "1.0" and end == "end":
            return self.content
        return ""

    def index(self, index):
        return "1.0"

    def config(self, **kwargs):
        pass

    def delete(self, start, end):
        self.deleted = True

    def insert(self, index, text, tag=None):
        self.insert_calls.append((index, text, tag))

    def tag_configure(self, tag, **kwargs):
        self.tag_configure_calls.append((tag, kwargs))

class LLMEditwin:
    def __init__(self):
        self.text = LLMText()
        self.explanation_panel = LLMText()
        self.show_explanation_panel = Mock()
        self.interp = None  # Simulate shell if needed

class LLMApiClient:
    def __init__(self, url):
        self.url = url
        self.last_message = None
        self.last_type = None

    def send_request(self, message, request_type):
        self.last_message = message
        self.last_type = request_type
        return "Explanation result"

class LLMExplanationTest(unittest.TestCase):

    @patch("idlelib.llm.LLMApiClient", new=LLMApiClient)
    def setUp(self):
        self.editwin = LLMEditwin()
        self.llm = LLM_explanation(self.editwin)

    def test_toggle_code_explain_event_with_selection(self):
        self.editwin.text.tags["sel"] = (1, 2)
        self.llm.toggle_code_explain_event()
        self.assertEqual(self.llm.api_client.last_type, "explain_code")
        self.assertIn("Explanation result", self.editwin.explanation_panel.insert_calls[0][1])

    # def test_toggle_code_explain_event_without_selection(self):
    #     self.editwin.text.tags["sel"] = (1, 2)
    #     self.llm.toggle_code_explain_event()
    #     self.assertEqual(self.llm.api_client.last_type, "summarize_file")
    #     self.assertIn("Explanation result", self.editwin.explanation_panel.insert_calls[0][1])

    def test_insert_markdown(self):
        panel = LLMText()
        self.llm.insert_markdown(panel, "**bold**\nHeader:\n• bullet\n`code`")
        inserted = "".join(call[1] for call in panel.insert_calls)
        self.assertIn("bold", inserted)
        self.assertIn("Header:", inserted)
        self.assertIn("bullet", inserted)
        self.assertIn("code", inserted)

    def test_extract_last_error_none(self):
        self.editwin.text.content = "no errors here"
        self.assertIsNone(self.llm.extract_last_error())

    def test_extract_last_error_simple(self):
        self.editwin.text.content = "no errors here"
        self.assertIsNone(self.llm.extract_last_error())

    def test_extract_last_error_traceback(self):
        # Simulate a traceback as would appear in the shell
        self.editwin.text.content = (
            ">>> 1/0\n"
            "Traceback (most recent call last):\n"
            "  File \"<stdin>\", line 1, in <module>\n"
            "ZeroDivisionError: division by zero\n"
            ">>> "
        )
        result = self.llm.extract_last_error()
        self.assertIn("Traceback (most recent call last):", result)
        self.assertIn("ZeroDivisionError", result)
        
        
class LLMExplanationGUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.text = tk.Text(self.root)
        self.panel = tk.Text(self.root)
        class Editwin:
            pass
        self.editwin = Editwin()
        self.editwin.text = self.text
        self.editwin.explanation_panel = self.panel
        self.editwin.show_explanation_panel = lambda: None
        self.llm = LLM_explanation(self.editwin)
        self.llm.api_client.send_request = lambda msg, typ: "GUI explanation"

    def test_explain_with_selection(self):
        self.text.insert("1.0", "print('hello world')")
        self.text.tag_add("sel", "1.0", "1.5")
        self.llm.toggle_code_explain_event()
        self.assertIn("GUI explanation", self.panel.get("1.0", "end"))

    def test_explain_without_selection(self):
        self.text.insert("1.0", "print('hello world')")
        self.llm.toggle_code_explain_event()
        self.assertIn("GUI explanation", self.panel.get("1.0", "end"))


if __name__ == '__main__':
    unittest.main(verbosity=2)