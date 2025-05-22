import re
import io
import sys
import tkinter.messagebox as messagebox
from tkinter import INSERT
from idlelib.llm_api import LLMApiClient
from pyflakes.api import check
from pyflakes.reporter import Reporter

URL = "https://backend-190.onrender.com/explain"

class LLM_explanation:
    def __init__(self, editwin):
        self.editwin = editwin
        self.text = editwin.text
        self.explanation_mode = False
        self.api_client = LLMApiClient(URL)
        self.text.bind("<KeyRelease>", lambda e: self.check_and_underline_errors())
        
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

            '''
                Put the response in a second screen 
            '''
            if response:
                explanation = f"{response}\n"
                if hasattr(self.editwin, 'show_explanation_panel'):
                    self.editwin.show_explanation_panel()
                panel = self.editwin.explanation_panel
                panel.config(state='normal')
                panel.delete('1.0', 'end')
                self.insert_markdown(panel, explanation)
                panel.config(state='disabled')
                
        except Exception as e:
            print("Error in code explanation feature:", e)
            messagebox.showerror("Error", f"Could not process explanation: {str(e)}")
            
    def insert_markdown(self, text_widget, content):
        text_widget.tag_configure("bold", font=("TkDefaultFont", 10, "bold"))
        text_widget.tag_configure("header", font=("TkDefaultFont", 11, "bold"))
        text_widget.tag_configure("bullet", lmargin1=20, lmargin2=30)
        text_widget.tag_configure("code", font=("Courier", 10), background="#8c5aff")

        lines = content.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r"^[A-Z][A-Z\s]+:$", stripped) or stripped.endswith(":"):
                text_widget.insert("end", line + "\n", "header")
            elif re.match(r"^(\*|•)\s+", stripped):
                bullet_line = "• " + stripped[2:] + "\n"
                text_widget.insert("end", bullet_line, "bullet")
            elif "**" in line:
                parts = re.split(r"(\*\*.*?\*\*)", line)
                for part in parts:
                    if part.startswith("**") and part.endswith("**"):
                        text_widget.insert("end", part[2:-2], "bold")
                    else:
                        text_widget.insert("end", part)
                text_widget.insert("end", "\n")
            elif re.search(r"`[^`]+`", line):
                parts = re.split(r"(`[^`]+`)", line)
                for part in parts:
                    if part.startswith("`") and part.endswith("`"):
                        text_widget.insert("end", part[1:-1], "code")
                    else:
                        text_widget.insert("end", part)
                text_widget.insert("end", "\n")
            else:
                text_widget.insert("end", line + "\n")

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
    
    def underline_error(self, line_number):
        # Underline the whole line in red
        self.text.tag_configure("error_underline", underline=True, foreground="red")
        self.text.tag_remove("error_underline", "1.0", "end")
        self.text.tag_add("error_underline", f"{line_number}.0", f"{line_number}.end")

    def check_and_underline_errors(self):
        self.text.tag_remove("error_underline", "1.0", "end")
        is_shell = hasattr(self.editwin, 'interp')
        error_lines = set()

        # if is_shell:
        #     # Only check the current input line in the shell
        #     insert_index = self.text.index("insert")
        #     line_number = insert_index.split('.')[0]
        #     line_start = f"{line_number}.0"
        #     line_end = f"{line_number}.end"
        #     line_content = self.text.get(line_start, line_end)
        #     # Skip prompt lines
        #     if line_content.strip().startswith((">>>", "...")):
        #         return
        #     content = line_content
        #     line_offset = int(line_number)

        #     # --- Bracket/quote error detection ---
        #     stack = []
        #     pairs = {'(': ')', '[': ']', '{': '}'}
        #     openers = pairs.keys()
        #     closers = pairs.values()
        #     for i, char in enumerate(content):
        #         if char in openers:
        #             stack.append((char, i))
        #         elif char in closers:
        #             if stack and pairs[stack[-1][0]] == char:
        #                 stack.pop()
        #             else:
        #                 idx = i
        #                 line = line_offset  # Always underline the current shell line
        #                 error_lines.add(line)
        #     if stack:
        #         _, idx = stack[-1]
        #         line = line_offset
        #         error_lines.add(line)
        #     single_quotes = content.count("'")
        #     double_quotes = content.count('"')
        #     if single_quotes % 2 != 0 or double_quotes % 2 != 0:
        #         error_lines.add(line_offset)

        #     # --- Linter-based error detection (pyflakes) for shell ---
        #     code = content
        #     output = io.StringIO()
        #     reporter = Reporter(output, output)
        #     check(code, "<input>", reporter=reporter)
        #     output.seek(0)
        #     for line in output:
        #         # Always underline the current shell line if any error
        #         if line.strip():
        #             error_lines.add(line_offset)

        # else:
            # Editor window: check all code
        if not is_shell:
            content = self.text.get("1.0", "end-1c")
            line_offset = 1

            # --- Bracket/quote error detection ---
            stack = []
            pairs = {'(': ')', '[': ']', '{': '}'}
            openers = pairs.keys()
            closers = pairs.values()
            for i, char in enumerate(content):
                if char in openers:
                    stack.append((char, i))
                elif char in closers:
                    if stack and pairs[stack[-1][0]] == char:
                        stack.pop()
                    else:
                        idx = i
                        line = content.count('\n', 0, idx) + line_offset
                        error_lines.add(line)
            if stack:
                _, idx = stack[-1]
                line = content.count('\n', 0, idx) + line_offset
                error_lines.add(line)
            single_quotes = content.count("'")
            double_quotes = content.count('"')
            if single_quotes % 2 != 0 or double_quotes % 2 != 0:
                last_quote = max(content.rfind("'"), content.rfind('"'))
                line = content.count('\n', 0, last_quote) + line_offset
                error_lines.add(line)

            # --- Linter-based error detection (pyflakes) ---
            code = content
            output = io.StringIO()
            reporter = Reporter(output, output)
            check(code, "<input>", reporter=reporter)
            output.seek(0)
            for line in output:
                match = re.match(r"<input>:(\d+):", line)
                if match:
                    error_lines.add(int(match.group(1)))

        # Underline all error lines
        for line_number in error_lines:
            self.text.tag_add("error_underline", f"{line_number}.0", f"{line_number}.end")
        if error_lines:
            self.text.tag_configure("error_underline", underline=True, foreground="red")
        else:
            self.text.tag_remove("error_underline", "1.0", "end")

