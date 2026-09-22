# ponytail: 一次性样张脚本，悬案簿样式定了就删
import pathlib, subprocess

BASE = pathlib.Path(r"E:\Cowork\Claude\kid-vocab")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
html = (BASE / "index.html").read_text(encoding="utf-8")

MOCK = r"""
// 每件悬案：词 + 破案进度（连续答对几次）
function caseRow(word, cn, dots, note, kind){
  var col = kind === 'fuzzy' ? 'var(--muted)' : 'var(--bad)';
  var s = '';
  for(var i=0;i<3;i++){
    s += '<i style="display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px;'+
         'background:'+(i<dots?col:'transparent')+';border:1.5px solid '+col+'"></i>';
  }
  return '<div style="background:var(--card);border:1px solid var(--line);border-radius:16px;'+
    'padding:12px 14px;margin-bottom:9px">'+
    '<div style="display:flex;align-items:baseline;gap:10px">'+
      '<b style="font-size:16.5px">'+word+'</b>'+
      '<span style="color:var(--muted);font-size:13.5px">'+cn+'</span>'+
    '</div>'+
    '<div style="margin-top:7px;display:flex;align-items:center;gap:9px">'+
      '<span>'+s+'</span>'+
      '<span style="color:var(--muted);font-size:11.5px">'+note+'</span>'+
    '</div></div>';
}
function panel(label, body){
  return '<div style="width:352px;flex:0 0 auto">'+
    '<div style="color:var(--muted);font-size:12px;font-weight:700;margin-bottom:9px;'+
    'letter-spacing:.5px">'+label+'</div>'+
    '<div style="background:radial-gradient(120% 70% at 50% 0%,var(--night2),var(--night) 70%);'+
    'border:1px solid var(--line);border-radius:26px;padding:18px 16px 22px;min-height:640px">'+
    body+'</div></div>';
}

var HOME =
  '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">'+
    '<b style="font-size:20px">小奇的侦探事务所</b><span style="font-size:19px">🔧</span></div>'+
  '<div style="display:flex;gap:8px;margin-bottom:14px">'+
    ['今日线索 14','连续天数 5','稳固词 23'].map(function(t,i){
      var n=t.split(' ')[1], l=t.split(' ')[0];
      return '<div style="flex:1;background:var(--card);border:1px solid var(--line);'+
        'border-radius:16px;padding:11px 4px;text-align:center">'+
        '<div style="font-size:21px;font-weight:800;color:'+(i===0?'var(--fox)':i===2?'var(--ok)':'var(--ink)')+'">'+n+'</div>'+
        '<div style="font-size:11.5px;color:var(--muted);margin-top:2px">'+l+'</div></div>';
    }).join('')+'</div>'+
  '<div style="background:var(--card);border:1px solid var(--line);border-radius:22px;'+
  'padding:16px;text-align:center;margin-bottom:12px">'+
    '<div style="height:150px;display:flex;align-items:center;justify-content:center">'+foxSVG(3)+'</div>'+
    '<div style="color:var(--muted);font-size:12.5px;margin-top:6px">正在调查 · 鸟类 3/12</div>'+
    '<div style="font-weight:800;font-size:17px;margin-top:3px">？？？</div></div>'+
  '<div style="background:var(--card);border:1px solid var(--line);border-radius:18px;'+
  'padding:13px 15px;display:flex;align-items:center;gap:12px;margin-bottom:14px">'+
    '<div style="width:40px;height:40px">'+foxSVG(1)+'</div>'+
    '<div><b style="font-size:15px">小奇</b> <i style="color:var(--muted);font-size:12px;font-style:normal">幼狐</i>'+
    '<div style="color:var(--muted);font-size:12.5px;margin-top:2px">今天线索不错，继续！</div></div></div>'+
  '<div style="background:linear-gradient(135deg,var(--fox),var(--fox-d));color:#fff;'+
  'border-radius:18px;padding:17px;text-align:center;font-weight:800;font-size:17px;'+
  'box-shadow:0 10px 24px rgba(232,99,26,.32);margin-bottom:10px">开始查案 · 3 分钟</div>'+
  '<div style="border:1px solid var(--line);border-radius:18px;padding:15px;text-align:center;'+
  'color:var(--muted);font-size:15px;font-weight:700;margin-bottom:10px">📖 动物图鉴 · 7/60</div>'+
  '<div style="border:1px solid var(--line);border-radius:18px;padding:15px;text-align:center;'+
  'color:var(--muted);font-size:15px;font-weight:700;position:relative">'+
  '🗂 悬案簿 · 5 件'+
  '<span style="position:absolute;top:-7px;right:14px;background:var(--bad);color:#fff;'+
  'font-size:11px;font-weight:800;border-radius:99px;padding:2px 8px">3 件有眉目</span></div>';

var CASES =
  '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">'+
    '<b style="font-size:20px">悬案簿</b><span style="font-size:19px;color:var(--muted)">←</span></div>'+
  '<div style="display:flex;gap:9px;margin-bottom:15px">'+
    '<div style="flex:1;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px;text-align:center">'+
      '<div style="font-size:23px;font-weight:800;color:var(--ok)">18</div>'+
      '<div style="font-size:11.5px;color:var(--muted);margin-top:2px">已破的案子</div></div>'+
    '<div style="flex:1;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px;text-align:center">'+
      '<div style="font-size:23px;font-weight:800;color:var(--bad)">5</div>'+
      '<div style="font-size:11.5px;color:var(--muted);margin-top:2px">还没破的</div></div></div>'+
  '<div style="background:var(--card2);border:1px solid var(--gold);border-radius:18px;padding:14px 15px;margin-bottom:17px">'+
    '<div style="font-weight:800;font-size:14.5px">🔍 3 件案子有眉目了</div>'+
    '<div style="color:var(--muted);font-size:12.5px;margin:4px 0 11px;line-height:1.55">'+
    '这几件你都答对过两次了，结成一批一次结了它们</div>'+
    '<div style="background:linear-gradient(135deg,var(--fox),var(--fox-d));color:#fff;'+
    'border-radius:14px;padding:12px;text-align:center;font-weight:800;font-size:14.5px">挑战这 3 件 →</div></div>'+
  '<div style="font-size:13px;font-weight:800;color:var(--bad);margin:0 0 9px">假线索 · 2 件</div>'+
  caseRow('hobby','业余爱好',2,'再答对 1 次就破案')+
  caseRow('paint','用颜料画',0,'栽了 2 次')+
  '<div style="font-size:13px;font-weight:800;color:var(--muted);margin:16px 0 9px">存疑 · 1 件</div>'+
  caseRow('join','成为……的一员',0,'上次答对了，可是想了很久','fuzzy')+
  '<div style="color:var(--muted);font-size:11.5px;text-align:center;margin-top:16px;line-height:1.7">'+
  '连续答对 3 次才算破案<br>答错一次从头数</div>';

document.body.innerHTML =
 '<div style="padding:26px 24px;font-family:system-ui;display:flex;gap:26px;align-items:flex-start">'+
 panel('① 首页 · 新加的入口', HOME) +
 panel('② 悬案簿', CASES) +
 '</div>';
"""

out = html.replace("</body>", "<script>\n" + MOCK + "\n</script>\n</body>")
p = BASE / "_mock_tmp.html"
p.write_text(out, encoding="utf-8")

png = BASE / "预览图" / "12_悬案簿样张.png"
subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--virtual-time-budget=9000",
                "--user-data-dir=" + str(BASE / "_edgeprof"),
                "--window-size=800,830", "--screenshot=" + str(png), p.as_uri()],
               capture_output=True, timeout=90)
print(("OK  " if png.exists() else "FAIL"), png.name)
p.unlink(missing_ok=True)
