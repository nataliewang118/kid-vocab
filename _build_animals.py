# 把动物图鉴数据灌进 index.html 的 ZOO / SERIES 常量。
# 加一个动物 = 加一个 ZOO_ANIMALS 条目（含 body 里的 SVG）再跑这个脚本。
#
# 动物按**系列**分组（鸟类 / 海洋 / 昆虫 / 爬行 / 哺乳动物…），每系列在图鉴里
# 有自己的页签和 0/N 进度，她点哪个页签就查哪个系列。
#
# 每个动物 3 条小知识，对应 3 个阶段：第一步 / 幼年 / 成年。
#
# ⚠️ 写小知识的规矩：**前两条绝对不能出现动物名字或它的招牌特征名称**，
# 只能给线索，让她自己猜。名字要到"成年"那一条才公布。
# 线索要一层比一层明显：第一步 → 幼年 → 成年（成年那条可以点破）。
#
# 事实我只写有把握的，拿不准的加"有的"限定（比如章鱼背贝壳只有部分种类会）。
import json, io, re, pathlib, sys

# ---------- 系列 ----------
# entry / hatch 是这一系列前两步的台词。卵生的用默认（蛋），
# 胎生的（哺乳动物）自己写开场——它们不下蛋，对不上"侦查到一颗蛋"。
# 单个动物可以用 entry_label / hatch_label 覆盖，写得更贴它自己。
SERIES = [
    {"id": "bird",   "cn": "鸟类",
     "entry": "侦查到一颗蛋",       "hatch": "蛋里孵出了小家伙"},
    {"id": "sea",    "cn": "海洋",
     "entry": "海底捡到一颗蛋",     "hatch": "蛋里孵出了小家伙"},
    {"id": "bug",    "cn": "昆虫",
     "entry": "叶片背面找到一颗卵", "hatch": "卵里钻出了小家伙"},
    {"id": "rept",   "cn": "爬行",
     "entry": "沙土里挖到一窝蛋",   "hatch": "蛋里孵出了小家伙"},
    # 哺乳动物照做，但开场不是蛋——它们胎生，第一步是她先发现的痕迹
    {"id": "mammal", "cn": "哺乳动物",
     "entry": "发现一串脚印",       "hatch": "窝里探出个小脑袋"},
]

# ---------- 通用蛋壳 ----------
# 200x210 的 viewBox 里，蛋占中间偏下；tint 是蛋壳底色，dark 是斑点色
EGG = ('<ellipse cx="100" cy="122" rx="56" ry="70" fill="{tint}"/>'
       '<ellipse cx="100" cy="122" rx="56" ry="70" fill="none" stroke="{dark}" stroke-width="3"/>'
       '<ellipse cx="78" cy="96" rx="9" ry="12" fill="{dark}" opacity=".55"/>'
       '<ellipse cx="122" cy="140" rx="11" ry="14" fill="{dark}" opacity=".55"/>'
       '<ellipse cx="112" cy="80" rx="7" ry="9" fill="{dark}" opacity=".45"/>'
       '<ellipse cx="82" cy="160" rx="8" ry="10" fill="{dark}" opacity=".45"/>')

# ---------- 通用脚印 ----------
# 哺乳动物不下蛋，"第一步"画一串脚印。tint 是掌垫色，dark 是轮廓色。
# 前后错开两枚，看着像走过一道路；爪尖用 dark 点出来。
PAW = ('<g transform="translate(0,26) rotate(-14 100 130)">'
       '<ellipse cx="100" cy="132" rx="34" ry="28" fill="{tint}"/>'
       '<ellipse cx="100" cy="132" rx="34" ry="28" fill="none" stroke="{dark}" stroke-width="3"/>'
       + "".join('<ellipse cx="%d" cy="%d" rx="9.5" ry="12" fill="{tint}"'
                 ' stroke="{dark}" stroke-width="2.5"/>' % p
                 for p in [(70,92), (92,80), (116,80), (138,92)])
       + '</g>'
       '<g transform="translate(-4,16) scale(.58)" opacity=".9">'
       '<ellipse cx="100" cy="132" rx="34" ry="28" fill="{tint}"/>'
       '<ellipse cx="100" cy="132" rx="34" ry="28" fill="none" stroke="{dark}" stroke-width="4"/>'
       + "".join('<ellipse cx="%d" cy="%d" rx="9.5" ry="12" fill="{tint}"'
                 ' stroke="{dark}" stroke-width="4"/>' % p
                 for p in [(70,92), (92,80), (116,80), (138,92)])
       + '</g>')

