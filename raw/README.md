# 原始资料

原则上只读，不直接改写。

```text
raw/
├── sources/     拆书样本、竞品章节、平台规则原文
├── assets/      封面、地图、参考图
└── feedback/    编辑反馈、读者评论截图
```

处理流程：`raw/` → 用 `skills/source-ingestion` 消化 → 写入 `wiki/`。
原文件保留，不覆盖、不删除。
