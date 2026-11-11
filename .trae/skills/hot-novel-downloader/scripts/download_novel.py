#!/usr/bin/env python3
"""通用小说下载器:按用户提供的书源配置下载并合并 TXT。

合规要求(必须阅读):
    本脚本不内置任何书源。--source-config 指向的 JSON 配置必须由使用者
    自行提供,且仅可描述其**有权访问**的内容(如免费公开章节)。
    下载结果仅供个人离线阅读,禁止抓取收费/VIP 章节,禁止二次分发。
    因此必须显式传入 --i-understand 才会运行。

书源配置 site.json 格式:
{
  "name": "my-source",
  "chapter_list_url": "https://example.com/book/{book_id}",
  "chapter_link_pattern": "<a href=\\"(/book/{book_id}/\\\\d+.html)\\"[^>]*>([^<]+)</a>",
  "chapter_url_base": "https://example.com",
  "content_selector": "css:#content  或  regex:<div id=\\"content\\">(.*?)</div>",
  "encoding": "utf-8"
}

用法:
    python3 download_novel.py --name "书名" --book-id 12345 \
        --source-config site.json --i-understand --outdir novels/
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

COMPLIANCE = """\
[合规确认] 你已确认:
  1) 该书源配置由你本人提供,且你有权访问其内容;
  2) 不抓取收费/VIP 章节; 3) 仅供个人离线阅读,不二次分发。
"""


def http_get(url: str, encoding: str = "utf-8", timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return raw.decode(encoding, errors="replace")


def extract_content(html: str, selector: str) -> str:
    kind, _, expr = selector.partition(":")
    if kind == "regex":
        m = re.search(expr, html, re.S)
        body = m.group(1) if m else ""
    elif kind == "css":
        # 极简 css 支持:#id 或 .class 或 tag,取首个匹配元素 innerHTML
        if expr.startswith("#"):
            pat = rf'<(\w+)[^>]*id="{re.escape(expr[1:])}"[^>]*>(.*?)</\1>'
        elif expr.startswith("."):
            pat = rf'<(\w+)[^>]*class="[^"]*{re.escape(expr[1:])}[^"]*"[^>]*>(.*?)</\1>'
        else:
            pat = rf"<({re.escape(expr)})[^>]*>(.*?)</\1>"
        m = re.search(pat, html, re.S)
        body = m.group(2) if m else ""
    else:
        raise ValueError(f"未知 selector 类型: {kind}(仅支持 css:/regex:)")
    body = re.sub(r"<br\s*/?>", "\n", body)
    body = re.sub(r"</p>", "\n\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    body = re.sub(r"&nbsp;?", " ", body)
    body = re.sub(r"&lt;", "<", body)
    body = re.sub(r"&gt;", ">", body)
    body = re.sub(r"&amp;", "&", body)
    return body.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="通用小说下载器(需自备书源配置)")
    ap.add_argument("--name", required=True, help="书名(用于目录/文件名)")
    ap.add_argument("--book-id", required=True, help="书源站内的书籍 ID")
    ap.add_argument("--source-config", required=True, help="书源配置 JSON 路径")
    ap.add_argument("--outdir", default="novels")
    ap.add_argument("--delay", type=float, default=1.5, help="章节请求间隔秒数(≥1)")
    ap.add_argument("--max-chapters", type=int, default=0, help="调试用:最多下载 N 章")
    ap.add_argument("--i-understand", action="store_true",
                    help="确认已阅读并同意合规要求(必需)")
    args = ap.parse_args()

    if not args.i_understand:
        print("ERROR: 必须显式传入 --i-understand 确认合规要求后方可运行。\n",
              file=sys.stderr)
        print(COMPLIANCE, file=sys.stderr)
        return 2
    print(COMPLIANCE, file=sys.stderr)

    with open(args.source_config, encoding="utf-8") as f:
        cfg = json.load(f)
    enc = cfg.get("encoding", "utf-8")
    delay = max(args.delay, 1.0)

    safe_name = re.sub(r'[\\/:*?"<>|]', "_", args.name)
    book_dir = os.path.join(args.outdir, safe_name)
    chap_dir = os.path.join(book_dir, "chapters")
    os.makedirs(chap_dir, exist_ok=True)

    list_url = cfg["chapter_list_url"].format(book_id=args.book_id)
    try:
        list_html = http_get(list_url, enc)
    except (urllib.error.URLError, OSError) as e:
        print(f"ERROR: 目录页抓取失败: {e}", file=sys.stderr)
        return 1

    pattern = cfg["chapter_link_pattern"].replace("{book_id}", re.escape(args.book_id))
    links = re.findall(pattern, list_html)
    if not links:
        print("ERROR: 目录页未匹配到章节链接(检查 chapter_link_pattern)",
              file=sys.stderr)
        return 1

    base = cfg.get("chapter_url_base", "")
    chapters, seen = [], set()
    for href, title in links:
        url = href if href.startswith("http") else base + href
        if url in seen:
            continue
        seen.add(url)
        chapters.append((url, title.strip()))
    if args.max_chapters:
        chapters = chapters[: args.max_chapters]

    print(f"共 {len(chapters)} 章,开始下载(间隔 {delay}s)...", file=sys.stderr)
    ok = 0
    for i, (url, title) in enumerate(chapters, 1):
        fn = os.path.join(chap_dir, f"{i:04d}_{re.sub(r'[\\\\/:*?\"<>|]', '_', title)[:40]}.txt")
        if os.path.exists(fn) and os.path.getsize(fn) > 0:
            ok += 1
            continue  # 断点续传
        try:
            html = http_get(url, enc)
            text = extract_content(html, cfg["content_selector"])
        except (urllib.error.URLError, OSError, ValueError) as e:
            print(f"  [{i}/{len(chapters)}] 失败: {title}: {e}", file=sys.stderr)
            time.sleep(delay)
            continue
        if not text:
            print(f"  [{i}/{len(chapters)}] 正文为空: {title}", file=sys.stderr)
            time.sleep(delay)
            continue
        with open(fn, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n{text}\n")
        ok += 1
        if i % 20 == 0:
            print(f"  进度 {i}/{len(chapters)}", file=sys.stderr)
        time.sleep(delay)

    # 合并全本
    merged = os.path.join(book_dir, f"{safe_name}.txt")
    files = sorted(f for f in os.listdir(chap_dir) if f.endswith(".txt"))
    with open(merged, "w", encoding="utf-8") as out:
        out.write(f"{args.name}\n\n")
        for fn in files:
            with open(os.path.join(chap_dir, fn), encoding="utf-8") as f:
                out.write(f.read().strip() + "\n\n")

    meta = {
        "name": args.name,
        "book_id": args.book_id,
        "source": cfg.get("name", "unknown"),
        "chapters_total": len(chapters),
        "chapters_ok": ok,
        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(os.path.join(book_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"完成: {ok}/{len(chapters)} 章 -> {merged}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