ZOO_ANIMALS = [
# ============================ 鸟类 ============================
{
  "id": "owl", "cn": "猫头鹰", "en": "Owl", "series": "bird",
  "tint": "#c9a86a", "dark": "#8a6c34",
  "skill": "无声飞行 · 听声定位",
  "facts": [
    "线索一：这颗蛋是白色的椭圆形，一窝有两到五颗。它的妈妈不筑巢，把蛋直接下在树洞里。",
    "线索二：小家伙一身白色绒毛，眼睛还睁不开，要过一星期才睁眼。它爸妈的羽毛边缘像梳子的齿，飞起来几乎没有声音。",
    "线索三：它两只耳朵的高低不一样，靠这个听出猎物的精确位置。白天眯着眼打盹，夜里才出门。它叫猫头鹰。",
  ],
  "body": (
    '<ellipse cx="100" cy="128" rx="58" ry="62" fill="#c9a86a"/>'
    '<ellipse cx="100" cy="144" rx="36" ry="42" fill="#f0e0bc"/>'
    '<path d="M56 84 L46 44 L84 66 Z" fill="#a8863f"/>'
    '<path d="M144 84 L154 44 L116 66 Z" fill="#a8863f"/>'
    '<path d="M44 120 C32 150 40 178 58 188 C50 162 48 140 52 120 Z" fill="#a8863f"/>'
    '<path d="M156 120 C168 150 160 178 142 188 C150 162 152 140 148 120 Z" fill="#a8863f"/>'
    '<circle cx="76" cy="106" r="27" fill="#f9f0da"/>'
    '<circle cx="124" cy="106" r="27" fill="#f9f0da"/>'
    '<circle cx="76" cy="106" r="13" fill="#2a2018"/>'
    '<circle cx="124" cy="106" r="13" fill="#2a2018"/>'
    '<circle cx="80" cy="101" r="4.5" fill="#fff"/>'
    '<circle cx="128" cy="101" r="4.5" fill="#fff"/>'
    '<path d="M100 118 L90 133 L110 133 Z" fill="#e8a13c"/>'
    '<path d="M84 188 l-8 11 M84 188 l0 12 M84 188 l8 11" stroke="#e8a13c" stroke-width="5" stroke-linecap="round" fill="none"/>'
    '<path d="M116 188 l-8 11 M116 188 l0 12 M116 188 l8 11" stroke="#e8a13c" stroke-width="5" stroke-linecap="round" fill="none"/>'
  ),
},
{
  "id": "penguin", "cn": "企鹅", "en": "Penguin", "series": "bird",
  "tint": "#9db4c4", "dark": "#4a6274",
  "skill": "叫声认亲 · 太阳导航",
  "facts": [
    "线索一：这颗蛋只有一颗，在南极的冬天出生。它没放在窝里，而是被放在爸爸的脚背上，用肚子下面那层皮盖着保暖。",
    "线索二：爸爸连续约两个月不吃东西，就站着守着它。小家伙出来时爸爸已经瘦了一大圈。它一身灰色绒毛，还不能下水。",
    "线索三：几万只挤在一起，每一只都靠独一无二的叫声找到自己的孩子。它们在暴风雪里也能靠太阳的位置认路。它叫企鹅。",
  ],
  "body": (
    '<ellipse cx="100" cy="132" rx="56" ry="66" fill="#2f4254"/>'
    '<ellipse cx="100" cy="144" rx="40" ry="52" fill="#f7f3ea"/>'
    '<ellipse cx="46" cy="150" rx="14" ry="34" fill="#26374a" transform="rotate(14 46 150)"/>'
    '<ellipse cx="154" cy="150" rx="14" ry="34" fill="#26374a" transform="rotate(-14 154 150)"/>'
    '<circle cx="76" cy="92" r="15" fill="#fff"/>'
    '<circle cx="124" cy="92" r="15" fill="#fff"/>'
    '<circle cx="77" cy="93" r="8" fill="#1c2836"/>'
    '<circle cx="125" cy="93" r="8" fill="#1c2836"/>'
    '<circle cx="80" cy="89" r="3" fill="#fff"/>'
    '<circle cx="128" cy="89" r="3" fill="#fff"/>'
    '<path d="M100 104 L88 116 L112 116 Z" fill="#f0a63c"/>'
    '<ellipse cx="70" cy="192" rx="20" ry="9" fill="#f0a63c"/>'
    '<ellipse cx="130" cy="192" rx="20" ry="9" fill="#f0a63c"/>'
  ),
},
{
  "id": "hummingbird", "cn": "蜂鸟", "en": "Hummingbird", "series": "bird",
  "tint": "#5fbfa4", "dark": "#2f7a68",
  "skill": "唯一能倒着飞 · 心跳上千",
  "facts": [
    "线索一：这是世界上最小的蛋，比一颗咖啡豆还小，只有两粒米那么重。它们的妈妈用蜘蛛丝和苔藓把窝粘在树枝上，窝只有半个核桃大。",
    "线索二：小家伙刚出壳时只有一只蜜蜂那么大，嘴巴短短的。等它长大，嘴巴会长得比整个脑袋还长。",
    "线索三：它是唯一能倒着飞、还能原地停住不动的鸟。翅膀每秒扇五十多下，心跳每分钟上千次，一天要吃下比自己还重的花蜜。它叫蜂鸟。",
  ],
  "body": (
    '<ellipse cx="78" cy="72" rx="26" ry="12" fill="#b8e6d6" opacity=".55" transform="rotate(-40 78 72)"/>'
    '<ellipse cx="122" cy="68" rx="24" ry="11" fill="#b8e6d6" opacity=".55" transform="rotate(30 122 68)"/>'
    '<path d="M88 168 L48 200 L78 204 Z" fill="#3f8f7a"/>'
    '<ellipse cx="104" cy="134" rx="40" ry="46" fill="#5fbfa4"/>'
    '<ellipse cx="106" cy="148" rx="24" ry="28" fill="#eafaf3"/>'
    '<circle cx="110" cy="86" r="30" fill="#5fbfa4"/>'
    # 细长喙：纯深色在深色底上看不见，描一圈浅边才立得住
    '<path d="M138 78 L190 100 L138 92 Z" fill="#3a4a58" stroke="#8fa3c4" stroke-width="1.6"/>'
    '<circle cx="120" cy="80" r="9" fill="#fff"/>'
    '<circle cx="123" cy="81" r="5" fill="#22303a"/>'
    '<circle cx="125" cy="79" r="1.8" fill="#fff"/>'
  ),
},
{
  "id": "woodpecker", "cn": "啄木鸟", "en": "Woodpecker", "series": "bird",
  "tint": "#b8574f", "dark": "#6e2f2a",
  "skill": "每秒凿二十下 · 自带减震",
  "facts": [
    "线索一：这些蛋下在树干上凿出来的洞里，一窝四到五颗，全是白色的。洞口朝着斜下方，雨水流不进去。",
    "线索二：小家伙在这个洞里长到羽毛齐全才出来。它的舌头特别长，平时收在脑袋后面绕一圈，用的时候才弹出去。",
    "线索三：它每秒能在木头上凿二十下，脑袋却不会疼——骨头里有海绵一样的减震结构。它敲木头找虫子，也靠敲击声告诉同伴这块地是它的。它叫啄木鸟。",
  ],
  "body": (
    '<rect x="158" y="-8" width="56" height="226" rx="14" fill="#6b4a2f"/>'
    '<path d="M166 30 h40 M166 78 h40 M166 126 h40 M166 174 h40" stroke="#54371f" stroke-width="3" opacity=".45"/>'
    '<path d="M74 198 L156 204 L150 178 Z" fill="#33393e"/>'
    '<ellipse cx="92" cy="140" rx="44" ry="50" fill="#f2f2ee"/>'
    '<path d="M50 120 C72 134 114 134 136 120 L136 136 C114 150 72 150 50 136 Z" fill="#33393e"/>'
    '<ellipse cx="108" cy="138" rx="30" ry="42" fill="#3f464c"/>'
    '<circle cx="96" cy="80" r="33" fill="#f2f2ee"/>'
    '<path d="M63 80 A33 33 0 0 1 129 80 Z" fill="#d0433a"/>'
    '<circle cx="110" cy="86" r="10" fill="#fff"/>'
    '<circle cx="113" cy="87" r="5.5" fill="#22303a"/>'
    '<circle cx="115" cy="85" r="2" fill="#fff"/>'
    # 喙要浅色：深色压在树干上也看不见
    '<path d="M126 78 L160 88 L126 96 Z" fill="#dfe4e8"/>'
  ),
},
{
  "id": "flamingo", "cn": "火烈鸟", "en": "Flamingo", "series": "bird",
  "tint": "#f2a0bc", "dark": "#b3607f",
  "skill": "粉色是吃出来的 · 单腿睡觉",
  "facts": [
    "线索一：这颗蛋是白色的，一窝只有一颗。它不放在窝里，而是堆在泥巴做的小土墩上，高到不会被水泡着。",
    "线索二：小家伙出壳时是灰白色的，一点都不粉。它会一直待在爸爸妈妈中间，一待就是好几个月，吃的是爸妈嘴里吐出来的红色糊糊。",
    "线索三：它长大以后是粉红色的，但这颜色不是天生的——是吃的小虾和藻类里的色素染上去的。它常常单腿站着睡觉，那样更省力。它叫火烈鸟。",
  ],
  "body": (
    '<ellipse cx="84" cy="140" rx="52" ry="38" fill="#f2a0bc"/>'
    '<ellipse cx="78" cy="152" rx="32" ry="22" fill="#fce0ea"/>'
    '<path d="M118 132 C154 128 168 100 156 74 C148 54 124 46 114 60 C108 70 118 82 130 78"'
    ' stroke="#f2a0bc" stroke-width="19" fill="none" stroke-linecap="round"/>'
    '<circle cx="122" cy="60" r="21" fill="#f2a0bc"/>'
    '<path d="M102 64 C94 68 86 76 88 84 C94 82 102 76 106 70 Z" fill="#f2a0bc"/>'
    '<path d="M138 60 L188 78 L138 80 Z" fill="#f8f2e8"/>'
    '<path d="M138 80 L188 78 L182 90 L138 86 Z" fill="#2f3438"/>'
    '<circle cx="128" cy="56" r="7" fill="#fff"/>'
    '<circle cx="130" cy="57" r="4" fill="#3a2a30"/>'
    '<path d="M66 174 L62 204" stroke="#e88fa8" stroke-width="6" stroke-linecap="round"/>'
    '<path d="M62 204 L50 208 M62 204 L74 208" stroke="#e88fa8" stroke-width="5" stroke-linecap="round"/>'
    '<path d="M104 174 L120 178 L114 190" stroke="#e88fa8" stroke-width="6" stroke-linecap="round" fill="none"/>'
  ),
},
{
  "id": "kingfisher", "cn": "翠鸟", "en": "Kingfisher", "series": "bird",
  "tint": "#4a9fe0", "dark": "#2a5a8c",
  "skill": "入水不溅 · 蓝色是光折出来的",
  "facts": [
    "线索一：这些蛋下在河岸边挖的洞里，洞口只有拳头大，里面却挖进半米多深。洞里垫的全是鱼骨头。",
    "线索二：小家伙出壳时眼睛还没睁开，两周后就开始张着大嘴要吃的，一天要吃十几条小鱼。",
    "线索三：它从树枝上一头扎进水里抓鱼，入水时几乎不溅起水花。它身上的蓝色其实是光折射出来的，不是羽毛本身的颜色。它叫翠鸟。",
  ],
  "body": (
    '<path d="M76 184 L36 204 L70 208 Z" fill="#2f6fb0"/>'
    '<ellipse cx="98" cy="140" rx="44" ry="48" fill="#4a9fe0"/>'
    '<ellipse cx="100" cy="154" rx="28" ry="30" fill="#f0a45c"/>'
    '<path d="M58 118 C40 140 44 170 64 178 C50 158 54 134 70 126 Z" fill="#3a86c8"/>'
    '<circle cx="104" cy="88" r="34" fill="#4a9fe0"/>'
    '<path d="M70 88 A34 34 0 0 1 138 88 Z" fill="#2f6fb0"/>'
    '<path d="M132 84 L190 102 L132 98 Z" fill="#3a4a58" stroke="#8fa3c4" stroke-width="1.6"/>'
    '<circle cx="116" cy="86" r="9" fill="#fff"/>'
    '<circle cx="119" cy="87" r="5" fill="#22303a"/>'
    '<circle cx="121" cy="85" r="1.8" fill="#fff"/>'
    '<path d="M90 186 l-6 14 M108 186 l0 14" stroke="#e8734a" stroke-width="5" stroke-linecap="round"/>'
  ),
},
{
  "id": "peacock", "cn": "孔雀", "en": "Peacock", "series": "bird",
  "tint": "#2f8f9a", "dark": "#1d5f6b",
  "skill": "一百多根尾羽 · 开成一面扇",
  "facts": [
    "线索一：这些蛋下在草丛里，一窝四到六颗，蛋壳是米黄色的。下完蛋以后，妈妈就不再长漂亮的长尾巴了。",
    "线索二：小家伙出壳就能跟着妈妈跑，头顶早早立起一小撮毛。这会儿还看不出来，谁将来会长成最漂亮的那只。",
    "线索三：它开屏时能把一百多根尾羽立成一整面扇子，上面布满像眼睛一样的花纹。它用这个吸引异性，也用它吓退敌人。它叫孔雀。",
  ],
  "body": (
    # 开屏：一根根羽毛摊成扇子，每根梢上一颗金边眼斑。
    # 别画成一整块实心——实心的读不出"羽毛"，眼斑也糊在里面
    ''.join('<g transform="translate(100,168) rotate(%d)">'
              '<path d="M-9 0 C-9 -52 -5 -74 0 -78 C5 -74 9 -52 9 0 Z"'
              ' fill="%s" stroke="#1d5f6b" stroke-width="2"/>'
              '<circle cx="0" cy="-60" r="11" fill="#e8c04a"/>'
              '<circle cx="0" cy="-60" r="7" fill="#1d5f6b"/>'
              '<circle cx="0" cy="-62" r="3" fill="#8fe0e8"/></g>'
              % (ang, ("#3fa8b4" if i % 2 else "#2f8f9a"))
              for i, ang in enumerate(range(-120, 121, 20)))
    + '<path d="M90 198 l-4 12 M110 198 l0 12" stroke="#e8b04a" stroke-width="5" stroke-linecap="round"/>'
    '<ellipse cx="100" cy="172" rx="28" ry="34" fill="#3fa8b4"/>'
    '<ellipse cx="100" cy="172" rx="28" ry="34" fill="none" stroke="#1d5f6b" stroke-width="2.5"/>'
    '<path d="M100 148 C96 122 100 102 108 92" stroke="#3fa8b4" stroke-width="16"'
    ' fill="none" stroke-linecap="round"/>'
    '<circle cx="110" cy="86" r="18" fill="#3fa8b4"/>'
    '<circle cx="110" cy="86" r="18" fill="none" stroke="#1d5f6b" stroke-width="2"/>'
    '<path d="M126 82 L152 90 L126 96 Z" fill="#e8b04a"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#1d5f6b" stroke-width="3" stroke-linecap="round"/>' % s
              for s in [(102,70,98,56), (108,68,108,54), (114,70,120,56)])
    + ''.join('<circle cx="%d" cy="%d" r="3.5" fill="#8fe0e8"/>' % p
              for p in [(98,54), (108,52), (120,54)])
    + '<circle cx="116" cy="82" r="5.5" fill="#fff"/>'
    '<circle cx="117" cy="83" r="3.2" fill="#1c2a30"/>'
  ),
},
{
  "id": "parrot", "cn": "鹦鹉", "en": "Parrot", "series": "bird",
  "tint": "#4fae6a", "dark": "#2c6e42",
  "skill": "两只脚趾朝后 · 学人说话",
  "facts": [
    "线索一：这些蛋藏在树洞里，一窝通常两颗。爸爸和妈妈轮流孵，孵出来以后一起喂。",
    "线索二：小家伙出壳时身上光秃秃的，眼睛还睁不开。它不会自己吃饭，要大人把食物嚼碎喂进嘴里。",
    "线索三：它脚上是两个脚趾朝前、两个朝后，能像人手一样抓着食物吃。它还能学会人说话，模仿几十种不同的声音。它叫鹦鹉。",
  ],
  "body": (
    '<path d="M96 176 C78 198 86 210 106 208 C90 202 92 188 104 180 Z" fill="#d0433a"/>'
    '<path d="M58 148 C36 168 40 198 64 204 C50 188 52 164 68 154 Z" fill="#3f9a5c"/>'
    '<path d="M142 148 C164 168 160 198 136 204 C150 188 148 164 132 154 Z" fill="#3f9a5c"/>'
    '<ellipse cx="100" cy="148" rx="42" ry="50" fill="#4fae6a"/>'
    '<ellipse cx="100" cy="158" rx="26" ry="32" fill="#eef5c8"/>'
    '<circle cx="100" cy="88" r="36" fill="#4fae6a"/>'
    '<circle cx="100" cy="104" r="24" fill="#e8f5c8"/>'
    '<path d="M122 90 C154 90 162 114 138 130 C148 112 140 100 122 100 Z" fill="#3a4a58" stroke="#8fa3c4" stroke-width="1.6"/>'
    '<circle cx="106" cy="84" r="10" fill="#fff"/>'
    '<circle cx="109" cy="85" r="5.5" fill="#2a2622"/>'
    '<circle cx="111" cy="83" r="2" fill="#fff"/>'
    '<path d="M92 194 l-6 12 M104 196 l0 12" stroke="#e8b04a" stroke-width="5" stroke-linecap="round"/>'
  ),
},
{
  "id": "swan", "cn": "天鹅", "en": "Swan", "series": "bird",
  "tint": "#f7f2e8", "dark": "#a89a86",
  "skill": "驮着孩子游 · 排队南飞",
  "facts": [
    "线索一：这些蛋放在水边用芦苇搭的大巢里，一窝五六颗。它们的爸爸妈妈会一直守在旁边，守到孵出来为止。",
    "线索二：小家伙出壳后一身灰绒，几天就能下水游泳。游累了就爬到妈妈背上，让妈妈驮着走。",
    "线索三：它全身白得发亮，脖子弯成一个细长的 S。飞的时候脖子伸得笔直，一只跟一只排成一条线往南走。它叫天鹅。",
  ],
  "body": (
    '<path d="M24 188 C58 178 142 178 176 188" stroke="#7fb8d8" stroke-width="5" fill="none" opacity=".55" stroke-linecap="round"/>'
    '<path d="M58 126 C30 136 22 162 40 178 C34 158 44 140 64 134 Z" fill="#eae2d2"/>'
    '<ellipse cx="94" cy="146" rx="58" ry="44" fill="#f7f2e8"/>'
    '<path d="M104 136 C122 110 120 78 108 58" stroke="#f7f2e8" stroke-width="20" fill="none" stroke-linecap="round"/>'
    '<circle cx="106" cy="52" r="20" fill="#f7f2e8"/>'
    '<path d="M124 48 L160 60 L126 68 Z" fill="#e8a13c"/>'
    '<path d="M118 66 L138 62 L118 78 Z" fill="#2f3438"/>'
    '<circle cx="112" cy="48" r="5.5" fill="#fff"/>'
    '<circle cx="114" cy="49" r="3.2" fill="#2a2622"/>'
  ),
},
{
  "id": "ostrich", "cn": "鸵鸟", "en": "Ostrich", "series": "bird",
  "tint": "#8f8578", "dark": "#5a5248",
  "skill": "一步跨四米 · 飞不起来",
  "facts": [
    "线索一：这是世界上最大的蛋，一颗顶二十多颗鸡蛋，壳厚到成年人站上去也踩不破。",
    "线索二：小家伙出壳时就有小鸡那么大，毛是棕灰色的。它长上几个月，就能跑得比人还快。",
    "线索三：它个子最高，却飞不起来，翅膀只是跑起来时用来保持平衡的。它一步能跨四米多，一脚能把狮子踢翻。它叫鸵鸟。",
  ],
  "body": (
    '<path d="M44 104 C22 114 16 138 30 152 C30 132 38 116 54 110 Z" fill="#4a4640"/>'
    '<ellipse cx="98" cy="122" rx="62" ry="54" fill="#4a4640"/>'
    '<ellipse cx="98" cy="142" rx="46" ry="36" fill="#d8d2c6"/>'
    '<path d="M100 70 C96 40 100 22 108 10" stroke="#e0c8b4" stroke-width="17" fill="none" stroke-linecap="round"/>'
    '<circle cx="110" cy="20" r="19" fill="#e0c8b4"/>'
    '<path d="M126 18 L156 26 L126 32 Z" fill="#d9a05a"/>'
    '<circle cx="116" cy="16" r="6" fill="#fff"/>'
    '<circle cx="117" cy="17" r="3.6" fill="#2a2622"/>'
    # 两条腿。画成四条会读成哺乳动物
    '<path d="M70 168 L64 200 L48 206" stroke="#d9a05a" stroke-width="8" fill="none" stroke-linecap="round"/>'
    '<path d="M126 168 L132 200 L148 206" stroke="#d9a05a" stroke-width="8" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "crow", "cn": "乌鸦", "en": "Crow", "series": "bird",
  "tint": "#4a5560", "dark": "#2a323a",
  "skill": "会用工具 · 记得住人脸",
  "facts": [
    "线索一：这些蛋是浅蓝绿色的，上面撒满褐色斑点，一窝三四颗。它们的爸妈把窝搭在高高的大树杈上，用树枝一根根卡住。",
    "线索二：小家伙出壳时光溜溜的，眼睛闭着，要爸妈喂上半个月。它从小就爱盯着大人看，看它们怎么找吃的。",
    "线索三：它会用树枝把小虫子从洞里钩出来，也会往瓶子里丢石子，让水位升上来喝到水。它记得住每一张人脸，能记好几年。它叫乌鸦。",
  ],
  "body": (
    '<ellipse cx="98" cy="136" rx="52" ry="56" fill="#3a444f"/>'
    '<path d="M92 182 L72 208 L122 206 Z" fill="#2c353e"/>'
    '<path d="M56 116 C36 140 42 176 66 186 C50 164 52 134 70 124 Z" fill="#2c353e"/>'
    '<path d="M142 116 C162 140 156 176 132 186 C148 164 146 134 128 124 Z" fill="#2c353e"/>'
    '<ellipse cx="98" cy="154" rx="30" ry="34" fill="#5a6673"/>'
    '<circle cx="100" cy="84" r="38" fill="#3a444f"/>'
    '<path d="M62 84 A38 38 0 0 1 138 84 Z" fill="#2c353e"/>'
    # 喙要浅色，不然和身体糊成一片
    '<path d="M134 78 L176 90 L134 96 Z" fill="#9aa4ad"/>'
    '<path d="M134 96 L176 90 L172 100 L134 101 Z" fill="#78838d"/>'
    '<circle cx="114" cy="84" r="9" fill="#fff"/>'
    '<circle cx="117" cy="85" r="5" fill="#1a2028"/>'
    '<circle cx="119" cy="83" r="1.8" fill="#fff"/>'
    '<path d="M84 190 l-8 12 M84 190 l8 12" stroke="#3a444f" stroke-width="5" stroke-linecap="round"/>'
    '<path d="M114 190 l-8 12 M114 190 l8 12" stroke="#3a444f" stroke-width="5" stroke-linecap="round"/>'
  ),
},
{
  "id": "eagle", "cn": "鹰", "en": "Eagle", "series": "bird",
  "tint": "#9a6b3f", "dark": "#5e3e1e",
  "skill": "两千米外看得见兔子 · 俯冲比高铁快",
  "facts": [
    "线索一：这些蛋是白色的，个头比鸡蛋大一圈，一窝通常两颗。它们的妈妈把窝搭在悬崖或高树顶上，一年年往上加树枝，窝会越长越大。",
    "线索二：小家伙先在窝里长出一身灰白绒毛，再慢慢换出深色羽毛。学飞要花好几个星期，头几次都是扑腾着摔回窝里。",
    "线索三：它能在两千米高看清地面上一只兔子，眼力是人的好几倍。它收起翅膀俯冲时，每小时能到三百公里，比高铁还快。它叫鹰。",
  ],
  "body": (
    # 展开的双翼
    '<path d="M100 118 C58 94 18 96 6 118 C38 124 68 136 100 152 Z" fill="#7d5730"/>'
    '<path d="M100 118 C142 94 182 96 194 118 C162 124 132 136 100 152 Z" fill="#7d5730"/>'
    '<path d="M100 122 C72 110 44 110 26 122 C54 130 78 140 100 152 Z" fill="#a87a45"/>'
    '<path d="M100 122 C128 110 156 110 174 122 C146 130 122 140 100 152 Z" fill="#a87a45"/>'
    '<path d="M84 180 L74 206 L126 206 L116 180 Z" fill="#6e4d2a"/>'
    '<ellipse cx="100" cy="142" rx="34" ry="46" fill="#8a6238"/>'
    '<ellipse cx="100" cy="156" rx="20" ry="28" fill="#d8c49c"/>'
    '<circle cx="100" cy="92" r="28" fill="#8a6238"/>'
    '<path d="M72 92 A28 28 0 0 1 128 92 Z" fill="#a87a45"/>'
    # 钩喙
    '<path d="M124 88 C146 88 154 104 138 118 C146 104 138 96 124 96 Z" fill="#e8b04a"/>'
    '<circle cx="110" cy="90" r="6.5" fill="#fff"/>'
    '<circle cx="112" cy="91" r="3.6" fill="#2a2018"/>'
    '<circle cx="113.5" cy="89" r="1.4" fill="#fff"/>'
    '<path d="M86 186 l-6 14 M100 188 l0 14 M114 186 l6 14" stroke="#e8b04a" stroke-width="5" stroke-linecap="round"/>'
  ),
},

# ============================ 海洋 ============================
{
  "id": "octopus", "cn": "章鱼", "en": "Octopus", "series": "sea",
  "tint": "#c98aa6", "dark": "#8a4a66",
  "skill": "一秒变色 · 三颗心脏",
  "facts": [
    "线索一：这些蛋一串一串挂着，像小葡萄，有好几万颗。它们的妈妈守在旁边不吃不喝，守到宝宝全孵出来才离开。",
    "线索二：小家伙只有米粒那么大，可身上已经长齐了将来要用的所有“手臂”。有的会把贝壳背在身上当盔甲。",
    "线索三：它有三颗心脏，血是蓝色的。一秒钟就能把全身颜色和皮肤上的凸起换一遍，变成石头或珊瑚的样子。它叫章鱼。",
  ],
  "body": (
    '<ellipse cx="100" cy="112" rx="56" ry="58" fill="#f07fa8"/>'
    '<circle cx="62" cy="136" r="9" fill="#f7a8c4" opacity=".85"/>'
    '<circle cx="138" cy="136" r="9" fill="#f7a8c4" opacity=".85"/>'
    '<circle cx="78" cy="112" r="17" fill="#fff"/>'
    '<circle cx="122" cy="112" r="17" fill="#fff"/>'
    '<circle cx="80" cy="113" r="9" fill="#3a1f2c"/>'
    '<circle cx="124" cy="113" r="9" fill="#3a1f2c"/>'
    '<circle cx="83" cy="109" r="3.5" fill="#fff"/>'
    '<circle cx="127" cy="109" r="3.5" fill="#fff"/>'
    '<path d="M56 158 C38 176 46 198 62 199 C50 189 54 172 68 166" fill="#e86a96"/>'
    '<path d="M76 168 C62 188 70 204 86 203 C73 195 76 180 88 174" fill="#f07fa8"/>'
    '<path d="M100 172 C93 191 100 206 114 203 C104 195 104 182 112 176" fill="#e86a96"/>'
    '<path d="M124 168 C138 188 130 204 114 203 C127 195 124 180 112 174" fill="#f07fa8"/>'
    '<path d="M144 158 C162 176 154 198 138 199 C150 189 146 172 132 166" fill="#e86a96"/>'
  ),
},
{
  "id": "turtle", "cn": "海龟", "en": "Sea turtle", "series": "sea",
  "tint": "#8fbcb0", "dark": "#4a7a70",
  "skill": "记住出生地的磁场",
  "facts": [
    "线索一：这些蛋埋在沙滩的坑里，上面用沙子盖好，有上百颗。它们的妈妈盖完沙子就回海里了，再也不会来看一眼。",
    "线索二：沙里的小家伙约好同时破壳，一起朝海的方向爬。这段路上它们只能靠数量多，换取活下来的机会。",
    "线索三：它能感知地球的磁场，记住了出生那片沙滩的“磁场味道”，几十年后还能准确游回同一个地方下蛋。它叫海龟。",
  ],
  "body": (
    '<ellipse cx="100" cy="140" rx="58" ry="44" fill="#5f9e8f"/>'
    '<ellipse cx="100" cy="140" rx="44" ry="33" fill="#8fbcb0"/>'
    '<path d="M100 107 L100 173 M70 118 L130 162 M130 118 L70 162" stroke="#5f9e8f" stroke-width="3.5" fill="none"/>'
    '<path d="M78 107 L78 173 M122 107 L122 173 M58 140 L142 140" stroke="#5f9e8f" stroke-width="3.5" fill="none"/>'
    '<ellipse cx="46" cy="104" rx="22" ry="13" fill="#7aab9d" transform="rotate(-32 46 104)"/>'
    '<ellipse cx="154" cy="104" rx="22" ry="13" fill="#7aab9d" transform="rotate(32 154 104)"/>'
    '<ellipse cx="52" cy="176" rx="19" ry="11" fill="#7aab9d" transform="rotate(28 52 176)"/>'
    '<ellipse cx="148" cy="176" rx="19" ry="11" fill="#7aab9d" transform="rotate(-28 148 176)"/>'
    '<ellipse cx="100" cy="80" rx="28" ry="25" fill="#9fcbbf"/>'
    '<circle cx="88" cy="76" r="10" fill="#fff"/>'
    '<circle cx="112" cy="76" r="10" fill="#fff"/>'
    '<circle cx="89" cy="77" r="5.5" fill="#243a34"/>'
    '<circle cx="113" cy="77" r="5.5" fill="#243a34"/>'
    '<circle cx="91" cy="74" r="2" fill="#fff"/>'
    '<circle cx="115" cy="74" r="2" fill="#fff"/>'
    '<path d="M94 93 C98 98 102 98 106 93" stroke="#243a34" stroke-width="3" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "seahorse", "cn": "海马", "en": "Seahorse", "series": "sea",
  "tint": "#e8a13c", "dark": "#a86a18",
  "skill": "爸爸负责怀宝宝",
  "facts": [
    "线索一：这些卵不是妈妈生的，是爸爸怀的。妈妈把卵产在爸爸肚子前面的育儿袋里，爸爸带着它们孵上两三个星期。",
    "线索二：小家伙从爸爸肚子里弹出来时只有米粒大，一出来就得自己找吃的，爸妈都不管了。",
    "线索三：它靠背上那片小鳍扇动着往前挪，游得比谁都慢，却能一天吃下几千只小虾。它站着游、用尾巴钩住水草，从不松手。它叫海马。",
  ],
  "body": (
    # 卷起来的尾巴
    '<path d="M104 170 C98 194 82 200 72 190 C64 182 72 172 82 176"'
    ' stroke="#e8a13c" stroke-width="13" fill="none" stroke-linecap="round"/>'
    # 弓着的身体
    '<path d="M96 84 C76 102 72 134 88 160 C100 176 118 172 122 152 C128 124 118 100 96 84 Z" fill="#e8a13c"/>'
    '<path d="M92 102 C82 116 80 140 90 156" stroke="#f7d08a" stroke-width="7" fill="none" stroke-linecap="round"/>'
    # 育儿袋
    '<path d="M86 136 C98 132 108 136 110 146 C104 156 92 156 86 148 Z" fill="#c9821e"/>'
    # 背鳍
    '<path d="M76 126 C62 132 60 152 72 158 C68 146 70 134 78 130 Z" fill="#f7c96a"/>'
    # 头 + 长吻
    '<path d="M96 84 C88 70 92 56 104 52" stroke="#e8a13c" stroke-width="17" fill="none" stroke-linecap="round"/>'
    '<circle cx="108" cy="52" r="15" fill="#e8a13c"/>'
    '<path d="M120 48 L158 57 L120 61 Z" fill="#c9821e"/>'
    '<path d="M104 38 C106 28 112 24 118 26" stroke="#c9821e" stroke-width="5" fill="none" stroke-linecap="round"/>'
    '<circle cx="110" cy="48" r="5.5" fill="#fff"/>'
    '<circle cx="111.5" cy="49" r="3.2" fill="#2a2018"/>'
  ),
},
{
  "id": "clownfish", "cn": "小丑鱼", "en": "Clownfish", "series": "sea",
  "tint": "#f07a2a", "dark": "#a84a10",
  "skill": "出生全是男孩 · 最大的会变成妈妈",
  "facts": [
    "线索一：这些卵粘在石头底下，一窝有好几百颗。它们的爸妈轮流守在旁边，用嘴把没长好的卵一颗颗挑掉。",
    "线索二：小家伙一孵出来，全都是男孩。它们住在一丛带毒刺的软软的东西里面，那里别的小鱼不敢进，只有它们不怕。",
    "线索三：一群里个头最大的那只，会慢慢变成妈妈。它身上有三道白条纹，跟那种带毒刺的东西住在一起，谁也不伤谁。它叫小丑鱼。",
  ],
  "body": (
    '<path d="M158 134 C184 124 192 106 174 96 C178 116 166 128 148 130 Z" fill="#e8702a"/>'
    '<path d="M118 84 C112 76 104 76 98 84 C110 88 116 96 118 108 Z" fill="#e8702a"/>'
    '<ellipse cx="98" cy="134" rx="58" ry="40" fill="#f07a2a"/>'
    '<path d="M64 102 C60 120 60 148 64 166" stroke="#f7f2ea" stroke-width="12" fill="none"/>'
    '<path d="M96 98 C92 120 92 148 96 170" stroke="#f7f2ea" stroke-width="12" fill="none"/>'
    '<path d="M128 104 C124 122 124 146 128 162" stroke="#f7f2ea" stroke-width="12" fill="none"/>'
    '<circle cx="46" cy="126" r="15" fill="#fff"/>'
    '<circle cx="44" cy="127" r="8" fill="#2a2018"/>'
    '<circle cx="47" cy="124" r="3" fill="#fff"/>'
    '<path d="M62 152 C72 162 86 164 96 158" stroke="#c85a18" stroke-width="4" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "starfish", "cn": "海星", "en": "Starfish", "series": "sea",
  "tint": "#e8734a", "dark": "#a8482a",
  "skill": "胳膊断了能长回来 · 眼睛在指尖",
  "facts": [
    "线索一：这些卵小得看不见，漂在水里，一次能产好几百万颗。它们不孵也不管，全靠数量多。",
    "线索二：小家伙刚孵出来是两边对称的，会游水。要经过好几次变身，才慢慢长出那副五个角的模样。",
    "线索三：它没有脑子，也没有血，靠海水在身体里流来流去活着。它的眼睛长在每条胳膊的尖上，胳膊断了还能长回来。它叫海星。",
  ],
  "body": (
    '<path d="M100 40 L117 90 L170 90 L127 122 L143 176 L100 146 L57 176 L73 122 L30 90 L83 90 Z"'
    ' fill="#e8734a" stroke="#a8482a" stroke-width="4" stroke-linejoin="round"/>'
    + ''.join('<circle cx="%d" cy="%d" r="4" fill="#8a3a24"/>' % p
              for p in [(100,60), (150,98), (133,155), (67,155), (50,98)])
    + '<circle cx="100" cy="110" r="20" fill="#f7a078"/>'
    '<circle cx="100" cy="110" r="7" fill="#e8734a"/>'
    + ''.join('<circle cx="%d" cy="%d" r="3" fill="#f7a078"/>' % p
              for p in [(100,82), (124,96), (116,128), (84,128), (76,96)])
  ),
},
{
  "id": "crab", "cn": "螃蟹", "en": "Crab", "series": "sea",
  "tint": "#e05a3a", "dark": "#a03018",
  "skill": "横着走 · 蜕壳连胃里的牙一起换",
  "facts": [
    "线索一：这些卵不放在水里，而是抱在妈妈肚子下面那片能翻开的壳里，要好几个星期。这段时间妈妈一直举着它慢慢挪。",
    "线索二：小家伙孵出来时完全不像妈妈，是个在水里游的小圆点，要蜕好几次壳，才慢慢长出八条腿和两只大钳子。",
    "线索三：它横着走，因为腿的关节只能朝两边弯。它一身硬壳，长大了就得把旧壳脱掉换新的，脱壳时连胃里的牙一起换。它叫螃蟹。",
  ],
  "body": (
    ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#c04326" stroke-width="7" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % seg
              for seg in [(60,150, 30,166, 20,190), (66,160, 40,180, 34,200),
                          (140,150, 170,166, 180,190), (134,160, 160,180, 166,200)])
    + '<path d="M44 112 C18 102 8 80 26 68 C22 88 34 100 52 104 Z" fill="#e05a3a" stroke="#c04326" stroke-width="3"/>'
    '<path d="M156 112 C182 102 192 80 174 68 C178 88 166 100 148 104 Z" fill="#e05a3a" stroke="#c04326" stroke-width="3"/>'
    '<ellipse cx="100" cy="130" rx="62" ry="42" fill="#e05a3a"/>'
    '<ellipse cx="100" cy="142" rx="44" ry="24" fill="#f09070"/>'
    '<path d="M76 130 C88 138 112 138 124 130" stroke="#a03018" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<path d="M84 94 L80 76 M116 94 L120 76" stroke="#c04326" stroke-width="6" stroke-linecap="round"/>'
    '<circle cx="80" cy="74" r="10" fill="#fff"/><circle cx="80" cy="74" r="5" fill="#2a2018"/>'
    '<circle cx="120" cy="74" r="10" fill="#fff"/><circle cx="120" cy="74" r="5" fill="#2a2018"/>'
  ),
},
{
  "id": "jellyfish", "cn": "水母", "en": "Jellyfish", "series": "sea",
  "tint": "#b08fd8", "dark": "#6a4a9c",
  "skill": "没有脑、没有心 · 九成是水",
  "facts": [
    "线索一：这些卵和别的海里的小动物不一样：先附在石头上长成一丛像小花的东西，再一层层脱开，变成会游的那种形态。",
    "线索二：小家伙一出来就长着妈妈的样子，只是很小。它不用学，从第一天就会一张一合地往上顶，往前漂。",
    "线索三：它没有脑子，也没有心脏和骨头，身体里百分之九十五都是水。身上那些细丝碰到东西就弹出毒针，麻翻了再送进嘴里。它叫水母。",
  ],
  "body": (
    '<path d="M40 128 C40 84 62 58 100 58 C138 58 160 84 160 128'
    ' C160 140 148 146 138 140 C128 134 116 142 106 140 C96 138 84 146 74 140'
    ' C64 134 40 140 40 128 Z" fill="#b08fd8"/>'
    '<path d="M56 108 C70 90 130 90 144 108 C130 98 70 98 56 108 Z" fill="#d8c0f0" opacity=".75"/>'
    + ''.join('<path d="M%d 138 C%d 162 %d 176 %d 200" stroke="#c8a8e8" stroke-width="6"'
              ' fill="none" stroke-linecap="round" opacity=".9"/>' % t
              for t in [(58,52,66,62), (76,70,84,80), (94,88,102,98),
                        (112,106,120,118), (130,124,138,136), (146,138,152,152)])
    + '<circle cx="82" cy="112" r="6" fill="#2a2040" opacity=".5"/>'
    '<circle cx="118" cy="112" r="6" fill="#2a2040" opacity=".5"/>'
  ),
},
{
  "id": "coral", "cn": "珊瑚", "en": "Coral", "series": "sea",
  "tint": "#e07a5a", "dark": "#a8482a",
  "skill": "看着像植物，其实是动物",
  "facts": [
    "线索一：这些卵很小，漂上几天就附到石头上，一辈子不再挪地方。",
    "线索二：小家伙坐定以后就不动了，只会往四周铺开。它其实是许许多多小东西挤在一起长，慢慢堆成一大丛。",
    "线索三：它看着像植物，其实是动物，嘴长在每一根枝的尖上。它和住在身体里的藻类互相养着，一起把海底堆成大片礁石。它叫珊瑚。",
  ],
  "body": (
    '<path d="M100 202 L100 124" stroke="#e07a5a" stroke-width="16" stroke-linecap="round"/>'
    '<path d="M100 132 C86 112 74 98 60 90" stroke="#e07a5a" stroke-width="14" fill="none" stroke-linecap="round"/>'
    '<path d="M100 132 C114 112 126 98 140 90" stroke="#e07a5a" stroke-width="14" fill="none" stroke-linecap="round"/>'
    '<path d="M100 124 C98 100 96 84 92 62" stroke="#e07a5a" stroke-width="14" fill="none" stroke-linecap="round"/>'
    '<path d="M78 108 C70 94 66 82 62 68" stroke="#e07a5a" stroke-width="11" fill="none" stroke-linecap="round"/>'
    '<path d="M122 108 C130 94 134 82 138 68" stroke="#e07a5a" stroke-width="11" fill="none" stroke-linecap="round"/>'
    + ''.join('<circle cx="%d" cy="%d" r="7" fill="#f7b09a" stroke="#a8482a" stroke-width="2.5"/>' % p
              for p in [(60,88), (140,88), (92,60), (62,66), (138,66)])
    + '<circle cx="100" cy="130" r="9" fill="#f7b09a" stroke="#a8482a" stroke-width="2.5"/>'
    '<path d="M52 204 C74 194 126 194 148 204" stroke="#8a9aa8" stroke-width="6" fill="none" stroke-linecap="round" opacity=".65"/>'
  ),
},
{
  "id": "urchin", "cn": "海胆", "en": "Sea urchin", "series": "sea",
  "tint": "#6a4a8c", "dark": "#3a2456",
  "skill": "五颗牙合成一盏灯 · 能把石头啃出洞",
  "facts": [
    "线索一：这些卵直接产在水里，能不能碰上全看运气。它们的爸妈排完就不管了。",
    "线索二：小家伙刚孵出来时两边对称、会游水，要经过好几次变身，才慢慢变成圆球落到海底安家。",
    "线索三：它是一个长满尖刺的球，靠尖刺撑着在石头上走路。它嘴上有五颗牙，合起来像一盏小灯，能把石头啃出洞来。它叫海胆。",
  ],
  "body": (
    ''.join('<path d="M100 132 L%d %d" stroke="#4a3266" stroke-width="5" stroke-linecap="round"/>' % p
              for p in [(100,24), (58,42), (142,42), (36,86), (164,86), (30,132), (170,132),
                        (38,178), (162,178), (64,208), (136,208), (100,210)])
    + '<circle cx="100" cy="132" r="62" fill="#6a4a8c"/>'
    '<circle cx="100" cy="132" r="42" fill="#8a68b0"/>'
    + ''.join('<circle cx="%d" cy="%d" r="5" fill="#c8b0e0" opacity=".85"/>' % p
              for p in [(78,110), (122,110), (100,140), (80,158), (120,158), (100,96)])
    + '<circle cx="84" cy="116" r="7" fill="#fff"/><circle cx="84" cy="117" r="4" fill="#2a1a3a"/>'
    '<circle cx="116" cy="116" r="7" fill="#fff"/><circle cx="116" cy="117" r="4" fill="#2a1a3a"/>'
    '<path d="M78 190 C88 198 112 198 122 190" stroke="#cfc4dd" stroke-width="4" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "squid", "cn": "鱿鱼", "en": "Squid", "series": "sea",
  "tint": "#e8b0b8", "dark": "#a86070",
  "skill": "喷水往后冲 · 深海里的大眼睛",
  "facts": [
    "线索一：这些卵一串串挂在海底，白白的一挂一挂，像一串小灯泡。它们的爸妈产完卵就死了，看不到宝宝孵出来。",
    "线索二：小家伙孵出来就带着十条腕，只是比例还不对——身体短短，腕却很长。它长得飞快，几个月就长成。",
    "线索三：它吸一口水，再从身体下面那根管子猛喷出去，靠这个往后冲。它有一对特别大的眼睛，黑漆漆的深海里也能看见一点光。它叫鱿鱼。",
  ],
  "body": (
    '<path d="M100 26 C122 26 132 52 132 94 L68 94 C68 52 78 26 100 26 Z" fill="#e8b0b8"/>'
    '<path d="M68 94 L132 94 L124 168 L76 168 Z" fill="#f0c8d0"/>'
    # 两侧的鳍
    '<path d="M70 52 C52 60 48 76 58 84 C58 70 64 60 74 56 Z" fill="#e8b0b8"/>'
    '<path d="M130 52 C148 60 152 76 142 84 C142 70 136 60 126 56 Z" fill="#e8b0b8"/>'
    # 十条腕
    + ''.join('<path d="M%d 168 C%d 188 %d 198 %d 206" stroke="#e8b0b8" stroke-width="7"'
              ' fill="none" stroke-linecap="round"/>' % t
              for t in [(80,74,68,62), (86,82,78,72), (94,92,88,84),
                        (106,102,110,114), (114,112,120,124), (120,120,130,134)])
    + '<circle cx="82" cy="76" r="12" fill="#fff"/><circle cx="80" cy="77" r="6.5" fill="#2a1a20"/>'
    '<circle cx="118" cy="76" r="12" fill="#fff"/><circle cx="120" cy="77" r="6.5" fill="#2a1a20"/>'
    '<path d="M92 118 C98 126 102 126 108 118" stroke="#a86070" stroke-width="4" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "oyster", "cn": "珍珠贝", "en": "Pearl oyster", "series": "sea",
  "tint": "#c8a8c0", "dark": "#8a6a80",
  "skill": "裹上几年就是一颗珠子",
  "facts": [
    "线索一：这些卵产在水里，爸妈排完就不管了，小宝宝孵出来先在水中漂一阵子。",
    "线索二：小家伙先在水中游，找到合适的地方就分泌出一层硬壳，把自己粘在石头上，再也不挪窝。",
    "线索三：它有两片壳，靠一根像筋一样的韧带开合。要是有粒沙子钻进去，它会一层层裹上亮亮的膜，裹上几年就成了一颗珠子。它叫珍珠贝。",
  ],
  "body": (
    '<path d="M100 200 C50 190 22 154 30 112 C36 80 66 62 100 62 C134 62 164 80 170 112'
    ' C178 154 150 190 100 200 Z" fill="#d8bcd0"/>'
    + ''.join('<path d="M100 66 L%d %d" stroke="#c0a0b8" stroke-width="3" opacity=".75"/>' % p
              for p in [(42,122), (58,178), (86,198), (114,198), (142,178), (158,122)])
    + '<path d="M100 200 C50 190 22 154 30 112 C36 80 66 62 100 62 C134 62 164 80 170 112"'
    ' fill="none" stroke="#8a6a80" stroke-width="5"/>'
    '<path d="M100 64 L100 200" stroke="#8a6a80" stroke-width="4" opacity=".5"/>'
    '<circle cx="100" cy="142" r="26" fill="#f7f2ea"/>'
    '<circle cx="92" cy="134" r="8" fill="#fff" opacity=".95"/>'
  ),
},
{
  "id": "eel", "cn": "鳗鱼", "en": "Eel", "series": "sea",
  "tint": "#6a7a5a", "dark": "#3a4630",
  "skill": "爬过湿草地换水塘",
  "facts": [
    "线索一：这些卵产在很远很远的海里，一片长满海草的地方。产完卵，它们的爸妈就再也没力气游回去了。",
    "线索二：小家伙孵出来是扁扁的一片，像柳叶，随海水漂上好几年，慢慢变成细长的样子，才游回江河里。",
    "线索三：它身子像蛇一样细长，背上的鳍和尾巴连成一条边。它能爬上岸，滑过湿漉漉的草地，去找另一个水塘。它叫鳗鱼。",
  ],
  "body": (
    '<path d="M188 176 C160 190 120 188 92 172 C64 156 46 130 36 100 C28 76 34 56 50 50"'
    ' stroke="#5f7050" stroke-width="28" fill="none" stroke-linecap="round"/>'
    '<path d="M188 176 C160 190 120 188 92 172 C64 156 46 130 36 100 C28 76 34 56 50 50"'
    ' stroke="#8a9c72" stroke-width="15" fill="none" stroke-linecap="round"/>'
    '<path d="M184 172 C158 184 124 182 98 168" stroke="#f0e8c8" stroke-width="7"'
    ' fill="none" stroke-linecap="round" opacity=".8"/>'
    '<circle cx="52" cy="56" r="23" fill="#5f7050"/>'
    '<circle cx="44" cy="52" r="9" fill="#fff"/>'
    '<circle cx="43" cy="53" r="5" fill="#1e2418"/>'
    '<circle cx="45" cy="50" r="1.8" fill="#fff"/>'
    '<path d="M30 62 C24 66 22 72 26 76" stroke="#3a4630" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
  ),
},

# ============================ 昆虫 ============================
{
  "id": "bee", "cn": "蜜蜂", "en": "Bee", "series": "bug",
  "tint": "#d8b662", "dark": "#8a6c28",
  "skill": "看得见紫外线 · 跳舞报路",
  "facts": [
    "线索一：这些蛋一颗一颗放在六边形的小格子里，一天能产上千颗。有一大群大人在专门照顾它们。",
    "线索二：小家伙从蛋里出来后，还要先变成幼虫、再变成蛹，二十天左右才长出翅膀。",
    "线索三：它看得见紫外线，花朵在它眼里有额外的花纹。它会跳舞告诉同伴花在哪、有多远，还能感知天空的偏振光认路。它叫蜜蜂。",
  ],
  "body": (
    '<ellipse cx="62" cy="96" rx="30" ry="20" fill="#bfe6f5" opacity=".72" transform="rotate(-25 62 96)"/>'
    '<ellipse cx="138" cy="96" rx="30" ry="20" fill="#bfe6f5" opacity=".72" transform="rotate(25 138 96)"/>'
    '<path d="M86 78 C82 62 74 56 64 54" stroke="#3a3020" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<path d="M114 78 C118 62 126 56 136 54" stroke="#3a3020" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<circle cx="62" cy="53" r="5" fill="#3a3020"/>'
    '<circle cx="138" cy="53" r="5" fill="#3a3020"/>'
    '<ellipse cx="100" cy="140" rx="48" ry="56" fill="#f0c04a"/>'
    '<path d="M55 122 C70 132 130 132 145 122 L145 138 C130 148 70 148 55 138 Z" fill="#3a3020"/>'
    '<path d="M58 161 C72 171 128 171 142 161 L140 175 C126 185 74 185 60 175 Z" fill="#3a3020"/>'
    '<path d="M100 196 L100 210" stroke="#3a3020" stroke-width="7" stroke-linecap="round"/>'
    '<circle cx="80" cy="108" r="13" fill="#fff"/>'
    '<circle cx="120" cy="108" r="13" fill="#fff"/>'
    '<circle cx="81" cy="109" r="7" fill="#3a3020"/>'
    '<circle cx="121" cy="109" r="7" fill="#3a3020"/>'
    '<circle cx="83" cy="106" r="2.5" fill="#fff"/>'
    '<circle cx="123" cy="106" r="2.5" fill="#fff"/>'
    '<path d="M90 128 C95 134 105 134 110 128" stroke="#3a3020" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "butterfly", "cn": "蝴蝶", "en": "Butterfly", "series": "bug",
  "tint": "#e8a03c", "dark": "#a85a18",
  "skill": "用脚尝味道 · 翅膀上全是鳞片",
  "facts": [
    "线索一：这些卵比芝麻还小，粘在叶子背面。孵出来的小家伙根本不是这副模样，是一条只会啃叶子的小肉虫。",
    "线索二：它一生要蜕好几次皮，最后一次把自己挂在枝上，外皮裂开，钻出一个湿漉漉的、完全不一样的身体。",
    "线索三：它的翅膀上铺着一层比头发丝还细的鳞片，所以一碰就掉粉。它的味觉长在脚上，往叶子上一站就知道甜不甜。它叫蝴蝶。",
  ],
  "body": (
    '<path d="M94 102 C70 62 36 46 26 62 C16 78 44 104 94 110 Z" fill="#e8a03c" stroke="#a85a18" stroke-width="3" stroke-linejoin="round"/>'
    '<path d="M106 102 C130 62 164 46 174 62 C184 78 156 104 106 110 Z" fill="#e8a03c" stroke="#a85a18" stroke-width="3" stroke-linejoin="round"/>'
    '<path d="M94 140 C72 158 48 186 62 196 C76 204 92 176 96 152 Z" fill="#f0bc68" stroke="#a85a18" stroke-width="3" stroke-linejoin="round"/>'
    '<path d="M106 140 C128 158 152 186 138 196 C124 204 108 176 104 152 Z" fill="#f0bc68" stroke="#a85a18" stroke-width="3" stroke-linejoin="round"/>'
    '<circle cx="54" cy="78" r="9" fill="#f7dca8"/><circle cx="146" cy="78" r="9" fill="#f7dca8"/>'
    '<circle cx="76" cy="178" r="7" fill="#f7dca8"/><circle cx="124" cy="178" r="7" fill="#f7dca8"/>'
    '<ellipse cx="100" cy="130" rx="10" ry="48" fill="#5a3a1a"/>'
    '<circle cx="100" cy="78" r="15" fill="#5a3a1a"/>'
    '<path d="M94 66 C88 48 78 40 70 42" stroke="#5a3a1a" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
    '<path d="M106 66 C112 48 122 40 130 42" stroke="#5a3a1a" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
    '<circle cx="68" cy="41" r="5" fill="#5a3a1a"/><circle cx="132" cy="41" r="5" fill="#5a3a1a"/>'
    '<circle cx="95" cy="76" r="4" fill="#f7f2ea"/><circle cx="105" cy="76" r="4" fill="#f7f2ea"/>'
  ),
},
{
  "id": "ant", "cn": "蚂蚁", "en": "Ant", "series": "bug",
  "tint": "#8a4a2a", "dark": "#4a2410",
  "skill": "能举起比自己重几十倍的东西",
  "facts": [
    "线索一：这些卵由妈妈一只一只看着长大。小家伙孵出来是没腿的白胖虫，得靠大一点的哥哥姐姐一口口喂。",
    "线索二：它长大前会把自己封进一个茧里睡上一阵，再咬开茧爬出来——这时才长得像家里其他人。",
    "线索三：它靠头上两根会摆动的须跟同伴说话，走路时留下看不见的气味当路标。它能举起比自己重几十倍的东西。它叫蚂蚁。",
  ],
  "body": (
    '<ellipse cx="100" cy="170" rx="27" ry="31" fill="#8a4a2a"/>'
    '<ellipse cx="100" cy="114" rx="15" ry="19" fill="#a05c36"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#5a2e16" stroke-width="5" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(88,106,60,96,48,124), (88,118,58,140,44,148),
                        (86,128,68,160,64,182), (112,106,140,96,152,124),
                        (112,118,142,140,156,148), (114,128,132,160,136,182)])
    + '<circle cx="100" cy="76" r="21" fill="#a05c36"/>'
    '<path d="M92 58 C80 40 64 34 54 38" stroke="#5a2e16" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<path d="M108 58 C120 40 136 34 146 38" stroke="#5a2e16" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<circle cx="86" cy="74" r="8" fill="#fff"/><circle cx="85" cy="75" r="4.5" fill="#2a1408"/>'
    '<circle cx="114" cy="74" r="8" fill="#fff"/><circle cx="115" cy="75" r="4.5" fill="#2a1408"/>'
    '<path d="M92 88 C97 94 103 94 108 88" stroke="#5a2e16" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "ladybug", "cn": "瓢虫", "en": "Ladybug", "series": "bug",
  "tint": "#d94a3a", "dark": "#9a2418",
  "skill": "一顿能吃几十只蚜虫",
  "facts": [
    "线索一：这些卵一簇簇立在叶子背面，黄黄的。孵出来的小家伙跟妈妈长得完全不像，是一条带刺的小灰虫。",
    "线索二：它吃得多、长得快，蜕几次皮之后，最后一次把自己固定在叶子上，从里面翻出一个圆圆的新身体。",
    "线索三：它背上的点数各不相同，有七个的，也有两个的。它一顿能吃几十只专门吸植物汁的小虫，是园子里的帮手。它叫瓢虫。",
  ],
  "body": (
    '<path d="M100 62 C154 62 178 100 178 132 C178 170 144 192 100 192'
    ' C56 192 22 170 22 132 C22 100 46 62 100 62 Z" fill="#d94a3a"/>'
    '<path d="M100 66 L100 190" stroke="#2a1a14" stroke-width="4.5"/>'
    '<path d="M100 62 C82 62 66 50 68 38 C72 27 86 22 100 22 C114 22 128 27 132 38'
    ' C134 50 118 62 100 62 Z" fill="#2a1a14"/>'
    '<path d="M88 32 C78 18 64 12 54 14" stroke="#2a1a14" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<path d="M112 32 C122 18 136 12 146 14" stroke="#2a1a14" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<circle cx="88" cy="44" r="7" fill="#fff"/><circle cx="112" cy="44" r="7" fill="#fff"/>'
    '<circle cx="87" cy="45" r="4" fill="#1a0e08"/><circle cx="113" cy="45" r="4" fill="#1a0e08"/>'
    + ''.join('<circle cx="%d" cy="%d" r="%d" fill="#2a1a14"/>' % p
              for p in [(62,100,13), (138,100,13), (58,146,12), (142,146,12),
                        (100,112,10), (78,172,10), (122,172,10)])
  ),
},
{
  "id": "dragonfly", "cn": "蜻蜓", "en": "Dragonfly", "series": "bug",
  "tint": "#3a9ab0", "dark": "#1e6a7e",
  "skill": "空中急停 · 大眼睛占半个头",
  "facts": [
    "线索一：这些卵产在水里，或者插进水草茎里。孵出来的小家伙住在水底，靠吸一口水再猛喷出去往前冲。",
    "线索二：它在水底要蜕好几次皮，一住就是一两年。最后一次它爬出水面，在草茎上裂开，飞出一个完全不同的身体。",
    "线索三：它两边翅膀能各扇各的，想停就停在半空，想倒着走也行。它那两只大眼睛占了半个头，四万多只小眼拼起来。它叫蜻蜓。",
  ],
  "body": (
    '<ellipse cx="60" cy="104" rx="46" ry="15" transform="rotate(-14 60 104)" fill="#dff0f4" stroke="#7fb0bc" stroke-width="2.5"/>'
    '<ellipse cx="140" cy="104" rx="46" ry="15" transform="rotate(14 140 104)" fill="#dff0f4" stroke="#7fb0bc" stroke-width="2.5"/>'
    '<ellipse cx="66" cy="134" rx="42" ry="13" transform="rotate(10 66 134)" fill="#eaf6f8" stroke="#7fb0bc" stroke-width="2.5"/>'
    '<ellipse cx="134" cy="134" rx="42" ry="13" transform="rotate(-10 134 134)" fill="#eaf6f8" stroke="#7fb0bc" stroke-width="2.5"/>'
    '<ellipse cx="100" cy="148" rx="10" ry="50" fill="#3a9ab0"/>'
    + ''.join('<path d="M92 %d L108 %d" stroke="#1e6a7e" stroke-width="2.5"/>' % (y, y)
              for y in [126, 146, 166, 186])
    + '<path d="M100 98 L100 118" stroke="#1e6a7e" stroke-width="12"/>'
    '<circle cx="100" cy="72" r="24" fill="#3a9ab0"/>'
    '<circle cx="88" cy="68" r="14" fill="#dff0f4" stroke="#1e6a7e" stroke-width="2.5"/>'
    '<circle cx="112" cy="68" r="14" fill="#dff0f4" stroke="#1e6a7e" stroke-width="2.5"/>'
    '<circle cx="88" cy="68" r="6" fill="#1a2c34"/><circle cx="112" cy="68" r="6" fill="#1a2c34"/>'
    '<path d="M88 96 C84 106 78 110 72 110 M112 96 C116 106 122 110 128 110"'
    ' stroke="#1e6a7e" stroke-width="4" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "firefly", "cn": "萤火虫", "en": "Firefly", "series": "bug",
  "tint": "#c8a83a", "dark": "#7a6210",
  "skill": "肚子会发光 · 光是拿来聊天的",
  "facts": [
    "线索一：这些卵也发一点微光，产在潮湿的草丛里。孵出来的小家伙住在土里，专门吃蜗牛，一住就是一两年。",
    "线索二：它从出生到长大大体一直亮着，只是小时候很弱。最后一次蜕皮之后长出翅膀，才变成会飞的那种。",
    "线索三：它肚子最后两节里有专门发光的器官，冷冰冰的，一点也不烫。它一闪一闪，是在跟同伴打招呼、说自己在哪儿。它叫萤火虫。",
  ],
  "body": (
    '<circle cx="100" cy="164" r="44" fill="#e8e04a" opacity=".18"/>'
    '<path d="M88 112 C60 92 44 100 52 122 C60 142 82 146 94 134 Z" fill="#e8e4d4" opacity=".85" stroke="#b0a888" stroke-width="2"/>'
    '<path d="M112 112 C140 92 156 100 148 122 C140 142 118 146 106 134 Z" fill="#e8e4d4" opacity=".85" stroke="#b0a888" stroke-width="2"/>'
    '<ellipse cx="100" cy="128" rx="21" ry="34" fill="#3a3228"/>'
    '<ellipse cx="100" cy="160" rx="18" ry="22" fill="#e8e04a"/>'
    '<ellipse cx="100" cy="160" rx="10" ry="12" fill="#f7f2a8"/>'
    '<circle cx="100" cy="88" r="18" fill="#4a4034"/>'
    '<circle cx="92" cy="86" r="7" fill="#fff"/><circle cx="91" cy="87" r="4" fill="#1a1610"/>'
    '<circle cx="108" cy="86" r="7" fill="#fff"/><circle cx="109" cy="87" r="4" fill="#1a1610"/>'
    '<path d="M92 72 C86 60 78 56 72 58 M108 72 C114 60 122 56 128 58"'
    ' stroke="#4a4034" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "cicada", "cn": "蝉", "en": "Cicada", "series": "bug",
  "tint": "#6a7a5a", "dark": "#3e4a34",
  "skill": "地下待好几年 · 唱歌的是男生",
  "facts": [
    "线索一：这些卵插在树枝里，孵出来的小家伙一落到地上，就钻进土里，抱住树根吸汁水。",
    "线索二：它在地底下要待上好几年，蜕好几次皮慢慢长大。等到某个夏天的晚上，它才爬出地面，爬上树。",
    "线索三：它爬上树后，背上裂开，钻出一个带翅膀的身体，留下一个空壳挂在树上。会大声唱歌的全是男生，女生不响。它叫蝉。",
  ],
  "body": (
    '<path d="M84 116 L34 194 L66 200 L98 142 Z" fill="#e4ecdc" opacity=".85" stroke="#9aa894" stroke-width="2"/>'
    '<path d="M116 116 L166 194 L134 200 L102 142 Z" fill="#e4ecdc" opacity=".85" stroke="#9aa894" stroke-width="2"/>'
    '<ellipse cx="100" cy="152" rx="25" ry="46" fill="#6a7a5a"/>'
    + ''.join('<path d="M79 %d L121 %d" stroke="#3e4a34" stroke-width="2.5" opacity=".7"/>' % (y, y)
              for y in [128, 148, 168, 186])
    + '<ellipse cx="100" cy="110" rx="26" ry="20" fill="#7a8a68"/>'
    '<ellipse cx="100" cy="78" rx="32" ry="22" fill="#6a7a5a"/>'
    '<circle cx="74" cy="74" r="13" fill="#f0f4ea" stroke="#3e4a34" stroke-width="2.5"/>'
    '<circle cx="126" cy="74" r="13" fill="#f0f4ea" stroke="#3e4a34" stroke-width="2.5"/>'
    '<circle cx="72" cy="75" r="6.5" fill="#1e2418"/><circle cx="128" cy="75" r="6.5" fill="#1e2418"/>'
    '<path d="M92 58 C88 46 82 42 76 42 M108 58 C112 46 118 42 124 42"'
    ' stroke="#3e4a34" stroke-width="3" fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d 122 L%d 176 L%d 198" stroke="#4e5c42" stroke-width="4.5" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(84,56,44), (94,78,68), (106,122,132), (116,144,156)])
  ),
},
{
  "id": "mantis", "cn": "螳螂", "en": "Mantis", "series": "bug",
  "tint": "#6aa84a", "dark": "#3e6a2a",
  "skill": "前腿像折刀 · 头能转过来看背后",
  "facts": [
    "线索一：这些卵装在一团硬硬的、像泡沫一样的壳里，粘在树枝上过冬。一个小壳里能装一百多个小家伙。",
    "线索二：小家伙孵出来就长着妈妈的样子，只是小得可怜。它们一出生就各自散开，连兄弟姐妹也互相躲着。",
    "线索三：它前面两条腿像折起来的刀，收着时看不出厉害，一伸出去就夹住了。它的头能转过去看背后。它叫螳螂。",
  ],
  "body": (
    ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#4e8a38" stroke-width="6" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(108,116,140,146,150,178), (112,132,148,166,158,196),
                        (92,120,64,150,58,182)])
    + '<path d="M104 178 C116 200 106 208 92 204" stroke="#4e8a38" stroke-width="13"'
    ' fill="none" stroke-linecap="round"/>'
    '<ellipse cx="106" cy="146" rx="17" ry="46" transform="rotate(11 106 146)" fill="#6aa84a"/>'
    '<path d="M100 100 L124 106 L116 132 L94 124 Z" fill="#5a9440"/>'
    '<path d="M96 62 L132 76 L104 96 Z" fill="#6aa84a"/>'
    '<path d="M126 66 L156 52 L154 78 Z" fill="#6aa84a"/>'
    '<path d="M96 62 L100 96" stroke="#3e6a2a" stroke-width="2.5"/>'
    '<circle cx="118" cy="76" r="9" fill="#f0f4e8"/><circle cx="122" cy="77" r="5" fill="#1e2c18"/>'
    '<path d="M92 100 C72 96 56 108 58 126 C60 144 78 150 88 140"'
    ' stroke="#5a9440" stroke-width="10" fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#3e6a2a" stroke-width="4" stroke-linecap="round"/>' % s
              for s in [(62,118,50,108), (60,134,46,130), (68,146,58,158)])
    + '<path d="M96 50 C86 36 74 32 64 36 M120 52 C130 40 142 36 150 40"'
    ' stroke="#3e6a2a" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "dungbeetle", "cn": "屎壳郎", "en": "Dung beetle", "series": "bug",
  "tint": "#4a3a2a", "dark": "#241a10",
  "skill": "推着球倒着走 · 靠星星认路",
  "facts": [
    "线索一：这些卵不产在地上，而是产在一个滚好的圆球里，埋进土中。小家伙就在球里孵出来，一出来就有吃的。",
    "线索二：它在球里长成胖胖的白虫，把整个球吃光，才在土里变成带壳的样子，再自己挖出来。",
    "线索三：它把这个球用后腿推着倒着走。夜里没有路标，它靠天上的星河认方向，走的是一条直线。它叫屎壳郎。",
  ],
  "body": (
    '<circle cx="52" cy="166" r="34" fill="#7a5c3a"/>'
    '<circle cx="52" cy="166" r="34" fill="none" stroke="#5a4028" stroke-width="3"/>'
    '<path d="M30 148 C46 160 46 182 32 194 M74 148 C58 160 58 182 72 194"'
    ' stroke="#5a4028" stroke-width="2.5" fill="none"/>'
    '<ellipse cx="134" cy="152" rx="42" ry="36" fill="#4a3a2a"/>'
    '<ellipse cx="134" cy="152" rx="42" ry="36" fill="none" stroke="#241a10" stroke-width="3"/>'
    '<path d="M134 118 L134 186" stroke="#241a10" stroke-width="3.5"/>'
    '<ellipse cx="140" cy="112" rx="26" ry="20" fill="#5a4632"/>'
    '<path d="M122 100 C104 92 92 76 96 62" stroke="#2e2418" stroke-width="7"'
    ' fill="none" stroke-linecap="round"/>'
    '<path d="M96 62 L86 54" stroke="#2e2418" stroke-width="5" stroke-linecap="round"/>'
    '<circle cx="128" cy="106" r="7" fill="#fff"/><circle cx="127" cy="107" r="4" fill="#1a1208"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#2e2418" stroke-width="5.5" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(102,158,82,146,72,160), (100,176,78,180,66,190),
                        (166,150,184,166,188,188), (162,176,172,194,168,202)])
    + '<path d="M66 192 L62 204 M176 190 L184 200" stroke="#2e2418" stroke-width="3.5"/>'
  ),
},
{
  "id": "silkworm", "cn": "蚕", "en": "Silkworm", "series": "bug",
  "tint": "#d8c8a0", "dark": "#8a7850",
  "skill": "吐一根丝能拉一千米",
  "facts": [
    "线索一：这些卵小得像一粒粒芝麻，孵出来的小家伙黑黑的、毛茸茸的，只有蚂蚁那么大。",
    "线索二：它一天到晚只干一件事——吃叶子。吃几天就撑得皮绷不住，蜕一次皮，再吃，一生长大要蜕四次。",
    "线索三：长够之后它不吃也不动，从嘴里吐出一根不断的丝，把自己一圈圈裹起来。一根丝拉直能有一千米长，人拿它织成绸子。它叫蚕。",
  ],
  "body": (
    '<path d="M30 176 C60 156 132 154 172 172 C150 196 54 198 30 176 Z" fill="#6aa84a"/>'
    '<path d="M100 160 L100 194" stroke="#3e6a2a" stroke-width="3" opacity=".8"/>'
    '<path d="M100 160 L58 188 M100 160 L142 188 M100 160 L36 178 M100 160 L164 178"'
    ' stroke="#3e6a2a" stroke-width="2" opacity=".6"/>'
    + ''.join('<ellipse cx="%d" cy="%d" rx="24" ry="22" fill="#e8dcc0" stroke="#b0a078" stroke-width="2.5"/>' % p
              for p in [(66,112), (110,104), (150,124), (168,150)])
    + ''.join('<path d="M%d %d L%d %d" stroke="#b0a078" stroke-width="2" opacity=".85"/>' % s
              for s in [(48,96,74,124), (90,88,116,120), (130,112,158,138), (152,138,176,164)])
    + '<circle cx="48" cy="108" r="26" fill="#e8dcc0" stroke="#b0a078" stroke-width="2.5"/>'
    '<circle cx="40" cy="102" r="6" fill="#3a3020"/><circle cx="56" cy="102" r="6" fill="#3a3020"/>'
    '<path d="M42 122 C48 128 56 128 62 122" stroke="#8a7850" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#8a7850" stroke-width="4" stroke-linecap="round"/>' % s
              for s in [(86,130,80,146), (120,124,126,142), (158,142,166,158)])
  ),
},
{
  "id": "rhinobeetle", "cn": "独角仙", "en": "Rhinoceros beetle", "series": "bug",
  "tint": "#5a3a24", "dark": "#2e1c10",
  "skill": "头上长角 · 能顶起自己八百倍重",
  "facts": [
    "线索一：这些卵产在烂木头或腐叶堆里。孵出来的小家伙是白白胖胖的一条，在腐土里慢慢啃着长大，一住就是大半年。",
    "线索二：长够之后它自己做一个土壳把自己关起来，在里面化开重拼，过一阵才带着硬壳和角钻出来。",
    "线索三：它头上顶着一只向前弯的角，前面还有一只小角，打架时能把对手挑起来甩出去。它能顶起比自己重八百倍的东西。它叫独角仙。",
  ],
  "body": (
    '<ellipse cx="104" cy="152" rx="52" ry="42" fill="#5a3a24"/>'
    '<ellipse cx="104" cy="152" rx="52" ry="42" fill="none" stroke="#2e1c10" stroke-width="3"/>'
    '<path d="M104 112 L104 192" stroke="#2e1c10" stroke-width="4"/>'
    '<path d="M62 124 C82 140 82 164 64 180 M146 124 C126 140 126 164 144 180"'
    ' stroke="#2e1c10" stroke-width="2.5" fill="none" opacity=".8"/>'
    '<ellipse cx="108" cy="108" rx="30" ry="20" fill="#6a4630"/>'
    '<path d="M84 96 C66 84 54 64 62 46 C76 44 90 58 96 78"'
    ' fill="#6a4630" stroke="#2e1c10" stroke-width="3"/>'
    '<path d="M128 94 C144 82 152 66 146 54" stroke="#6a4630" stroke-width="7"'
    ' fill="none" stroke-linecap="round"/>'
    '<circle cx="92" cy="106" r="8" fill="#fff"/><circle cx="91" cy="107" r="4.5" fill="#1a1008"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#2e1c10" stroke-width="6" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(66,154,44,152,34,170), (64,172,42,180,32,196),
                        (142,154,164,152,174,170), (144,172,166,180,176,196)])
    + '<path d="M32 196 L22 202 M176 196 L186 202" stroke="#2e1c10" stroke-width="3.5"/>'
  ),
},
{
  "id": "mosquito", "cn": "蚊子", "en": "Mosquito", "series": "bug",
  "tint": "#8a7a6a", "dark": "#4a3a30",
  "skill": "靠闻汗味找人 · 咬人的都是女生",
  "facts": [
    "线索一：这些卵产在水面上，一粒粒粘成一排像小黑筏子。孵出来的小家伙在水里扭来扭去，靠一根管子探出水面呼吸。",
    "线索二：它在水里蜕几次皮，最后一次变成一个不吃的壳，浮在水面裂开，飞出一个带翅膀的身体。前后只要十来天。",
    "线索三：它靠闻人身上的汗味和呼出的气来找人。咬人吸血的全是女生，男生只喝花里的甜水。它叫蚊子。",
  ],
  "body": (
    # 细长口器 + 六条细长腿，别画胖，一胖就成苍蝇了
    '<ellipse cx="70" cy="76" rx="36" ry="9" transform="rotate(-28 70 76)"'
    ' fill="#dfe0dc" opacity=".85" stroke="#b0a89c" stroke-width="1.8"/>'
    '<ellipse cx="130" cy="72" rx="34" ry="8" transform="rotate(26 130 72)"'
    ' fill="#dfe0dc" opacity=".85" stroke="#b0a89c" stroke-width="1.8"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#4a3a30" stroke-width="3" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(96,126,66,150,48,146), (104,152,82,176,66,182),
                        (116,140,146,152,168,148), (120,162,140,184,160,196)])
    + '<path d="M104 106 C112 138 116 164 118 190" stroke="#8a7a6a" stroke-width="15"'
    ' fill="none" stroke-linecap="round"/>'
    '<path d="M104 106 C112 138 116 164 118 190" stroke="#4a3a30" stroke-width="2"'
    ' fill="none" opacity=".4"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#4a3a30" stroke-width="2" opacity=".6"/>' % s
              for s in [(106,126,120,142), (108,148,122,164), (110,170,122,184)])
    + '<circle cx="90" cy="96" r="19" fill="#8a7a6a"/>'
    '<path d="M80 82 C68 60 56 50 44 46 M98 78 C106 58 118 48 130 44"'
    ' stroke="#4a3a30" stroke-width="3" fill="none" stroke-linecap="round"/>'
    '<circle cx="82" cy="92" r="10" fill="#fff"/><circle cx="81" cy="93" r="5.5" fill="#1e1610"/>'
    '<circle cx="100" cy="92" r="10" fill="#fff"/><circle cx="101" cy="93" r="5.5" fill="#1e1610"/>'
    '<path d="M74 108 L26 142" stroke="#3a2e26" stroke-width="4" stroke-linecap="round"/>'
  ),
},

