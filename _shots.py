# ponytail: 一次性截图脚本，验完就删
import pathlib, subprocess

BASE = pathlib.Path(r"E:\Cowork\Claude\kid-vocab")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
html = (BASE / "index.html").read_text(encoding="utf-8")

SEED = """
var SEED = {pet:{name:"小奇",form:1,born:1},
  zoo:{active:"bird", by:{bird:{cur:0,step:2,got:[]}}}, uw:{},
  app:{streak:5,lastDay:"2026-09-19",todayDate:"2026-09-20",todayClues:14,todayNew:3,sessions:5},
  cfg:{minutes:3,newLimit:8}};
var ST=[5,5,5,5,4,4,4,3,3,3,2,2,2,2,2,2];
// 每 17 个词标一个到期的，这样 3/4/5 年级都有复习词
var k=0; WORDS.forEach(function(w,i){ if(i%17===0) SEED.uw[w.id]={stage:ST[k++%ST.length], nextReview:Date.now()-1000, lastSeen:Date.now(), correct:2, wrong:0}; });
// 悬案簿：10 件有眉目（首页红标才会亮）+ 2 件刚开案 + 1 件已破 + 1 件存疑
function cs(w,o){ SEED.uw[w.id]=Object.assign({stage:2,nextReview:Date.now()-1000,lastSeen:Date.now(),
  correct:3,wrong:0,fuzzy:0,solved:0}, o); }
var ck=0; WORDS.forEach(function(w,i){
  if(i%53===0 && ck<10){ cs(w,{stage:3,correct:5,wrong:1,solved:2}); ck++; } });
cs(WORDS[7],  {stage:1,correct:1,wrong:2});
cs(WORDS[45], {stage:1,correct:1,wrong:1,fuzzy:1});
cs(WORDS[88], {stage:4,correct:6,wrong:2,solved:3});
cs(WORDS[31], {stage:2,correct:3,fuzzy:1});
// 入册时间铺开一点，截图才看得出标签的几种读法（刚刚/昨天/几天前/日期）
var _aged=0;
WORDS.forEach(function(w){ var u=SEED.uw[w.id];
  if(u && (u.wrong>0 || u.fuzzy)) u.caseAt = Date.now() - (_aged++ % 14) * 864e5 - 7200e3; });
// 刚添的两条：假线索那条 solved=0 本来沉底，看它会不会被顶上来
SEED.uw[WORDS[120].id] = {stage:1,nextReview:Date.now()-1000,lastSeen:Date.now(),
  correct:0,wrong:1,fuzzy:0,solved:0,caseAt:Date.now()-25e3};
SEED.uw[WORDS[31].id].caseAt = Date.now() - 45e3;
SEED.app.broken = 12;
// 切屏有 0.22s 淡入，无头截图会抓在半透明的那一帧，关掉它保证每次拍得一样
var _fr=document.createElement('style');
_fr.textContent='.screen.on{animation:none!important}';
document.head.appendChild(_fr);
"""

LIGHT = """
var _st=document.createElement('style'); _st.textContent=`
:root{--night:#fdf7ec;--night2:#fff4e0;--card:#fff;--card2:#fff8ec;--line:#ecdfc8;
--ink:#3a2f22;--muted:#8a7a63;--gold:#d99a12;--ok:#2f9e5e;--bad:#dd4747}
body{background:radial-gradient(120% 70% at 50% 0%,#fff4e0,#fdf7ec 70%)}
.opt.right{background:rgba(78,201,123,.16);color:#1d7a45}
.opt.wrong{background:rgba(255,107,107,.14);color:#b32c2c}
.btn.primary{box-shadow:0 10px 24px rgba(232,99,26,.25)}
`; document.head.appendChild(_st);
"""

