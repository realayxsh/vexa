
"""
Migration script:
  1. Replace all hard-coded emoji literals with e.<name> references
  2. Convert plain strings containing emoji refs to f-strings
  3. Add `from utils.emojis import e` where needed
  4. Rename bot class Ventura → Dilbar in code
  5. Replace user-facing "Ventura" display strings with "DILBAR < 3"
"""

import os, re

# ── Emoji literal → attribute name mapping ──────────────────────────────────
EMOJI_MAP = {
    "<a:green_tick:1103363669263405157>": "e.green_tick",
    "<a:red_cross:1103371611983327322>":  "e.red_cross",
    "<:tick:1076042204310679562>":         "e.tick",
    "<:cross:1077478135794245743>":        "e.cross",
    "<a:cross:1096447109470896169>":       "e.cross_anim",
    "<:dot_white:1103476115709890682>":    "e.dot_white",
    "<a:arrow:1096441081031295026>":       "e.arrow",
    "<:online:1103971128445239388>":       "e.online",
    "<:offline:1103971376320221216>":      "e.offline",
    "<:idle:1103971198464954479>":         "e.idle",
    "<:dnd:1103971230454910996>":          "e.dnd",
    "<a:status:1103968091311972352>":      "e.status_anim",
    "<:general:1103357467762626671>":      "e.general",
    "<:icons_music:1103357638080737320>":  "e.music",
    "<:welcome:1103358088922279986>":      "e.welcome",
    "<:icons_premiumchannel:1103358451490496644>": "e.premium",
    "<:Icon_Ticket:1103358644747251742>":  "e.ticket",
    "<:icons_serverpartner:1103359488150483054>": "e.server",
    "<:Moderation:1103359662293798955>":   "e.moderation",
    "<:icons_games:1103359802979131432>":  "e.games",
    "<:utility:1103360055195213975>":      "e.utility",
    "<:IconVoice:1103360243276206322>":    "e.icon_voice",
    "<:voice:1103360369629614141>":        "e.voice",
    "<:nsfw32:1103360693119496262>":       "e.nsfw",
    "<:encryption:1103360958748954654>":   "e.encryption",
    "<:paint_icons:1103361121727037601>":  "e.paint",
    "<:icon_verified:1104655495618379786>":"e.verified",
    "<:role:1103972602294304778>":         "e.role",
    "<:discord:1103964847709896765>":      "e.discord_icon",
    "<:users:1103964989800337460>":        "e.users",
    "<:python:1103965211762884728>":       "e.python",
    "<:IconPing:1103965446312575009>":     "e.ping",
    "<:developer:1103965691859697725>":    "e.developer",
    "<:King:1103728930277556284>":         "e.king",
    "<a:war:1085999886459228292>":         "e.war",
    "<a:booster_icon:1103966226239209513>":"e.booster",
    "<:HYPERSQUAD_EVENTS:1103966515549712395>": "e.hypersquad_events",
    "<:hypersquad:1103966700635951165>":   "e.hypersquad",
    "<:bravery:1103966926142701638>":      "e.bravery",
    "<:Brilliance:1103967070338687068>":   "e.brilliance",
    "<:EarlySupport:1103963190192259142>": "e.early_support",
    "<:active_developer:1103967384416559145>": "e.active_dev",
    "<:CertifiedModerator:1072720350900670576>": "e.certified_mod",
    "<a:ventura_staff:1072720458585223279>": "e.staff_anim",
    "<:partners:1103962673823088712>":     "e.partners",
    "<:StaffBadge:1103729149169905795>":   "e.staff_badge",
    "<:crown1:1072718187147300924>":       "e.crown",
    "<:icons_speakerlow:1084727725513789474>": "e.speaker_low",
    "<:emote:1083286116788097036>":        "e.emote1",
    "<:emote:1083285893651107860>":        "e.emote2",
    "<:jk_stop:1072904929062170634>":      "e.jk_stop",
    "<:IconVoice:1084709816410308719>":    "e.icon_voice2",
    "<a:Black_Diamond:1115859193103122483>": "e.black_diamond",
    "<a:Playing:1103975756989747250>":     "e.playing",
    "<:Room_icon_Stage:1103975106457387038>": "e.stage_icon",
    "<:artic_uptime:1103974519439372358>": "e.uptime",
    "<:Fb_Like:1103969818572509224>":      "e.fb_like",
    "<:Dislike:1103969904933216266>":      "e.dislike",
    "<a:KEKW_bruh:1072834782477688832>":   "e.kekw",
    "<a:dev:1072465734338363463>":         "e.dev_anim",
}

# Sort by length descending so longer IDs are matched first (avoids partial matches)
SORTED_EMOJIS = sorted(EMOJI_MAP.items(), key=lambda x: len(x[0]), reverse=True)

IMPORT_LINE = "from utils.emojis import e\n"

def needs_f_prefix(s: str) -> bool:
    """Return True if string s contains {e. references but no f prefix."""
    return "{e." in s

def make_fstring(line: str) -> str:
    """
    For each string literal in the line that contains {e. references
    but no f prefix, add the f prefix.
    """
    # Match optional prefix + quote style + content + closing quote
    # We handle both single and double quote, non-greedy
    pattern = re.compile(
        r"""(?<![fFrRbBuU])((?:[bBuU])?)((?:\"\"\"|\'{3}|\"|\'))""",
        re.DOTALL
    )

    result = list(line)
    # Work on a copy to find positions
    offset = 0
    for m in re.finditer(
        r"""(?<![fFrRbBuU])((?:[bBuU])?)([\"\']{1,3})""", line
    ):
        prefix = m.group(1)
        quote = m.group(2)
        start = m.start()
        # find matching close quote
        try:
            end = line.index(quote, m.end())
        except ValueError:
            continue
        content = line[m.end():end]
        if needs_f_prefix(content):
            ins_pos = start + offset
            result.insert(ins_pos, "f")
            offset += 1
    return "".join(result)


