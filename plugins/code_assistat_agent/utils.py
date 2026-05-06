import json, re

def safe_json(text):
    try:
        match = re.search(r"```json(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1)
        return json.loads(text)
    except Exception:
        return {}