# ============================ 爬行 ============================
{
  "id": "chameleon", "cn": "变色龙", "en": "Chameleon", "series": "rept",
  "tint": "#8fc4a0", "dark": "#4a7a5c",
  "skill": "双眼各看各的 · 弹舌捕虫",
  "facts": [
    "线索一：这些蛋埋在土里，一窝十几到几十颗。妈妈下完就不管了，全靠土壤的温度慢慢孵，要等好几个月。",
    "线索二：小家伙一破壳就自己爬出来找虫子吃。它两只眼睛能各看各的方向，一只看左边，一只看右边。",
    "线索三：它变色主要不是为了躲藏，而是为了调体温和跟同伴说话。舌头弹出去能超过身体长度的一倍半。它叫变色龙。",
  ],
  "body": (
    '<path d="M150 168 C178 168 188 146 176 132 C167 121 152 126 152 139 C152 148 161 150 165 146"'
    ' stroke="#6fc48a" stroke-width="13" fill="none" stroke-linecap="round"/>'
    '<path d="M60 118 L70 103 L80 118 L92 103 L104 118 L116 103 L128 118 L140 105 L148 120 Z" fill="#4f9c6a"/>'
    '<ellipse cx="104" cy="140" rx="52" ry="36" fill="#6fc48a"/>'
    '<ellipse cx="72" cy="118" rx="34" ry="30" fill="#7ed09a"/>'
    '<path d="M54 96 C58 77 77 75 85 90 C72 88 62 92 54 96 Z" fill="#4f9c6a"/>'
    '<path d="M42 127 C48 135 58 137 66 133" stroke="#3f8c5c" stroke-width="4.5" fill="none" stroke-linecap="round"/>'
    '<circle cx="76" cy="112" r="19" fill="#8fe0aa"/>'
    '<circle cx="76" cy="112" r="11" fill="#f7f0c0"/>'
    '<circle cx="76" cy="112" r="5.5" fill="#2a3a2e"/>'
    '<circle cx="78" cy="110" r="2" fill="#fff"/>'
    '<path d="M74 172 l-6 12 M82 174 l0 12 M90 172 l6 12" stroke="#4f9c6a" stroke-width="7" stroke-linecap="round" fill="none"/>'
    '<path d="M126 172 l-6 12 M134 174 l0 12" stroke="#4f9c6a" stroke-width="7" stroke-linecap="round" fill="none"/>'
  ),
},
{
  "id": "gecko", "cn": "壁虎", "en": "Gecko", "series": "rept",
  "tint": "#c8b48a", "dark": "#8a7850",
  "skill": "脚底有细毛 · 天花板也能倒着走",
  "facts": [
    "线索一：这些蛋只有黄豆大，白白的、壳很软，常常两个粘在一起贴在墙角或树皮上。",
    "线索二：小家伙一破壳就长着爸妈的样子，只是小得多。它脚趾下面有一片片细毛，能扒住最滑的玻璃。",
    "线索三：它脚趾上那片细毛靠看不见的吸力贴住墙面，天花板也能倒着走。尾巴断了还能再长一条。它叫壁虎。",
  ],
  "body": (
    '<path d="M152 152 C180 148 192 128 184 108 C178 94 164 96 162 108"'
    ' stroke="#c8b48a" stroke-width="19" fill="none" stroke-linecap="round"/>'
    '<ellipse cx="106" cy="146" rx="48" ry="27" fill="#c8b48a"/>'
    '<path d="M64 138 C48 128 42 112 50 98" stroke="#c8b48a" stroke-width="22"'
    ' fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#c8b48a" stroke-width="10" stroke-linecap="round"/>' % s
              for s in [(82,168,66,196), (104,170,104,200), (128,168,144,196),
                        (66,124,44,132), (66,114,42,100)])
    + ''.join('<circle cx="%d" cy="%d" r="7" fill="#d8c49c"/>' % p
              for p in [(64,198), (104,202), (146,198), (42,134), (40,98)])
    + '<ellipse cx="52" cy="86" rx="27" ry="21" fill="#d8c49c"/>'
    '<circle cx="42" cy="80" r="12" fill="#f7f2e0"/><circle cx="42" cy="80" r="4" fill="#2a2418"/>'
    '<path d="M42 68 L42 92" stroke="#2a2418" stroke-width="3"/>'
    '<circle cx="60" cy="76" r="9" fill="#f7f2e0"/><circle cx="60" cy="76" r="3.5" fill="#2a2418"/>'
    '<path d="M60 67 L60 85" stroke="#2a2418" stroke-width="2.5"/>'
    '<path d="M34 68 C28 58 22 54 16 54" stroke="#8a7850" stroke-width="3" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "python", "cn": "蟒蛇", "en": "Python", "series": "rept",
  "tint": "#9a8a5a", "dark": "#5a4a28",
  "skill": "不用毒 · 靠一圈圈收紧",
  "facts": [
    "线索一：这些蛋比鸡蛋大得多，一窝能有三四十颗。妈妈盘在蛋堆上，靠身体一抖一抖地发热，孵上两三个月。",
    "线索二：小家伙一破壳就有半米长，从第一天起就会自己缠住猎物。它不追，蹲着等，靠嘴边的热窝感知温度找到对方。",
    "线索三：它没有毒，靠一圈圈收紧把猎物勒住。它能一口气吞下比自己头大好几倍的整只猎物，下巴能脱开。它叫蟒蛇。",
  ],
  "body": (
    '<path d="M58 100 C50 136 40 172 56 192 C76 210 116 206 124 186'
    ' C132 166 112 152 96 162 C82 172 90 192 108 192"'
    ' stroke="#9a8a5a" stroke-width="30" fill="none" stroke-linecap="round"/>'
    '<path d="M58 100 C50 136 40 172 56 192 C76 210 116 206 124 186'
    ' C132 166 112 152 96 162 C82 172 90 192 108 192"'
    ' stroke="#5a4a28" stroke-width="30" fill="none" stroke-linecap="round"'
    ' stroke-dasharray="5 17" opacity=".45"/>'
    '<ellipse cx="60" cy="76" rx="32" ry="25" fill="#a89767"/>'
    '<ellipse cx="60" cy="76" rx="32" ry="25" fill="none" stroke="#5a4a28" stroke-width="3"/>'
    '<circle cx="46" cy="68" r="8" fill="#f7f0d0"/><circle cx="46" cy="68" r="3.5" fill="#2a2410"/>'
    '<circle cx="74" cy="68" r="8" fill="#f7f0d0"/><circle cx="74" cy="68" r="3.5" fill="#2a2410"/>'
    '<path d="M56 96 L56 110 M64 96 L64 110" stroke="#5a4a28" stroke-width="4" stroke-linecap="round"/>'
    '<path d="M60 112 C56 128 50 140 44 150 M60 112 C64 128 70 140 76 150"'
    ' stroke="#c85a6a" stroke-width="4" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "cobra", "cn": "眼镜蛇", "en": "Cobra", "series": "rept",
  "tint": "#6a6a4a", "dark": "#3a3a24",
  "skill": "脖子能撑开 · 喷毒几米远",
  "facts": [
    "线索一：这些蛋产在一堆枯叶里，一窝二三十颗。妈妈会守在旁边，谁靠近就昂起头来吓唬谁。",
    "线索二：小家伙一破壳就带毒，从第一天起就能自己捕食。它脖子两侧的皮能撑开，看着比实际大一圈。",
    "线索三：它脖子后面有一对像眼镜一样的斑纹，一撑开就吓退敌人。它的毒能让人喘不上气，有的还会喷出几米远。它叫眼镜蛇。",
  ],
  "body": (
    '<path d="M78 204 C70 168 84 128 94 100" stroke="#6a6a4a" stroke-width="32"'
    ' fill="none" stroke-linecap="round"/>'
    '<path d="M94 102 C56 94 38 70 54 48 C74 26 126 24 148 46 C164 64 150 94 106 102 Z"'
    ' fill="#7a7a56" stroke="#3a3a24" stroke-width="3"/>'
    '<path d="M74 66 C86 84 114 84 126 66" stroke="#3a3a24" stroke-width="5"'
    ' fill="none" stroke-linecap="round"/>'
    '<ellipse cx="100" cy="66" rx="36" ry="23" fill="#6a6a4a"/>'
    '<circle cx="84" cy="60" r="7" fill="#f7f0d0"/><circle cx="84" cy="60" r="3.5" fill="#1e1e10"/>'
    '<circle cx="116" cy="60" r="7" fill="#f7f0d0"/><circle cx="116" cy="60" r="3.5" fill="#1e1e10"/>'
    '<path d="M100 86 L100 104 M100 104 L90 116 M100 104 L110 116"'
    ' stroke="#c85a6a" stroke-width="4" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "crocodile", "cn": "鳄鱼", "en": "Crocodile", "series": "rept",
  "tint": "#4a6a4a", "dark": "#26402a",
  "skill": "下巴只能上下撕 · 咬合力最强的嘴",
  "facts": [
    "线索一：这些蛋埋在河边的沙土或烂草堆里，一窝几十颗。妈妈守在旁边，谁靠近就张着大嘴冲过去。",
    "线索二：小家伙在蛋里就会叫，妈妈听见了会扒开土帮它们出来。它一出生就长着牙，自己下水找吃的。",
    "线索三：它背上排着一行行硬疙瘩，尾巴又长又有力，能在水里把猎物扫晕。它的下巴不能左右嚼，只能往下撕。它叫鳄鱼。",
  ],
  "body": (
    '<path d="M150 170 C180 168 194 148 188 126 C184 108 168 102 158 110"'
    ' stroke="#4a6a4a" stroke-width="24" fill="none" stroke-linecap="round"/>'
    '<ellipse cx="116" cy="158" rx="54" ry="32" fill="#4a6a4a"/>'
    '<path d="M74 140 L18 148 L18 162 L74 160 Z" fill="#4a6a4a"/>'
    '<path d="M74 130 L22 138 L22 150 L74 150 Z" fill="#567a56"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d Z" fill="#f7f2e0"/>' % s
              for s in [(60,150,64,162,56,161), (48,151,52,163,44,162), (36,152,40,164,32,163)])
    + ''.join('<path d="M%d %d L%d %d L%d %d Z" fill="#26402a"/>' % s
              for s in [(78,132,88,114,96,134), (100,130,112,110,120,132),
                        (124,132,138,114,144,134), (150,136,164,122,166,142)])
    + '<circle cx="92" cy="126" r="9" fill="#f7f0c0"/><circle cx="92" cy="126" r="3.5" fill="#1a2418"/>'
    '<path d="M96 118 C104 110 116 110 124 116" stroke="#26402a" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#3a5a3a" stroke-width="11" stroke-linecap="round"/>' % s
              for s in [(90,180,78,198), (132,180,144,198)])
  ),
},
{
  "id": "tortoise", "cn": "陆龟", "en": "Tortoise", "series": "rept",
  "tint": "#7a6a4a", "dark": "#4a3a24",
  "skill": "壳跟肋骨长在一起 · 能活一百多岁",
  "facts": [
    "线索一：这些蛋是白的、圆圆的。妈妈用后腿在沙土里挖个坑，把蛋产进去再埋好，然后就走。",
    "线索二：小家伙要自己顶开蛋壳，从土里爬出来。它一出生背上就带着那副硬壳，一辈子背着，越长越大。",
    "线索三：它背上那副壳是和肋骨长在一起的，脱不下来。它的腿粗得像柱子，能在干旱的地方几个月不吃不喝。它叫陆龟。",
  ],
  "body": (
    '<path d="M56 172 L52 196" stroke="#8a7a5a" stroke-width="22" stroke-linecap="round"/>'
    '<path d="M146 172 L150 196" stroke="#8a7a5a" stroke-width="22" stroke-linecap="round"/>'
    '<ellipse cx="34" cy="152" rx="26" ry="19" fill="#8a7a5a"/>'
    '<circle cx="24" cy="144" r="6" fill="#2a2418"/>'
    '<path d="M12 158 C6 160 4 166 8 170" stroke="#6a5a3a" stroke-width="3" fill="none" stroke-linecap="round"/>'
    '<path d="M100 66 C158 66 182 104 182 138 C182 168 144 184 100 184'
    ' C56 184 18 168 18 138 C18 104 42 66 100 66 Z" fill="#7a6a4a"/>'
    '<path d="M100 66 C158 66 182 104 182 138 C182 168 144 184 100 184'
    ' C56 184 18 168 18 138 C18 104 42 66 100 66 Z" fill="none" stroke="#4a3a24" stroke-width="4"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#4a3a24" stroke-width="3"/>' % s
              for s in [(100,68,60,120), (100,68,140,120), (60,120,140,120),
                        (60,120,44,164), (140,120,156,164), (60,120,100,182),
                        (140,120,100,182)])
    + '<ellipse cx="100" cy="120" rx="40" ry="30" fill="#8a7a5a" opacity=".55"/>'
  ),
},
{
  "id": "komodo", "cn": "科莫多巨蜥", "en": "Komodo dragon", "series": "rept",
  "tint": "#6a5a44", "dark": "#3a2e1e",
  "skill": "世界最大的蜥蜴 · 咬一口等它慢慢倒",
  "facts": [
    "线索一：这些蛋埋在土坑或白蚁堆里，一窝二十来颗。妈妈守着，怕别的同类来挖。",
    "线索二：小家伙一破壳就赶紧爬树，因为大个子的同类会把它当点心。它在树上待好几年，长够大了才下来。",
    "线索三：它是世界上最大的那种，能长到三米。它嘴里带着几十种细菌，咬一口就跑，等对方慢慢倒下。它叫科莫多巨蜥。",
  ],
  "body": (
    '<path d="M152 168 C186 166 200 146 194 122" stroke="#6a5a44" stroke-width="21"'
    ' fill="none" stroke-linecap="round"/>'
    '<ellipse cx="112" cy="160" rx="56" ry="27" fill="#6a5a44"/>'
    '<path d="M62 154 C46 148 38 138 40 126" stroke="#6a5a44" stroke-width="21"'
    ' fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#3a2e1e" stroke-width="5" stroke-linecap="round"/>' % s
              for s in [(84,136,80,126), (100,134,98,124), (116,134,118,124),
                        (132,136,138,126), (148,142,156,132)])
    + '<ellipse cx="48" cy="116" rx="30" ry="18" fill="#7a6a54"/>'
    '<circle cx="42" cy="110" r="7" fill="#f7f0d0"/><circle cx="42" cy="110" r="3.5" fill="#1e1610"/>'
    '<path d="M22 122 L2 128 M2 128 L-8 120 M2 128 L-8 136"'
    ' stroke="#c85a6a" stroke-width="4" fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#4a3e2e" stroke-width="11" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(78,180,58,196,52,200), (146,180,166,196,172,200)])
  ),
},
{
  "id": "iguana", "cn": "绿鬣蜥", "en": "Green iguana", "series": "rept",
  "tint": "#5aa84a", "dark": "#2e6a2a",
  "skill": "背上一排尖刺 · 下巴挂着肉片",
  "facts": [
    "线索一：这些蛋是白的、软壳的，一窝二三十颗，埋在河边的沙里，孵上三个月。",
    "线索二：小家伙一破壳就长着背上那排尖片，只是很短。它住在靠水的树上，一有危险就跳进水里游走。",
    "线索三：它下巴上挂着一片圆圆的肉，背上排着一行尖刺。它吃素的，吃叶子花果，尾巴一甩能抽疼人。它叫绿鬣蜥。",
  ],
  "body": (
    '<path d="M156 154 C188 154 200 134 196 110" stroke="#5aa84a" stroke-width="19"'
    ' fill="none" stroke-linecap="round"/>'
    '<ellipse cx="108" cy="150" rx="56" ry="30" fill="#5aa84a"/>'
    '<circle cx="40" cy="142" r="15" fill="#7ac868"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d Z" fill="#2e6a2a"/>' % s
              for s in [(62,124,66,100,74,122), (80,120,86,94,94,118),
                        (98,118,106,92,114,118), (118,118,128,94,134,120),
                        (138,122,150,100,152,126), (158,128,172,110,170,136),
                        (176,140,190,124,186,148)])
    + '<ellipse cx="54" cy="124" rx="30" ry="20" fill="#6ab85a"/>'
    '<circle cx="44" cy="118" r="8" fill="#f7f0c0"/><circle cx="44" cy="118" r="4" fill="#1e2c18"/>'
    '<path d="M30 132 C34 142 46 144 56 138" stroke="#2e6a2a" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#3e8a36" stroke-width="12" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(74,172,56,190,50,196), (140,172,158,190,164,196)])
  ),
},
{
  "id": "rattlesnake", "cn": "响尾蛇", "en": "Rattlesnake", "series": "rept",
  "tint": "#b0a070", "dark": "#6a5c34",
  "skill": "尾巴会沙沙响 · 靠热窝看见温度",
  "facts": [
    "线索一：这些蛋不产下来，是在妈妈肚子里就孵好了，一胎能生十几条。小家伙生下来就有毒。",
    "线索二：小家伙尾巴尖上只有一个不响的小疙瘩，每蜕一次皮就多一环，长到五六环才摇得出声。",
    "线索三：它尾巴尖上那一串空环一摇就沙沙响，是警告你别过来。它靠嘴边的热窝在黑暗里看得见温度。它叫响尾蛇。",
  ],
  "body": (
    '<path d="M132 202 L140 208 L146 200 L152 210 L160 202 L166 212"'
    ' stroke="#8a7a4a" stroke-width="6" fill="none" stroke-linejoin="round" stroke-linecap="round"/>'
    '<path d="M58 100 C50 138 42 176 56 198 C76 214 116 208 122 188'
    ' C128 168 108 156 94 166 C82 176 92 194 108 192"'
    ' stroke="#b0a070" stroke-width="26" fill="none" stroke-linecap="round"/>'
    '<path d="M58 100 C50 138 42 176 56 198 C76 214 116 208 122 188'
    ' C128 168 108 156 94 166 C82 176 92 194 108 192"'
    ' stroke="#6a5c34" stroke-width="26" fill="none" stroke-linecap="round"'
    ' stroke-dasharray="3 15" opacity=".5"/>'
    '<ellipse cx="60" cy="76" rx="32" ry="23" fill="#bcac7c"/>'
    '<ellipse cx="60" cy="76" rx="32" ry="23" fill="none" stroke="#6a5c34" stroke-width="3"/>'
    '<circle cx="46" cy="68" r="7" fill="#f7f0d0"/><circle cx="46" cy="68" r="3" fill="#2a2410"/>'
    '<circle cx="74" cy="68" r="7" fill="#f7f0d0"/><circle cx="74" cy="68" r="3" fill="#2a2410"/>'
    '<circle cx="52" cy="60" r="3.5" fill="#6a5c34"/><circle cx="68" cy="60" r="3.5" fill="#6a5c34"/>'
    '<path d="M60 96 L60 108 M60 108 L50 118 M60 108 L70 118"'
    ' stroke="#c85a6a" stroke-width="4" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "frilled", "cn": "伞蜥", "en": "Frilled lizard", "series": "rept",
  "tint": "#c8a05a", "dark": "#8a6428",
  "skill": "撑开脖子吓人 · 用两条后腿跑",
  "facts": [
    "线索一：这些蛋埋在土里，一窝十几颗。妈妈下完就走，靠土温慢慢孵。",
    "线索二：小家伙一破壳脖子上就带着那圈皱皮，只是还撑不太开。它天生会跑，而且跑起来只用后腿。",
    "线索三：它一害怕就把脖子那圈皱皮整个撑开，撑得比身子还宽，再张大嘴吓人。它逃跑时两条后腿直立奔跑。它叫伞蜥。",
  ],
  "body": (
    # 皱皮领子：小一圈，别做成一圈鬃毛——做大了会读成狮子
    ''.join('<g transform="translate(84,120) rotate(%d)">'
              '<path d="M0 0 L-12 -46 L12 -42 Z" fill="#d0a860" stroke="#8a6428"'
              ' stroke-width="2.5" stroke-linejoin="round"/></g>' % ang
              for ang in range(-140, 141, 20))
    + '<path d="M152 152 C184 152 196 132 190 108" stroke="#c8a05a" stroke-width="20"'
    ' fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d Z" fill="#8a6428"/>' % s
              for s in [(102,134,110,120,118,136), (124,130,134,116,140,134),
                        (146,132,158,120,160,140)])
    + '<ellipse cx="116" cy="148" rx="52" ry="30" fill="#c8a05a"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#b08a46" stroke-width="12" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(88,174,66,194,60,200), (144,174,166,194,172,200)])
    + '<path d="M92 134 C82 118 72 108 60 104" stroke="#c8a05a" stroke-width="26"'
    ' fill="none" stroke-linecap="round"/>'
    '<ellipse cx="54" cy="106" rx="34" ry="24" transform="rotate(-12 54 106)" fill="#d8b06a"/>'
    '<path d="M30 100 C14 96 4 88 2 80 C14 80 28 84 40 92 Z" fill="#d8b06a"/>'
    '<path d="M22 116 C30 132 48 138 62 130" stroke="#8a6428" stroke-width="4.5"'
    ' fill="none" stroke-linecap="round"/>'
    '<circle cx="46" cy="98" r="10" fill="#f7f0d0"/><circle cx="46" cy="98" r="5" fill="#2a2410"/>'
    '<circle cx="34" cy="82" r="3.5" fill="#8a6428"/>'
    '<path d="M74 88 C80 78 88 74 96 76" stroke="#8a6428" stroke-width="3.5"'
    ' fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "thornydevil", "cn": "魔蜥", "en": "Thorny devil", "series": "rept",
  "tint": "#c08a5a", "dark": "#7a4e26",
  "skill": "皮肤能喝水 · 脖子后面有个假脑袋",
  "facts": [
    "线索一：这些蛋埋在沙洞里，一窝三五颗，孵上三四个月。",
    "线索二：小家伙一破壳就浑身长着硬刺，走起路来一顿一顿的，好像风一吹就要倒。",
    "线索三：它从头到尾披着一身尖刺，喝水不用嘴——皮肤上的沟槽能把露水一路送到嘴里。它脖子后面还有一个假脑袋。它叫魔蜥。",
  ],
  "body": (
    '<ellipse cx="104" cy="150" rx="52" ry="34" fill="#c08a5a"/>'
    '<path d="M150 154 C176 152 188 136 184 118" stroke="#c08a5a" stroke-width="19"'
    ' fill="none" stroke-linecap="round"/>'
    ''.join('<path d="M%d %d L%d %d" stroke="#7a4e26" stroke-width="7" stroke-linecap="round"/>' % s
              for s in [(70,118,60,90), (92,116,90,84), (114,116,120,84),
                        (136,120,148,92), (158,128,176,112), (176,140,192,132),
                        (58,170,42,192), (88,184,82,208), (124,184,132,208),
                        (152,174,166,192), (46,124,24,118), (44,150,20,152)])
    + '<circle cx="34" cy="134" r="18" fill="#d09a6a"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#7a4e26" stroke-width="5" stroke-linecap="round"/>' % s
              for s in [(30,116,26,104), (18,124,8,116), (16,146,4,148)])
    + '<ellipse cx="62" cy="128" rx="26" ry="20" fill="#d09a6a"/>'
    '<circle cx="52" cy="122" r="7" fill="#f7f0d0"/><circle cx="52" cy="122" r="3.5" fill="#2a1c10"/>'
    '<path d="M40 138 C46 144 56 144 62 138" stroke="#7a4e26" stroke-width="3" fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d L%d %d" stroke="#a8763e" stroke-width="12" fill="none"'
              ' stroke-linecap="round" stroke-linejoin="round"/>' % s
              for s in [(76,174,58,192,52,198), (138,174,158,192,164,198)])
  ),
},
{
  "id": "skink", "cn": "石龙子", "en": "Skink", "series": "rept",
  "tint": "#8a7a5a", "dark": "#4a3e28",
  "skill": "鳞片像涂了油 · 尾巴比身子还长",
  "facts": [
    "线索一：这些蛋埋在松土或落叶下面，一窝几颗，靠土温慢慢孵。",
    "线索二：小家伙一破壳就长着光滑发亮的鳞片，四条腿又短又小，常常贴着地面滑着走。",
    "线索三：它一身鳞片又光又亮，像涂了油。它的腿很短，走起来几乎像贴着地面滑。尾巴断了能再长一条。它叫石龙子。",
  ],
  "body": (
    '<path d="M148 150 C182 148 194 128 190 104" stroke="#8a7a5a" stroke-width="17"'
    ' fill="none" stroke-linecap="round"/>'
    '<ellipse cx="108" cy="148" rx="48" ry="25" fill="#8a7a5a"/>'
    '<path d="M74 134 C82 124 94 118 110 118 C128 118 142 126 150 138"'
    ' stroke="#c8bca0" stroke-width="6" fill="none" stroke-linecap="round" opacity=".85"/>'
    '<ellipse cx="60" cy="130" rx="28" ry="19" fill="#9a8a6a"/>'
    '<circle cx="50" cy="124" r="7" fill="#f7f0d0"/><circle cx="50" cy="124" r="3.5" fill="#2a2418"/>'
    '<path d="M36 140 C42 146 52 146 58 140" stroke="#4a3e28" stroke-width="3" fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#9a8a6a" stroke-width="10" stroke-linecap="round"/>' % s
              for s in [(80,170,66,190), (128,170,142,190)])
    + '<path d="M160 122 C176 112 190 108 198 110" stroke="#8a7a5a" stroke-width="12"'
    ' fill="none" stroke-linecap="round" opacity=".5"/>'
  ),
},

