# 生成主屏幕图标。产出 icon-512.png / icon-180.png
# 两个坑（都踩过）：
#   1. 布局必须用显式 px —— 百分比尺寸在无头 Edge 的小窗口下画不出来
#   2. 狐狸没填满 viewBox（尾巴撑到右边缘、重心偏左），直接按 82% 摆会显得很小，
#      所以按内容包围盒换算缩放和偏移
import pathlib, subprocess

BASE = pathlib.Path(__file__).parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
html = (BASE / "index.html").read_text(encoding="utf-8")

VB_W, VB_H = 200, 210          # viewBox 尺寸
BX0, BX1, BY0, BY1 = 56, 200, 28, 190   # 狐狸实际占的包围盒（viewBox 坐标）
FILL = 0.88                    # 狐狸占画布的比例

def layout(size):
    sc = size * FILL / max(BX1 - BX0, BY1 - BY0)
    return {
        "S": size,
        "W": round(VB_W * sc), "H": round(VB_H * sc),
        "L": round(size / 2 - (BX0 + BX1) / 2 * sc),
        "T": round(size / 2 - (BY0 + BY1) / 2 * sc),
    }

TPL = """
var s = foxSVG(2);
document.body.innerHTML =
  '<div style="position:fixed;left:0;top:0;width:%(S)dpx;height:%(S)dpx;' +
  'background:radial-gradient(88%% 68%% at 50%% 36%%,#22365a,#0a1120 74%%)"></div>' +
  '<div style="position:fixed;left:%(L)dpx;top:%(T)dpx;width:%(W)dpx;height:%(H)dpx">' + s + '</div>';
"""

def build(size, name):
    page = BASE / "_icon.html"
    page.write_text(html.replace("</body>", "<script>" + (TPL % layout(size)) + "</script>\n</body>"),
                    encoding="utf-8")
    out = BASE / name
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--virtual-time-budget=2000",
                    "--user-data-dir=" + str(BASE / "_edgeprof"),
                    "--window-size=%d,%d" % (size, size),
                    "--screenshot=" + str(out), page.as_uri()],
                   capture_output=True, timeout=90)
    page.unlink(missing_ok=True)
    return out.exists()

print("icon-512.png", build(512, "icon-512.png"))
print("icon-180.png", build(180, "icon-180.png"))
