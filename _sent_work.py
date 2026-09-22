# ponytail: 句子关的例句工作台。作家写在 原始数据/sentences.txt（一行一句，别的手改），
#   这个脚本只是拿它跟词表对账：python _sent_work.py list / check
import json, io, re, sys, pathlib
from collections import Counter

BASE = pathlib.Path(__file__).parent
SRC = BASE / "原始数据"
TXT = SRC / "sentences.txt"
ALL = SRC / "sentences_all.txt"      # 额外的人名白名单之外的自造词放这儿（一般不用）

# ---- 词表合并（跟 _build_words.py 同一套口径，别改歪了） ----
best = {}
for f in sorted(SRC.glob("words-yl*.json")):
    fg = int(re.search(r"yl(\d+)", f.stem).group(1))
    for w in json.load(io.open(f, encoding="utf-8")):
        word = (w.get("word") or "").strip()
        cn = (w.get("cn") or "").strip()
        if not word or not cn:
            continue
        k, g = word.lower(), int(w.get("grade") or fg)
        o = best.get(k)
        if o and o["grade"] <= g:
            continue
        best[k] = {"word": word, "cn": cn, "grade": g, "unit": w.get("unit") or 0}
WORDS = sorted(best.values(), key=lambda w: (w["grade"], w["unit"], w["word"].lower()))

def kind(w):
    s = w["word"]
    if re.search(r"[.!?。！？]$", s) or s.count(" ") >= 3:
        return "整句"
    return "词组" if " " in s else "单词"

# 纯功能词：虚词做填空没意义。**半虚词（have/go/look/take/may/it）一律留下**，它们有实义、能考。
FUNC = set("""a an the and or but if because in on at of to for with from by as
is am are was were be been do does did have has had
can could may might must shall should will would
my your his her its our their mine yours this that these those
i you he she it we they me him us them
not no yes here there where when what who how why which
too very also up down out off over under again then than
""".split())

TARGETS = [w for w in WORDS if kind(w) in ("单词", "词组") and w["word"].lower() not in FUNC]

# ---- 不超纲：词表内的词 + 常见屈折 + 白名单 ----
ALLOW = {p.lower() for w in WORDS for p in re.split(r"[\s/]+", w["word"])}
ALLOW |= {w["word"].lower().rstrip(".!?") for w in WORDS}
# 连字符词（ping-pong）拆开也算认识——课本上就是这么念的
ALLOW |= {p.lower() for w in WORDS for p in w["word"].split("-")}
WHITE = set("""tom amy ben anna lily mike jack lucy sam emma green brown
li wang zhang liu chen yang zhao huang zhou wu xu sun ma zhu hu guo lin he gao luo

one two three four five six seven eight nine ten eleven twelve
twenty thirty forty fifty sixty seventy eighty ninety hundred
ok okay oh ah ha wow hey hmm
i'm it's that's don't can't isn't let's there's
weekend nd""".split())
ALLOW |= WHITE
if ALL.exists():
    ALLOW |= {l.strip().lower() for l in io.open(ALL, encoding="utf-8") if l.strip()}
IRREG = {"children": "child", "feet": "foot", "men": "man", "women": "woman",
         "teeth": "tooth", "mice": "mouse", "went": "go", "gone": "go",
         "saw": "see", "seen": "see", "ate": "eat", "eaten": "eat",
         "ran": "run", "came": "come", "got": "get", "made": "make",
         "took": "take", "taken": "take", "wrote": "write", "drew": "draw",
         "found": "find", "gave": "give", "told": "tell", "said": "say",
         "better": "good", "best": "good", "worse": "bad", "worst": "bad",
         "sat": "sit", "put": "put", "read": "read", "flew": "fly"}

