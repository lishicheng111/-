import json, subprocess, csv, io, re, sys, time

BASE = "/workspace/.trae/tmp"
nodes = []
for f in ["family.json", "friends1.json", "friends2.json"]:
    d = json.load(open(f"{BASE}/{f}"))
    nodes.extend(d["data"]["nodes"])
nodes = [n for n in nodes if n["title"] != "伙伴信息模板"]

def run(args):
    p = subprocess.run(["lark-cli"] + args, capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except Exception:
        try:
            return json.loads(p.stderr)
        except Exception:
            return {"ok": False, "raw": (p.stdout or p.stderr)[:200]}

def read_char(n):
    tok = n["obj_token"]
    doc = run(["docs", "+fetch", "--doc", tok])
    if not doc.get("ok"):
        return {"title": n["title"], "error": "doc fetch fail", "raw": str(doc)[:160]}
    html = doc["data"]["document"]["content"]
    m = re.search(r'<sheet[^>]*sheet-id="([^"]+)"[^>]*token="([^"]+)"', html)
    if not m:
        return {"title": n["title"], "error": "no embedded sheet"}
    sid, stoken = m.group(1), m.group(2)
    r = run(["sheets", "+csv-get", "--spreadsheet-token", stoken, "--range", f"{sid}!A1:H29"])
    if not r.get("ok"):
        return {"title": n["title"], "error": "sheet read fail", "raw": str(r)[:160], "stoken": stoken, "sid": sid}
    text = r["data"]["annotated_csv"]
    rows = {}
    for line in text.splitlines():
        mm = re.match(r"\[row=(\d+)\] (.*)", line)
        if not mm:
            continue
        idx = int(mm.group(1))
        vals = next(csv.reader(io.StringIO(mm.group(2))))
        rows[idx] = [v.strip() for v in vals] + [""] * 8
    def g(row, col=1):
        return rows.get(row, [""] * 8)[col]
    return {
        "title": n["title"],
        "node_token": n["node_token"],
        "name": g(2, 4) or n["title"].split("-")[-1],
        "race": g(5, 1),
        "job": g(15, 1),
        "personality": g(16, 1),
        "background": g(7, 1),
        "friend": g(23, 1),
        "enemy": g(24, 1),
        "family_bond": g(27, 1),
        "partner_bond": g(28, 1),
        "stoken": stoken,
        "sid": sid,
    }

out = []
for i, n in enumerate(nodes):
    res = read_char(n)
    out.append(res)
    print(f"{i+1}/{len(nodes)} {n['title']}", file=sys.stderr)
    time.sleep(0.05)

json.dump(out, open(f"{BASE}/chars.json", "w"), ensure_ascii=False, indent=1)
errs = [o for o in out if "error" in o]
print(json.dumps({"count": len(out), "errors": len(errs)}, ensure_ascii=False))
