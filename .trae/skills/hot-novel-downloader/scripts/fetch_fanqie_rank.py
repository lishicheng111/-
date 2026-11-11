#!/usr/bin/env python3
"""抓取番茄小说榜单,输出真实书名(经详情页还原,无字体混淆)。

用法:
    python3 fetch_fanqie_rank.py [--url URL] [--top N] [--no-detail] [--out FILE]

已验证(2026-11):番茄 /rank 与 /page/<bookId> 均可直连;
榜单页列表文字被自定义字体混淆(PUA 字符),详情页 <title> 为干净书名。
"""
import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
BASE = "https://fanqienovel.com"


def http_get(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def extract_initial_state(html: str) -> dict:
    """按花括号配平提取 window.__INITIAL_STATE__ 的 JSON。"""
    i = html.find("window.__INITIAL_STATE__=")
    if i < 0:
        return {}
    start = html.find("{", i)
    depth = 0
    for j in range(start, len(html)):
        c = html[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start:j + 1])
                except json.JSONDecodeError:
                    return {}
    return {}


def find_books(node, acc):
    if isinstance(node, dict):
        if ("bookName" in node or "book_name" in node) and \
           ("bookId" in node or "book_id" in node):
            acc.append(node)
            return
        for v in node.values():
            find_books(v, acc)
    elif isinstance(node, list):
        for v in node:
            find_books(v, acc)


def clean_name_from_detail(book_id: str) -> str:
    """详情页 <title> 格式:<书名>完整版在线免费阅读_<书名>小说_番茄小说官网"""
    html = http_get(f"{BASE}/page/{book_id}")
    m = re.search(r"<title>(.*?)完整版在线免费阅读", html)
    if m:
        return m.group(1).strip()
    m = re.search(r"<title>([^_<>]+)", html)
    return m.group(1).strip() if m else ""


def has_pua(text: str) -> bool:
    return any(0xE000 <= ord(c) <= 0xF8FF for c in text)


def main() -> int:
    ap = argparse.ArgumentParser(description="抓取番茄小说榜单")
    ap.add_argument("--url", default=f"{BASE}/rank", help="榜单页 URL")
    ap.add_argument("--top", type=int, default=20, help="取前 N 本")
    ap.add_argument("--no-detail", action="store_true",
                    help="跳过详情页(书名可能含混淆字符,不推荐)")
    ap.add_argument("--out", default="", help="输出 JSON 文件路径(默认 stdout)")
    ap.add_argument("--delay", type=float, default=0.8, help="详情页请求间隔秒数")
    args = ap.parse_args()

    try:
        html = http_get(args.url)
    except (urllib.error.URLError, OSError) as e:
        print(f"ERROR: 榜单页抓取失败: {e}", file=sys.stderr)
        return 1

    data = extract_initial_state(html)
    raw_books: list = []
    find_books(data, raw_books)

    seen, books = set(), []
    for b in raw_books:
        bid = str(b.get("bookId") or b.get("book_id"))
        if not bid or bid in seen:
            continue
        seen.add(bid)
        books.append({
            "rank": len(books) + 1,
            "book_id": bid,
            "name_raw": b.get("bookName") or b.get("book_name") or "",
            "author": re.sub(r"[-]", "", str(b.get("author") or "")),
            "read_count": int(b.get("read_count") or b.get("readCount") or 0),
            "source": "fanqie",
            "detail_url": f"{BASE}/page/{bid}",
        })
        if len(books) >= args.top:
            break

    if not books:
        print("ERROR: 未解析到任何书籍(页面结构可能已变更)", file=sys.stderr)
        return 1

    if not args.no_detail:
        for b in books:
            if has_pua(b["name_raw"]) or not b["name_raw"]:
                try:
                    b["name"] = clean_name_from_detail(b["book_id"])
                except (urllib.error.URLError, OSError):
                    b["name"] = b["name_raw"]
                time.sleep(args.delay)
            else:
                b["name"] = b["name_raw"]
    else:
        for b in books:
            b["name"] = b["name_raw"]

    out = json.dumps(books, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out + "\n")
        print(f"OK: {len(books)} 本书已写入 {args.out}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
