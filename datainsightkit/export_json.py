import json

def render_json(report):
    return json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
