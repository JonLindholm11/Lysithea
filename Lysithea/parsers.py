# lysithea/parsers.py
"""
Parse AI responses to extract code and explanations
"""

import re

def extract_code_from_response(response_text):
    """Extract code block from AI response and remove documentation comments"""
    pattern = r'```(?:javascript|python|jsx|js|py|typescript|ts)?\n(.*?)```'
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    if matches:
        code = matches[0].strip()
        code = re.sub(r'/\*\*.*?\*/', '', code, flags=re.DOTALL)
        code = re.sub(r'\n{3,}', '\n\n', code)
        return code.strip()
    
    return None

def extract_explanation_from_response(response_text):
    """Extract explanation text (everything after code block)"""
    parts = re.split(r'```.*?```', response_text, flags=re.DOTALL)
    if len(parts) > 1:
        return parts[-1].strip()
    return response_text.strip()