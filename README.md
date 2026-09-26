# 写作库

一个纯静态的个人写作博客。所有文字以 Markdown 存放在 `content/`，推送后由 GitHub Actions 自动编译并发布到 GitHub Pages。

**网址**：https://huangpingsheng.github.io/writing-library/

---

## 改一篇文章（最常用）

### 电脑上

1. 打开 https://github.com/huangpingsheng/writing-library/tree/main/content
2. 一层层点进类目 / 子类文件夹，找到那篇 `.md`
3. 点右上角铅笔图标 ✎
4. 改文字 → 拉到底部点 **Commit changes**

### 手机上

1. 用手机浏览器打开博客，进入那篇文章
2. 点标题下面的 **✎ 编辑这篇**（会直接跳到 GitHub 的编辑页）
3. 改完点 **Commit changes**

改完后大约 1 分钟，网站自动更新。不用你装任何东西。

---

## 新增一篇

1. 打开 https://github.com/huangpingsheng/writing-library/new/main/content
2. 文件名填 `篇名.md`
3. 内容复制 `content/_模板.md` 里的样子，改掉开头的几行
4. **Commit changes**

文件放在哪个文件夹都行，网站上的归类是按文件开头的 `category` / `subcategory` 认的，不是按文件夹。

### 开头这几行是什么

文件最上面夹在两条 `---` 之间的部分叫 frontmatter，它决定这篇在网站上怎么显示：

| 字段 | 作用 | 不写会怎样 |
|---|---|---|
| `title` | 篇名 | 用文件名 |
| `category` | 大类目 | 进「未分类」 |
| `subcategory` | 子类 | 进「未分类」 |
| `type` | 体裁（散文 / 诗歌 / 设定…） | 显示「笔记」 |
| `tone` | 情绪（冷静 / 痛苦 / 温柔…） | 显示「未标注」 |
| `tags` | 标签，会显示成小圆片 | 无 |
| `summary` | 一句话摘要 | 自动取正文开头 |
| `quote` | 金句，单独高亮一行 | 不显示 |
| `entities` | 世界元素，可点击横向串联 | 从文末「## 世界元素」取 |

**这些都可以不写**，写了更好看。字数是脚本自动数的，不用自己填。

---

## 换主题

网站右上角 **主题** 按钮里有 5 套配色：

- **暖纸**（默认，米白 + 赭红）
- **墨夜**（深色）
- **青瓷**（冷绿灰）
- **报刊**（黑白高对比，衬线字体）
- **午夜蓝**（深蓝）

选择会记在浏览器里。想加新的一套，或者调整某一套的配色，跟 TRAE 说一声就行——配色全部是 `site/index.html` 顶部的一段 CSS 变量，改十几个色值就能换一套。

---

## 本地预览

需要装过 Python 3。

```
python tools/build.py
```

然后打开 `dist/index.html` 就能看。产物在 `dist/`，不会进仓库。

---

## 仓库结构

```
content/                  ← 你的文章，平时只改这里
├── _模板.md              新建文章时复制它
├── 01_日月循环宇宙/
│   └── 01.1_主线正文/
│       └── 日月循环补充.md
└── ...（12 个类目，48 个子类）

site/index.html           ← 网站界面（配色、布局都在这）
tools/build.py            ← 编译器：content/ → dist/
tools/categories.json     ← 类目名称、顺序、描述，以及站点配置
.github/workflows/deploy.yml   ← 自动发布流程
dist/                     ← 构建产物，自动生成，已忽略
```

## 站点配置

`tools/categories.json` 里的 `site` 段：

```json
"site": {
  "title": "写作库",
  "repo": "huangpingsheng/writing-library",
  "branch": "main",
  "content_dir": "content"
}
```

`repo` 决定文章页那个「✎ 编辑这篇」按钮跳到哪。改了仓库名记得同步改这里。

同一个文件里的 `categories` 段控制类目的显示名、顺序和首页上的一句话描述。新增类目时在这里加一条，`order` 决定它排第几。

---

## 自动发布是怎么走的

```
你在 GitHub 上改了一个 .md
        ↓
GitHub Actions 收到推送（.github/workflows/deploy.yml）
        ↓
跑 python tools/build.py，把所有 md 编译成 dist/data.js
        ↓
发布到 GitHub Pages
```

发布状态可以在这里看：https://github.com/huangpingsheng/writing-library/actions

如果某次改完网站没更新，多半是构建报错了，去上面那个页面点开最近一次运行看红色那步的日志。