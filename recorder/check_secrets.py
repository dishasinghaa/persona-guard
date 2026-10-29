"""Screen resident-supplied secrets BEFORE they are used anywhere.

    python3 recorder/check_secrets.py data/resident_secrets.json

Expected file (kept on your laptop, gitignored, never uploaded):
    [{"id": "r01", "nickname": "Aarav", "secret": "PURPLE-OTTER-17", "consent": true}, ...]

Flags anything that looks like a REAL credential or personal data (email, phone, card number,
government-ID-like digit runs, API-key prefixes, long random strings, URLs), missing consent,
duplicates, and secrets too short/long to test properly. It never prints a full secret:
output is masked. Exit code 1 if anything is flagged.
"""
import json, re, sys

PATTERNS = [
    ("email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("URL", re.compile(r"https?://|www\.", re.I)),
    ("phone-like number", re.compile(r"(?<!\d)(\+?\d[\d\s().-]{8,}\d)(?!\d)")),
    ("API-key prefix", re.compile(r"\b(sk-|pk_|AKIA|ghp_|gho_|xox[bap]-|AIza|eyJ)", re.I)),
]

def luhn(d):
    s, alt = 0, False
    for ch in reversed(d):
        n = int(ch)
        if alt:
            n *= 2
            if n > 9: n -= 9
        s += n; alt = not alt
    return s % 10 == 0

def mask(s):
    return s[:2] + "*" * max(0, len(s) - 3) + s[-1:] if len(s) > 3 else "***"

def problems(item):
    out = []
    sec = str(item.get("secret", ""))
    if item.get("consent") is not True:
        out.append("no explicit consent: true")
    if not 6 <= len(sec) <= 40:
        out.append(f"length {len(sec)} outside 6..40")
    for name, rx in PATTERNS:
        if rx.search(sec):
            out.append("looks like " + name)
    digits = re.sub(r"\D", "", sec)
    if len(digits) >= 12:
        out.append("12+ digits (card / ID / account-like)")
    if 13 <= len(digits) <= 19 and luhn(digits):
        out.append("passes card-number checksum")
    if len(sec) >= 20 and re.fullmatch(r"[A-Za-z0-9+/_=-]+", sec) and len(set(sec)) > 12:
        out.append("long random-looking string (real token?)")
    return out

def main(path):
    items = json.load(open(path, encoding="utf-8"))
    bad, seen = 0, {}
    for it in items:
        ps = problems(it)
        key = str(it.get("secret", "")).strip().lower()
        if key in seen:
            ps.append(f"duplicate of {seen[key]}")
        seen[key] = it.get("id")
        status = "FLAG" if ps else "ok  "
        bad += bool(ps)
        print(f"{status} {str(it.get('id')):6s} {mask(str(it.get('secret',''))):20s} " + "; ".join(ps))
    print(f"\n{len(items)} secrets, {bad} flagged. Use only the 'ok' ones; ask the owner of each flagged one for a made-up replacement.")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
