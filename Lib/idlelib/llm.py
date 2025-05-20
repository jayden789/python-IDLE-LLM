import re
from sys import maxsize as INFINITY
import requests

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
        
         # Send to API
        try:
            response = requests.post(
                "https://backend-190.onrender.com/api/chat", 
                json={"message": selection}
            )
            response.raise_for_status()
            explanation = response.json().get("reply", "No explanation returned.")
        except Exception as e:
            print("Error contacting LLM API:", e)
            return

        # Insert explanation into editor (optional: below selection)
        # self.text.insert("sel.last", f"\n# Explanation:\n# {explanation.replace('\n', '\n# ')}\n")
        
        print("Explanation:", explanation)