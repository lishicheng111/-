import json, subprocess, sys

ROOT = "nodcneJqnih3rJuHCNky2UMAkOc"

def run(args, check=True):
    p = subprocess.run(["lark-cli"] + args, capture_output=True, text=True)
    try:
        d = json.loads(p.stdout)
        if check and not d.get("ok"):
            print(f"ERR {args[:3]}: {d}", file=sys.stderr)
        return d
    except Exception:
        return {"ok": False, "raw": (p.stdout or p.stderr)[:200]}

dirs = [
    "00_方法", "01_项目上下文", "02_资料库", "03_任务单",
    "04_产出", "05_技能", "06_模板", "07_日志", "09_归档",
]

created = {}
for name in dirs:
    d = run(["drive", "+create-folder", "--folder-token", ROOT, "--name", name])
    tok = d.get("data", {}).get("token") or d.get("data", {}).get("folder_token")
    if not tok and d.get("data"):
        tok = list(d["data"].values())[0] if isinstance(d["data"], dict) else None
    created[name] = tok
    print(f"{name} -> {tok}")

# 子目录
subs = {
    "02_资料库": ["角色档案", "生活身份", "角色特质", "参考来源"],
    "04_产出": ["01_候选概念", "02_AI审核", "03_人工审核", "04_角色设定", "05_人设深化", "06_立绘表达方案"],
    "09_归档": ["旧资料库", "旧产出", "旧技能"],
}
for parent, names in subs.items():
    pt = created[parent]
    for n in names:
        d = run(["drive", "+create-folder", "--folder-token", pt, "--name", n])
        tok = d.get("data", {}).get("token") or list(d.get("data", {}).values())[0] if isinstance(d.get("data"), dict) else None
        created[f"{parent}/{n}"] = tok
        print(f"  {parent}/{n} -> {tok}")

json.dump(created, open("/tmp/trae_scan/folders.json", "w"), ensure_ascii=False, indent=1)
print("\nFOLDERS OK")
