
def render_json(json):
    if not json.get("full_text", ""):
        return ""

    return json["full_text"]
