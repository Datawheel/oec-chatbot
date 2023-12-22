import re
import regex

def clean_string(text):
    return text.replace(", ", "%2C").replace(" ,", "%2C").strip()


def string_to_vars(text):
    """
    Splits the output of the GPT model into Variables, Measures and Cuts. Also sets Sort order and Limit for the output.
    """
    v = text.split("ariables:")[1].split("//")[0].strip(".")
    m = text.split("easures:")[1].split("//")[0].strip(".")
    
    if "Cuts" in text: c = text.split("uts:")[1].split('//')[0].strip(".")
    else: c = ""

    if "Sort" in text: s = text.split("ort:")[1].split("//")[0].strip(".").strip()
    else: s = "Desc"
    
    if "Limit" in text: l = text.split("imit:")[1].split("//")[0].strip(".").strip()
    else: l = ""

    if "Growth" in text: g = text.split("rowth:")[1].split("//")[0].strip(".").strip()
    else: g = ""

    return v, m, c, s, l, g


def extract_text_from_markdown_single_backticks(text):
    """
    Extracts any sub-string enclosed within backticks in a string.
    """
    regex = r"`([\s\S]+?)`"
    matches = re.findall(regex, text)

    if matches:
        extracted_text = matches[0]
    else:
        extracted_text = text

    return extracted_text


def extract_text_from_markdown_triple_backticks_aux(text):
    """
    Extracts any sub-string enclosed within triple backticks
    """
    matches = re.findall(r"```([\s\S]+?)```", text)
    if matches:
        return matches[0]
    return text


def extract_text_from_markdown_triple_backticks(raw_str):
    """
    Use regular expression to find JSON content between outermost curly brackets
    """
    match = regex.search(r'\{(?:[^{}]|(?R))*\}', raw_str)
    if match:
        json_content = match.group(0)
        return json_content
    else:
        return ""