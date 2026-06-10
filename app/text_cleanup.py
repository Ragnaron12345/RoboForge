import re


def cleanup_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"^```(?:markdown|md)?\s*\n", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\n```\s*$", "", text.strip())
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def strip_code_fence(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:[a-zA-Z0-9_+-]+)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip() + "\n"
    return text + "\n"
