#!/usr/bin/env python3
"""百度贴吧讨论度验证:判定榜单小说是否"有讨论度"。

用法:
    python3 check_tieba_heat.py --input rank.json [--out verified.json]
    python3 check_tieba_heat.py --input rank.json \
        --browser-fill '{"书名A": {"followers": 12345, "posts": 67890}}'

热度门槛(可用参数调整):
    high: 关注 >= --high-followers(默认 10000)
    mid : 关注 >= --min-followers(默认 1000) 且 帖子 >= --min-posts(默认 5000)
    none: 不满足以上,判定不达标

注意:贴吧会拦截数据中心 IP(403)。直连失败时该书标记 blocked,
请用浏览器打开 https://tieba.baidu.com/f?kw=<书名> 读取"关注/帖子"数,
再用 --browser-fill 回填后重跑。
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def parse_num(text: str) -> int:
    text = text.replace(",", "").strip()
    m = re.match(r"^([\d.]+)\s*([wW万]?)", text)
    if not m:
        return 0
    n = float(m.group(1))
    if m.group(2):
        n *= 10000
    return int(n)


def fetch_bar_stats(name: str) -> dict:
    """直连贴吧抓吧页。返回 {status, followers, posts}。status: ok/blocked/no_bar"""
    url = "https://tieba.baidu.com/f?kw=" + urllib.parse.quote(name) + "&ie=utf-8"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return {"status": "blocked" if e.code in (403, 404) else "error",
                "followers": 0, "posts": 0}
    except (urllib.error.URLError, OSError):
        return {"status": "blocked", "followers": 0, "posts": 0}

    if "吧尚未建立" in html or "尚未创建" in html:
        return {"status": "no_bar", "followers": 0, "posts": 0}

    followers = posts = 0
    m = re.search(r'关注[^0-9万wW]{0,10}([\d.,]+[万wW]?)', html)
    if m:
        followers = parse_num(m.group(1))
    m = re.search(r'贴子[^0-9万wW]{0,10}([\d.,]+[万wW]?)', html) or \
        re.search(r'帖子[^0-9万wW]{0,10}([\d.,]+[万wW]?)', html)
    if m:
        posts = parse_num(m.group(1))
    if followers == 0 and posts == 0 and "tieba" not in html:
        return {"status": "blocked", "followers": 0, "posts": 0}
    return {"status": "ok", "followers": followers, "posts": posts}


def judge(stats: dict, hi_f: int, min_f: int, min_p: int) -> str:
    if stats["status"] != "ok":
        return "blocked" if stats["status"] == "blocked" else "none"
    if stats["followers"] >= hi_f:
        return "high"
    if stats["followers"] >= min_f and stats["posts"] >= min_p:
        return "mid"
    return "none"


def main() -> int:
    ap = argparse.ArgumentParser(description="贴吧讨论度验证")
    ap.add_argument("--input", required=True, help="榜单 JSON(fetch_fanqie_rank 输出)")
    ap.add_argument("--out", default="", help="输出 JSON(默认覆盖输入文件)")
    ap.add_argument("--browser-fill", default="",
                    help='浏览器读取结果回填,JSON: {"书名": {"followers": N, "posts": M}}')
    ap.add_argument("--high-followers", type=int, default=10000)
    ap.add_argument("--min-followers", type=int, default=1000)
    ap.add_argument("--min-posts", type=int, default=5000)
    ap.add_argument("--delay", type=float, default=1.5)
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        books = json.load(f)

    fill = json.loads(args.browser_fill) if args.browser_fill else {}

    blocked_names = []
    for b in books:
        name = b.get("name") or b.get("name_raw") or ""
        if name in fill:
            stats = {"status": "ok", "followers": int(fill[name].get("followers", 0)),
                     "posts": int(fill[name].get("posts", 0))}
            method = "browser"
        else:
            stats = fetch_bar_stats(name)
            method = "http"
            time.sleep(args.delay)
        b["tieba"] = {
            "bar_url": "https://tieba.baidu.com/f?kw=" + urllib.parse.quote(name),
            "followers": stats["followers"],
            "posts": stats["posts"],
            "method": method,
        }
        b["heat"] = judge(stats, args.high_followers,
                          args.min_followers, args.min_posts)
        if b["heat"] == "blocked":
            blocked_names.append(name)

    for b in books:
        b["passed"] = b.get("heat") in ("high", "mid")

    out_path = args.out or args.input
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    passed = sum(1 for b in books if b["passed"])
    print(f"OK: {passed}/{len(books)} 本通过热度验证 -> {out_path}", file=sys.stderr)
    if blocked_names:
        print("BLOCKED(需浏览器回填):", file=sys.stderr)
        for n in blocked_names:
            print(f"  - {n}  https://tieba.baidu.com/f?kw={urllib.parse.quote(n)}",
                  file=sys.stderr)
        print("读取关注/帖子数后用 --browser-fill 回填重跑。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
