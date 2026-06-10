from __future__ import annotations


def ensure_card_format(text: str) -> str:
    """Convert fragile Markdown tables into German vertical cards."""
    lines = text.splitlines()
    out: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        nonlocal table
        if not table:
            return
        headers = [cell.strip() for cell in table[0].strip("|").split("|")]
        rows = table[2:] if len(table) > 1 and set(table[1].replace("|", "").replace(":", "").strip()) <= {"-"} else table[1:]
        out.append("\n### Aus Tabellen automatisch erzeugte Karten")
        for row in rows:
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            if not any(cells):
                continue
            title = cells[0] or "Element"
            out.append(f"\n#### {title}")
            for header, value in zip(headers[1:], cells[1:]):
                if value:
                    out.append(f"- {header}: {value}")
        table = []

    for line in lines:
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table.append(line)
        else:
            flush_table()
            out.append(line)
    flush_table()
    return "\n".join(out).strip() + "\n"
