# 通用项目启动包设计文档

## 1. 背景与目标

本项目的目标是建立一套适合个人工作方式的通用项目启动包。每当开启一个新项目时，可以把这套模板复制到项目文件夹中，让 Agent 自动完成项目目标澄清、资料整理、知识库建设、日志记录、输出管理，以及后续的技能和 Agent 行为优化。

这套系统的核心不是一次性生成文档，而是建立一个能持续演化的工作环境：

- 项目资料可以被系统化吸收。
- 对话中的重要判断可以沉淀。
- Agent 可以在后续会话中快速恢复上下文。
- 工作日志可以用于复盘和优化。
- 技能和 Agent 规则可以根据实际使用不断改进。

## 2. 需求整理

根据讨论，项目启动包需要支持以下能力。

### 2.1 自动询问项目目标

启动新项目时，Agent 应先询问并整理项目目标，而不是直接进入执行。需要确认的信息包括：

- 项目要达成什么结果
- 成功标准是什么
- 目标用户或目标读者是谁
- 已有资料在哪里
- 项目的范围和边界
- 时间、工具、格式、保密等限制
- 用户希望 Agent 的主动程度
- 哪些事情必须先确认，哪些可以由 Agent 自主判断

这些信息应写入 `memory/project-brief.md`、`memory/goals.md` 和 `memory/open-questions.md`。

### 2.2 建立 Markdown 文件库

每个项目需要一个本地 Markdown 文件库，用来保存项目状态、长期知识、工作过程和交付成果。它不只是文档目录，而是 Agent 的项目记忆系统。

文件库需要区分：

- 原始资料
- 项目记忆
- LLM Wiki
- 输出成果
- 项目技能

### 2.3 建立 LLM Wiki 作为项目知识库

LLM Wiki 应作为项目的长期知识层，用来保存被整理、交叉引用和持续更新的知识。它不是简单的资料摘要，也不是临时 RAG 检索结果。

参考 Karpathy 关于 LLM Wiki 的思路，Wiki 应该是一个 persistent, compounding artifact，也就是一个持续存在并不断积累价值的知识制品。

参考来源：

