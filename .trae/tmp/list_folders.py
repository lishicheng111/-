import json, subprocess, sys

def run(args, check=True):
    p = subprocess.run(["lark-cli"] + args, capture_output=True, text=True)
    try:
        d = json.loads(p.stdout)
        if check and not d.get("ok"):
            print(f"ERR {' '.join(args[:3])}: {d}", file=sys.stderr)
        return d
    except Exception:
        return {"ok": False, "raw": (p.stdout or p.stderr)[:300]}

ROOT = "nodcneJqnih3rJuHCNky2UMAkOc"

# 先列出根目录下已有的文件夹
r = run(["drive", "files", "list", "--folder-token", ROOT, "--page-all", "--page-limit", "3"])
folders = {}
for f in r["data"]["files"]:
    if f["type"] == "folder":
        folders[f["name"]] = f["token"]

print("根目录文件夹:", json.dumps(folders, ensure_ascii=False, indent=2))

subs = {
    "02_资料库": ["角色档案", "生活身份", "角色特质", "参考来源"],
    "04_产出": ["01_候选概念", "02_AI审核", "03_人工审核", "04_角色设定", "05_人设深化", "06_立绘表达方案"],
    "09_归档": ["旧资料库", "旧产出", "旧技能"],
}
for parent, names in subs.items():
    pt = folders.get(parent)
    if not pt:
        print(f"no parent {parent}", file=sys.stderr); continue
    r2 = run(["drive", "files", "list", "--folder-token", pt, "--page-all", "--page-limit", "2"])
    for f in r2.get("data", {}).get("files", []):
        if f["type"] == "folder":
            folders[f"{parent}/{f['name']}"] = f["token"]

json.dump(folders, open("/tmp/trae_scan/folders.json", "w"), ensure_ascii=False, indent=1)
print("\n所有文件夹 token 已保存")
for k,v in folders.items(): print(f"  {k} -> {v}")
