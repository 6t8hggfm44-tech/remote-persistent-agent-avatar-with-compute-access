"""Deterministic display fixtures; these functions never call an AI or tools."""


def make_reply(content, persona):
    openings = {
        "warm": "Thanks for sharing that.",
        "direct": "Here is the preview.",
        "thoughtful": "Let’s give that a little structure.",
        "playful": "Let’s get the idea on the workbench.",
    }
    quote = content if len(content) <= 220 else content[:217] + "…"
    lines = [
        "[Local preview · scripted response, not AI]",
        "{} I’m {}. {}".format(openings[persona["tone"]], persona["name"], persona["role"]),
        'Your message: “{}”'.format(quote),
    ]
    if persona["response_length"] != "short":
        lines.append("This conversation is saved on this computer. You can try a sample task to see the local queue run, complete, or cancel.")
    if persona["response_length"] == "detailed":
        lines.append("A real model, microphone, avatar, external tools, and Executive Agent integration are not connected. This example only demonstrates the interface and durable state.")
    if persona["instructions"]:
        lines.append("Your custom persona notes are saved for a future AI connection; this scripted preview does not interpret them.")
    return "\n\n".join(lines)


def make_draft(title, persona):
    return (
        "Local sample outline · scripted, not AI\n\n"
        "{}\n\n"
        "1. Define the desired outcome.\n"
        "2. List the information and resources needed.\n"
        "3. Choose one small next step.\n"
        "4. Review the result before taking action.\n\n"
        "Prepared as a preview for {}. No external action was performed."
    ).format(title, persona["name"])
