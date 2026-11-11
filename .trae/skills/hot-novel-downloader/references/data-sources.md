# 数据源参考(2026-11-11 沙箱实测)

## 番茄小说(直连可用)

### 榜单页 `https://fanqienovel.com/rank`
- 普通 UA 直连返回 200,SSR HTML。
- `window.__INITIAL_STATE__={...}` 内嵌 JSON,含每本书:
  `bookId`、`bookName`(**可能被字体混淆**)、`author`(可能混淆)、`read_count`(数字,可信)。
- 提取方式:按花括号配平截取 JSON,递归找含 `bookId`+`bookName` 的字典。
- 分类榜单页结构相同,URL 形如 `/rank/<type>_<gender>_<category>`。

### 字体混淆(重要)
- 榜单列表文字使用自定义 woff 字体,部分汉字被替换为 PUA 私用区字符
  (U+E000–U+F8FF),如 `惹\ue49c枝`。
- **解决办法**:访问详情页 `https://fanqienovel.com/page/<bookId>`,
  其 `<title>` 为干净文本,格式:
  `<书名>完整版在线免费阅读_<书名>小说_番茄小说官网`
- `read_count` 等数字字段不受混淆影响。

## 起点中文网(直连被拦,用浏览器)

- `https://www.qidian.com/rank/hotsales/` 等榜单直连返回 **202**(反爬验证页)。
- 处理:用浏览器技能打开榜单页,等验证通过后读取书籍列表
  (`.book-mid-info h2 a` 为书名,`.author .name` 为作者)。
- 常用榜单:`/rank/hotsales/`(热销)、`/rank/yuepiao/`(月票)、
  `/rank/readIndex/`(阅读指数)、`/rank/recom/`(推荐票)。

## 百度贴吧(直连被拦,用浏览器)

- 吧页 `https://tieba.baidu.com/f?kw=<书名>` 直连返回 **403**;
  站内搜索 `/f/search/res` 连接被重置;百度搜索同样拦截数据中心 IP。
- 处理:用浏览器技能打开吧页,读取页面顶部"关注:xxx / 帖子:xxx"。
- 判定:关注 ≥10000 → high;关注 ≥1000 且帖子 ≥5000 → mid;吧不存在 → none。
- 浏览器读取结果用 `check_tieba_heat.py --browser-fill` 回填,格式:
  `{"书名": {"followers": 12345, "posts": 67890}}`

## 浏览器操作要点

1. 打开目标 URL → 等待页面加载;
2. 起点若出现滑块/验证,请用户协助完成(`browser_waiting_for_user_interaction`);
3. 读取榜单或吧页数据后回填脚本,不要在脚本里硬编码绕过验证码的逻辑。
