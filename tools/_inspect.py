import os, re, json, io, sys
from collections import Counter, defaultdict

VAULT = r"D:\新建文件夹\写作库\写作库_Obsidian"
OUT = r"D:\新建文件夹\写作库\blog\tools\_inspect_report.txt"

lines = []
def w(s=""):
    lines.append(str(s))

def read(p):
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with io.open(p, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with io.open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def parse_fm(text):
    if not text.startswith("---"):
        return None, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        return None, text
    raw = m.group(1)
    body = text[m.end():]
    data = {}
    cur = None
    for ln in raw.split("\n"):
        if not ln.strip():
            continue
        if re.match(r"^\s*-\s", ln) and cur:
            data.setdefault(cur, [])
            if isinstance(data[cur], list):
                data[cur].append(ln.strip()[1:].strip().strip('"').strip("'"))
            continue
        mm = re.match(r"^([A-Za-z_\u4e00-\u9fff][^:]*):\s*(.*)$", ln)
        if mm:
            k = mm.group(1).strip()
            v = mm.group(2).strip()
            cur = k
            if v == "":
                data[k] = []
            elif v.startswith("[") and v.endswith("]"):
                inner = v[1:-1].strip()
                data[k] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
            else:
                data[k] = v.strip('"').strip("'")
    return data, body

md_files = []
for root, dirs, files in os.walk(VAULT):
    dirs[:] = [d for d in dirs if d not in (".obsidian", ".git")]
    for fn in files:
        if fn.lower().endswith(".md"):
            md_files.append(os.path.join(root, fn))

w("md 文件总数: %d" % len(md_files))

no_fm = []
fm_keys = Counter()
empty_body = []
word_counts = []
cat_counter = Counter()
sub_counter = Counter()
tone_counter = Counter()
type_counter = Counter()
missing_fields = defaultdict(int)
sample_shown = 0

for p in md_files:
    rel = os.path.relpath(p, VAULT)
    text = read(p)
    fm, body = parse_fm(text)
    if fm is None:
        no_fm.append(rel)
        continue
    for k in fm:
        fm_keys[k] += 1
    body_stripped = body.strip()
    if not body_stripped:
        empty_body.append(rel)
    word_counts.append(len(re.sub(r"\s", "", body_stripped)))
    cat_counter[str(fm.get("category", "<无>"))] += 1
    sub_counter[str(fm.get("subcategory", "<无>"))] += 1
    tone_counter[str(fm.get("tone", "<无>"))] += 1
    type_counter[str(fm.get("type", "<无>"))] += 1
    for req in ("title", "category", "subcategory", "type", "tone", "words", "tags", "summary", "quote", "entities"):
        if req not in fm or fm.get(req) in ("", [], None):
            missing_fields[req] += 1

w("无 frontmatter 的文件数: %d" % len(no_fm))
for x in no_fm[:40]:
    w("   " + x)
w()
w("frontmatter 字段出现次数:")
for k, v in fm_keys.most_common():
    w("   %-20s %d" % (k, v))
w()
w("缺失字段统计:")
for k, v in sorted(missing_fields.items(), key=lambda x: -x[1]):
    w("   %-20s 缺 %d" % (k, v))
w()
w("空正文文件数: %d" % len(empty_body))
for x in empty_body[:20]:
    w("   " + x)
w()
w("category 分布:")
for k, v in cat_counter.most_common():
    w("   %-40s %d" % (k, v))
w()
w("subcategory 数量: %d" % len(sub_counter))
for k, v in sub_counter.most_common(60):
    w("   %-40s %d" % (k, v))
w()
w("tone 分布:")
for k, v in tone_counter.most_common():
    w("   %-20s %d" % (k, v))
w()
w("type 分布:")
for k, v in type_counter.most_common():
    w("   %-20s %d" % (k, v))
w()
if word_counts:
    w("字数: min=%d max=%d avg=%d total=%d" % (min(word_counts), max(word_counts), sum(word_counts)//len(word_counts), sum(word_counts)))
w()
w("=== 目录树（一级/二级）===")
for d in sorted(os.listdir(VAULT)):
    fp = os.path.join(VAULT, d)
    if os.path.isdir(fp) and d != ".obsidian":
        subs = [x for x in sorted(os.listdir(fp)) if os.path.isdir(os.path.join(fp, x))]
        w("%s/  (%d 个子目录)" % (d, len(subs)))
        for s in subs:
            n = len([f for f in os.listdir(os.path.join(fp, s)) if f.lower().endswith(".md")])
            w("    %s/  %d 篇" % (s, n))

w()
w("=== 样本：一篇 md 的原始内容（前 60 行）===")
sample = None
for p in md_files:
    if os.path.basename(p) == "日月循环补充.md":
        sample = p
        break
if sample is None and md_files:
    sample = md_files[0]
if sample:
    w("path: " + sample)
    w("-" * 60)
    for i, ln in enumerate(read(sample).split("\n")[:60]):
        w("%3d| %s" % (i + 1, ln))

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("OK ->", OUT)