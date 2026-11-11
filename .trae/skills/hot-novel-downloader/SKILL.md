---
name: "hot-novel-downloader"
description: "发现并下载高热度中文网文:聚合番茄/起点真实榜单,用百度贴吧讨论度交叉验证热度后下载。当用户要求找热门网文、下载小说、追榜单作品、批量整理小说时使用。"
---

# Hot Novel Downloader(热门网文下载器)

自动完成「榜单发现 → 热度验证 → 下载」三步流水线,确保下载的小说是**真实存在且热度可信**的作品。

## 热度判定标准(硬性门槛)

一部小说必须**同时满足**以下两条才算"热度高",缺一不可:

1. **在榜**:出现在番茄小说排行榜(fanqienovel.com/rank)或起点中文网榜单(qidian.com/rank)上;
2. **有讨论度**:百度贴吧存在该书的同名吧,且满足以下任一条件:
   - 吧关注数 ≥ 10000(默认阈值,可用 `--min-followers` 调整);
   - 吧关注数 ≥ 1000 且帖子数 ≥ 5000。

两项数据都必须来自**实际抓取到的页面**,禁止凭模型记忆编造书名、榜单排名或贴吧数据。

## 数据源可达性(2026-11 实测)

| 数据源 | 直连 HTTP | 说明 |
|---|---|---|
| 番茄榜单 `/rank` | ✅ 200 | SSR 页面,`window.__INITIAL_STATE__` 含 bookId/作者/在读数;**列表文字被自定义字体混淆(PUA 字符)**,需访问详情页取真实书名 |
| 番茄详情页 `/page/<bookId>` | ✅ 200 | `<title>` 是**未混淆**的干净书名 |
| 起点榜单 | ⚠️ 202 | 反爬验证,**必须改用浏览器**(见下) |
| 百度贴吧 | ❌ 403 | 数据中心 IP 被拦,**必须改用浏览器** |

被拦截时,使用浏览器类技能(如 TRAE-browseruse)打开对应页面人工/自动读取,详见 [references/data-sources.md](references/data-sources.md)。

## 工作流程

### 第 1 步:采集榜单

```bash
python3 .trae/skills/hot-novel-downloader/scripts/fetch_fanqie_rank.py \
    --top 20 --out /tmp/rank_fanqie.json
```

- 脚本抓取番茄总榜,从 `__INITIAL_STATE__` 提取 bookId/作者/在读数,再逐个访问详情页把混淆书名还原为真实书名。
- 起点榜单:用浏览器打开 `https://www.qidian.com/rank/hotsales/`(或月票榜 `/rank/yuepiao/` 等),提取书名/作者,手工补入 JSON,格式与脚本输出一致。

### 第 2 步:贴吧热度验证

```bash
python3 .trae/skills/hot-novel-downloader/scripts/check_tieba_heat.py \
    --input /tmp/rank_fanqie.json --out /tmp/verified.json
```

- 脚本先尝试直连贴吧;若返回 BLOCKED,按提示用浏览器打开 `https://tieba.baidu.com/f?kw=<书名>`,读取"关注"和"帖子"数量,以 `--browser-fill '<json>'` 回填。
- 输出每本书的 `heat: high/mid/none` 判定;只保留 `high/mid` 的书。

### 第 3 步:确认并下载

先把「在榜 ∩ 贴吧有热度」的候选清单(书名/作者/榜单名次/贴吧数据)展示给用户确认,然后:

```bash
python3 .trae/skills/hot-novel-downloader/scripts/download_novel.py \
    --name "书名" --source-config site.json --i-understand \
    --outdir novels/
```

`site.json` 由使用者提供,描述一个**其有权使用的书源**的章节列表页/章节页 URL 模板与正文 CSS 选择器。脚本不内置任何第三方书源。

## 合规红线(必须遵守)

- 仅用于**个人离线阅读**,禁止批量抓取收费/VIP 章节,禁止二次分发、上传或商用;
- 不得内置、推荐或默认使用盗版聚合站;书源配置必须由用户自行提供并对其合法性负责;
- 遵守目标站 robots 协议与访问频率限制(脚本默认间隔 ≥1.5s);
- 榜单/贴吧数据如实呈现,抓不到就明说,不得虚构。

## 输出结构

```
novels/
├── <书名>/
│   ├── chapters/0001_<章节名>.txt ...
│   ├── <书名>.txt        # 合并全本
│   └── meta.json         # 书名/作者/来源/榜单/贴吧数据/下载时间
└── index.json            # 本次任务全部书籍汇总
```
