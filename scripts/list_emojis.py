"""Build a self-contained emoji inventory without importing or starting the bot."""
import ast
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CUSTOM = re.compile(r"<a?:[A-Za-z0-9_]+:\d+>")
# Emoji code-point ranges, including variation selectors and ZWJ sequences.
UNICODE = re.compile(
    r"[\U0001F000-\U0001FAFF\u2300-\u23FF\u2500-\u27FF\u2B00-\u2BFF]"
    r"[\uFE0E\uFE0F]?(?:\u200D"
    r"[\U0001F000-\U0001FAFF\u2300-\u23FF\u2500-\u27FF\u2B00-\u2BFF]"
    r"[\uFE0E\uFE0F]?)*"
)


def matches(text):
    return set(CUSTOM.findall(text)) | set(UNICODE.findall(CUSTOM.sub("", text)))


def build_inventory():
    config = ROOT / "utils/emojis.py"
    tree = ast.parse(config.read_text())
    definitions = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        definitions[target.id] = node.value.value

    inline = {}
    for folder in ("core", "cogs", "utils"):
        for path in (ROOT / folder).rglob("*.py"):
            if path == config:
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for emoji in matches(node.value):
                        inline.setdefault(emoji, set()).add(
                            f"{path.relative_to(ROOT)}:{node.lineno}")
    # Stored welcome templates and other JSON settings may also contain emojis.
    def scan_json(value, source):
        if isinstance(value, str):
            for emoji in matches(value):
                inline.setdefault(emoji, set()).add(source)
        elif isinstance(value, dict):
            for item in value.values():
                scan_json(item, source)
        elif isinstance(value, list):
            for item in value:
                scan_json(item, source)

    for path in ROOT.glob("*.json"):
        scan_json(json.loads(path.read_text()), path.name)

    # The old migration script contains historical values, not runtime settings.
    legacy_path = ROOT / "scripts/migrate_emojis_and_rename.py"
    legacy = set()
    if legacy_path.exists():
        for node in ast.walk(ast.parse(legacy_path.read_text())):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                legacy.update(CUSTOM.findall(node.value))

    def table(rows, headings):
        return "<table><thead><tr>" + "".join(
            f"<th>{html.escape(x)}</th>" for x in headings
        ) + "</tr></thead><tbody>" + "".join(
            "<tr>" + "".join(f"<td><code>{html.escape(str(x))}</code></td>"
                            for x in row) + "</tr>" for row in rows
        ) + "</tbody></table>"

    content = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Yawr Support — Complete Emoji List</title>
<style>body{{font:16px system-ui;margin:32px auto;max-width:1100px;padding:0 20px;
color:#20242c}}table{{border-collapse:collapse;width:100%;margin:24px 0}}
td,th{{padding:10px;border:1px solid #ddd;text-align:left;overflow-wrap:anywhere}}
th{{background:#f2f4f8}}code{{white-space:pre-wrap}}h2{{margin-top:36px}}</style>
<h1>Yawr Support — Complete Emoji List</h1>
<p>Edit the central entries in <code>utils/emojis.py</code>.
Animated replacements use <code>&lt;a:emoji_name:emoji_id&gt;</code>.
Use the actual ID of an animated emoji your bot can access; adding “a” to a static
emoji does not animate it. Enable Use External Emojis when using another server's
emojis. Duplicate values have multiple aliases.</p>
<h2>Central config: {len(definitions)} entries</h2>
{table(definitions.items(), ["Setting", "Current value"])}
<h2>Inline emojis in runtime code and stored settings: {len(inline)} unique values</h2>
<p>These locations are not controlled by the central config. Comments and the
historical migration script are excluded from this section.</p>
{table(((emoji, ", ".join(sorted(paths))) for emoji, paths in sorted(inline.items())),
       ["Emoji", "Locations"])}
<h2>Historical custom emojis: {len(legacy)} unique values</h2>
<p>These are old values in <code>scripts/migrate_emojis_and_rename.py</code>,
not current central settings. Do not rerun that script to change the emojis.</p>
{table(((x,) for x in sorted(legacy)), ["Historical value"])}
</html>"""
    output = ROOT / "generated-artifacts/emoji-list.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)
    print(f"{len(definitions)} central entries; {len(inline)} inline values; "
          f"{len(legacy)} historical custom values. Report: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    build_inventory()
