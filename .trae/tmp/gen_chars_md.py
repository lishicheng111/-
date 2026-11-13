import json, subprocess, sys, re, time, os

def run(args, check=True):
    p = subprocess.run(["lark-cli"] + args, capture_output=True, text=True)
    try:
        d = json.loads(p.stdout)
        if check and not d.get("ok"):
            print(f"ERR {' '.join(args[:3])}: {d}", file=sys.stderr)
        return d
    except Exception:
        return {"ok": False, "raw": (p.stdout or p.stderr)[:200]}

F = json.load(open("/workspace/.trae/tmp/folders.json"))
TARGET = F["02_资料库/角色档案"]
chars = json.load(open("/workspace/.trae/tmp/chars.json"))

def safe_name(s):
    return re.sub(r'[\\/:*?"<>|\s]+', '_', str(s))[:50]

def get_char_id(title):
    m = re.match(r'(wife|hero|npc)_(\d+)(.*)', title)
    if m:
        cat = m.group(1)
        num = m.group(2)
        suffix = re.sub(r'[-\s]', '', m.group(3))
        return f"{cat}_{num}{suffix}" if suffix else f"{cat}_{num}"
    return safe_name(title)[:30]

def char_url(node_token):
    return f"https://hjjxo8h8vu.feishu.cn/wiki/{node_token}"

def md_content(c):
    title = c["title"]
    char_id = get_char_id(title)
    name = c["name"]
    race = c.get("race", "")
    job = c.get("job", "")
    personality = c.get("personality", "")
    background = c.get("background", "")
    friend = c.get("friend", "")
    enemy = c.get("enemy", "")
    fam_bond = c.get("family_bond", "")
    partner_bond = c.get("partner_bond", "")
    url = char_url(c["node_token"])
    
    notes = []
    if "苏西" in title and name == "尼贝尔":
        notes.append("名称字段被错误填写为「尼贝尔」，但角色页标题和其他字段确认为苏西。")
    
    for k, v in [("友情", friend), ("恩怨", enemy), ("羁绊-家人", fam_bond), ("羁绊-伙伴", partner_bond)]:
        if v and len(v) > 30 and any(s in v for s in ["。", "和", "关系", "认识"]):
            notes.append(f"{k}字段包含整句描述，无法解析为关系边：「{v[:50]}」")
    
    cat = "家人" if title.startswith("wife") else ("伙伴" if title.startswith("hero") else "NPC")
    
    return f"""---
char_id: {char_id}
name: {name}
title_original: {title}
category: {cat}
source: {url}
scan_date: 2026-11-13
---

# {char_id} · {name}

> 原始角色页：[{title}]({url})
> 扫描建立于 2026-11-13

## 基础信息

| 字段 | 值 |
|---|---|
| 英文 ID | {char_id} |
| 中文名 | {name} |
| 资料库归类 | {cat}资料库 |
| 种族 | {race} |
| 职业 / 身份 | {job} |

## 背景故事

{background}

## 性格

{personality}

## 关系

### 友情
{friend or "（空）"}

### 恩怨
{enemy or "（空）"}

### 羁绊-家人
{fam_bond or "（空）"}

### 羁绊-伙伴
{partner_bond or "（空）"}

## 原始资料

- 飞书角色页：{url}
- 内嵌基础信息表 token：{c.get("stoken", "N/A")}
- 内嵌表 sheet_id：{c.get("sid", "N/A")}

## 信息备注
{chr(10).join(["- " + n for n in notes]) if notes else "- 无异常"}
"""

LOCAL_DIR = "/workspace/.trae/tmp/chars_md"
os.makedirs(LOCAL_DIR, exist_ok=True)

print(f"准备生成 {len(chars)} 份角色档案 MD...", file=sys.stderr)
created = []
failed = []

for i, c in enumerate(chars):
    title = c["title"]
    if title == "伙伴信息模板":
        continue
    
    char_id = get_char_id(title)
    fname = f"{char_id}_{safe_name(c['name'])}.md"
    fpath = os.path.join(LOCAL_DIR, fname)
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(md_content(c))
    
    d = run(["markdown", "+create", "--folder-token", TARGET, "--file", fpath, "--name", fname], check=False)
    if d.get("ok"):
        created.append(fname)
        print(f"  [{i+1}/{len(chars)}] ✓ {char_id} {c['name']}", file=sys.stderr)
    else:
        failed.append((fname, str(d)[:150]))
        print(f"  [{i+1}/{len(chars)}] ✗ {char_id} {c['name']} -> {str(d)[:100]}", file=sys.stderr)
    time.sleep(0.4)

print(f"\n成功 {len(created)}/{len(chars)} 失败 {len(failed)}", file=sys.stderr)
if failed:
    print("失败:", file=sys.stderr)
    for f, e in failed[:10]: print(f"  {f}: {e}", file=sys.stderr)

json.dump({"created": created, "failed": failed}, open("/workspace/.trae/tmp/upload_result.json", "w"), ensure_ascii=False, indent=1)