FORMS = """
document.body.innerHTML='<div style="padding:24px;font-family:system-ui;color:var(--ink)">'+
 '<div style="font-size:21px;font-weight:800">狐狸 5 个形态</div>'+
 '<div style="color:var(--muted);font-size:13px;margin:4px 0 18px">每进一形态，多一件侦探装备</div>'+
 '<div style="display:flex;flex-wrap:wrap;gap:14px">'+
 [1,2,3,4,5].map(function(f){
   return '<div style="width:216px;text-align:center;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:12px 8px">'+
     '<div style="height:216px">'+foxSVG(f)+'</div>'+
     '<div style="font-weight:800;font-size:16px;margin-top:2px">'+f+' · '+FORM_NAME[f-1]+'</div>'+
     '<div style="color:var(--muted);font-size:12px;margin-top:4px;line-height:1.45">'+FORM_DESC[f-1]+'</div></div>';
 }).join('')+'</div></div>';
"""

def build(name, tail):
    out = html.replace("</body>", "<script>\n" + SEED + tail + "\n</script>\n</body>")
    p = BASE / name
    p.write_text(out, encoding="utf-8")
    return p

STAGES = """
document.body.innerHTML='<div style="padding:24px;font-family:system-ui;color:var(--ink)">'+
 '<div style="font-size:21px;font-weight:800">一只动物，3 轮解锁</div>'+
 '<div style="color:var(--muted);font-size:13px;margin:4px 0 18px">每查完一轮长一步。前两步只给线索，名字要等她猜到最后</div>'+
 '<div style="display:flex;gap:14px;flex-wrap:wrap">'+
 [1,2,3].map(function(st){
   var a=ZOO[0];
   return '<div style="width:206px;text-align:center;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:12px 10px">'+
     '<div style="height:206px">'+zooSVG(a,st)+'</div>'+
     '<div style="font-weight:800;font-size:14px;margin-top:2px">'+stepLabel(a,st)+'</div>'+
     '<div style="color:var(--fox);font-size:12px;margin-top:4px;font-weight:700">'+(st>=3?a.cn:'？？？')+'</div>'+
     '<div style="color:var(--muted);font-size:11px;margin-top:5px;line-height:1.6;text-align:left">'+a.facts[st-1]+'</div></div>';
 }).join('')+
 '</div>'+
 SERIES.map(function(s){
   return '<div style="font-size:15px;font-weight:800;margin:26px 0 12px">'+s.cn+
     '（'+zList(s.id).length+'）</div>'+
     '<div style="display:flex;gap:10px;flex-wrap:wrap">'+
     zList(s.id).map(function(a){
       return '<div style="width:140px;text-align:center;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:8px">'+
         '<div style="height:124px">'+zooSVG(a,3)+'</div>'+
         '<div style="font-weight:800;font-size:13px">'+a.cn+'</div>'+
         '<div style="color:var(--muted);font-size:10.5px;margin-top:3px;line-height:1.4">'+a.skill+'</div></div>';
     }).join('')+'</div>';
 }).join('')+
 '</div>';
"""

