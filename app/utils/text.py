import re


def clean_telegram_text(text: str) -> str:
    # Markdown headings: ### Анализ -> Анализ
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Bold / italic markers
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")

    # Backticks
    text = text.replace("`", "")

    return text.strip()