def process_file(path: str):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        original = f.read()

    content = original
    replaced = False

    # 1. Replace each emoji literal
    for emoji, varname in SORTED_EMOJIS:
        if emoji in content:
            content = content.replace(emoji, "{" + varname + "}")
            replaced = True

    if not replaced:
        return False

    # 2. Convert affected strings to f-strings line by line
    lines = content.splitlines(keepends=True)
    new_lines = []
    for line in lines:
        if "{e." in line:
            line = make_fstring(line)
        new_lines.append(line)
    content = "".join(new_lines)

    # 3. Add import if not already present
    if IMPORT_LINE.strip() not in content:
        # Insert after the last existing import block line
        import_inserted = False
        lines2 = content.splitlines(keepends=True)
        for i, l in enumerate(lines2):
            if l.startswith("from utils") or l.startswith("import utils"):
                lines2.insert(i + 1, IMPORT_LINE)
                import_inserted = True
                break
        if not import_inserted:
            # Put after all imports at the top
            for i, l in enumerate(lines2):
                if l.strip() and not l.startswith("#") and not l.startswith("from ") and not l.startswith("import "):
                    lines2.insert(i, IMPORT_LINE)
                    import_inserted = True
                    break
        if not import_inserted:
            lines2.insert(0, IMPORT_LINE)
        content = "".join(lines2)

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def rename_bot_name(path: str):
    """
    - In code: Ventura (class/import) → Dilbar
    - In user-facing strings: 'Ventura' as display text → 'DILBAR < 3'
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    original = content

    # User-facing display strings first (before code rename)
    display_patterns = [
        (r"'Thanks For Using Ventura'", "'Thanks For Using DILBAR < 3'"),
        (r'"Thanks For Using Ventura"', '"Thanks For Using DILBAR < 3"'),
        (r'f"Server List of Ventura', 'f"Server List of DILBAR < 3'),
        (r"f'Server List of Ventura", "f'Server List of DILBAR < 3"),
        (r'f"List of Blacklisted users of Ventura', 'f"List of Blacklisted users of DILBAR < 3'),
        (r"f'List of Blacklisted users of Ventura", "f'List of Blacklisted users of DILBAR < 3"),
        (r'f"No Prefix of Ventura', 'f"No Prefix of DILBAR < 3'),
        (r"f'No Prefix of Ventura", "f'No Prefix of DILBAR < 3"),
        (r'"Create A Embed Using Ventura"', '"Create A Embed Using DILBAR < 3"'),
        (r"'Create A Embed Using Ventura'", "'Create A Embed Using DILBAR < 3'"),
        (r'"Ventura • Page', '"DILBAR < 3 • Page'),
        (r"'Ventura • Page", "'DILBAR < 3 • Page"),
        (r"'Ventura\n", "'DILBAR < 3\n"),
        (r'"Ventura\n', '"DILBAR < 3\n'),
        # Help embed title
        (r'"VesTrol |', '"DILBAR < 3 |'),
        (r"'VesTrol |", "'DILBAR < 3 |"),
    ]
    for old, new in display_patterns:
        content = content.replace(old, new)

    # Rename code-level class/import references
    code_renames = [
        ("from core.Ventura import Ventura", "from core.Dilbar import Dilbar"),
        ("from core import Cog, Ventura, Context", "from core import Cog, Dilbar, Context"),
        ("from core import Ventura, Cog, Context", "from core import Dilbar, Cog, Context"),
        ("from core import Ventura, Cog", "from core import Dilbar, Cog"),
        ("from core import Cog, Ventura", "from core import Cog, Dilbar"),
        ("from core import Cog,Ventura, Context", "from core import Cog, Dilbar, Context"),
        ("from core import Cog,Ventura", "from core import Cog, Dilbar"),
        ("from .Ventura import Ventura", "from .Dilbar import Dilbar"),
        ("from core import Ventura", "from core import Dilbar"),
        ("client: Ventura", "client: Dilbar"),
        ("bot: Ventura", "bot: Dilbar"),
        ("class Ventura(", "class Dilbar("),
        ("client = Ventura()", "client = Dilbar()"),
        ("async def Ventura_stats()", "async def dilbar_stats()"),
        ("await client.loop.create_task(Ventura_stats())", "await client.loop.create_task(dilbar_stats())"),
        # help.py has its own local instantiation
        ("client = Ventura()\n", ""),  # remove stray re-instantiation in help.py
    ]
    for old, new in code_renames:
        content = content.replace(old, new)

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


# ── Walk the project ────────────────────────────────────────────────────────
skip_dirs = {"__pycache__", ".git", "node_modules", ".local", "artifacts", "scripts", "lib"}
root = "/home/runner/workspace"

emoji_count = 0
rename_count = 0

for dirpath, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(dirpath, fname)
        if process_file(fpath):
            emoji_count += 1
            print(f"  [emoji] {fpath.replace(root+'/', '')}")
        if rename_bot_name(fpath):
            rename_count += 1
            print(f"  [name]  {fpath.replace(root+'/', '')}")

print(f"\nDone! Emoji migrated: {emoji_count} files | Bot name renamed: {rename_count} files")
