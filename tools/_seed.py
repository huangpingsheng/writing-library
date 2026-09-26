import os, io, re, json, shutil

OLD_DATA = r"D:\新建文件夹\写作库\网页版\data.js"
VAULT = r"D:\新建文件夹\写作库\写作库_Obsidian"
BLOG = r"D:\新建文件夹\写作库\blog"
CONTENT = os.path.join(BLOG, "content")
TOOLS = os.path.join(BLOG, "tools")

def norm(s):
    """归一化类目名：去掉空格与间隔号，用于跨来源匹配"""
    return re.sub(r"[\s\u3000·・\-—_]+", "", str(s or ""))

# ---------- 1. 从旧 data.js 提取类目元信息 ----------
with io.open(OLD_DATA, "r", encoding="utf-8-sig") as f:
    raw = f.read()
obj, _ = json.JSONDecoder().raw_decode(raw[raw.index("{"):])
LIB = obj

cat_meta = {}
for i, c in enumerate(LIB["cats"]):
    cat_meta[norm(c["name"])] = {
        "key": norm(c["name"]),
        "display": c["name"],
        "icon": c.get("icon", ""),
        "desc": c.get("desc", ""),
        "order": i,
    }

# ---------- 2. 复制正文到 content/ ----------
if os.path.isdir(CONTENT):
    shutil.rmtree(CONTENT)
os.makedirs(CONTENT)

copied, skipped, excluded_dirs = [], [], []
folder_count = {}

for d in sorted(os.listdir(VAULT)):
    src_dir = os.path.join(VAULT, d)
    if not os.path.isdir(src_dir) or d.startswith("."):
        continue
    if not re.match(r"^\d\d_", d):
        continue
    if d.startswith("00_"):          # 00_索引 是 Obsidian 的导航层，不进博客
        excluded_dirs.append(d)
        continue
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        for fn in sorted(files):
            if not fn.lower().endswith(".md"):
                continue
            if fn.startswith("_索引"):
                skipped.append(os.path.relpath(os.path.join(root, fn), VAULT))
                continue
            rel = os.path.relpath(os.path.join(root, fn), VAULT)
            dst = os.path.join(CONTENT, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, fn), dst)
            copied.append(rel)
            folder_count[rel.split(os.sep)[0]] = folder_count.get(rel.split(os.sep)[0], 0) + 1

print("排除目录: " + ", ".join(excluded_dirs))
print("复制正文: %d 篇" % len(copied))
print("跳过类目索引: %d 篇" % len(skipped))
for k in sorted(folder_count):
    print("   %-26s %d" % (k, folder_count[k]))

# ---------- 3. 校验：content 里每个 category 都能匹配到元信息 ----------
def parse_fm_category(text):
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return None
    mm = re.search(r"^category:\s*(.+)$", m.group(1), re.M)
    if not mm:
        return None
    return mm.group(1).strip().strip('"').strip("'")

seen = {}
for rel in copied:
    with io.open(os.path.join(CONTENT, rel), "r", encoding="utf-8-sig") as f:
        t = f.read()
    c = parse_fm_category(t)
    seen[norm(c)] = seen.get(norm(c), 0) + 1

print("\ncontent 中的 category 分布:")
unmatched = []
for k in sorted(seen, key=lambda x: cat_meta.get(x, {}).get("order", 99)):
    meta = cat_meta.get(k)
    flag = "" if meta else "  <<< 无元信息"
    if not meta:
        unmatched.append(k)
    print("   %-24s %3d 篇   显示名=%s%s" % (k, seen[k], meta["display"] if meta else "-", flag))
print("未匹配: %s" % (unmatched if unmatched else "无"))

# ---------- 4. 写出 categories.json ----------
cats_out = {}
for k, v in cat_meta.items():
    if k in seen:
        cats_out[k] = v

out = {
    "site": {
        "title": "写作库",
        "subtitle": "碎片与长文，一字未删",
        "repo": "REPO_PLACEHOLDER",
        "branch": "main",
        "content_dir": "content",
    },
    "categories": cats_out,
    "fallback_category": {
        "key": "__uncat__",
        "display": "未分类",
        "icon": "",
        "desc": "新加的、还没归类的文字。",
        "order": 99,
    },
}
with io.open(os.path.join(TOOLS, "categories.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(out, ensure_ascii=False, indent=2))
print("\ncategories.json 已写出，匹配类目 %d 个" % len(cats_out))