import re
import tkinter.messagebox as messagebox
from tkinter import INSERT
from idlelib.llm_api import LLMApiClient

URL = "https://backend-190.onrender.com/explain"

class LLM_explanation:
    def __init__(self, editwin):
        self.editwin = editwin
        self.text = editwin.text
        self.explanation_mode = False
        self.api_client = LLMApiClient(URL)
        
    def toggle_code_explain_event(self, event=None):
        try:
            has_selection = self.text.tag_ranges("sel")
            
            if has_selection:
                selection = self.text.get("sel.first", "sel.last")
                message = selection
                request_type = "explain_code"
            else:
                file_content = self.text.get("1.0", "end")
                message = file_content
                request_type = "summarize_file"
            
            is_shell = hasattr(self.editwin, 'interp')
            
            if is_shell and not has_selection:
                error_info = self.extract_last_error()
                
                if not error_info:
                    cursor_pos = self.text.index(INSERT)
                    cursor_line = int(cursor_pos.split('.')[0])
                    
                    for i in range(max(1, cursor_line-5), cursor_line+5):
                        line_text = self.text.get(f"{i}.0", f"{i}.end")
                        if re.search(r"(?:Error|Exception):", line_text):
                            line_start = f"{i}.0"
                            line_end = f"{i}.end"
                            error_info = self.text.get(line_start, line_end)
                            context_start = max(1, i-2)
                            context_end = min(int(self.text.index("end").split('.')[0]), i+3)
                            error_info = self.text.get(f"{context_start}.0", f"{context_end}.0")
                            break
                
                if error_info:
                    message = error_info
                    request_type = "explain_error"
                else:
                    messagebox.showinfo("Explanation", 
                                    "Please select code to explain or position cursor on an error message.")
                    return
                    
            response = self.api_client.send_request(message, request_type)
            if response:
                print("Response from LLM API:", response)
                
        except Exception as e:
            print("Error in code explanation feature:", e)
            messagebox.showerror("Error", f"Could not process explanation: {str(e)}")

    def extract_last_error(self):
        text = self.text.get("1.0", "end")
        
        traceback_pattern = r"Traceback \(most recent call last\):.*?(?=>>>|\Z)"
        error_match = re.search(traceback_pattern, text, re.DOTALL)
        
        if error_match:
            return error_match.group(0)
        
        try:
            error_ranges = self.text.tag_ranges("ERROR")
            if error_ranges:
                start_idx = error_ranges[0]
                end_idx = error_ranges[1]
                tagged_error = self.text.get(start_idx, end_idx)
                if tagged_error:
                    line_start = self.text.index(f"{start_idx} linestart")
                    line_end = self.text.index(f"{end_idx} lineend")
                    return self.text.get(line_start, line_end)
        except Exception as e:
            print("Error checking for error tags:", e)
        
        error_pattern = r"(?:Error|Exception|SyntaxError|NameError|TypeError|ValueError|AttributeError|ImportError|IndentationError|TabError|KeyError|IndexError|RuntimeError):[^\n]+(?:\n\s+[^\n]+)*"
        simple_error_match = re.search(error_pattern, text)
        
        if simple_error_match:
            return simple_error_match.group(0)
        
        last_lines = text.split("\n")[-10:]
        for line in last_lines:
            if re.match(r"^\s+\w+Error:", line):
                error_index = text.rfind(line)
                if error_index > 0:
                    context_start = text.rfind("\n", 0, error_index) + 1
                    context_end = text.find("\n\n", error_index)
                    if context_end == -1:
                        context_end = len(text)
                    return text[context_start:context_end].strip()
        
        return None
