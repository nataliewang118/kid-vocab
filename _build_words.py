# 把 原始数据/words-yl*.json 合并灌进 index.html 的 WORDS 常量。
# 文件名里的数字就是年级（words-yl3.json -> 3 年级，words-yl5a.json -> 5 年级）。
# 同一个词出现在多个年级时按最早的年级算——三年级的词不该当五年级新词再教一遍。
import json, io, re, pathlib, sys
from collections import Counter

BASE = pathlib.Path(__file__).parent
SRC = BASE / "原始数据"

files = sorted(SRC.glob("words-yl*.json"))
if not files:
    sys.exit("原始数据/ 里没找到 words-yl*.json")

best = {}
for f in files:
    m = re.search(r"words-yl(\d+)", f.stem)
    if not m:
        sys.exit("文件名看不出年级：%s（要长成 words-yl5a.json 这样）" % f.name)
    fallback_grade = int(m.group(1))
    # 每册来源的标记（app 设置页按它开关整册）。显式 book 优先，否则用 term 推（3/4 年级），
    # 再否则用文件名里的字母（words-yl5a.json -> 5A）。旧版补的册自带 book，如 5Bv1。
    m2 = re.search(r"words-yl\d+([a-z])", f.stem)
    file_letter = m2.group(1).upper() if m2 else ""
    for w in json.load(io.open(f, encoding="utf-8")):
        word = (w.get("word") or "").strip()
        cn = (w.get("cn") or "").strip()
        if not word or not cn:
            continue
        key = word.lower()
        grade = int(w.get("grade") or fallback_grade)
        ph = (w.get("phonetic") or "").strip()
        if w.get("term"):
            suf = "A" if int(w["term"]) == 1 else "B"
        else:
            suf = file_letter or "A"
        book = (w.get("book") or "").strip() or (str(grade) + suf)
        old = best.get(key)
        if old:
            if old["grade"] <= grade:
                if not old["phonetic"] and ph:
                    old["phonetic"] = ph          # 低年级那份没音标，拿高年级的补上
                continue
        best[key] = {"unit": w.get("unit") or 0, "word": word,
                     "cn": cn, "phonetic": ph, "grade": grade, "book": book}

words = sorted(best.values(), key=lambda w: (w["grade"], w["unit"], w["word"].lower()))
blob = ("var WORDS = " + json.dumps(words, ensure_ascii=False, separators=(",", ":")) +
        ";\nWORDS.forEach(function(w,i){ w.id = 'w'+i; if(!w.grade) w.grade = 5; });")

p = BASE / "index.html"
html = p.read_text(encoding="utf-8")
new, n = re.subn(r"var WORDS = \[.*?\];\s*\nWORDS\.forEach\(function\(w,i\)\{ w\.id = 'w'\+i;[^\n]*\}\);",
                 lambda m: blob, html, count=1, flags=re.S)
if n != 1:
    sys.exit("没找到 WORDS 块，index.html 结构变了")
p.write_text(new, encoding="utf-8")

c = Counter(w["grade"] for w in words)
print("灌入 %d 词：%s" % (len(words), "，".join("%d年级 %d" % (g, c[g]) for g in sorted(c))))
