# 出题引擎的回归测试：造一个假词库，在无头 Edge 里跑断言，看 <title> 里的结果。
#   用法：python _test.py && <Edge> --headless=new --dump-dom _test.html | grep -o "<title>[^<]*"
# 改完 buildPool / nextQ / answer 后跑一遍，别靠肉眼。
import pathlib

TEST = r"""
<script>
var log=[], err=[];
window.onerror=function(m){ err.push(String(m)); };
function t(n,c){ log.push((c?'PASS ':'FAIL ')+n); }

/* ---------- 一、真实词库：格式 + 连答 60 题 ---------- */
try{
  t('真实词库带年级', WORDS.every(function(w){ return w.grade>=1; }));
  t('真实词库无空 word/cn', WORDS.every(function(w){ return w.word && w.cn && w.id; }));

  S = blank();
  var rp = buildPool();
  t('真实数据冷启动 5 年级新词=8', rp.filter(function(w){return w.grade>=5;}).length===8);
  t('真实数据冷启动低年级=40(30热身+10送分)',
    rp.filter(function(w){return w.grade<5;}).length===40);

  Q = { pool:[], i:0, total:0, correct:0, wrong:0, combo:0, best:0,
        endAt: Date.now()+300000, total_ms:300000, locked:false, served:{} };
  nextQ();
  for(var n=0;n<60;n++){
    var bs = document.querySelectorAll('#q-opts .opt');
    if(bs.length!==4) throw new Error('第'+n+'题选项数='+bs.length);
    var cw = Q.cur;
    var rt = [].filter.call(bs, function(b){ return b.textContent===cw.cn; })[0];
    if(!rt) throw new Error('第'+n+'题找不到正确项 '+cw.word);
    answer(rt, n%4!==0, cw);       // 3/4 答对，1/4 答错
    Q.locked=false;
  }
  t('连答 60 题无异常', true);
  t('答完有掌握度记录', Object.keys(S.uw).length>0);
  t('stage 不超 5 且不降级', Object.keys(S.uw).every(function(k){
      var u=S.uw[k]; return u.stage<=5 && u.stage>=0 && 'nextReview' in u && 'wrong' in u; }));
  t('todayNew 不超每日额度', S.app.todayNew<=S.cfg.newLimit);
}catch(e){ t('真实词库段抛异常: '+e.message, false); }

/* ---------- 二、假词库：出题池逻辑 ---------- */
// 1-4 年级各 60 词 + 5 年级 200 词（够刷，不会中途枯竭）
var fake=[];
[1,2,3,4].forEach(function(g){ for(var i=0;i<60;i++)
  fake.push({grade:g, word:'g'+g+'w'+i, cn:'词'+g+'-'+i, phonetic:'', unit:1}); });
for(var i=0;i<200;i++) fake.push({grade:5, word:'g5w'+i, cn:'五'+i, phonetic:'', unit:1});
WORDS = fake; WORDS.forEach(function(w,i){ w.id='w'+i; });

S = blank(); S.cfg.newLimit = 8;

var iv = interleave([1,2,3,4,5,6,7,8],[9,10]);
t('interleave 撒开', iv.length===10 && iv.indexOf(9)<6 && iv.indexOf(10)>5);
t('interleave 无新词', JSON.stringify(interleave([1,2],[]))==='[1,2]');
t('interleave 无复习词', JSON.stringify(interleave([],[7,8]))==='[7,8]');

var p = buildPool();
t('冷启动 5 年级新词=8', p.filter(function(w){return w.grade>=5;}).length===8);
t('冷启动低年级=40(30热身+10送分)', p.filter(function(w){return w.grade<5;}).length===40);

S.app.todayNew = 8;
var p2 = buildPool();
t('额度用完 无 5 年级新词', p2.filter(function(w){return w.grade>=5;}).length===0);
t('额度用完 仍有 1-4 年级', p2.filter(function(w){return w.grade<5;}).length>0);
S.app.todayNew = 5;
t('剩 3 个额度', newRoom()===3);

S.app.todayDate = '2000-01-01';
t('跨天额度重置', newRoom()===8 && S.app.todayNew===0);

var p3 = buildPool({'w0':1,'w1':1,'w2':1});
t('exclude 排除生效', !p3.some(function(w){return w.id==='w0'||w.id==='w1'||w.id==='w2';}));

// ---- 送分题 ----
// 冷启动没有"已答熟"的词，退化成三年级基础词，总数 30 热身 + 8 新词 + 10 送分
S = blank(); S.cfg.newLimit = 8;
var pf = buildPool();
t('冷启动池子=48（含10送分）', pf.length===48);
t('冷启动有三年级基础词', pf.filter(function(w){return w.grade<=3;}).length>=10);

// 造 40 个已答熟的词（stage>=3 且复习期还没到）→ 应当整批混进 10 个
S = blank(); S.cfg.newLimit = 8;
WORDS.forEach(function(w,i){ if(i<40) S.uw[w.id] =
  {stage:4, nextReview:Date.now()+3*864e5, lastSeen:Date.now(), correct:5, wrong:0, fuzzy:0}; });
function isGift(w){ var u=S.uw[w.id]; return u && u.stage>=3 && u.nextReview>Date.now(); }
var pg = buildPool();
t('每批混进 10 个送分题', pg.filter(isGift).length===10);
var gp = []; pg.forEach(function(w,i){ if(isGift(w)) gp.push(i); });
t('送分题撒开了(不挤末尾)', gp[gp.length-1]-gp[0] > 10 && gp[gp.length-1] < pg.length-1);
t('送分题不重复', new Set(gp).size===gp.length);

// 答熟的词不够 10 个时，用三年级基础词补齐
S = blank(); S.cfg.newLimit = 8;
WORDS.forEach(function(w,i){ if(i<4) S.uw[w.id] =
  {stage:4, nextReview:Date.now()+3*864e5, lastSeen:Date.now(), correct:5, wrong:0, fuzzy:0}; });
var ps = buildPool();
t('不够时用基础词补齐', ps.filter(isGift).length===4 && ps.filter(function(w){
    return w.grade<=3 && !isGift(w); }).length>=6);

// ---- 题量不限：正常推进 300 题不结算 ----
S = blank(); S.cfg.newLimit = 8; S.cfg.minutes = 5;
Q = { pool:[], i:0, total:0, correct:0, wrong:0, combo:0, best:0,
      endAt: Date.now()+300000, total_ms:300000, locked:false, served:{} };
nextQ();
t('空池能补出题', !!Q.cur);
var n=0; while(n++<300 && Q) nextQ();
t('推进 300 题不结算', !!Q && Q.i>300);
t('served 数与出题数一致', !!Q && Object.keys(Q.served).length===Q.i);
var ids = Q ? Q.pool.map(function(w){return w.id;}) : [];
t('池内无重复题', new Set(ids).size===ids.length);

// ---- 5 年级新词当天只计一次 ----
S = blank(); S.cfg.newLimit = 8;
Q = { pool:[], i:0, total:0, correct:0, wrong:0, combo:0, best:0,
      endAt: Date.now()+300000, total_ms:300000, locked:false, served:{} };
nextQ();
var w5 = WORDS.filter(function(w){return w.grade>=5;})[0];
Q.cur = w5;
var btn = document.querySelectorAll('#q-opts .opt')[0];
answer(btn, true, w5);
t('首次答 5 年级新词 -> todayNew=1', S.app.todayNew===1);
Q.locked = false;
answer(btn, true, w5);
t('同一个词不重复计数', S.app.todayNew===1);

// ---- 时间到才结算 ----
Q.endAt = Date.now()-1;
nextQ();
t('时间到走 finish', Q===null);

/* ---------- 三、动物图鉴推进（分系列） ---------- */
var B = 'bird';
S = blank();
t('起手 0 步未解锁', zState(B).step===0 && zGot(B).length===0);
t('默认激活第一个系列', activeSeries()===SERIES[0].id);

var r1 = advanceZoo();
t('第1轮 -> 第1步', r1 && r1.step===1 && r1.unlocked===false && r1.animal.id===zList(B)[0].id);
var r2 = advanceZoo();
t('第2轮 -> 幼年(step2)', r2.step===2 && r2.unlocked===false);
var r3 = advanceZoo();
t('第3轮 -> 成年并解锁', r3.step===3 && r3.unlocked===true);
t('解锁后进本系列图鉴', zGot(B).length===1 && zGot(B)[0]===zList(B)[0].id);
t('成年才公布名字', r3.animal.facts[2].indexOf(r3.animal.cn)>=0);
t('推进只动本系列', zGot('sea').length===0 && zGot('bug').length===0);

// 鸟类 N 只 × 3 轮（N 不写死，加动物不用改这里）
var NB = zList(B).length;
for(var k=0;k<NB*3-3;k++) advanceZoo();
t('鸟类查完刚好集齐 ' + NB + ' 只', zGot(B).length===NB);
t('图鉴不重复计数', new Set(zGot(B)).size===NB);
t('集齐后不再越界', zState(B).cur===zList(B).length-1);
var nx = advanceZoo();
t('鸟类集齐后自动转下一个系列', nx && nx.series!=='bird' && nx.step===1);

// 一路推到底：所有系列都集齐（推得比需要多，多的那些该返回 null）
for(var k=0;k<ZOO.length*3+20;k++) advanceZoo();
t('所有系列都集齐', zooTotal()===ZOO.length);
t('全部集齐后返回 null', advanceZoo()===null);
t('集齐后推进不越界', SERIES.every(function(s){
    return zState(s.id).cur===zList(s.id).length-1; }));

// 形态跟**总**解锁数走（60 只 → 阈值 [0,1,2,30,60]），阈值由 formMin 算，不写死
function setTotal(n){
  S.zoo.by = {};
  var left = n;
  SERIES.forEach(function(s){
    var L = zList(s.id), take = Math.max(0, Math.min(left, L.length));
    left -= take;
    S.zoo.by[s.id] = {cur:0, step:0, got:L.slice(0,take).map(function(a){ return a.id; })};
  });
}
var FM = formMin();
t('形态阈值 5 档且严格递增',
  FM.length===5 && FM[0]===0 && FM.every(function(v,i){ return i===0 || v>FM[i-1]; }));
t('阈值封顶 = 动物总数', FM[4]===ZOO.length);
t('解锁数刚好卡上阈值就升形态', FM.every(function(v,i){
    setTotal(v); return formOf()===i+1; }));
t('差一只不升形态', FM.every(function(v,i){
    if(v<2) return true;
    setTotal(v-1); return formOf()===i; }));

// 名字在她自己猜出来之前不许漏
t('线索1/2 不含动物名', ZOO.every(function(a){
    return a.facts[0].indexOf(a.cn)<0 && a.facts[1].indexOf(a.cn)<0; }));
t('第一步和本体都画了', ZOO.every(function(a){ return a.entry && a.body; }));
t('每只都归了系列', ZOO.every(function(a){
    return SERIES.some(function(s){ return s.id===a.series; }); }));
t('每个系列都有开场词', SERIES.every(function(s){
    return s.cn && s.entry && s.hatch; }));

// 第一步的台词：卵生系列是蛋，哺乳系列是脚印
t('鸟类的开场是蛋', stepLabel(zList('bird')[0], 1)==='侦查到一颗蛋');
t('鸟类的幼年是破壳', stepLabel(zList('bird')[0], 2)==='蛋里孵出了小家伙');
t('成年那条不用系列词', stepLabel(zList('bird')[0], 3)===STEP_LABEL[3]);
t('动物自己写了就用它的',
  stepLabel({series:'bird', entryLabel:'树上有个洞'}, 1)==='树上有个洞');
t('动物自己写了幼年也用它的',
  stepLabel({series:'bird', hatchLabel:'探出个小脑袋'}, 2)==='探出个小脑袋');

// 哺乳动物这一系列：开场不是蛋，第一步画的是脚印
var MAM = zList('mammal')[0];
t('哺乳系列的开场不是蛋', stepLabel(MAM, 1)==='发现一串脚印');
t('哺乳系列的幼年不是破壳', stepLabel(MAM, 2)==='窝里探出个小脑袋');
// 蛋的签名是 rx="56"；脚印是一堆扁椭圆，没有这个尺寸
t('哺乳第一步画的是脚印不是蛋', zooSVG(MAM, 1).indexOf('rx="56"')<0);
t('卵生第一步还是蛋', zooSVG(zList('bird')[0], 1).indexOf('rx="56"')>=0);
t('水里那几只自己换了开场词',
  ['whale','dolphin','bat'].every(function(id){
    var a = ZOO.filter(function(x){ return x.id===id; })[0];
    return !!a && a.entryLabel && stepLabel(a, 1)!=='发现一串脚印'; }));
t('自换开场的那几只也是自己的 entry',
  ['whale','dolphin','bat'].every(function(id){
    var a = ZOO.filter(function(x){ return x.id===id; })[0];
    return a && a.entry && a.entry.length>0; }));
S = blank(); S.zoo.active = 'mammal';
var rm = advanceZoo();
t('切到哺乳系列就能推进', rm && rm.series==='mammal' && rm.step===1);
renderZoo();
t('哺乳系列的页签出现了', [].some.call(document.querySelectorAll('#zoo-tabs .ztab'),
    function(b){ return b.dataset.s==='mammal'; }));

// 每个系列都补齐到 12：图鉴一页 3 列 × 4 行正好铺满
t('5 个系列都在', SERIES.length===5);
t('每个系列都是 12 只', SERIES.every(function(s){ return zList(s.id).length===12; }));
t('总数 60', ZOO.length===60);
t('id 不重复', new Set(ZOO.map(function(a){ return a.id; })).size===ZOO.length);

// 图鉴渲染
S = blank();
[0,1,2,3].forEach(function(st){ zooSVG(ZOO[0], st); });
t('zooSVG 四档都画得出来', true);
mountZoo($('r-fox'), ZOO[0], 3);
t('mountZoo 塞得进 DOM', $('r-fox').querySelector('svg')!==null);
renderZoo();
t('图鉴页签 = 有动物的系列数', document.querySelectorAll('#zoo-tabs .ztab').length===SERIES.length);
t('图鉴只显示当前系列', document.querySelectorAll('#zoo-grid .zoo-card').length===zList('bird').length);
t('集齐前图鉴全锁',
  document.querySelectorAll('#zoo-grid .zoo-card.lock').length===zList('bird').length);
t('当前系列的页签是高亮的',
  document.querySelectorAll('#zoo-tabs .ztab.on').length===1 &&
  document.querySelector('#zoo-tabs .ztab.on').dataset.s===activeSeries());

// 点别的页签能切过去，而且只切自己那一页
document.querySelectorAll('#zoo-tabs .ztab')[1].click();
t('点页签切换当前系列', S.zoo.active!=='bird');
t('切换后图鉴换了一批卡',
  document.querySelectorAll('#zoo-grid .zoo-card').length===zList(S.zoo.active).length);
renderZoo();

// 冷启动（装了 App 还没查过案）首页要能渲染，且名字是问号
S = blank(); renderHome();
t('冷启动首页不抛', $('p-name').textContent==='？？？');
t('冷启动 0 步无进度条', $('p-bar').innerHTML.indexOf('on')<0);
t('冷启动不剧透线索', $('p-clue').textContent.indexOf('叫')<0 && !!$('pet-host').innerHTML);
t('冷启动首页标出系列名', $('p-lab').textContent.indexOf('鸟类')>=0);

// 全部集齐之后首页还有东西看，不报错
S = blank(); setTotal(ZOO.length);
SERIES.forEach(function(s){ zState(s.id).step = ZOO_STEP; });
renderHome();
t('全集齐后首页仍可渲染', $('p-lab').textContent.indexOf('集齐')>=0 && !!$('pet-host').innerHTML);
t('全集齐后返回 null', advanceZoo()===null);

// 老存档（一条连续进度）升级上来：要按系列归位
localStorage.setItem(KEY, JSON.stringify({pet:{name:'小奇'},uw:{},app:{},cfg:{},
  zoo:{cur:5, step:2, got:['owl','octopus','chameleon']}}));
S = load();
t('老存档搬进新结构', !!(S.zoo.by && S.zoo.by.bird));
t('老存档解锁的按系列归位',
  zGot('bird').indexOf('owl')>=0 && zGot('sea').indexOf('octopus')>=0 &&
  zGot('rept').indexOf('chameleon')>=0);
t('老存档总数没丢', zooTotal()===3);
t('老存档在手的进度搬回它的系列',
  zState('bird').step===2 && zList('bird')[zState('bird').cur].id==='penguin');
renderHome();
t('老存档首页不抛', !!$('pet-host').innerHTML);

// 存档里压根没有 zoo（更老的版本）
localStorage.setItem(KEY, JSON.stringify({pet:{name:'小奇'},uw:{},app:{},cfg:{}}));
S = load();
t('没 zoo 的老存档补出空结构', S.zoo && S.zoo.by && Object.keys(S.zoo.by).length===0);
t('没 zoo 的老存档默认激活第一系列', activeSeries()===SERIES[0].id);
renderHome();
t('没 zoo 的老存档首页不抛', !!$('pet-host').innerHTML);
t('老存档补出音效开关', S.cfg.sfx===true);

/* ---------- 四、连对鼓励 ---------- */
t('2 连对不庆祝', comboHit(0)===0 && comboHit(1)===0 && comboHit(2)===0);
t('3/5/8/12/20 各自一级', [3,5,8,12,20].map(comboHit).join(',')==='1,2,3,4,5');
t('中间数不庆祝', [4,6,7,9,11,13,19].every(function(n){ return comboHit(n)===0; }));
t('21 不庆祝(没到下一档)', comboHit(21)===0);
t('20 之后每 10 一次', comboHit(30)===6 && comboHit(40)===6 && comboHit(50)===6);
t('里程碑文案都在', COMBO_MARKS.every(function(n){ return !!COMBO_WORD[n]; }));
t('超出表格的档位有兜底文案', comboWord(30,6).indexOf('30')>=0);

// 答对要冒庆祝字，答错要把连对清零
S = blank(); S.cfg.sfx = false;            // 测试里不出声
S.app.todayDate = todayStr();
Q = { pool:[], i:0, total:0, correct:0, wrong:0, combo:0, best:0,
      endAt: Date.now()+300000, total_ms:300000, locked:false, served:{} };
nextQ();
function pick(correct){
  var b = document.querySelectorAll('#q-opts .opt')[0];
  Q.locked = false;
  answer(b, correct, Q.cur);
}
// 前面那 60 题也冒过庆祝字，先把它清掉再验，不然测的是上一段的残留
$('q-mark').classList.remove('on'); $('q-mark').textContent = '';
pick(true);
t('答对没有「其实是蒙的」了', document.querySelectorAll('.fb .fuzzy').length===0);
t('1 连对不冒字', !$('q-mark').classList.contains('on'));
pick(true);
pick(true);
t('3 连对冒庆祝字', $('q-mark').textContent==='连破 3 案！' && $('q-mark').classList.contains('on'));
t('3 连对有音效级别', comboHit(3)===1);
pick(false);
t('答错清零连对', Q.combo===0);
t('最长连对留了记录', Q.best===3);
t('答错的词排到明天', S.uw[Q.cur.id].nextReview - Date.now() > 86000e3);

/* ---------- 五、悬案簿 ---------- */
// 造一局假测试：池子里只放指定那个词，答完再换下一个
function newQ(){
  return { pool:[], i:0, total:0, correct:0, wrong:0, combo:0, best:0,
           endAt: Date.now()+300000, total_ms:300000, locked:false, served:{}, shownAt:0 };
}
function serveWord(w){ Q.pool = [w]; Q.i = 0; nextQ(); return Q.cur; }
function at(ms){ Q.shownAt = Date.now() - ms; }     // 假装她想了 ms 那么久
function tap(ok){
  Q.locked = false;
  answer(document.querySelectorAll('#q-opts .opt')[0], ok, Q.cur);
}

// 状态分类：什么算悬案、什么算存疑
S = blank(); S.cfg.sfx = false;
var CW = WORDS.slice(0, 7).map(function(w){ return w.id; });
function setCase(i, o, w){
  var u = rec(w || CW[i]);
  for(var k in o) u[k] = o[k];
}
setCase(0, {wrong:0, solved:0});                      // 从没错过
setCase(1, {wrong:1, solved:0});                      // 栽过一次
setCase(2, {wrong:2, solved:1});
setCase(3, {wrong:3, solved:2});                      // 有眉目
setCase(4, {wrong:1, solved:3});                      // 已破
setCase(5, {wrong:0, solved:0, fuzzy:1});             // 只存疑
setCase(6, {wrong:2, solved:0, fuzzy:1});             // 又错又慢
t('从没错过的词不算悬案', caseKind(CW[0])==='');
t('栽过一次就立案', caseKind(CW[1])==='bad');
t('破了的案子摘出悬案簿', caseKind(CW[4])==='');
t('答对但慢的算存疑', caseKind(CW[5])==='fuzzy');
t('又错又慢的算假线索', caseKind(CW[6])==='bad');
t('悬案簿总数不含已破和没栽过的', caseTotal()===5);
t('有眉目的只有 solved>=2 的', casesReady().length===1 && casesReady()[0].id===CW[3]);
t('悬案里快破的排最前面', caseList('bad')[0].id===CW[3]);
t('假线索和存疑分开筛', caseList('fuzzy').length===1 && caseList('fuzzy')[0].id===CW[5]);

// 点词条 = 只听发音，不进练习、不动进度
var snapC = JSON.stringify(S.uw), topC = caseList()[0].id;
Q = null; renderCases();
var rowC = document.querySelector('#case-list .case-row');
t('每条悬案都带发音开关',
  document.querySelectorAll('#case-list .case-row .spk').length===caseTotal() &&
  document.querySelectorAll('#case-list .case-row').length===caseTotal());
t('词条挂着词的 id', rowC && rowC.dataset.id===topC);
rowC.click();
t('点词条不动任何进度', JSON.stringify(S.uw)===snapC);
t('点词条不会开出练习', Q===null);
t('点列表空白处不抛也不动数据', (function(){
    $('case-list').click(); return JSON.stringify(S.uw)===snapC; })());

// 顶部统计卡：点「假线索」「存疑」跳到下面对应那一段
t('两张卡都挂着跳转目标',
  !!document.querySelector('#case-stats [data-go="case-sec-bad"]') &&
  !!document.querySelector('#case-stats [data-go="case-sec-fuzzy"]'));
t('跳转目标确实在页面上', !!$('case-sec-bad') && !!$('case-sec-fuzzy'));
t('目标段就在各自第一条前面',
  $('case-sec-bad').nextElementSibling.classList.contains('case-row') &&
  $('case-sec-fuzzy').nextElementSibling.classList.contains('case-row'));
t('点卡滚到那一段且不动数据', (function(){
    var hit = null, sec = $('case-sec-fuzzy'), old = sec.scrollIntoView;
    sec.scrollIntoView = function(o){ hit = o; };
    document.querySelector('#case-stats [data-go="case-sec-fuzzy"]').click();
    sec.scrollIntoView = old;
    return !!hit && hit.block==='start' && JSON.stringify(S.uw)===snapC; })());
t('已破那张卡不给跳', !document.querySelector('#case-stats .stat.ok[data-go]'));

// 答对不攒破案进度：没栽过的词根本不是案子
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
S.app.avgMs = 2000; S.app.msN = 20;
Q = newQ();
for(var i=0;i<3;i++){ serveWord(WORDS[2]); at(500); tap(true); }
t('没栽过的词答对 3 次也不算破案',
  S.uw[WORDS[2].id].solved===0 && S.app.broken===0 && caseKind(WORDS[2].id)==='');
t('没栽过的词根本不进悬案簿', caseTotal()===0);
t('快答对正常升级到 3 级', S.uw[WORDS[2].id].stage===3);

// 答对但反常地慢：级别不动、按当前级别重排，同时记成存疑
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
S.app.avgMs = 2000; S.app.msN = 20;
Q = newQ();
var WS = WORDS[3], uS = rec(WS.id);
serveWord(WS); at(6000); tap(true);
t('慢答对：级别不动', uS.stage===0);
t('慢答对：按当前级别重排(10 分钟)', uS.nextReview - Date.now() <= 602000);
t('慢答对记成存疑', uS.fuzzy===1 && caseKind(WS.id)==='fuzzy');
serveWord(WS); at(400); tap(true);
t('再答对且不慢就摘掉存疑', uS.fuzzy===0 && caseKind(WS.id)==='');
t('摘掉后正常升级', uS.stage===1 && uS.nextReview - Date.now() > 86000e3);

// 卡住了盯着看很久：这正是她真实会发生的情况，必须算慢
var WX = WORDS[8], uX = rec(WX.id);
serveWord(WX); at(20000); tap(true);
t('想 20 秒也算慢', uX.fuzzy===1 && caseKind(WX.id)==='fuzzy');
t('超长思考不污染基线', S.app.avgMs < 3000);
// 1 分半以上当成"人走开了"，丢掉不记
var WY = WORDS[9], uY = rec(WY.id);
serveWord(WY); at(90000); tap(true);
t('90 秒当成走开了不记慢', uY.fuzzy===0 && caseKind(WY.id)==='');
// 头几题还没基线，也得有个绝对兜底，不然第一次上场永远测不出慢
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
Q = newQ();
var WZ = WORDS[10], uZ = rec(WZ.id);
serveWord(WZ); at(9000); tap(true);
t('没基线时按绝对阈值兜底(9 秒算慢)', uZ.fuzzy===1);
serveWord(WZ); at(1200); tap(true);
t('没基线时 1.2 秒不算慢', uZ.fuzzy===0);

/* -- 入册时间：她要知道"哪一条是刚添的" -- */
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
Q = newQ();
var WT = WORDS[11], uT = rec(WT.id);
serveWord(WT); tap(false);
var t1 = uT.caseAt;
t('立案会盖上入册时间', t1 > 0 && Date.now() - t1 < 5000);
// 同一件案子再栽一次，还是那件案子，时间不能跟着动
uT.caseAt = t1 = Date.now() - 3*DAY;
serveWord(WT); tap(false);
t('同一件案子再栽不改入册时间', uT.caseAt === t1 && uT.wrong === 2);
// 答对推进进度也不改——案子没变
serveWord(WT); at(300); tap(true);
t('答对推进进度不改入册时间', uT.caseAt === t1);
// 已破的案子晾 2 天再栽，那是**新案**，时间要重盖
uT.solved = 3; uT.wrong = 3; uT.caseAt = Date.now() - 2*DAY;
serveWord(WT); tap(false);
t('已破的案子重开要重盖入册时间', uT.caseAt > Date.now() - 5000);

// 存疑这条：0→1 才算入册；已经立案的词被标成 fuzzy，不能冲掉立案时间
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
S.app.avgMs = 2000; S.app.msN = 20;
Q = newQ();
var WQ = WORDS[12], uQ = rec(WQ.id);
serveWord(WQ); at(8000); tap(true);
var t2 = uQ.caseAt;
t('变存疑会盖上入册时间', t2 > 0 && caseKind(WQ.id)==='fuzzy');
serveWord(WQ); at(8000); tap(true);        // 还慢，仍是 0→1 之外的重复
t('一直是存疑就不重盖', uQ.caseAt === t2);
serveWord(WQ); at(300); tap(true);         // 变利索，出列表
t('摘掉存疑后时间留着不影响判断', caseKind(WQ.id)==='');
uQ.caseAt = Date.now() - 5*DAY;
serveWord(WQ); at(8000); tap(true);        // 又变慢 -> 重新入册
t('再次变存疑要重盖入册时间', uQ.caseAt > Date.now() - 5000);

// 已经立案（假线索）的词慢答对 -> 也会被标 fuzzy，但显示成假线索，
// 入册时间得留在立案那一刻
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
S.app.avgMs = 2000; S.app.msN = 20;
Q = newQ();
var WV = WORDS[13], uV = rec(WV.id);
serveWord(WV); tap(false);                  // 先立案
var t3 = uV.caseAt = Date.now() - 4*DAY;    // 假装 4 天前立的
serveWord(WV); at(9000); tap(true);         // 慢答对
t('立案的词慢答对仍算假线索', uV.fuzzy===1 && caseKind(WV.id)==='bad');
t('立案的词慢答对不冲掉立案时间', uV.caseAt === t3);

// 时间标签怎么念
t('10 分钟内显示刚刚', whenLabel(Date.now() - 60e3)==='刚刚');
t('当天显示今天', whenLabel(Date.now() - 3600e3)==='今天');
t('隔天显示昨天', whenLabel(new Date(todayStr(new Date(Date.now()-DAY))+'T12:00:00').getTime())==='昨天');
t('一周内给几天前', whenLabel(Date.now() - 3*DAY)==='3 天前');
t('超过一周直接写日期',
  /^\d{1,2}-\d{1,2}$/.test(whenLabel(Date.now() - 30*DAY)));
t('没有时间就不显示', whenLabel(0)==='' && whenLabel(undefined)==='');
// 老存档没这个字段，退回 lastSeen，总比空着强
t('老存档退回 lastSeen', caseAt({lastSeen: 12345})===12345 && caseAt({})===0);

// 排序：今天新入册的顶到最前，其余照旧按快破案的排前面
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
var S1 = WORDS[14].id, S2 = WORDS[15].id, S3 = WORDS[16].id;
rec(S1).wrong = 1; rec(S1).solved = 2; rec(S1).caseAt = Date.now() - 9*DAY;   // 快破了，老
rec(S2).wrong = 1; rec(S2).solved = 0; rec(S2).caseAt = Date.now() - 9*DAY;   // 新立过，老
rec(S3).wrong = 1; rec(S3).solved = 0; rec(S3).caseAt = Date.now() - 60e3;    // 今天刚立
var ord = caseList('bad').map(function(w){ return w.id; });
t('今天新入册的顶到最前', ord[0]===S3);
t('其余仍按快破案的排前面', ord.indexOf(S1) < ord.indexOf(S2));
t('入册时间渲染进了行里',
  (function(){ renderCases(); return !!document.querySelector('.case-row[data-id="'+S3+'"] .when'); })());
t('标签写的是「刚刚 入册」',
  (function(){ return document.querySelector('.case-row[data-id="'+S3+'"] .when').textContent==='刚刚 入册'; })());

// 答错：没破的案子进度保留，破了的那件重新开案
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
Q = newQ();
var WA = WORDS[4], WB = WORDS[5];
rec(WA.id).wrong = 2; rec(WA.id).solved = 2;
rec(WB.id).wrong = 5; rec(WB.id).solved = 3;
serveWord(WA); tap(false);
t('答错不清零破案进度', S.uw[WA.id].solved===2);
t('答错的案子还在悬案簿里', caseKind(WA.id)==='bad');
t('答错的词排到明天', S.uw[WA.id].nextReview - Date.now() > 86000e3);
serveWord(WB); tap(false);
t('已破的案子再答错要重开', S.uw[WB.id].solved===0);
t('重开后回到悬案簿', caseKind(WB.id)==='bad' && S.app.broken===0);

// 攒够 10 件有眉目才给挑战入口
S = blank(); S.cfg.sfx = false;
WORDS.slice(0, 9).forEach(function(w){ var u = rec(w.id); u.wrong = 1; u.solved = 2; });
renderCases();
t('9 件还没到挑战门槛', casesReady().length===9 && !$('btn-chal'));
t('没有存疑时那张卡点不动', !document.querySelector('#case-stats [data-go="case-sec-fuzzy"]'));
t('这时假线索卡还是能跳', !!document.querySelector('#case-stats [data-go="case-sec-bad"]'));
t('没到门槛时告诉她还差几件', $('case-challenge').innerHTML.indexOf('再有 1 件')>=0);
renderHome();
t('没到门槛首页不挂红标', $('case-ready').className.indexOf('on')<0);
t('首页入口报总数', $('case-n').textContent==='9');
var u10 = rec(WORDS[9].id); u10.wrong = 1; u10.solved = 2;
renderCases(); renderHome();
t('10 件就出挑战按钮', casesReady().length===10 && !!$('btn-chal'));
t('10 件首页挂出红标', $('case-ready').className.indexOf('on')>=0 &&
  $('case-ready').textContent.indexOf('10 件')>=0);
t('挑战入口只收有眉目的那 10 件', (function(){
    $('btn-chal').click();
    return !!Q && Q.chal===true && Q.total===10 && Q.pool.length===10;
  })());

// 挑战：不计时，测完回悬案簿；不给动物进度、不算连续天数、破一案 +2 线索
t('挑战不计时', Q.endAt===Infinity);
t('挑战里的题都是悬案',
  Q.pool.every(function(w){ return (S.uw[w.id].solved||0)===2; }));
S.app.avgMs = 2000; S.app.msN = 20;
for(var k=0;k<10;k++){
  var id = Q.cur.id;
  at(600); tap(true);
  if(k===0){
    t('挑战里破一案 +2 线索', S.uw[id].solved===3 && S.app.todayClues===2);
    t('破案时给的是「破案！」不是「线索 +1」',
      $('q-fb').innerHTML.indexOf('破案！')>=0);
  }
  advance();                                   // 手动进下一件；第 10 件会撞上收尾
}
t('这 10 件全破了', S.app.broken===10 && caseTotal()===0);
t('挑战每题 +1、破案再 +1', S.app.todayClues===20);
t('挑战测完就回悬案簿', !Q && $('scr-cases').classList.contains('on'));
t('挑战不走结算页', !$('scr-result').classList.contains('on'));
t('挑战不推进图鉴', zooTotal()===0);
t('挑战不算连续天数', S.app.streak===0 && S.app.sessions===0 && S.app.lastDay==='');
t('回来亮出连破件数', $('case-win').innerHTML.indexOf('连破 10 件')>=0);
t('横幅上写清额外线索', $('case-win').innerHTML.indexOf('+20')>=0);
renderCases();
t('横幅只亮一次', $('case-win').innerHTML==='');
t('全破之后悬案簿是空的', $('case-list').innerHTML.indexOf('悬案簿是空的')>=0);
t('已经破掉的不再进挑战', casesReady().length===0);

/* ---------- 六、集中练（假线索 / 存疑） ---------- */
// 这一段的核心：练习**只推到「有眉目」就停**，不会把「10 件有眉目」这个状态吃空。
S = blank(); S.cfg.sfx = false; S.cfg.minutes = 5; S.app.todayDate = todayStr();
WORDS.slice(0, 3).forEach(function(w){ var u = rec(w.id); u.wrong = 1; u.solved = 0; });
rec(WORDS[10].id).fuzzy = 1;
renderCases();
t('假线索段挂了集中练入口', !!document.querySelector('#case-sec-bad [data-drill="bad"]'));
t('存疑段挂了集中练入口', !!document.querySelector('#case-sec-fuzzy [data-drill="fuzzy"]'));
t('集中练入口没抢走统计卡的跳转', !!document.querySelector('#case-stats [data-go="case-sec-bad"]'));

$('case-sec-bad').querySelector('[data-drill]').click();
t('点假线索进集中练', !!Q && Q.drill===true && Q.kind==='bad');
t('练习池是全部假线索，不是只有眉目那几件', Q.total===3 && Q.pool.length===3);
t('练习是限时的（不像挑战那样不计时）',
  Q.endAt > Date.now() && Math.round((Q.endAt-Date.now())/60000)===5);

// 同一件案子连答对 3 次：封顶在 2，绝不破案
S.app.avgMs = 2000; S.app.msN = 20;
S.app.todayClues = 0;
var WD = WORDS[0], uD = rec(WD.id);
for(var n=0;n<3;n++){ serveWord(WD); at(600); tap(true); }
t('练习里答对推破案进度', uD.solved>=1);
t('练习里封顶在 2，连对 3 次也不破案', uD.solved===2 && S.app.broken===0);
t('练习不破案所以案子还在簿子上', caseKind(WD.id)==='bad');
t('练到 2 就算「有眉目」，能顶挑战门槛', uD.solved>=CASE_READY);
t('练习每题只给 1 条线索（没有破案那个 +2）', S.app.todayClues===3);

// 封顶不是锁死：脱掉练习模式，正常轮再答对一次照样破案
Q.drill = false; Q.kind = null;
serveWord(WD); at(600); tap(true);
t('出了练习再答对一次就破案（是封顶不是锁死）',
  uD.solved===3 && S.app.broken===1 && caseKind(WD.id)==='');
clearInterval(Q.timer); Q = null;

// 存疑那条路：答得快就出列表——这是它唯一的"收益"
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
rec(WORDS[1].id).fuzzy = 1; rec(WORDS[2].id).fuzzy = 1;
renderCases();
$('case-sec-fuzzy').querySelector('[data-drill]').click();
t('点存疑进集中练', !!Q && Q.drill===true && Q.kind==='fuzzy' && Q.total===2);
S.app.avgMs = 2000; S.app.msN = 20;
serveWord(WORDS[1]); at(500); tap(true);
t('存疑里答快了就出列表', rec(WORDS[1].id).fuzzy===0 && caseKind(WORDS[1].id)==='');
t('存疑出列表算进这轮收益', Q.gain===1);
serveWord(WORDS[2]); at(9000); tap(true);
t('存疑仍然答得慢就留着', rec(WORDS[2].id).fuzzy===1 && caseKind(WORDS[2].id)==='fuzzy');
t('没变利索就不计收益', Q.gain===1);
t('存疑怎么练都碰不到破案计数',
  (rec(WORDS[1].id).solved||0)===0 && S.app.broken===0);
clearInterval(Q.timer); Q = null;

// 练完这一批就回悬案簿：不走结算页、不推动物、不算连续天数
S = blank(); S.cfg.sfx = false; S.cfg.minutes = 5; S.app.todayDate = todayStr();
WORDS.slice(0, 2).forEach(function(w){
  var u = rec(w.id); u.wrong = 1; u.solved = 1;         // 差一次就到有眉目
});
renderCases();
$('case-sec-bad').querySelector('[data-drill]').click();
S.app.avgMs = 2000; S.app.msN = 20;
at(600); tap(true); advance();                          // 第 1 件
at(600); tap(true); advance();                          // 第 2 件 → 池子空了，收尾
t('练完这一批就回悬案簿', !Q && $('scr-cases').classList.contains('on'));
t('练习不走结算页', !$('scr-result').classList.contains('on'));
t('练习不推进图鉴', zooTotal()===0);
t('练习不算连续天数', S.app.streak===0 && S.app.sessions===0 && S.app.lastDay==='');
t('回来亮出练了几题', $('case-win').innerHTML.indexOf('练了 2 题')>=0);
t('横幅报的是又攒了几件有眉目（不是破了几件）',
  $('case-win').innerHTML.indexOf('2 件案子有眉目')>=0 &&
  $('case-win').innerHTML.indexOf('连破')<0);
renderCases();
t('练习横幅只亮一次', $('case-win').innerHTML==='');
t('练完案子还在簿子上，只是都到了有眉目',
  caseList('bad').length===2 && casesReady().length===2);

// 中途按 ✕ 退出：挑战/集中练都不推进动物，而且退回悬案簿（她就是从那儿进来的）
S = blank(); S.cfg.sfx = false; S.app.todayDate = todayStr();
rec(WORDS[0].id).wrong = 1;
renderCases();
$('case-sec-bad').querySelector('[data-drill]').click();
S.app.avgMs = 2000; S.app.msN = 20;
at(600); tap(true);
var _cf2 = window.confirm; window.confirm = function(){ return true; };
$('btn-quit').click();
window.confirm = _cf2;
t('✕ 退出集中练不推进图鉴', zooTotal()===0 && !Q);
t('✕ 退出集中练回悬案簿，不是回首页',
  $('scr-cases').classList.contains('on') && !$('scr-home').classList.contains('on'));
S = blank(); S.cfg.sfx = false; Q = null;

// 结算页：只有这轮真添了新东西才给悬案簿入口
S = blank(); S.cfg.sfx = false; S.cfg.minutes = 3; S.app.todayDate = todayStr();
startSession();
S.app.avgMs = 2000; S.app.msN = 20;
serveWord(WORDS[0]); tap(false);                       // 头一回栽 → 新案子
t('答错立案计一次', Q.newCase===1);
serveWord(WORDS[0]); tap(false);                       // 同一件再错，不算新添
t('同一件案子再答错不重复计数', Q.newCase===1 && Q.newFuzzy===0);
serveWord(WORDS[1]); at(8000); tap(true);              // 慢答对 → 新存疑
t('慢答对记一笔新存疑', Q.newFuzzy===1);
finish();
t('结算页写出新添的案子', $('r-cases').innerHTML.indexOf('1 件案子')>=0);
t('结算页写出新添的存疑', $('r-cases').innerHTML.indexOf('1 件存疑')>=0);
t('结算页有去悬案簿的入口', !!$('r-cases-go'));
$('r-cases-go').click();
t('点入口进悬案簿', $('scr-cases').classList.contains('on'));

// 这轮什么都没添：那行不许出现
S = blank(); S.cfg.sfx = false; S.cfg.minutes = 3; S.app.todayDate = todayStr();
startSession();
S.app.avgMs = 2000; S.app.msN = 20;
serveWord(WORDS[5]); at(500); tap(true);               // 快答对，什么都没添
finish();
t('没新添东西就不出现那行', $('r-cases').innerHTML==='' && !$('r-cases-go'));
t('没新添时结算页照常显示',
  $('r-correct').textContent==='1' && $('scr-result').classList.contains('on'));

// 速度榜（英译中）：只记英译中、按**每分钟答对数**降序、封顶 5 条、本轮标出来。
// 关键在"每分钟"——不然 3 分钟的轮次会无脑压过 1 分钟的
try{
S = blank(); S.cfg.sfx = false; S.cfg.minutes = 3; S.app.todayDate = todayStr();
S.speed = [{r:1, at:Date.now()-2*864e5},{r:0.5, at:Date.now()-864e5}];
startSession();                                             // 英译中，3 分钟
S.app.avgMs = 2000; S.app.msN = 20;
for(var _si=0;_si<6;_si++){ serveWord(WORDS[_si]); at(500); tap(true); }
finish();
t('速度榜记下本轮速率 每分钟2个', S.speed.length===3 && S.speed[0].r===2);
t('速度榜按速率降序', S.speed[0].r>=S.speed[1].r && S.speed[1].r>=S.speed[2].r);
t('结算页画出速度榜', document.querySelectorAll('#r-speed-list .spd-row').length===3);
t('榜上写的是每分钟', $('r-speed-list').textContent.indexOf('每分钟 2 个')>=0);
t('本轮那条被标出来', !!$('r-speed-list').querySelector('.spd-row.me'));

// 时长不同也能公平比：1 分钟答 6 个(6/分) 该压过 3 分钟答 12 个(4/分)
S.speed = [];
recordSpeed(12, 3);
recordSpeed(6, 1);
t('短时长高速度能压过长时长', S.speed[0].r===6 && S.speed[1].r===4);
t('速率带一位小数', (function(){ S.speed=[]; recordSpeed(10, 3); return S.speed[0].r===3.3; })());

S.speed = [];
['1','2','3','4','5'].forEach(function(v,i){ recordSpeed(+v, 1); });
recordSpeed(9, 1);
t('速度榜封顶 5 条', S.speed.length===5 && S.speed[0].r===9);

// 老格式（{n} 记答对数）读进来该被丢掉，不然口径混着比
var _ls = localStorage.getItem(KEY);
S.speed = [{r:9, at:Date.now()}]; save();
var _raw = JSON.parse(localStorage.getItem(KEY)); _raw.speed.push({n:999, at:Date.now()});
localStorage.setItem(KEY, JSON.stringify(_raw));
S = load();
t('老格式速度记录被丢弃', S.speed.length===1 && S.speed[0].r===9);
localStorage.setItem(KEY, _ls);

// 中译英不进速度榜
S = blank(); S.cfg.sfx = false; S.cfg.minutes = 3; S.app.todayDate = todayStr();
S.app.doneEn2cn = 1; S.app.cn2en = [WORDS[0].id, WORDS[1].id];
startSession('cn2en');
S.app.avgMs = 2000; S.app.msN = 20;
serveWord(WORDS[0]); at(500); tap(true);
finish();
t('中译英不进速度榜', !S.speed.length);
}catch(e){ t('速度榜段抛异常: ' + e.message, false); }

S = blank(); S.cfg.sfx = false; Q = null;   // 后面音效段别被残留的定时器搅和

// 设置里的「清空全部数据」：新加的悬案簿也得跟着清干净
S = blank(); S.cfg.sfx = false;
var uR = rec(WORDS[0].id); uR.wrong = 3; uR.solved = 2;
S.app.broken = 7; S.app.streak = 5; S.pet.name = '小奇';
advanceZoo(); advanceZoo(); advanceZoo(); save();   // 3 轮才解锁一只
t('清空前确实有东西', caseTotal()===1 && zooTotal()===1 && S.app.broken===7);
var _cf = window.confirm, _al = window.alert;
window.confirm = function(){ return true; }; window.alert = function(){};
$('btn-reset').click();
window.confirm = _cf; window.alert = _al;
t('清空后悬案簿归零', caseTotal()===0 && (S.app.broken||0)===0);
t('清空后图鉴归零', zooTotal()===0 && Object.keys(S.uw).length===0);
t('清空后连续天数归零', S.app.streak===0 && S.app.sessions===0);
t('清空后回到起名页', $('scr-name').classList.contains('on') && !S.pet.name);
t('清空后本地存档也没了', !localStorage.getItem(KEY));
t('清空后答题速度基线也归零', !S.app.avgMs && !S.app.msN);

/* ---------- 七、句子关（数据 / 题干 / 选项 / 奖励 / 蛋不动） ---------- */
// 真 SENTS 是注入脚本预挖好空的；通配词（show ... around 等）没进，运行时按 hasSent 滤掉
var SENTS0 = SENTS, WORDS0 = WORDS, speak0 = speak;
try{
  var sKeys = Object.keys(SENTS0);
  t('SENTS 有数据且每条都挖了空',
    sKeys.length > 500 && sKeys.every(function(k){ return SENTS0[k].indexOf('___') >= 0; }));
  t('通配词没进 SENTS', SENTS0['show ... around'] === undefined && SENTS0['put...in order'] === undefined);

  // 逻辑面装一个配得上假词库的假 SENTS（真 SENTS 的键是真词，对不上假词）
  var fw = [
    {id:'s1', word:'meat',  cn:'肉',    grade:3, phonetic:'/mi:t/', unit:1},
    {id:'s2', word:'milk',  cn:'牛奶',  grade:3, phonetic:'', unit:1},
    {id:'s3', word:'bread', cn:'面包',  grade:4, phonetic:'', unit:1},
    {id:'s4', word:'tall',  cn:'高的',  grade:4, phonetic:'', unit:1},
    {id:'s5', word:'show ... around', cn:'带参观', grade:4, phonetic:'', unit:1}
  ];
  WORDS = fw;
  SENTS = { meat:'I eat ___ for lunch.', milk:'I drink ___ every day.',
            bread:'The ___ is soft.', tall:'He is very ___.' };

  S = blank(); S.cfg.sfx = false;
  var sp = buildSentPool();
  t('句子关池子只收有句子的词', sp.length === 4 && sp.every(function(w){ return w.word !== 'show ... around'; }));

  // 出题：句子挖空、无音标、四个英文选项、正确项唯一、不自动朗读
  var spoken = [];
  speak = function(x){ spoken.push(x); };
  Q = newQ(); Q.dir = 'sent';
  serveWord(sp[0]);
  t('句子关方向标对', Q.dir === 'sent');
  t('题干是挖空的句子', $('q-word').textContent.indexOf('___') >= 0
    && $('q-word').textContent === SENTS[Q.cur.word.toLowerCase()]);
  t('题干不给音标', $('q-ph').textContent === '');
  t('出题不自动朗读（朗读=泄答案）', spoken.length === 0);
  var bs = document.querySelectorAll('#q-opts .opt');
  var labels = [].map.call(bs, function(b){ return b.textContent; });
  t('四个选项且不重复', bs.length === 4 && new Set(labels).size === 4);
  t('选项全是英文（无中文）', labels.every(function(x){ return !/[一-鿿]/.test(x); }));
  t('正确项唯一', labels.filter(function(x){ return x === Q.cur.word; }).length === 1);

  // 答对：线索 +1、不进中译英队列、答完才念一遍
  var c0 = S.app.todayClues;
  tap(true);
  t('答对线索 +1', S.app.todayClues === c0 + 1);
  t('句子关的词不进中译英队列', S.app.cn2en.length === 0);
  t('答完才念答案', spoken.length === 1);
  // 句子关答对念的是**整句**（把 ___ 填回那个词），不是孤零零一个词
  t('答对念整句', spoken[0] === SENTS[Q.cur.word.toLowerCase()].replace('___', Q.cur.word));
  t('念出来的整句没有空', spoken[0].indexOf('___') < 0);
  $('btn-speak').onclick();
  t('句子关「再听一遍」也念整句', spoken.length === 2 && spoken[1] === spoken[0]);

  // 答错：反馈不吐中文，把词填回整句
  serveWord(sp[1]);
  tap(false);
  var fb = $('q-fb').textContent;
  t('答错只念那个词、不念整句', spoken.length === 3 && spoken[2] === Q.cur.word);
  t('答错反馈不露中文词义', fb.indexOf(Q.cur.cn) < 0);
  t('答错反馈含填回整句', fb.indexOf(SENTS[Q.cur.word.toLowerCase()].replace('___', Q.cur.word)) >= 0);

  // 结算：记 doneSent，但不掺和蛋
  finish();
  t('句子关记 doneSent', S.app.doneSent === 1);
  t('句子关不碰两个方向完成标记', S.app.doneEn2cn === 0 && S.app.doneCn2en === 0);
  t('句子关不算两个方向', bothDirsDone() === false);
  t('句子关不推进蛋', zooStep().why === 'needEn2cn');

  // 分发：markDirDone('sent') 单独验一遍
  S = blank(); S.cfg.sfx = false;
  markDirDone('sent');
  t('markDirDone sent 不污染英译中', S.app.doneSent === 1 && S.app.doneEn2cn === 0 && S.app.doneCn2en === 0);
}catch(e){ t('句子关: '+e.message, false); }
speak = speak0; WORDS = WORDS0; SENTS = SENTS0;

/* ---------- 八、中译英（方向 / 队列 / 题干 / 不发音） ---------- */
// 先用真词库空跑一遍：138 个带空格的词、17 组同中文释义、有些词没音标，
// 这些只有真数据里才有，假词库造不出来
try{
  S = blank(); S.cfg.sfx = false;
  S.app.doneEn2cn = 1;
  S.app.cn2en = WORDS.slice(0, 60).map(function(w){ return w.id; });
  var rpool = buildCn2enPool();
  t('真词库中译英池子非空', rpool.length > 0);
  Q = { pool:rpool, i:0, total:rpool.length, dir:'cn2en', correct:0, wrong:0, combo:0, best:0,
        endAt: Date.now()+300000, total_ms:300000, locked:false, served:{}, shownAt:0 };
  var n = 0;
  while(Q && n < 60){
    if(Q.i >= Q.pool.length) break;
    nextQ();
    var bs0 = document.querySelectorAll('#q-opts .opt');
    if(bs0.length !== 4) throw new Error('第'+n+'题选项数='+bs0.length);
    var labels = [].map.call(bs0, function(b){ return b.textContent; });
    if(new Set(labels).size !== 4) throw new Error('第'+n+'题选项有重复: '+labels.join('/'));
    var ans = Q.cur;
    var hit = [].filter.call(bs0, function(b){ return b.textContent===ans.word; });
    if(hit.length !== 1) throw new Error('第'+n+'题正确项不唯一: '+ans.word+' in '+labels.join('/'));
    if(!$('q-word').textContent) throw new Error('第'+n+'题题干是空的');
    if($('q-ph').textContent !== '') throw new Error('第'+n+'题漏了音标');
    Q.locked = false; Q.shownAt = Date.now();
    answer(hit[0], n%3!==0, ans);
    Q.locked = false;
    n++;
  }
  t('真词库中译英连答 '+n+' 题无异常', n > 0);
}catch(e){ t('真词库中译英: '+e.message, false); }

// 这一段的假词库要撑得住"干扰项优先同年级同首字母"，所以每个年级都造一批同首字母的
var cw2=[];
[3,4].forEach(function(g){ for(var i=0;i<40;i++)
  cw2.push({id:'b'+g+'_'+i, word:'b'+g+i, cn:'蝙蝠'+g+'-'+i, grade:g, phonetic:'[b]', unit:1}); });
for(var i=0;i<40;i++) cw2.push({id:'z'+i, word:'zoo'+i, cn:'动物园'+i, grade:3, phonetic:'', unit:1});
cw2.push({id:'syn1', word:'dad',   cn:'爸爸',   grade:3, phonetic:'', unit:1});  // 同 cn 的一对
cw2.push({id:'syn2', word:'father',cn:'爸爸',   grade:4, phonetic:'', unit:1});
cw2.push({id:'poly', word:'apple', cn:'苹果；苹果树', grade:3, phonetic:'', unit:1});  // 多义
var REAL_WORDS = WORDS;
WORDS = cw2;

S = blank(); S.cfg.sfx = false;

// -- 方向页：没做英译中之前中译英是灰的 --
function dirPage(){ show('scr-dir'); }
dirPage();
t('方向页两张牌都在', !!$('btn-en2cn') && !!$('btn-cn2en'));
t('没做英译中时中译英是灰的', $('btn-cn2en').disabled===true);
t('英译中常开', $('btn-en2cn').disabled===false);
t('灰着的时候给了提示', $('dir-hint').textContent.indexOf('先刷一轮英译中')===0);

// -- 英译中：答对的进队列，答错的不进 --
var QE = function(){ Q = newQ(); Q.dir='en2cn'; };
QE(); serveWord(WORDS[0]); Q.shownAt = Date.now(); tap(true);
t('英译中答对 -> 进中译英队列', S.app.cn2en.length===1 && S.app.cn2en[0]===WORDS[0].id);
QE(); serveWord(WORDS[1]); Q.shownAt = Date.now(); tap(false);
t('英译中答错 -> 不进队列', S.app.cn2en.indexOf(WORDS[1].id)<0);
QE(); serveWord(WORDS[2]); Q.shownAt = Date.now(); tap(true);
t('再答对一个 -> 提到队首', S.app.cn2en[0]===WORDS[2].id && S.app.cn2en.length===2);
QE(); serveWord(WORDS[0]); Q.shownAt = Date.now(); tap(true);
t('队里已有的不会重复占位', S.app.cn2en.length===2 && S.app.cn2en[0]===WORDS[0].id);

// -- 跨天：队列留着，方向标记清掉 --
S.app.doneEn2cn = 1; S.app.doneCn2en = 1; S.app.todayDate = '2000-01-01';
var keep = S.app.cn2en.slice();
rollDay();
t('跨天不清中译英队列', JSON.stringify(S.app.cn2en)===JSON.stringify(keep) && keep.length>0);
t('跨天清掉方向标记', !S.app.doneEn2cn && !S.app.doneCn2en);
// 队列里混进一个已经不在词表里的 id（改词表才会出现）
S.app.cn2en.push('已经不存在的词'); S.app.todayDate = '2000-01-01';
rollDay();
t('跨天顺手剔掉失效的词', S.app.cn2en.indexOf('已经不存在的词')<0 && S.app.cn2en.length===keep.length);

// -- 题干：中文、不给音标、不自动发音、「再听一遍」按不了 --
var spok=[], _speak=speak;
speak = function(w){ spok.push(w); };
S.app.doneEn2cn = 1;
Q = newQ(); Q.dir='cn2en'; S.app.cn2en = [WORDS[0].id, WORDS[1].id];
Q.pool = [WORDS[0], WORDS[1]]; Q.i = 0; Q.total = 2;
spok = []; nextQ();
t('中译英题干是中文', $('q-word').textContent===WORDS[0].cn);
t('中译英不给音标', $('q-ph').textContent==='');
t('中译英不自动发音', spok.length===0);
t('中译英答题时「再听一遍」按不了', $('btn-speak').disabled===true);
t('中译英选项是英文', [].every.call(document.querySelectorAll('#q-opts .opt'),
  function(b){ return WORDS.some(function(x){ return x.word===b.textContent; }); }));

// -- 干扰项：不跟答案同 cn、不同拼写，且优先同年级同首字母 --
Q.locked = false; tap(true);
t('答完就恢复发音', spok.length===1);
t('答完「再听一遍」解禁', $('btn-speak').disabled===false);
t('考到就出队', S.app.cn2en.indexOf(WORDS[0].id)<0);
var bs = document.querySelectorAll('#q-opts .opt');
var right = [].filter.call(bs, function(b){ return b.textContent===WORDS[0].word; })[0];
var dis = [].filter.call(bs, function(b){ return b!==right; });
t('中译英干扰项不跟答案同拼写', dis.every(function(b){ return b.textContent!==WORDS[0].word; }));
t('中译英干扰项都跟答案同首字母（形近）',
  dis.every(function(b){ return b.textContent.charAt(0)===WORDS[0].word.charAt(0); }));
t('中译英干扰项都跟答案同年级',
  dis.every(function(b){ return WORDS.filter(function(x){return x.word===b.textContent;})[0].grade===WORDS[0].grade; }));

// 同 cn 的那 17 组：俩词绝不能同时出现在一道题里（两个都"对"）
var synId = ['syn1','syn2'];
S.app.cn2en = synId.slice(); S.app.doneEn2cn = 1;
for(var k=0;k<30;k++){
  Q = newQ(); Q.dir='cn2en'; Q.pool=[WORDS.filter(function(x){return x.id==='syn1';})[0]];
  Q.i=0; Q.total=1; nextQ();
  var bs2 = document.querySelectorAll('#q-opts .opt');
  t('同义词不出现在同一题的选项里', [].every.call(bs2, function(b){ return b.textContent!=='father'; }));
  Q.locked=false; tap(true);
  break;   // 造一次就够，剩下的是同一段代码
}

// -- 多义释义只取第一个义项 --
S.app.cn2en = ['poly'];
Q = newQ(); Q.dir='cn2en'; Q.pool=[WORDS.filter(function(x){return x.id==='poly';})[0]];
Q.i=0; Q.total=1; nextQ();
t('多义释义只取第一个', $('q-word').textContent==='苹果' && $('q-word').textContent.indexOf('；')<0);
Q.locked=false; tap(true);

// -- 池子：队列 + 送分题，只铺一次，不补池 --
S.app.cn2en = WORDS.slice(0,3).map(function(w){ return w.id; });
var inQueue = {}; S.app.cn2en.forEach(function(id){ inQueue[id]=1; });
var giftN = WORDS.filter(function(w){
  var u = S.uw[w.id]; return u && u.stage>=EASY_STAGE && !inQueue[w.id];
}).length;
var cpool = buildCn2enPool();
t('中译英池子 = 队列 + 送分题', cpool.length === 3 + Math.min(10, giftN));
t('中译英池子不重复',
  cpool.length===Object.keys(cpool.reduce(function(m,w){m[w.id]=1;return m;},{})).length);
t('中译英池子只有队列和答熟了的词', cpool.every(function(w){
  var u = S.uw[w.id];
  return inQueue[w.id] || (u && u.stage>=EASY_STAGE); }));
Q = { pool:[], i:0, total:0, dir:'cn2en', correct:0, wrong:0, combo:0, best:0,
      endAt: Date.now()+300000, total_ms:300000, locked:false, served:{}, shownAt:0 };
Q.pool = [WORDS[0]]; Q.i = 0; Q.total = 1;
nextQ(); Q.locked = false; tap(true);
advance();                                   // 结算页的 setTimeout 在同步测试里不会自己跑
t('中译英刷完池子就结算（不补池）', Q===null);
t('中译英也走结算页', $('scr-result').classList.contains('on'));
t('中译英做完就算这个方向完成', S.app.doneCn2en===1);

// -- 蛋：两轮都做完才长一步，一天只长一次 --
S = blank(); S.cfg.sfx = false;
S.app.todayDate = todayStr();
S.app.cn2en = [WORDS[0].id];                 // 队列得有存货，不然"池空也算完成"会提前放行
S.app.doneEn2cn = 0; S.app.doneCn2en = 0;
t('一个方向都没做 -> 蛋不动', (function(){ var z=zooStep(); return !z.adv && z.why==='needEn2cn'; })());
S.app.doneEn2cn = 1;
t('只做完英译中 -> 蛋不动', (function(){ var z=zooStep(); return !z.adv && z.why==='needCn2en'; })());
S.app.doneCn2en = 1;
var st1 = zooStep();
t('两个方向都做完 -> 长一步', !!st1.adv && st1.adv.step===1);
t('长完之后当天不再长', (function(){ var z=zooStep(); return !z.adv && z.why==='today'; })());
t('同一轮里重复调用不会再长', zState(activeSeries()).step===1);

// 池子空也算中译英完成（英译中一个都没答对，中译英压根没东西可考）
S = blank(); S.cfg.sfx = false;
S.app.todayDate = todayStr();
S.app.doneEn2cn = 1; S.app.cn2en = []; S.app.doneCn2en = 0;
t('中译英池子空也算完成', bothDirsDone()===true);
t('池空时照样长一步', (function(){ var z=zooStep(); return !!z.adv && z.adv.step===1; })());
t('池空时方向页给中译英打勾',
  (function(){ show('scr-dir'); return $('dir-d2').textContent.indexOf('✓')>=0; })());
t('池空时中译英那张牌还是灰的（没东西可考）', $('btn-cn2en').disabled===true);
t('做完一轮后方向页给英译中打勾',
  (function(){ show('scr-dir'); return $('dir-d1').textContent.indexOf('✓')>=0; })());

// -- ✕ 退出算完成这一轮，但挑战 / 集中练不推进 --
S = blank(); S.cfg.sfx = false;
S.app.todayDate = todayStr();
S.app.doneEn2cn = 1;
S.app.cn2en = WORDS.slice(0,5).map(function(w){ return w.id; });
show('scr-dir');
t('做完英译中之后中译英解禁', $('btn-cn2en').disabled===false);
$('btn-cn2en').onclick();
t('从方向页能进中译英', !!Q && Q.dir==='cn2en');
var stepBefore = zState(activeSeries()).step;
nextQ(); Q.shownAt = Date.now(); tap(true);
window.confirm = function(){ return true; };
$('btn-quit').onclick();
t('✕ 退出算做完这个方向', S.app.doneCn2en===1);
t('✕ 退出也不白走（英译中做过了，蛋照长）', zState(activeSeries()).step===stepBefore+1);
t('✕ 退出回首页', $('scr-home').classList.contains('on'));

Q = null;                  // 把挂着的 advance 定时器变成空操作，后面的断言不受影响
WORDS = REAL_WORDS;
S.cfg.sfx = false;

/* ---------- 九、音效 ---------- */
S = blank();
S.cfg.sfx = false;
t('关掉音效就不建 AudioContext', ac()===null);
S.cfg.sfx = true;
try{
  sfxRight(); sfxCombo(1); sfxCombo(3); sfxCombo(6); sfxStable();
  t('音效函数都不抛', true);
}catch(e){ t('音效函数都不抛: '+e.message, false); }
S.cfg.sfx = false;   // 后面的断言别再出声

// 离线把音频真渲染出来量峰值。削顶了听着刺耳，但耳朵分不出是"削顶"还是"就该这么响"
// ——这个只能量。峰值太高＝几个振荡器叠爆了，太低＝等于没响
function setTitle(){
  document.title = 'TESTRESULT ' + log.join(' | ') + ' ERR:' + err.join(';');
}
setTitle();
try{
  S.cfg.sfx = true;
  var OFF = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, 44100 * 3, 44100);
  var _ac = ac; ac = function(){ return OFF; };
  sfxRight(); sfxCombo(6); sfxStable();
  ac = _ac; S.cfg.sfx = false;
  OFF.startRendering().then(function(buf){
    var d = buf.getChannelData(0), peak = 0, sq = 0;
    for(var i = 0; i < d.length; i++){
      var v = Math.abs(d[i]); if(v > peak) peak = v; sq += d[i] * d[i];
    }
    var rms = Math.sqrt(sq / d.length);
    t('音效峰值不削顶 (peak=' + peak.toFixed(2) + ' rms=' + rms.toFixed(3) + ')',
      peak > .05 && peak <= 1);
    setTitle();
  });
}catch(e){ t('离线渲染音效: ' + e.message, false); setTitle(); }
</script>
"""

BASE = pathlib.Path(__file__).parent
html = (BASE / "index.html").read_text(encoding="utf-8")
(BASE / "_test.html").write_text(html.replace("</body>", TEST + "</body>"), encoding="utf-8")
print("wrote _test.html")