- [Karpathy: LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

### 2.4 分析用户提供的资料

当用户提供文件、链接、会议记录、说明文档、聊天记录或其他资料时，Agent 需要执行资料摄取流程：

- 识别资料类型
- 提取关键事实
- 总结主要内容
- 识别实体、概念、流程、决策和问题
- 更新相关 Wiki 页面
- 建立来源索引
- 标记冲突和不确定信息
- 把长期有效的信息写入 Wiki
- 把过程信息写入日志

### 2.5 完善 Agent 描述、技能和上下文

系统需要能根据项目资料和用户偏好，生成或更新本项目的 Agent 工作方式，包括：

- Agent 在本项目中的角色
- Agent 应遵守的工作流程
- 每次启动时应读取哪些上下文
- 应优先使用哪些技能
- 哪些用户偏好需要长期记住
- 哪些输出格式需要保持一致

这些内容应沉淀到 `AGENTS.md`、`memory/user-preferences.md` 和相关技能中。

### 2.6 记录日志

每次重要工作后，Agent 应记录日志。日志用于后续复盘、优化和上下文恢复。

日志应记录：

- 本次目标
- 做了什么
- 修改或生成了哪些文件
- 关键判断
- 重要决策
- 用户纠正或偏好
- 遇到的问题
- 下一步建议

日志可分为两类：

- `memory/worklog/`：工作过程日志
- `wiki/log.md`：Wiki 演化日志

### 2.7 根据日志和对话自动优化

系统需要形成闭环。Agent 应定期根据日志和对话总结，优化：

- `AGENTS.md`
- 项目技能
- Wiki 结构
- 用户偏好
- 上下文读取规则
- 常用输出模板

优化不应默认直接覆盖核心规则。建议先生成优化提案，由用户确认后再写入正式文件。

## 3. 核心设计原则

### 3.1 区分输入、记忆、知识和输出

项目文件库应明确区分不同类型的信息：

```text
raw/     = 原始输入资料
memory/  = 项目状态、偏好、决策和过程记忆
wiki/    = 编译后的长期知识
output/  = 可交付成果
skills/  = 可复用工作方法
```

这样可以避免所有内容混在一起，降低未来 Agent 恢复上下文的成本。

### 3.2 Wiki 不是资料仓库，而是编译后的知识层

原始资料应放在 `raw/`。Wiki 中保存的是 Agent 消化后的知识，包括实体、概念、流程、综合分析、冲突记录和来源映射。

每加入一份资料，Agent 不应只生成一篇摘要，而应把这份资料融入已有 Wiki。

### 3.3 对话中的高价值内容要写回 Wiki

用户和 Agent 的对话可能产生长期有用的信息。例如：

- 一个重要判断
- 一个项目策略
- 一个反复使用的分析框架
- 一份对比表
- 一个经过确认的偏好

这些内容不应只留在聊天记录中。Agent 应判断它们属于 `memory/`、`wiki/` 还是 `output/`。

### 3.4 输出成果必须独立管理

`wiki/` 是知识库，`output/` 才是交付物目录。报告、方案、规格说明、提示词、导出文件、上下文包等都应放入 `output/`。

这可以让项目中的“内部知识”和“对外成果”保持分离。

## 4. 推荐目录结构

```text
project/
  AGENTS.md
  README.md

  raw/
    sources/
    assets/

  memory/
    project-brief.md
    goals.md
    user-preferences.md
    open-questions.md
    decisions.md
    worklog/

  wiki/
    index.md
    log.md
    overview.md
    source-map.md
    sources/
    entities/
    concepts/
    workflows/
    syntheses/
    comparisons/
    queries/
    contradictions/
    stale/

  output/
    index.md
    drafts/
    reports/
    specs/
    prompts/
    context-packs/
    exports/
    releases/

  skills/
    project-intake/
    markdown-vault/
    source-ingestion/
    wiki-maintainer/
    wiki-query/
    wiki-lint/
    output-builder/
    agent-optimizer/
```

## 5. 各目录职责

### 5.1 `raw/`

保存原始资料，原则上只读。

适合存放：

- 用户提供的原始文档
- 下载的网页或文章
- 会议记录原文
- 数据文件
- 图片、截图、素材
- 外部系统导出的文件

Agent 不应随意改写 `raw/` 中的内容。若需要清洗或转写，应把结果放到 `wiki/sources/` 或 `work/`。

### 5.2 `memory/`

保存项目状态和过程记忆。

建议文件：

- `project-brief.md`：项目背景和目标
- `goals.md`：目标、成功标准和阶段目标
- `user-preferences.md`：用户偏好、工作习惯和输出要求
- `open-questions.md`：待确认问题
- `decisions.md`：已确认的重要决策
- `worklog/`：按日期或任务记录工作日志

### 5.3 `wiki/`

保存 LLM 编译后的长期知识。

建议文件和目录：

- `index.md`：Wiki 导航地图
- `log.md`：Wiki 演化日志
- `overview.md`：项目总体知识概览
- `source-map.md`：来源到 Wiki 页面的映射
- `sources/`：每份资料的消化结果
- `entities/`：人物、组织、产品、系统、模块等实体
- `concepts/`：概念、术语、原则、框架
- `workflows/`：流程、操作方法、业务链路
- `syntheses/`：综合分析
- `comparisons/`：对比和评估
- `queries/`：高价值问答和分析沉淀
- `contradictions/`：冲突、矛盾和不确定信息
- `stale/`：疑似过时内容

### 5.4 `output/`

保存交付物。

建议文件和目录：

- `index.md`：输出成果索引
- `drafts/`：草稿
- `reports/`：报告
- `specs/`：规格说明
- `prompts/`：可复用提示词
- `context-packs/`：给 Agent 或其他工具使用的上下文包
- `exports/`：对外导出文件
- `releases/`：正式版本或里程碑交付

### 5.5 `skills/`

保存项目初始化和维护技能。技能应尽量短小、明确、可复用。

## 6. 初始化技能设计

### 6.1 `project-intake`

用途：项目启动时询问目标、范围、成功标准和限制。

职责：

- 询问项目目标
- 提取用户偏好
- 识别项目边界
- 生成 `memory/project-brief.md`
- 生成或更新 `memory/goals.md`
- 记录待确认问题

### 6.2 `markdown-vault`

用途：创建标准 Markdown 文件库。

职责：

- 建立目录结构
- 创建基础 Markdown 文件
- 初始化 `wiki/index.md`
- 初始化 `output/index.md`
- 初始化日志文件

### 6.3 `source-ingestion`

用途：分析用户提供的资料并写入 Wiki。

职责：

- 扫描 `raw/sources/`
- 为每份资料建立 source summary
- 提取实体、概念、流程和决策
- 更新相关 Wiki 页面
- 建立来源映射
- 标记冲突和不确定信息
- 写入 `wiki/log.md`

### 6.4 `wiki-maintainer`

用途：维护 Wiki 的结构和内容质量。

职责：

- 更新目录索引
- 补充交叉链接
- 合并重复页面
- 拆分过长页面
- 保持页面格式一致
- 将对话中的长期知识写回 Wiki

### 6.5 `wiki-query`

用途：基于 Wiki 回答问题，并把高价值回答写回 Wiki。

职责：

- 先读 `wiki/index.md`
- 再读取相关页面
- 回答用户问题
- 判断答案是否具有长期价值
- 必要时写入 `wiki/queries/` 或相关概念页

### 6.6 `wiki-lint`

用途：检查 Wiki 健康状态。

职责：

- 找出孤立页面
- 找出重复概念
- 找出缺少来源的结论
- 找出矛盾信息
- 找出疑似过时内容
- 找出缺失页面
- 生成 Wiki 维护建议

### 6.7 `output-builder`

用途：从 Wiki 和 memory 中生成交付物。

职责：

- 生成报告、方案、规格说明、提示词和上下文包
- 区分草稿和正式输出
- 更新 `output/index.md`
- 记录输出依赖的来源和 Wiki 页面

### 6.8 `agent-optimizer`

用途：根据日志、对话和用户纠正优化 Agent。

职责：

- 分析 `memory/worklog/`
- 分析 `wiki/log.md`
- 识别重复出现的用户偏好
- 发现 Agent 容易误解的地方
- 提出 `AGENTS.md` 修改建议
- 提出技能新增或调整建议
- 经用户确认后更新规则

## 7. `AGENTS.md` 应包含的核心规则

`AGENTS.md` 是给 Agent 看的项目操作协议。建议包含以下规则。

### 7.1 启动规则

每次开始工作时，Agent 应优先读取：

1. `memory/project-brief.md`
2. `memory/goals.md`
3. `memory/user-preferences.md`
4. `memory/open-questions.md`
5. `wiki/index.md`
6. `output/index.md`

如果这些文件不存在，应运行初始化流程。

### 7.2 资料处理规则

当发现新资料时：

1. 原始资料放入 `raw/sources/`
2. 不直接改写原始资料
3. 使用 `source-ingestion` 分析资料
4. 更新 `wiki/sources/`
5. 将长期知识整合进相关 Wiki 页面
6. 更新 `wiki/source-map.md`
7. 写入 `wiki/log.md`

### 7.3 Wiki 更新规则

以下内容应写入 Wiki：

- 长期有效的事实
- 被确认的概念定义
- 项目流程
- 系统结构
- 重要分析
- 关键决策的知识背景
- 有复用价值的问题和答案

以下内容不应直接写入 Wiki：

- 临时想法
- 未确认猜测
- 一次性执行细节
- 中间草稿
- 未经处理的原始资料

### 7.4 日志规则

每次重要工作后，Agent 应更新日志。

工作过程写入：

```text
memory/worklog/YYYY-MM-DD.md
```

Wiki 演化写入：

```text
wiki/log.md
```

输出成果写入：

```text
output/index.md
```

### 7.5 输出规则

任何交付物都应放入 `output/`，而不是放在 `wiki/` 或 `memory/` 中。

输出文件应尽量包含：

- 标题
- 日期
- 版本
- 用途
- 来源
- 依赖的 Wiki 页面
- 状态：草稿、待确认、正式、已导出

### 7.6 优化规则

当出现以下情况时，应运行 `agent-optimizer`：

- 用户多次纠正同类问题
- 同一类任务重复出现
- Wiki 结构变得混乱
- 日志显示某个流程低效
- 项目进入新阶段
- 用户要求优化 Agent 或技能

优化核心规则前，应先生成建议并让用户确认。

## 8. `README.md` 应包含的内容

`README.md` 是给人看的项目说明。建议包含：

- 这个项目是什么
- 如何启动
- 目录结构说明
- 如何添加资料
- 如何查看 Wiki
- 如何查看输出
- 如何让 Agent 更新知识库
- 如何让 Agent 优化技能
- 常用指令示例

示例指令：

```text
请根据 raw/sources 里的新资料更新 LLM Wiki。
请读取项目记忆，告诉我当前项目状态。
请基于 wiki 生成一份报告，放到 output/reports。
请检查 Wiki 是否有过时、重复或矛盾内容。
请根据最近的日志优化 AGENTS.md 和技能。
```

## 9. LLM Wiki 工作流

### 9.1 Ingest 工作流

当加入新资料时：

1. 将资料放入 `raw/sources/`
2. Agent 读取资料
3. 在 `wiki/sources/` 生成资料摘要
4. 更新相关实体页
5. 更新相关概念页
6. 更新相关流程页
7. 更新综合分析页
8. 更新 `wiki/source-map.md`
9. 如有冲突，写入 `wiki/contradictions/`
10. 更新 `wiki/index.md`
11. 写入 `wiki/log.md`

### 9.2 Query 工作流

当用户提问时：

1. 读取 `wiki/index.md`
2. 定位相关页面
3. 读取必要上下文
4. 回答问题
5. 判断答案是否值得沉淀
6. 如有长期价值，写入 `wiki/queries/` 或相关页面
7. 必要时更新日志

### 9.3 Lint 工作流

定期执行：

1. 检查孤立页面
2. 检查重复页面
3. 检查缺少来源的结论
4. 检查冲突信息
5. 检查过时内容
6. 检查索引是否完整
7. 输出维护建议

### 9.4 Output 工作流

当需要交付成果时：

1. 明确交付物用途
2. 读取相关 memory 和 wiki 页面
3. 生成草稿到 `output/drafts/`
4. 用户确认后进入正式目录
5. 更新 `output/index.md`
6. 记录来源和版本

## 10. 建议的第一版实施顺序

第一阶段：建立骨架

- 创建目录结构
- 创建 `AGENTS.md`
- 创建 `README.md`
- 创建 `memory/` 基础文件
- 创建 `wiki/index.md`、`wiki/log.md`、`wiki/source-map.md`
- 创建 `output/index.md`

第二阶段：建立初始化技能

- `project-intake`
- `markdown-vault`
- `source-ingestion`
- `wiki-maintainer`

第三阶段：建立闭环能力

- `wiki-query`
- `wiki-lint`
- `output-builder`
- `agent-optimizer`

第四阶段：实际项目试运行

- 用一个真实项目测试
- 导入少量资料
- 观察 Agent 是否能正确更新 Wiki
- 观察日志是否有复盘价值
- 根据问题优化 `AGENTS.md` 和技能

## 11. 待确认问题

后续进入落地阶段前，建议确认：

- 这套模板主要用于代码项目、研究项目、产品项目，还是全部通用？
- 是否需要同时支持中文和英文？
- `raw/` 中是否会包含隐私或敏感资料？
- 输出成果是否需要固定格式，例如报告、PRD、周报、会议纪要？
- Agent 优化是否默认只生成建议，还是允许自动修改？
- 是否需要脚本一键初始化新项目？
- 是否需要把这套模板做成 Codex Skill？

## 12. 一句话总结

这套系统的目标是把新项目从“一次聊天”升级为“可持续维护的知识工作环境”：原始资料进入 `raw/`，项目状态沉淀在 `memory/`，长期知识编译到 `wiki/`，交付成果放入 `output/`，技能和 `AGENTS.md` 让 Agent 在每个新项目中越来越贴合你的工作方式。
