#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
写作库博客 · 构建脚本
把 content/ 里的 Markdown 编译成 dist/data.js（window.LIB），并把 site/index.html 复制过去。

在仓库根目录运行：  python tools/build.py
"""
import os
import io
import re
import sys
import json
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
SITE = os.path.join(ROOT, "site")
DIST = os.path.join(ROOT, "dist")
CONFIG = os.path.join(ROOT, "tools", "categories.json")

COLORS = ["#C0562A", "#8A6FB0", "#C2557F", "#4E7FA6", "#3E8C7E", "#B08428",
          "#7A9A4E", "#A05C9E", "#5F7A8A", "#B5654A", "#6B7FB3", "#8C8579"]

NAV_HEADINGS = ("回到", "相关文字", "世界元素", "相关", "标签")


def read_text(path):
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            with io.open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with io.open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def norm(s):
    return re.sub(r"[\s\u3000·・\-—_]+", "", str(s or ""))


def parse_frontmatter(text):
    """返回 (dict, body)。没有 frontmatter 时返回 ({}, text)。"""
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        return {}, text
    data, cur = {}, None
    for ln in m.group(1).split("\n"):
        if not ln.strip():
            continue
        if re.match(r"^\s*-\s", ln) and cur:
            if not isinstance(data.get(cur), list):
                data[cur] = []
            data[cur].append(ln.strip()[1:].strip().strip('"').strip("'"))
            continue
        mm = re.match(r"^([^:]+):\s*(.*)$", ln)
        if not mm:
            continue
        k = mm.group(1).strip()
        v = mm.group(2).strip()
        cur = k
        if v == "":
            data[k] = []
        elif v.startswith("[") and v.endswith("]"):
            data[k] = [x.strip().strip('"').strip("'")
                       for x in v[1:-1].split(",") if x.strip()]
        else:
            data[k] = v.strip('"').strip("'")
    return data, text[m.end():]


def collect_wikilinks(section_text):
    out = []
    for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", section_text):
        t = m.group(1).strip()
        if t and t not in out:
            out.append(t)
    return out


def split_body(body):
    """把正文拆成 (纯正文, 相关文字链接, 世界元素链接)"""
    lines = body.split("\n")

    # 1) 去掉开头的 callout（> [!abstract] 摘要 / > [!quote] 原文一句）
    i = 0
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith(">")):
        i += 1
    # 2) 去掉紧跟其后的分隔线
    while i < len(lines) and (lines[i].strip() == "" or re.match(r"^-{3,}\s*$", lines[i].strip())):
        i += 1
    rest = lines[i:]

    # 3) 尾部导航区：优先找 "## 回到"，其次 "## 相关文字"、"## 世界元素"
    #    判定条件是该标题之后必须出现双链 [[...]]，避免误伤正文里同名的小标题
    cut = len(rest)
    for target in NAV_HEADINGS[:3]:
        found = None
        for j, ln in enumerate(rest):
            if re.match(r"^##\s*%s\s*$" % target, ln.strip()) and "[[" in "\n".join(rest[j:]):
                found = j
                break
        if found is not None:
            cut = found
            break
    while cut > 0 and (rest[cut - 1].strip() == "" or re.match(r"^-{3,}\s*$", rest[cut - 1].strip())):
        cut -= 1

    main = rest[:cut]
    tail = rest[cut:]

    links, ents = [], []
    tail_text = "\n".join(tail)
    for sec in re.split(r"^##\s+", tail_text, flags=re.M):
        head = sec.split("\n", 1)[0].strip()
        if head.startswith("相关"):
            links = collect_wikilinks(sec)
        elif head.startswith("世界元素"):
            ents = collect_wikilinks(sec)

    text = "\n".join(main).strip()
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text, links, ents


def count_words(text):
    return len(re.sub(r"\s", "", text))


def first_sentence(text, limit=70):
    flat = re.sub(r"\s+", " ", text).strip()
    if not flat:
        return ""
    return flat[:limit] + ("…" if len(flat) > limit else "")


def main():
    if not os.path.isfile(CONFIG):
        sys.exit("找不到 tools/categories.json")
    with io.open(CONFIG, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    site = cfg.get("site", {})
    cat_meta = cfg.get("categories", {})
    fallback = cfg.get("fallback_category", {"key": "__uncat__", "display": "未分类",
                                             "icon": "", "desc": "新加的、还没归类的文字。", "order": 99})

    if not os.path.isdir(CONTENT):
        sys.exit("找不到 content/ 目录")

    # ---------- 扫描 ----------
    buckets = {}      # cat_key -> {sub_id -> {name, order, files[]}}
    stats = {"total": 0, "uncat": 0, "no_fm": 0}

    for root, dirs, files in os.walk(CONTENT):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for fn in sorted(files):
            if not fn.lower().endswith(".md"):
                continue
            if fn.startswith("_"):      # _模板.md 之类不参与发布
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            raw = read_text(full)
            fm, body = parse_frontmatter(raw)
            if not fm:
                stats["no_fm"] += 1

            text, links, tail_ents = split_body(body)

            cat_raw = fm.get("category", "")
            ckey = norm(cat_raw) if cat_raw else fallback["key"]
            if ckey not in cat_meta:
                ckey = fallback["key"]
                stats["uncat"] += 1

            sub_raw = fm.get("subcategory", "") or ""

            # 子类 id / 排序取自所在文件夹（如 01.1_主线正文）
            reldir = os.path.relpath(root, CONTENT).replace("\\", "/")
            parts = [p for p in reldir.split("/") if p and p != "."]
            folder = parts[1] if len(parts) > 1 else ""
            sm = re.match(r"^([\d.]+)_(.+)$", folder)
            if sm:
                sub_id, sub_order = sm.group(1), sm.group(1)
                sub_name = sub_raw or sm.group(2)
            else:
                sub_id, sub_order = "00", "99"
                sub_name = sub_raw or "未分类"

            ents = fm.get("entities") or []
            if isinstance(ents, str):
                ents = [ents] if ents else []
            if not ents:
                ents = tail_ents

            tags = fm.get("tags") or []
            if isinstance(tags, str):
                tags = [tags] if tags else []
            # 去掉 "类目/子类"、"类型/x"、"情绪/x" 这类结构性标签
            tags = [t for t in tags if t.count("/") == 0]

            words_raw = fm.get("words")
            try:
                words_fm = int(str(words_raw).strip()) if words_raw not in (None, "") else 0
            except ValueError:
                words_fm = 0
            words = count_words(text)

            f = {
                "file": fn,
                "path": rel,
                "title": fm.get("title") or os.path.splitext(fn)[0],
                "words": words,
                "wordsDeclared": words_fm,
                "type": fm.get("type") or "笔记",
                "tone": fm.get("tone") or "未标注",
                "summary": fm.get("summary") or first_sentence(text),
                "tags": tags,
                "entities": ents,
                "characters": [],
                "links": links,
                "quote": fm.get("quote") or "",
                "text": text,
                "sub": sub_id,
                "subName": sub_name,
            }

            cat = buckets.setdefault(ckey, {})
            sub = cat.setdefault(sub_id, {"id": sub_id, "name": sub_name,
                                          "order": sub_order, "files": []})
            sub["files"].append(f)
            stats["total"] += 1

    # ---------- 组装 ----------
    def cat_order(k):
        if k == fallback["key"]:
            return 999
        return cat_meta.get(k, {}).get("order", 99)

    cats_out = []
    for ci, ckey in enumerate(sorted(buckets, key=cat_order)):
        meta = cat_meta.get(ckey) or (fallback if ckey == fallback["key"] else
                                      {"display": ckey, "icon": "", "desc": ""})
        subs = []
        for sid in sorted(buckets[ckey], key=lambda s: (buckets[ckey][s]["order"], s)):
            sub = buckets[ckey][sid]
            sub["files"].sort(key=lambda x: (-x["words"], x["title"]))
            subs.append({
                "id": sid,
                "name": sub["name"],
                "files": sub["files"],
            })
        allf = [f for s in subs for f in s["files"]]
        cats_out.append({
            "id": "%02d" % (ci + 1),
            "key": ckey,
            "name": meta["display"],
            "icon": meta.get("icon", ""),
            "desc": meta.get("desc", ""),
            "count": len(allf),
            "words": sum(f["words"] for f in allf),
            "subs": subs,
        })

    lib = {"site": site, "cats": cats_out}

    # ---------- 输出 ----------
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    with io.open(os.path.join(DIST, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.LIB=")
        f.write(json.dumps(lib, ensure_ascii=False, separators=(",", ":")))
        f.write(";\n")

    for name in os.listdir(SITE):
        s = os.path.join(SITE, name)
        d = os.path.join(DIST, name)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

    total_words = sum(c["words"] for c in cats_out)
    print("构建完成")
    print("  篇数     : %d" % stats["total"])
    print("  总字数   : %s" % format(total_words, ","))
    print("  类目     : %d" % len(cats_out))
    print("  子类     : %d" % sum(len(c["subs"]) for c in cats_out))
    if stats["uncat"]:
        print("  未分类   : %d 篇（放在「未分类」里）" % stats["uncat"])
    if stats["no_fm"]:
        print("  无元信息 : %d 篇（已按文件名/正文自动补全）" % stats["no_fm"])
    print("  产物     : dist/data.js + dist/index.html")
    for c in cats_out:
        print("    %-16s %3d 篇  %8s 字" % (c["name"], c["count"], format(c["words"], ",")))


if __name__ == "__main__":
    main()