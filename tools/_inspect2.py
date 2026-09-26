import os, io, re

VAULT = r"D:\新建文件夹\写作库\写作库_Obsidian"
OUT = r"D:\新建文件夹\写作库\blog\tools\_inspect_tail.txt"
lines = []
def w(s=""):
    lines.append(str(s))

def read(p):
    with io.open(p, "r", encoding="utf-8-sig") as f:
        return f.read()

def tail(path, n=45, label=""):
    w("=" * 70)
    w("### " + label + " :: " + os.path.relpath(path, VAULT))
    w("=" * 70)
    t = read(path).split("\n")
    for i, ln in enumerate(t[-n:]):
        w("%4d| %s" % (len(t) - n + i + 1, ln))
    w()

tail(os.path.join(VAULT, r"01_日月循环宇宙\01.1_主线正文\日月循环补充.md"), 50, "正文尾部")

# 一个实体笔记
ent_dir = os.path.join(VAULT, r"00_索引\实体")
ents = [f for f in os.listdir(ent_dir) if f.endswith(".md")]
w("实体笔记数量: %d" % len(ents))
tail(os.path.join(ent_dir, ents[0]), 40, "实体笔记")

# 一个索引笔记
idx_dir = os.path.join(VAULT, "00_索引")
idx = [f for f in os.listdir(idx_dir) if f.endswith(".md")]
w("索引笔记: " + ", ".join(idx))
if idx:
    tail(os.path.join(idx_dir, idx[0]), 45, "索引笔记")

tail(os.path.join(VAULT, "Home.md"), 40, "Home")

# 检查所有正文的尾部模式
print_pat = 0
for root, dirs, files in os.walk(VAULT):
    dirs[:] = [d for d in dirs if d != ".obsidian"]
    for fn in files:
        if not fn.endswith(".md"):
            continue
        p = os.path.join(root, fn)
        t = read(p)
        if "回到" in t or "相关文字" in t or "世界元素" in t:
            print_pat += 1
w("含「回到/相关文字/世界元素」导航区的文件数: %d" % print_pat)

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("OK")