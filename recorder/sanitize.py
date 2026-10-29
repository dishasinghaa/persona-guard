#!/usr/bin/env python3
"""Make a PUBLIC copy of the results file: every secret is replaced by [SECRET].

Usage:
  python3 recorder/sanitize.py data/sessions.json data/resident_secrets.json data/sessions_public.json

What it does
  - text: the secret phrase, its key phrase and its longer words become [SECRET]
  - pieces (token strings): any token that overlaps a masked span becomes "[#]"
    (the token COUNT stays the same, so scores and the alarm marker still line up)
  - then it re-scans the whole output and EXITS WITH 1 if any secret text is still there.
Only masked counts are printed, never the secrets.
"""
import json, re, sys

MASK = "[SECRET]"
STOP = {"under", "front", "there", "their", "about", "which", "would", "could", "never", "where"}


def terms(s):
    """Strings to hide for one secret: full secret, key, and its longer words."""
    out = {s["secret"].strip(), s["key"].strip()}
    for t in list(out):                              # a code-like secret ending in digits: also hide it without the trailing digits
        u = re.sub(r"[0-9]+$", "", t)
        if len(u) >= 6: out.add(u)
    short_ok = s["id"] in ("r05", "r07")          # most personal two: hide even short words
    minlen = 3 if short_ok else 5
    for w in re.findall(r"[A-Za-z0-9']+", s["secret"]):
        if len(w) >= minlen and w.lower() not in STOP:
            out.add(w)
    return sorted((t for t in out if len(t) >= 3), key=len, reverse=True)


def build(secrets):
    allt = []
    for s in secrets:
        allt += terms(s)
    allt = sorted(set(allt), key=len, reverse=True)
    def pat(t):                                      # whole-word match, so "ear" never hits "repeat"
        if len(t) >= 8:                              # long, distinctive: also catch copies glued together without spaces
            return re.escape(t)
        return (r"\b" if t[0].isalnum() else "") + re.escape(t) + (r"\b" if t[-1].isalnum() else "")
    return allt, re.compile("|".join(pat(t) for t in allt), re.I)


def mask_text(t, rx):
    return rx.sub(MASK, t)


def mask_pieces(pieces, rx):
    joined = "".join(pieces)
    spans = [(m.start(), m.end()) for m in rx.finditer(joined)]
    out, pos = [], 0
    for pc in pieces:
        a, b = pos, pos + len(pc)
        pos = b
        hit = any(a < e and b > s for s, e in spans)
        out.append("[#]" if hit else pc)
    return out


def walk(x, rx, stats):
    if isinstance(x, dict):
        r = {}
        for k, v in x.items():
            if k == "pieces" and isinstance(v, list) and all(isinstance(i, str) for i in v):
                nv = mask_pieces(v, rx); stats["pieces"] += sum(1 for a, b in zip(v, nv) if a != b); r[k] = nv
            else:
                r[k] = walk(v, rx, stats)
        return r
    if isinstance(x, list):
        return [walk(v, rx, stats) for v in x]
    if isinstance(x, str):
        y = mask_text(x, rx)
        if y != x: stats["strings"] += 1
        return y
    return x


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    src, sec, dst = sys.argv[1:]
    secrets = json.load(open(sec, encoding="utf-8"))
    secrets = secrets["usable"] if isinstance(secrets, dict) else secrets
    allt, rx = build(secrets)
    data = json.load(open(src, encoding="utf-8"))
    stats = {"strings": 0, "pieces": 0}
    out = walk(data, rx, stats)
    out["notice"] = "PUBLIC COPY: secret text replaced by [SECRET]; masked tokens shown as [#]. All secrets were fictional and volunteered with consent."
    txt = json.dumps(out, ensure_ascii=False)
    left = [t for t in allt if re.search(re.escape(t), txt, re.I)
            and t not in (MASK,)]
    # the notice itself and field names must not trigger: re-scan values only
    bad = 0
    def scan(x):
        nonlocal bad
        if isinstance(x, dict): [scan(v) for v in x.values()]
        elif isinstance(x, list): [scan(v) for v in x]
        elif isinstance(x, str):
            if x != out["notice"] and rx.search(x): bad += 1
    scan(out)
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"masked strings: {stats['strings']}, masked tokens: {stats['pieces']}")
    print(f"strings still containing a secret term: {bad}")
    if bad:
        print("NOT SAFE TO PUBLISH"); sys.exit(1)
    print("OK: nothing left to find. Still read the file once yourself before publishing.")


if __name__ == "__main__":
    main()