# ============================ 哺乳动物 ============================
# 这一组胎生，第一步不是蛋，是脚印（paw: True → 用 PAW 那套掌印）。
# 鲸 / 海豚 / 蝙蝠 例外：它们各有自己的痕迹，用 entry_svg + entry_label 覆盖。
{
  "id": "elephant", "cn": "大象", "en": "Elephant", "series": "mammal", "paw": True,
  "tint": "#9aa0a8", "dark": "#5a6068",
  "skill": "鼻子有几万块肌肉 · 脚掌能听远处",
  "facts": [
    "线索一：这里没有蛋，只有一串又大又圆的脚印，比脸盆还大。旁边还有被连根拔起的草和折断的树枝。",
    "线索二：小家伙一出生就有一百来公斤，站都站不稳，得妈妈用鼻子扶着。它吃妈妈的奶要吃上好几年。",
    "线索三：它用鼻子喝水、洗澡、捡东西，鼻子上有几万块肌肉。它的耳朵大得能扇风，脚掌还能听到很远地方的震动。它叫大象。",
  ],
  "body": (
    '<path d="M160 172 C186 172 196 156 192 138" stroke="#9aa0a8" stroke-width="14"'
    ' fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d 178 L%d 206" stroke="#8e959c" stroke-width="26" stroke-linecap="round"/>' % s
              for s in [(84,80), (120,118), (152,148), (176,174)])
    + '<ellipse cx="118" cy="138" rx="60" ry="46" fill="#9aa0a8"/>'
    '<circle cx="58" cy="118" r="46" fill="#9aa0a8"/>'
    '<circle cx="76" cy="110" r="32" fill="#7e858c"/>'
    '<path d="M28 142 C14 166 16 192 32 202" stroke="#9aa0a8" stroke-width="24"'
    ' fill="none" stroke-linecap="round"/>'
    '<path d="M28 142 C14 166 16 192 32 202" stroke="#7e858c" stroke-width="3"'
    ' fill="none" opacity=".7" stroke-dasharray="3 9"/>'
    '<path d="M36 160 C30 178 36 190 48 194" stroke="#f7f2ea" stroke-width="7"'
    ' fill="none" stroke-linecap="round"/>'
    '<circle cx="44" cy="104" r="9" fill="#f7f2ea"/><circle cx="44" cy="104" r="4.5" fill="#2a2e34"/>'
    '<path d="M22 128 C34 140 54 142 68 132" stroke="#5a6068" stroke-width="4"'
    ' fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "giraffe", "cn": "长颈鹿", "en": "Giraffe", "series": "mammal", "paw": True,
  "tint": "#d8a83c", "dark": "#8a6218",
  "skill": "脖子只有七块骨头 · 几乎站着睡",
  "facts": [
    "线索一：沙地上一串深深的蹄印，每一步都跨得特别远。抬头看，树顶那一层叶子被啃掉了一整圈。",
    "线索二：小家伙是从两米高的地方掉到地上的，摔得懵懵的。它出生半小时就能站起来，第一天就有一米八。",
    "线索三：它脖子上只有七块骨头，和人的一样多，只是一块就有一支笔那么长。它几乎都是站着睡的，一天只睡两小时。它叫长颈鹿。",
  ],
  "body": (
    ''.join('<path d="M%d 180 L%d 208" stroke="#c8952e" stroke-width="17" stroke-linecap="round"/>' % s
              for s in [(102,94), (128,120), (152,146), (176,168)])
    + '<path d="M84 96 C80 130 82 156 92 172" stroke="#d8a83c" stroke-width="28"'
    ' fill="none" stroke-linecap="round"/>'
    '<path d="M76 100 C74 132 78 156 86 170" stroke="#8a6218" stroke-width="4"'
    ' fill="none" opacity=".55" stroke-dasharray="4 10"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#8a6218" stroke-width="3.5" stroke-linecap="round"/>' % s
              for s in [(72,88,62,76), (84,84,78,70), (96,82,98,66)])
    + '<ellipse cx="88" cy="74" rx="28" ry="19" fill="#d8a83c"/>'
    '<path d="M74 62 C70 50 74 44 80 46" stroke="#8a6218" stroke-width="5" fill="none" stroke-linecap="round"/>'
    '<circle cx="79" cy="44" r="7" fill="#8a6218"/>'
    '<path d="M104 66 C114 58 124 58 130 64" stroke="#8a6218" stroke-width="5" fill="none" stroke-linecap="round"/>'
    '<circle cx="72" cy="70" r="7" fill="#f7f2ea"/><circle cx="72" cy="70" r="3.5" fill="#2a2410"/>'
    '<path d="M62 82 C70 90 82 90 90 82" stroke="#8a6218" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
    '<ellipse cx="134" cy="176" rx="52" ry="32" fill="#d8a83c"/>'
    + ''.join('<path d="M%d %d l%d %d l%d %d l%d %d Z" fill="#8a6218" opacity=".75"/>' % s
              for s in [(112,158, 12,-8, 14,4, 4,12), (140,156, 12,-6, 14,4, 4,12),
                        (168,164, 12,-8, 12,4, 4,12), (100,182, 10,-6, 12,4, 4,10),
                        (134,182, 12,-6, 12,4, 4,10), (162,186, 10,-6, 10,4, 4,10)])
  ),
},
{
  "id": "lion", "cn": "狮子", "en": "Lion", "series": "mammal", "paw": True,
  "tint": "#d8a050", "dark": "#8a5a1c",
  "skill": "打猎主要靠妈妈 · 吼声传好几公里",
  "facts": [
    "线索一：草丛里有一片压平的印子，旁边散着几撮黄毛和啃得干干净净的骨头。夜里听到过一声很远的吼。",
    "线索二：小家伙生下来眼睛还没睁开，身上带着暗色的斑点，长大才褪掉。妈妈会把它叼来叼去换地方藏。",
    "线索三：它头上那圈毛越长越黑，是身份的记号。家里主要是妈妈和阿姨们出去打猎，爸爸负责守地盘。它叫狮子。",
  ],
  "body": (
    '<path d="M164 178 C186 176 194 158 188 140" stroke="#d8a050" stroke-width="12"'
    ' fill="none" stroke-linecap="round"/>'
    '<circle cx="190" cy="134" r="11" fill="#8a5a1c"/>'
    + ''.join('<path d="M%d 182 L%d 208" stroke="#c8923e" stroke-width="22" stroke-linecap="round"/>' % s
              for s in [(96,88), (126,120), (152,144), (176,168)])
    + '<ellipse cx="128" cy="150" rx="54" ry="36" fill="#d8a050"/>'
    '<circle cx="70" cy="114" r="48" fill="#a8702c"/>'
    + ''.join('<circle cx="%d" cy="%d" r="13" fill="#8a5a1c"/>' % p
              for p in [(70,66), (30,88), (26,138), (52,166), (100,170), (114,140), (114,90)])
    + '<circle cx="72" cy="116" r="35" fill="#e8bc74"/>'
    '<circle cx="58" cy="108" r="7" fill="#f7f2ea"/><circle cx="58" cy="108" r="3.5" fill="#2a1e0c"/>'
    '<circle cx="86" cy="108" r="7" fill="#f7f2ea"/><circle cx="86" cy="108" r="3.5" fill="#2a1e0c"/>'
    '<path d="M62 132 C68 140 78 140 84 132" stroke="#8a5a1c" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<path d="M72 126 L72 132 M66 134 L78 134" stroke="#8a5a1c" stroke-width="3.5" stroke-linecap="round"/>'
  ),
},
{
  "id": "tiger", "cn": "老虎", "en": "Tiger", "series": "mammal", "paw": True,
  "tint": "#e08a2c", "dark": "#8a4a10",
  "skill": "爱下水会游泳 · 条纹连皮上都有",
  "facts": [
    "线索一：泥地上一串圆圆的掌印，看不见爪尖的印子——它走路时把爪收在肉里。旁边树皮上有几道抓痕。",
    "线索二：小家伙生下来眼睛睁不开，要十来天才看见东西。它跟着妈妈学两年，才敢自己去占一片地盘。",
    "线索三：它身上的条纹连皮肤上都有，不是染的。它爱下水、会游泳，一只就能拖走比它自己还重的猎物。它叫老虎。",
  ],
  "body": (
    '<path d="M160 176 C186 174 196 156 190 136" stroke="#e08a2c" stroke-width="13"'
    ' fill="none" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#8a4a10" stroke-width="4" stroke-linecap="round"/>' % s
              for s in [(172,166,178,152), (180,158,188,148)])
    + ''.join('<path d="M%d 180 L%d 206" stroke="#d07c22" stroke-width="22" stroke-linecap="round"/>' % s
              for s in [(94,86), (124,118), (152,144), (176,168)])
    + '<ellipse cx="128" cy="150" rx="56" ry="38" fill="#e08a2c"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#8a4a10" stroke-width="7" stroke-linecap="round"/>' % s
              for s in [(112,116,108,134), (132,112,130,132), (152,118,156,138),
                        (170,132,178,144), (104,168,102,182), (144,180,146,192)])
    + '<circle cx="64" cy="112" r="46" fill="#e08a2c"/>'
    '<path d="M34 76 L26 54 L50 66 Z" fill="#e08a2c"/>'
    '<path d="M94 76 L102 54 L78 66 Z" fill="#e08a2c"/>'
    '<path d="M40 68 L36 56 L48 62 Z" fill="#c87a3a"/>'
    '<path d="M88 68 L92 56 L80 62 Z" fill="#c87a3a"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#8a4a10" stroke-width="6" stroke-linecap="round"/>' % s
              for s in [(50,76,44,88), (78,76,84,88), (34,104,26,112), (94,104,102,112),
                        (58,140,62,150), (72,142,78,150)])
    + '<circle cx="52" cy="106" r="8" fill="#f7f2ea"/><circle cx="52" cy="106" r="4" fill="#2a1e0c"/>'
    '<circle cx="78" cy="106" r="8" fill="#f7f2ea"/><circle cx="78" cy="106" r="4" fill="#2a1e0c"/>'
    '<path d="M54 132 C60 140 70 140 76 132" stroke="#8a4a10" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<path d="M65 124 L65 132" stroke="#8a4a10" stroke-width="4" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#f7f2ea" stroke-width="3" stroke-linecap="round"/>' % s
              for s in [(52,138,48,152), (78,138,82,152)])
  ),
},
{
  "id": "panda", "cn": "熊猫", "en": "Panda", "series": "mammal", "paw": True,
  "tint": "#f0f0ee", "dark": "#2e2e2c",
  "skill": "一天吃十几个小时竹子 · 假装的大拇指",
  "facts": [
    "线索一：竹林里有一堆咬断的竹竿，切口很齐，像被大剪刀咔嚓剪过。地上还有圆圆的掌印和几撮黑白相间的毛。",
    "线索二：小家伙生下来只有一百多克，粉红色，没毛，眼睛也睁不开。它长得极慢，好几个月才能自己走。",
    "线索三：它一天要吃十几个小时竹子，吃进去的大部分都消化不掉，所以几乎一直在吃。它抓竹子那根大拇指其实是一块变大的腕骨。它叫熊猫。",
  ],
  "body": (
    ''.join('<path d="M%d %d L%d %d" stroke="#2e2e2c" stroke-width="26" stroke-linecap="round"/>' % s
              for s in [(96,182,82,206), (130,180,144,204)])
    + '<ellipse cx="132" cy="150" rx="58" ry="46" fill="#f0f0ee"/>'
    '<path d="M74 122 C60 128 52 148 56 166" stroke="#2e2e2c" stroke-width="24"'
    ' fill="none" stroke-linecap="round"/>'
    '<ellipse cx="182" cy="150" rx="20" ry="26" fill="#2e2e2c"/>'
    '<circle cx="66" cy="106" r="46" fill="#f0f0ee"/>'
    '<circle cx="34" cy="68" r="20" fill="#2e2e2c"/>'
    '<circle cx="100" cy="68" r="20" fill="#2e2e2c"/>'
    '<ellipse cx="48" cy="104" rx="16" ry="19" transform="rotate(-18 48 104)" fill="#2e2e2c"/>'
    '<ellipse cx="86" cy="104" rx="16" ry="19" transform="rotate(18 86 104)" fill="#2e2e2c"/>'
    '<circle cx="48" cy="104" r="6" fill="#f0f0ee"/><circle cx="48" cy="104" r="3" fill="#1a1a18"/>'
    '<circle cx="86" cy="104" r="6" fill="#f0f0ee"/><circle cx="86" cy="104" r="3" fill="#1a1a18"/>'
    '<ellipse cx="67" cy="134" rx="16" ry="11" fill="#2e2e2c"/>'
    '<path d="M58 138 C64 148 72 148 78 138" stroke="#2e2e2c" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "kangaroo", "cn": "袋鼠", "en": "Kangaroo", "series": "mammal", "paw": True,
  "tint": "#c8823c", "dark": "#7a4a18",
  "skill": "只会往前跳 · 尾巴当第五条腿",
  "facts": [
    "线索一：沙地上两行印子——两只大脚印并排，中间还跟着一小串细长的拖痕，像有东西在地上拖着走。",
    "线索二：小家伙生下来只有花生米大，自己爬进妈妈肚子上的口袋里，在里面住上好几个月才探头出来看。",
    "线索三：它刚出生只有花生米大，得自己爬进妈妈的育儿袋。它只会往前跳，不会倒退，粗尾巴还能当第五条腿撑住身体。它叫袋鼠。",
  ],
  "body": (
    '<path d="M156 190 C188 190 200 168 194 140 C190 122 180 114 172 118"'
    ' stroke="#c8823c" stroke-width="24" fill="none" stroke-linecap="round"/>'
    '<ellipse cx="108" cy="144" rx="42" ry="50" fill="#c8823c"/>'
    '<ellipse cx="98" cy="160" rx="26" ry="32" fill="#d89a58"/>'
    '<ellipse cx="76" cy="76" rx="27" ry="31" fill="#c8823c"/>'
    '<path d="M60 58 C50 32 54 22 62 22 C70 24 72 40 70 54 Z" fill="#c8823c"/>'
    '<path d="M90 58 C98 32 104 24 110 26 C114 32 106 46 100 58 Z" fill="#c8823c"/>'
    '<ellipse cx="52" cy="86" rx="20" ry="14" fill="#d89a58"/>'
    '<circle cx="44" cy="84" r="4.5" fill="#3a2610"/>'
    '<circle cx="66" cy="72" r="7" fill="#f7f2ea"/><circle cx="66" cy="72" r="3.5" fill="#3a2610"/>'
    '<circle cx="88" cy="72" r="7" fill="#f7f2ea"/><circle cx="88" cy="72" r="3.5" fill="#3a2610"/>'
    '<path d="M66 128 C76 138 88 136 94 126" stroke="#7a4a18" stroke-width="8"'
    ' fill="none" stroke-linecap="round"/>'
    '<path d="M62 188 L48 208" stroke="#a86a2e" stroke-width="14" stroke-linecap="round"/>'
    '<path d="M34 208 L14 206 C8 204 8 198 14 196 L56 194" fill="#a86a2e"'
    ' stroke="#7a4a18" stroke-width="2.5" stroke-linejoin="round"/>'
  ),
},
{
  "id": "whale", "cn": "鲸", "en": "Whale", "series": "mammal",
  "tint": "#5a7a9a", "dark": "#2e4a66",
  "entry_label": "海面上喷起一道水柱",
  "hatch_label": "水底下冒出个大家伙",
  "entry_svg": (
    '<path d="M56 96 C48 70 54 50 68 40 M56 96 C62 70 72 54 88 46"'
    ' stroke="#bfe0f0" stroke-width="8" fill="none" stroke-linecap="round" opacity=".9"/>'
    '<ellipse cx="100" cy="150" rx="60" ry="34" fill="#4a6a8a"/>'
    '<ellipse cx="100" cy="150" rx="60" ry="34" fill="none" stroke="#2e4a66" stroke-width="3"/>'
    '<path d="M56 160 C72 174 112 176 140 166" stroke="#bfe0f0" stroke-width="4"'
    ' fill="none" opacity=".6" stroke-linecap="round"/>'
    '<path d="M158 130 C174 118 186 116 192 124 C186 134 174 142 164 148 Z" fill="#4a6a8a"/>'
  ),
  "skill": "一次吸几千升水 · 会唱歌",
  "facts": [
    "线索一：海面上喷起一道好几米高的水柱，接着水面下浮出一个黑色的背，比船还长。",
    "线索二：小家伙生下来就有好几米，是妈妈在水里把它托到水面上的——它得先学会喘第一口气。",
    "线索三：它一次能吸进好几千升水，再把里面的小虾滤出来吃掉。它会唱歌，一首能传很远，而且年年都在变。它叫鲸。",
  ],
  "body": (
    '<path d="M94 92 C102 70 118 62 130 66 C118 78 112 84 108 94 Z" fill="#5a7a9a"/>'
    '<path d="M192 106 C206 88 212 70 204 62 C198 80 190 92 180 100 Z" fill="#5a7a9a"/>'
    '<path d="M188 140 C202 152 210 166 202 174 C194 160 186 150 176 144 Z" fill="#5a7a9a"/>'
    '<ellipse cx="100" cy="136" rx="76" ry="46" fill="#5a7a9a"/>'
    '<path d="M56 94 C50 70 56 52 68 44 M56 94 C62 70 72 56 86 50"'
    ' stroke="#bfe0f0" stroke-width="8" fill="none" stroke-linecap="round" opacity=".9"/>'
    '<ellipse cx="66" cy="170" rx="24" ry="12" transform="rotate(-16 66 170)" fill="#4a6a8a"/>'
    + ''.join('<path d="M%d 168 C%d 176 %d 178 %d 176" stroke="#8aa8c0" stroke-width="3"'
              ' fill="none" opacity=".7" stroke-linecap="round"/>' % t
              for t in [(56,64,76,80), (74,82,94,98), (92,100,112,116)])
    + '<path d="M32 146 C48 158 68 162 88 158" stroke="#2e4a66" stroke-width="4"'
    ' fill="none" stroke-linecap="round"/>'
    '<circle cx="52" cy="124" r="8" fill="#f7f2ea"/><circle cx="52" cy="124" r="4" fill="#1e3040"/>'
  ),
},
{
  "id": "dolphin", "cn": "海豚", "en": "Dolphin", "series": "mammal",
  "tint": "#7aa8c4", "dark": "#3a6a86",
  "entry_label": "水面划过一道背鳍",
  "hatch_label": "水花里跳出个小家伙",
  "entry_svg": (
    '<path d="M30 190 C50 172 84 162 118 166 C152 170 172 180 184 192"'
    ' stroke="#7aa8c4" stroke-width="14" fill="none" stroke-linecap="round"/>'
    '<path d="M118 166 C112 138 122 118 142 112 C138 138 130 154 124 166 Z" fill="#5a8aa8"/>'
    '<ellipse cx="100" cy="128" rx="54" ry="30" fill="#7aa8c4"/>'
    '<path d="M46 128 C40 124 38 118 42 114 C50 114 56 118 60 122 Z" fill="#7aa8c4"/>'
    '<path d="M92 104 C98 88 110 84 118 88 C110 96 104 100 102 108 Z" fill="#5a8aa8"/>'
    '<circle cx="56" cy="122" r="6" fill="#f7f2ea"/><circle cx="56" cy="122" r="3" fill="#1e3a4a"/>'
  ),
  "skill": "一半脑子睡觉 · 靠回声看东西",
  "facts": [
    "线索一：水面划过一道弯弯的鳍，接着一群影子飞快掠过，还跟了船游了一阵。",
    "线索二：小家伙是尾巴先出来的，一出生就被妈妈顶到水面上吸第一口气。它贴着妈妈游，吃奶要吃一年多。",
    "线索三：它睡觉时只让一半脑子休息，另一半留着呼吸。它用额头前面那块鼓包发出声音，听回声就知道前面有什么。它叫海豚。",
  ],
  "body": (
    '<path d="M92 106 C100 86 116 80 128 84 C114 96 108 104 104 112 Z" fill="#6a98b4"/>'
    '<path d="M170 126 C186 110 196 100 202 104 C198 118 190 132 180 142 Z" fill="#6a98b4"/>'
    '<path d="M172 158 C186 170 192 182 188 192 C180 180 172 170 162 162 Z" fill="#6a98b4"/>'
    '<path d="M34 152 C58 110 118 96 158 116 C186 130 190 150 178 158'
    ' C140 180 62 178 34 152 Z" fill="#7aa8c4"/>'
    '<path d="M34 152 C22 150 14 144 16 136 C28 132 40 136 48 142 Z" fill="#8ab4cc"/>'
    '<path d="M40 148 C60 164 108 172 150 166" stroke="#d8ecf4" stroke-width="7"'
    ' fill="none" stroke-linecap="round" opacity=".8"/>'
    '<path d="M44 146 C56 152 70 154 82 152" stroke="#3a6a86" stroke-width="3.5"'
    ' fill="none" stroke-linecap="round"/>'
    '<circle cx="60" cy="140" r="7" fill="#f7f2ea"/><circle cx="60" cy="140" r="3.5" fill="#1e3a4a"/>'
    '<path d="M52 160 C62 166 76 166 86 160" stroke="#3a6a86" stroke-width="3" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "bat", "cn": "蝙蝠", "en": "Bat", "series": "mammal",
  "tint": "#6a5a6a", "dark": "#3a2e3a",
  "entry_label": "山洞顶上有窸窣声",
  "hatch_label": "洞顶掉下个小家伙",
  "entry_svg": (
    '<path d="M100 60 L100 96" stroke="#4a3e4a" stroke-width="5" stroke-linecap="round"/>'
    '<path d="M64 92 C62 74 76 60 98 60 C120 60 134 74 132 92'
    ' C132 116 118 132 98 132 C78 132 64 116 64 92 Z" fill="#6a5a6a"/>'
    '<path d="M70 76 C64 66 62 58 66 56 C72 58 78 66 80 74 Z" fill="#6a5a6a"/>'
    '<path d="M128 76 C134 66 136 58 132 56 C126 58 120 66 118 74 Z" fill="#6a5a6a"/>'
    '<path d="M82 134 C86 150 90 160 92 168 M114 134 C110 150 106 160 104 168"'
    ' stroke="#4a3e4a" stroke-width="4" fill="none" stroke-linecap="round"/>'
  ),
  "skill": "唯一会飞的哺乳动物 · 靠回声看路",
  "facts": [
    "线索一：山洞顶上有细细的窸窣声，抬头看是一排倒挂着的小身影，挤在一起。",
    "线索二：小家伙生下来就挂在妈妈身上，妈妈飞出去找吃的也带着它。它要吃几个月的奶才能自己飞。",
    "线索三：它是唯一会飞的哺乳动物，翅膀其实是一张撑开的皮，手指骨撑在里面。它在全黑的洞里靠回声认路。它叫蝙蝠。",
  ],
  "body": (
    '<path d="M94 128 C70 104 32 92 12 100 C2 120 18 152 44 166'
    ' C62 176 84 176 96 166 Z" fill="#6a5a6a"/>'
    '<path d="M106 128 C130 104 168 92 188 100 C198 120 182 152 156 166'
    ' C138 176 116 176 104 166 Z" fill="#6a5a6a"/>'
    + ''.join('<path d="M%d %d C%d %d %d %d %d %d" stroke="#4a3e4a" stroke-width="3"'
              ' fill="none" opacity=".8"/>' % t
              for t in [(92,130, 62,116, 34,110, 14,102),
                        (108,130, 138,116, 166,110, 186,102),
                        (94,148, 66,146, 40,144, 20,138),
                        (106,148, 134,146, 160,144, 180,138)])
    + '<ellipse cx="100" cy="142" rx="22" ry="38" fill="#7a6878"/>'
    '<path d="M84 112 C76 90 78 78 84 76 C90 80 92 96 92 108 Z" fill="#6a5a6a"/>'
    '<path d="M116 112 C124 90 122 78 116 76 C110 80 108 96 108 108 Z" fill="#6a5a6a"/>'
    '<circle cx="92" cy="118" r="7" fill="#f7f2ea"/><circle cx="92" cy="118" r="3.5" fill="#2a1e28"/>'
    '<circle cx="108" cy="118" r="7" fill="#f7f2ea"/><circle cx="108" cy="118" r="3.5" fill="#2a1e28"/>'
    '<path d="M92 158 L92 166 M96 158 L96 166 M104 158 L104 166 M108 158 L108 166"'
    ' stroke="#f7f2ea" stroke-width="3" stroke-linecap="round"/>'
    '<path d="M86 176 L82 190 M100 178 L100 192 M114 176 L118 190"'
    ' stroke="#4a3e4a" stroke-width="4" fill="none" stroke-linecap="round"/>'
  ),
},
{
  "id": "hedgehog", "cn": "刺猬", "en": "Hedgehog", "series": "mammal", "paw": True,
  "tint": "#8a7a5a", "dark": "#4a3e28",
  "skill": "一夜走好几公里 · 卷成球谁都咬不动",
  "facts": [
    "线索一：落叶堆里有一团会动的小刺球，碰一下它立刻缩成一团，只听见轻轻的哼哼声。",
    "线索二：小家伙刚出生时身上是软的、湿的，刺都收在里面，过一天才慢慢竖起来。它睁眼要两个星期。",
    "线索三：它一害怕就把自己卷成一个球，刺全朝外，谁也下不了嘴。它一个晚上能走上好几公里找虫子吃。它叫刺猬。",
  ],
  "body": (
    # 刺要画成三角（底下宽）。画成细线就变成蜘蛛腿了——试过
    ''.join('<g transform="translate(106,150) rotate(%d)">'
              '<path d="M-13 -34 L0 -84 L13 -34 Z" fill="#5a4a34"/></g>' % ang
              for ang in range(-168, 169, 16))
    + '<ellipse cx="106" cy="150" rx="64" ry="48" fill="#8a7a5a"/>'
    + ''.join('<circle cx="%d" cy="%d" r="5" fill="#4a3e28" opacity=".55"/>' % p
              for p in [(84,128), (110,122), (136,128), (96,160), (124,162), (150,152)])
    + '<ellipse cx="46" cy="164" rx="30" ry="25" fill="#d8c49c"/>'
    '<circle cx="26" cy="172" r="9" fill="#3a2e1c"/>'
    '<circle cx="52" cy="152" r="8" fill="#f7f2ea"/><circle cx="52" cy="152" r="4" fill="#2a2010"/>'
    '<circle cx="62" cy="140" r="9" fill="#a89878"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#8a7a5a" stroke-width="9" stroke-linecap="round"/>' % s
              for s in [(80,186,72,202), (112,188,118,204)])
  ),
},
{
  "id": "polarbear", "cn": "北极熊", "en": "Polar bear", "series": "mammal", "paw": True,
  "tint": "#e8e8dc", "dark": "#8a9098",
  "skill": "毛是空心的 · 能游几十公里",
  "facts": [
    "线索一：雪地上一串宽大的掌印，一路走到冰边就断了。印子上几乎没有爪尖，边上还有拖过的痕迹。",
    "线索二：小家伙生在雪洞里，出生时只有几百克，没毛也看不见。它要在洞里吃几个月的奶才出来见天日。",
    "线索三：它的毛其实是空心透明的，看着才发白，皮下面却是黑的。它游泳能游几十公里，趴在冰洞边上等海豹冒头。它叫北极熊。",
  ],
  "body": (
    ''.join('<path d="M%d 182 L%d 208" stroke="#e0e0d4" stroke-width="26" stroke-linecap="round"/>' % s
              for s in [(92,84), (124,118), (152,146), (176,170)])
    + '<path d="M172 174 C190 168 196 152 190 140" stroke="#e8e8dc" stroke-width="9"'
    ' fill="none" stroke-linecap="round"/>'
    '<ellipse cx="130" cy="152" rx="60" ry="42" fill="#e8e8dc"/>'
    '<circle cx="66" cy="112" r="46" fill="#e8e8dc"/>'
    '<circle cx="34" cy="76" r="15" fill="#e8e8dc"/><circle cx="34" cy="76" r="8" fill="#c8c8bc"/>'
    '<circle cx="98" cy="76" r="15" fill="#e8e8dc"/><circle cx="98" cy="76" r="8" fill="#c8c8bc"/>'
    '<ellipse cx="34" cy="134" rx="24" ry="18" fill="#dcdcd0"/>'
    '<circle cx="22" cy="130" r="7" fill="#3a3a34"/>'
    '<path d="M14 142 C22 148 34 148 42 142" stroke="#8a9098" stroke-width="3" fill="none" stroke-linecap="round"/>'
    '<circle cx="52" cy="104" r="7" fill="#3a3a34"/><circle cx="52" cy="104" r="3.5" fill="#1a1a16"/>'
    '<circle cx="84" cy="104" r="7" fill="#3a3a34"/><circle cx="84" cy="104" r="3.5" fill="#1a1a16"/>'
    '<circle cx="44" cy="156" r="17" fill="#dcdcd0" stroke="#8a9098" stroke-width="2.5"/>'
    '<circle cx="44" cy="156" r="8" fill="#c8c8bc"/>'
  ),
},
{
  "id": "squirrel", "cn": "松鼠", "en": "Squirrel", "series": "mammal", "paw": True,
  "tint": "#c8783c", "dark": "#7a4218",
  "skill": "埋果子忘了挖 · 帮树长新苗",
  "facts": [
    "线索一：树根边堆着一小堆啃开的果壳，旁边土里还有好几个浅浅的小坑。树干上留着爪尖刮出来的细印子。",
    "线索二：小家伙生下来没毛、眼睛闭着，一个多月才睁眼。它第一次出窝时，尾巴还细得像根绳子。",
    "线索三：它把果子埋进土里过冬，忘了挖出来的那些就长成了小树。它靠尾巴保持平衡，还摇着尾巴跟同伴吵架。它叫松鼠。",
  ],
  "body": (
    '<path d="M148 172 C188 166 202 122 178 90 C160 66 128 66 122 88'
    ' C144 92 158 108 158 132 C158 152 152 164 142 172 Z" fill="#c8783c"/>'
    '<path d="M150 162 C176 154 184 122 170 100 C160 84 140 84 136 98'
    ' C152 104 160 116 160 134 C160 148 156 156 150 162 Z"'
    ' fill="none" stroke="#a86028" stroke-width="4"/>'
    '<ellipse cx="110" cy="154" rx="42" ry="34" fill="#c8783c"/>'
    '<ellipse cx="100" cy="164" rx="28" ry="22" fill="#e0a468"/>'
    '<circle cx="76" cy="118" r="32" fill="#c8783c"/>'
    '<path d="M56 96 C50 76 54 68 60 68 C66 70 68 84 66 94 Z" fill="#c8783c"/>'
    '<path d="M92 92 C98 72 104 66 110 68 C112 74 104 86 98 94 Z" fill="#c8783c"/>'
    '<circle cx="66" cy="112" r="8" fill="#f7f2ea"/><circle cx="66" cy="112" r="4" fill="#2a1a0c"/>'
    '<circle cx="90" cy="112" r="8" fill="#f7f2ea"/><circle cx="90" cy="112" r="4" fill="#2a1a0c"/>'
    '<ellipse cx="72" cy="136" rx="14" ry="10" fill="#e0a468"/>'
    '<circle cx="68" cy="134" r="3.5" fill="#3a2410"/>'
    '<path d="M72 140 L72 146 M66 144 L78 144" stroke="#3a2410" stroke-width="3" stroke-linecap="round"/>'
    '<circle cx="86" cy="148" r="13" fill="#a86028"/>'
    '<path d="M86 136 L80 126 M86 136 L92 126" stroke="#7a4218" stroke-width="3.5" stroke-linecap="round"/>'
    + ''.join('<path d="M%d %d L%d %d" stroke="#c8783c" stroke-width="11" stroke-linecap="round"/>' % s
              for s in [(96,180,86,198), (128,182,138,198)])
  ),
},
]