jobs = [
    ("1_狐狸5个形态.png",  FORMS, 760, 660),
    ("2_动物图鉴一览.png", STAGES, 800, 3400),
    ("3_首页_深色.png",    'S=SEED; save(); show("scr-home");', 620, 940),
    ("4_首页_浅色.png",    LIGHT + 'S=SEED; save(); show("scr-home");', 620, 940),
    ("5_动物图鉴.png",     'S=SEED; S.zoo.by.bird={cur:3,step:1,got:[zList("bird")[0].id,zList("bird")[1].id,zList("bird")[2].id]};'
                          ' save(); renderZoo(); show("scr-zoo");', 620, 900),
    ("6_结算_长成.png",    'S=SEED; S.zoo.by.bird.step=2; save(); show("scr-home"); startSession(); Q.correct=14; Q.wrong=1; Q.best=7; finish();', 620, 940),
    ("7_刷词_深色.png",    'S=SEED; save(); show("scr-home"); startSession();', 620, 940),
    ("8_刷词_浅色.png",    LIGHT + 'S=SEED; save(); show("scr-home"); startSession();', 620, 940),
    # 连对里程碑：把动画冻在放大那一刻，不然截图时它已经淡没了
    ("9_连对庆祝.png",     'S=SEED; save(); show("scr-home"); startSession(); Q.combo=2;'
                          ' window.advance=function(){};'
                          ' [].filter.call(document.querySelectorAll("#q-opts .opt"),'
                          '   function(x){return x.textContent===Q.cur.cn;})[0].click();'
                          ' var st=document.createElement("style");'
                          ' st.textContent=".mark.on{animation:none!important;opacity:1!important;'
                          'transform:scale(1.12)!important}"; document.head.appendChild(st);', 620, 940),
    ("10_设置.png",        'S=SEED; save(); show("scr-home"); openCfg();', 620, 940),
    ("11_悬案簿.png",      'S=SEED; save(); show("scr-cases");', 620, 1560),
    # 第三次答对一件悬案：卡在"🎉 破案！"那一帧。advance 先换成空函数，
    # 不然 1.2 秒后它会自己翻到下一题，截图就什么都抓不到了
    ("12_破案瞬间.png",    'S=SEED; save(); show("scr-home"); startSession();'
                          ' var w=WORDS[0]; window.advance=function(){};'
                          ' Q.pool=[w]; Q.i=0; nextQ();'
                          ' [].filter.call(document.querySelectorAll("#q-opts .opt"),'
                          '   function(x){return x.textContent===w.cn;})[0].click();', 620, 940),
    # 结算页新添悬案/存疑时才出现的那行入口
    ("13_结算_悬案入口.png",
     'S=SEED; save(); show("scr-home"); startSession(); S.app.avgMs=2000; S.app.msN=20;'
     ' Q.pool=[WORDS[6]]; Q.i=0; nextQ(); Q.locked=false;'
     ' answer(document.querySelectorAll("#q-opts .opt")[0], false, Q.cur);'     # 头一回栽
     ' Q.pool=[WORDS[9]]; Q.i=0; nextQ(); Q.locked=false; Q.shownAt=Date.now()-8000;'
     ' answer(document.querySelectorAll("#q-opts .opt")[0], true, Q.cur);'      # 慢答对
     ' Q.correct=11; Q.wrong=2; Q.best=6; finish();', 620, 940),
    # 集中练：跟正常轮一样限时倒计时（不是挑战那个"悬案挑战"字样）
    ("14_集中练.png",
     'S=SEED; save(); show("scr-cases");'
     ' $("case-sec-bad").querySelector("[data-drill]").click();', 620, 940),
    # 选方向：刷过英译中、队列里也有存货，两张牌都是亮的
    ("15_选方向.png",
     'S=SEED; S.app.doneEn2cn=1; S.app.cn2en=WORDS.slice(0,12).map(function(w){return w.id;});'
     ' S.app.todayDate=todayStr(); save(); show("scr-dir");', 620, 940),
    # 中译英：题干是中文、选项是英文，还没答所以「再听一遍」是灰的
    ("16_中译英.png",
     'S=SEED; S.app.doneEn2cn=1; S.app.cn2en=WORDS.slice(0,12).map(function(w){return w.id;});'
     ' S.app.todayDate=todayStr(); save(); show("scr-dir"); startSession("cn2en");', 620, 940),
]

for name, tail, w, h in jobs:
    p = build("_shots_tmp.html", tail)
    png = BASE / "预览图" / name
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--virtual-time-budget=8000",
                    "--user-data-dir=" + str(BASE / "_edgeprof"),
                    "--window-size=%d,%d" % (w, h),
                    "--screenshot=" + str(png), p.as_uri()],
                   capture_output=True, timeout=90)
    print(("OK  " if png.exists() else "FAIL"), png.name)
    p.unlink(missing_ok=True)
