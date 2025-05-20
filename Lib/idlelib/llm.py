import re
from sys import maxsize as INFINITY

class LLM_explanation:
    def __init__(self, editwin):
        self.editwin = editwin
        self.text = editwin.text
        self.explanation_mode = False
        
    def toggle_code_explain_event(self, event=None):
        """
        Toggle the explanation mode on or off.
        """
        selection = self.text.get("sel.first", "sel.last")