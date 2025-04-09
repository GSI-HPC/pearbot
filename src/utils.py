import re

def remove_reasoning(text):
    # match <think>...</think> only at the beginning of the string
    pattern = r'^\s*<think>.*?</think>\s*'
    # Use re.sub with re.DOTALL to match across multiple lines
    result = re.sub(pattern, '', text, flags=re.DOTALL)
    return result