# ---------- 校验 + 生成 ----------
SERIES_IDS = [s["id"] for s in SERIES]
zoo = []
for a in ZOO_ANIMALS:
    if len(a["facts"]) != 3:
        sys.exit("%s 的小知识不是 3 条（要对应第一步/幼年/成年）" % a["id"])
    if a["series"] not in SERIES_IDS:
        sys.exit("%s 的系列 %r 不在 SERIES 里" % (a["id"], a.get("series")))
    # 前两条不许出现动物名字，不然谜题一开始就破了
    for i in (0, 1):
        if a["cn"] in a["facts"][i]:
            sys.exit("%s 的第 %d 条线索里出现了动物名字，会剧透" % (a["id"], i + 1))
    if a["cn"] not in a["facts"][2]:
        sys.exit("%s 的成年那条没点破名字" % a["id"])
    z = {
        "id": a["id"], "cn": a["cn"], "en": a["en"], "series": a["series"],
        "tint": a["tint"], "dark": a["dark"], "skill": a["skill"],
        "facts": a["facts"],
        "body": a["body"],
    }
    # 第一步的样子：默认是按配色自动配的蛋；胎生的动物自己画（entry_svg），
    # 或者干脆写 entry=None 表示"这一步没有具体形象"，只用文字线索。
    if "entry_svg" in a:
        z["entry"] = a["entry_svg"]
    elif a.get("entry_blank"):
        z["entry"] = ""
    else:
        # 胎生的（标记 paw）画脚印，其余画蛋
        tpl = PAW if a.get("paw") else EGG
        z["entry"] = tpl.replace("{tint}", a["tint"]).replace("{dark}", a["dark"])
    if a.get("entry_label"): z["entryLabel"] = a["entry_label"]
    if a.get("hatch_label"): z["hatchLabel"] = a["hatch_label"]
    zoo.append(z)

# 只输出真的有动物的系列，空系列不占页签
used = set(a["series"] for a in zoo)
series = [s for s in SERIES if s["id"] in used]

BASE = pathlib.Path(__file__).parent
p = BASE / "index.html"
html = p.read_text(encoding="utf-8")

def inject(html, name, value):
    blob = "var %s = %s;" % (name, json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    new, n = re.subn(r"var %s = \[.*?\];" % name, lambda m: blob, html, count=1, flags=re.S)
    if n != 1:
        sys.exit("没找到 %s 块，index.html 结构变了" % name)
    return new

html = inject(html, "SERIES", series)
html = inject(html, "ZOO", zoo)
p.write_text(html, encoding="utf-8")

for s in series:
    ids = [a["cn"] for a in zoo if a["series"] == s["id"]]
    print("  %s（%d）：%s" % (s["cn"], len(ids), "、".join(ids)))
print("灌入 %d 个动物，%d 个系列" % (len(zoo), len(series)))
