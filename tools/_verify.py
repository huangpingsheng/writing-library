import io, json, re, os

DIST = r"D:\新建文件夹\写作库\blog\dist\data.js"
OUT = r"D:\新建文件夹\写作库\blog\tools\_verify.txt"
lines = []
def w(s=""):
    lines.append(str(s))

raw = io.open(DIST, "r", encoding="utf-8").read()
LIB = json.loads(raw[raw.index("{"):].rstrip().rstrip(";"))

flat = []
for c in LIB["cats"]:
    for s in c["subs"]:
        for f in s["files"]:
            f["_cat"] = c["name"]
            f["_sub"] = s["name"]
            flat.append(f)

w("篇数: %d" % len(flat))
w("site: %s" % json.dumps(LIB.get("site", {}), ensure_ascii=False))
w()

bad = {"callout": [], "nav": [], "frontmatter": [], "nosub": [], "empty": []}
for f in flat:
    t = f["text"]
    if "[!" in t and re.search(r"\[!\w+\]", t):
        bad["callout"].append(f["title"])
    if re.search(r"^##\s*(回到|相关文字|世界元素)\s*$", t, re.M):
        bad["nav"].append(f["title"])
    if t.lstrip().startswith("---") or re.search(r"^title:\s", t, re.M):
        bad["frontmatter"].append(f["title"])
    if not f.get("sub") or not f.get("subName"):
        bad["nosub"].append(f["title"])
    if not t.strip():
        bad["empty"].append(f["title"])

for k, v in bad.items():
    w("%-12s %d 篇" % (k, len(v)))
    for x in v[:8]:
        w("      " + x)
w()

w("=" * 70)
w("抽样：3 篇的完整字段与正文开头")
w("=" * 70)
for title in ["日月循环补充", "饥饿", "梦"]:
    f = next((x for x in flat if x["title"] == title), None)
    if not f:
        w("未找到 " + title)
        continue
    w("--- %s ---" % f["title"])
    w("  path      : %s" % f["path"])
    w("  cat/sub   : %s / %s (%s)" % (f["_cat"], f["_sub"], f["sub"]))
    w("  words     : %d (声明 %d)" % (f["words"], f["wordsDeclared"]))
    w("  type/tone : %s / %s" % (f["type"], f["tone"]))
    w("  tags      : %s" % ", ".join(f["tags"]))
    w("  entities  : %s" % ", ".join(f["entities"][:10]))
    w("  links     : %s" % ", ".join(f["links"][:6]))
    w("  quote     : %s" % f["quote"][:50])
    w("  正文前 120 字: %s" % re.sub(r"\s+", " ", f["text"])[:120])
    w("  正文末 80 字 : %s" % re.sub(r"\s+", " ", f["text"])[-80:])
    w()

w("=" * 70)
w("最长 / 最短")
w("=" * 70)
srt = sorted(flat, key=lambda x: -x["words"])
for f in srt[:3]:
    w("  长: %-20s %6d 字  %s" % (f["title"], f["words"], f["_cat"]))
for f in srt[-3:]:
    w("  短: %-20s %6d 字  %s" % (f["title"], f["words"], f["_cat"]))

w()
w("=" * 70)
w("子类清单")
w("=" * 70)
for c in LIB["cats"]:
    w("%s  %s  (%d 篇 / %d 字)" % (c["id"], c["name"], c["count"], c["words"]))
    for s in c["subs"]:
        w("    %-8s %-16s %d 篇" % (s["id"], s["name"], len(s["files"])))

io.open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print("OK")