def known(tok):
    t = tok.lower()
    if t in ALLOW or t in IRREG:
        return True
    for suf, rep in (("ies", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"),
                     ("ing", ""), ("ing", "e"), ("d", ""), ("er", ""), ("est", ""),
                     ("er", "e"), ("ly", ""), ("n't", "")):
        if t.endswith(suf) and t[: -len(suf)] + rep in ALLOW:
            return True
    return False

def toks(s):
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", s)

# 词表里有两条是课本的占位写法：「show ... around」「put...in order」。
# 「...」是省略的宾语（show me around / put your books in order），得当成通配，
# 不然字面匹配永远匹配不到，词必现这一关会假报错。挖空时整段一起挖。
def word_re(word):
    parts = re.split(r"\s*\.\.\.\s*", word.strip())
    return r"\b" + r".+?".join(re.escape(p) for p in parts if p) + r"\b"

def blanked(en, word):
    return re.sub(word_re(word), "___", en, count=1, flags=re.I)

def load():
    out = {}
    dup = []
    if TXT.exists():
        for i, line in enumerate(io.open(TXT, encoding="utf-8"), 1):
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3:
                dup.append("%d 行格式不对（要 word | 英文 | 中文）：%s" % (i, line))
                continue
            w, en, zh = parts
            if w.lower() in out:
                dup.append("%d 行 %s 重复了" % (i, w))
            out[w.lower()] = {"word": w, "en": en, "zh": zh}
    return out, dup

def cmd_list():
    S, _ = load()
    miss = [w for w in TARGETS if w["word"].lower() not in S]
    c = Counter(w["grade"] for w in miss)
    print("还差 %d 条：%s" % (len(miss), "，".join("%d年级 %d" % (g, c[g]) for g in sorted(c))))
    print(" | ".join(w["word"] for w in miss))

def cmd_check(verbose=False):
    S, fmt = load()
    # 「同义」不算失败：运行时挑干扰项本来就排掉了 x.cn === w.cn 的词，
    # 所以同释义的另一个词根本进不了选项。这里只当提示列出来，方便肉眼扫一眼。
    bad = {"格式": fmt, "词必现": [], "不超纲": [], "重复句": [], "多余": [], "同义(提示)": []}
    cn_of = {}
    for w in WORDS:
        cn_of.setdefault(w["cn"], []).append(w["word"])
    tgt_ok = {w["word"].lower(): w for w in TARGETS}
    for k, v in S.items():
        if k not in tgt_ok:
            bad["多余"].append("%s（不在清单里：功能词 / 整句 / 词表没有）" % k)
            continue
        en, wd = v["en"], v["word"]
        if not re.search(word_re(wd), en, re.I):
            bad["词必现"].append("%s: %s" % (wd, en))
        miss = sorted({t for t in toks(en) if not known(t)})
        if miss:
            bad["不超纲"].append("%s: %s  ← %s" % (wd, en, " ".join(miss)))
        same = [x for x in cn_of.get(tgt_ok[k]["cn"], []) if x.lower() != k]
        if same:
            bad["同义(提示)"].append("%s (%s) 与 %s 同释义" % (wd, tgt_ok[k]["cn"], "/".join(same)))
    seen = {}
    for k, v in S.items():
        key = blanked(v["en"], v["word"]).lower()
        if key in seen:
            bad["重复句"].append("%s 与 %s 共用「%s」" % (v["word"], seen[key], v["en"]))
        seen[key] = v["word"]
    done = len(set(S) & set(tgt_ok))
    print("已写 %d / %d" % (done, len(TARGETS)))
    n = 0
    for name, items in bad.items():
        if not items:
            continue
        if not name.endswith("(提示)"):
            n += len(items)
        print("%-6s %d" % (name, len(items)))
        for x in items[: (999 if verbose else 10)]:
            print("   ", x)
    return n

# 把句子注入 index.html 成 var SENTS = {小写词: 已挖空的英文句}。
# 挖空在注入时用 blanked() 预做好，运行时零正则。含「...」的通配词跳过——
# 挖空会把整段宾语一起吃掉，答案≠词表写法，没法当四选一的正确项。
def cmd_inject():
    if cmd_check():
        print("对账没过，先修句子再注入")
        sys.exit(1)
    S, fmt = load()
    if fmt:
        print("句子格式有误，先修：")
        for x in fmt:
            print("   ", x)
        sys.exit(1)
    sents = {}
    for w in TARGETS:
        k = w["word"].lower()
        if k not in S or "..." in w["word"]:
            continue
        sents[k] = blanked(S[k]["en"], S[k]["word"])
    html_path = BASE / "index.html"
    html = io.open(html_path, encoding="utf-8").read()
    blob = "var SENTS = " + json.dumps(sents, ensure_ascii=False, separators=(",", ":")) + ";"
    new, n = re.subn(r"var SENTS = \{[^}]*\};", blob, html, count=1)
    if n == 1:
        html = new                       # 已注入过 → 整体替换（幂等）
    else:
        # 首次注入：插在 WORDS.forEach 那一行之后
        pat = r"(WORDS\.forEach\(function\(w,i\)\{[^\n]*\}\);)"
        new, n = re.subn(pat, r"\1\n\n// 句子关数据：小写词 → 已挖空的英文句（python _sent_work.py inject 生成）\n" + blob, html, count=1)
        if n != 1:
            sys.exit("没找到 WORDS.forEach 注入点，index.html 结构变了？")
        html = new
    io.open(html_path, "w", encoding="utf-8").write(html)
    print("已注入 %d 条句子" % len(sents))

if __name__ == "__main__":
    args = sys.argv[1:]
    if "list" in args:
        cmd_list()
    elif "inject" in args:
        cmd_inject()
    else:
        sys.exit(1 if cmd_check("-v" in args) else 0)