'''
less strict version of linter 
Only checking unclosed quotation and bracket for shell 
Using linter only for editor window
def check_and_underline_errors(self):
    self.text.tag_remove("error_underline", "1.0", "end")
    is_shell = hasattr(self.editwin, 'interp')
    error_lines = set()

    if is_shell:
        # Only check the current input line in the shell
        insert_index = self.text.index("insert")
        line_number = insert_index.split('.')[0]
        line_start = f"{line_number}.0"
        line_end = f"{line_number}.end"
        line_content = self.text.get(line_start, line_end)
        # Skip prompt lines
        if line_content.strip().startswith((">>>", "...")):
            return
        content = line_content
        line_offset = int(line_number)

        # --- Bracket/quote error detection only ---
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        openers = pairs.keys()
        closers = pairs.values()
        for i, char in enumerate(content):
            if char in openers:
                stack.append((char, i))
            elif char in closers:
                if stack and pairs[stack[-1][0]] == char:
                    stack.pop()
                else:
                    error_lines.add(line_offset)
        if stack:
            error_lines.add(line_offset)
        single_quotes = content.count("'")
        double_quotes = content.count('"')
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            error_lines.add(line_offset)

    else:
        # Editor window: check all code, including linter
        content = self.text.get("1.0", "end-1c")
        line_offset = 1

        # --- Bracket/quote error detection ---
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        openers = pairs.keys()
        closers = pairs.values()
        for i, char in enumerate(content):
            if char in openers:
                stack.append((char, i))
            elif char in closers:
                if stack and pairs[stack[-1][0]] == char:
                    stack.pop()
                else:
                    idx = i
                    line = content.count('\n', 0, idx) + line_offset
                    error_lines.add(line)
        if stack:
            _, idx = stack[-1]
            line = content.count('\n', 0, idx) + line_offset
            error_lines.add(line)
        single_quotes = content.count("'")
        double_quotes = content.count('"')
        if single_quotes % 2 != 0 or double_quotes % 2 != 0:
            last_quote = max(content.rfind("'"), content.rfind('"'))
            line = content.count('\n', 0, last_quote) + line_offset
            error_lines.add(line)

        # --- Linter-based error detection (pyflakes) ---
        code = content
        output = io.StringIO()
        reporter = Reporter(output, output)
        check(code, "<input>", reporter=reporter)
        output.seek(0)
        for line in output:
            match = re.match(r"<input>:(\d+):", line)
            if match:
                error_lines.add(int(match.group(1)))

    # Underline all error lines
    for line_number in error_lines:
        self.text.tag_add("error_underline", f"{line_number}.0", f"{line_number}.end")
    if error_lines:
        self.text.tag_configure("error_underline", underline=True, foreground="red")
    else:
        self.text.tag_remove("error_underline", "1.0", "end")
'''
