# -*- coding: utf-8 -*-
"""fig7 -- 贴身段（1 米硅胶管）怎么固定在身上背着用"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schematic_lib import *

W, H = 1560, 1235
s = Sch(W, H, '贴身段固定方案 —— 怎么把 1 米硅胶管穿在身上还不被背包压瘪')

SKIN = (247, 224, 208)
CLOTH = (222, 236, 248)
EVA = (255, 243, 205)
MESH = (232, 234, 238)
BAG = (108, 116, 128)
TUBE = (60, 140, 210)
DKGREEN = (0, 110, 60)


def arrow_down(d, x, y0, y1, color=RED, w=5):
    d.line([x, y0, x, y1 - 12], fill=color, width=w)
    d.polygon([(x - 11, y1 - 12), (x + 11, y1 - 12), (x, y1)], fill=color)


def tube_circle(d, x, y, r=17, color=TUBE):
    d.ellipse([x - r, y - r, x + r, y + r], fill=(240, 250, 255), outline=color, width=4)


def section_title(x, y, text):
    s.d.rounded_rectangle([x, y - 20, x + 34, y + 20], radius=7, fill=(235, 240, 248),
                          outline=(150, 165, 190), width=2)
    s.txt(x + 17, y, text, 20, BLACK, bold=True, anchor='mm')
    return x + 50


# ======================================================================
#  ① 分层剖面（左上）
# ======================================================================
tx = section_title(60, 100, '1')
s.txt(tx, 100, '分层结构（从里往外）', 22, BLACK, bold=True)

LX0, LX1 = 110, 500
arrow_down(s.d, 245, 138, 176)
arrow_down(s.d, 390, 138, 176)
s.txt(60, 148, '背包 /\n肩带的\n压力', 14, RED, anchor='lm')

s.box(LX0, 176, LX1, 214, '背包背板 / 肩带', fill=BAG, outline=(70, 76, 86), fs=17, tcolor='white')
s.box(LX0, 219, LX1, 250, '防磨网布（薄）', fill=MESH, outline=GRAY, fs=16)
s.box(LX0, 255, LX1, 365, '', fill=EVA, outline=(196, 160, 40), width=3, r=8)
for txx in (195, 305, 415):
    tube_circle(s.d, txx, 310)
s.txt(LX0 + 10, 270, 'EVA 泡棉垫 5mm（开槽）', 15, (140, 110, 20), anchor='lm')
s.box(LX0, 370, LX1, 406, '速干衣', fill=CLOTH, outline=(120, 160, 200), fs=17)
s.box(LX0, 411, LX1, 458, '皮肤', fill=SKIN, outline=(200, 150, 120), fs=17)

s.txt(LX1 + 16, 195, '压力来源', 15, GRAY)
s.txt(LX1 + 16, 234, '防止肩带磨管', 15, GRAY)
s.txt(LX1 + 16, 300, '管子嵌在槽里，', 15, DKGREEN, bold=True)
s.txt(LX1 + 16, 322, 'EVA 替它扛住压力', 15, DKGREEN, bold=True)
s.txt(LX1 + 16, 388, '吸汗 + 隔冷凝水', 15, GRAY)
s.txt(LX1 + 16, 434, '换热面', 15, GRAY)

s.box(60, 482, 700, 578, '', fill=GREENBG, outline=GREEN, width=3)
s.txt(78, 508, '槽宽 = 管外径 8mm，槽深 = 管径的 2/3（约 5mm）', 16, DKGREEN, bold=True)
s.txt(78, 538, '垂直压力全部由 EVA 承担，管子只受泡棉的弹性反力，压不瘪', 15, DKGREEN)
s.txt(78, 562, '露出的 1/3 管壁照常贴皮肤换热，泡棉的保温影响很小', 15, DKGREEN)

# ======================================================================
#  ② 垫子俯视图（右上）
# ======================================================================
tx = section_title(790, 100, '2')
s.txt(tx, 100, '垫子俯视图（管子走蛇形）', 22, BLACK, bold=True)

PX0, PX1, PY0, PY1 = 810, 1150, 145, 505
s.box(PX0, PY0, PX1, PY1, '', fill=(252, 252, 248), outline=BLACK, width=3, r=14)

ys = [455, 372, 289, 206]
pts = []
for i, y in enumerate(ys):
    a, b = (PX0 + 40, PX1 - 40) if i % 2 == 0 else (PX1 - 40, PX0 + 40)
    pts.append((a, y)); pts.append((b, y))
    if i < len(ys) - 1:
        pts.append((b, ys[i + 1]))
s.d.line(pts, fill=TUBE, width=9, joint='curve')
s.dot(pts[0][0], pts[0][1], TUBE, 10)
s.dot(pts[-1][0], pts[-1][1], TUBE, 10)
s.txt(PX0 + 66, 488, '进水', 14, BLUE, anchor='lm')
s.txt(PX0 + 66, 176, '出水', 14, BLUE, anchor='lm')

s.txt((PX0 + PX1) // 2, PY1 + 32, '25 cm（4 道 x 25cm = 1 米）', 15, BLACK, anchor='mm')
s.txt(PX0 - 12, (PY0 + PY1) // 2, '24cm', 14, GRAY, anchor='rm')

s.box(1180, 145, 1520, 578, '', fill=(245, 248, 252), outline=GRAY, width=2)
s.txt(1200, 180, '穿在身上怎么用', 17, BLACK, bold=True)
for i, line in enumerate([
        '一块垫子 =', '前胸 或 后背，', '二选一（1米只够一块）', '',
        '关键是：', '背包压在 EVA 上，', '不是压在管子上。', '',
        '管子只在 EVA 的', '槽里悬着，', '受力的是泡棉。', '',
        '松紧带用宽的', '（5cm 弹力带 +', '插扣），别用细绳。']):
    s.txt(1200, 214 + i * 25, line, 14, BLACK)

# ======================================================================
#  ③ 固定方式 对 / 错（中排，全宽）
# ======================================================================
tx = section_title(60, 640, '3')
s.txt(tx, 640, '固定方式：对 / 错', 22, BLACK, bold=True)

cols = [(60, 520), (540, 1000), (1020, 1480)]
BY0, BY1 = 672, 990
mid = (BY0 + BY1) // 2

# --- 错：卡箍环向勒紧 ---
x0, x1 = cols[0]
s.box(x0, BY0, x1, BY1, '', fill=REDBG, outline=RED, width=3)
s.txt((x0 + x1) // 2, BY0 + 32, 'X   304 卡箍勒紧', 18, RED, bold=True, anchor='mm')
s.d.rectangle([x0 + 60, mid - 30, x1 - 60, mid + 30], outline=(90, 90, 90), width=5)
s.d.ellipse([x0 + 78, mid - 22, x1 - 78, mid + 22], outline=TUBE, width=4, fill=(240, 250, 255))
s.txt((x0 + x1) // 2, mid + 80, '环向勒出永久凹痕', 15, RED, anchor='mm')
s.txt((x0 + x1) // 2, mid + 106, '金属边缘还会割伤软管', 15, RED, anchor='mm')
s.txt((x0 + x1) // 2, mid + 142, '卡箍的正确用途：只用在宝塔头的软管接头', 14, GRAY, anchor='mm')

# --- 对：开槽嵌入 ---
x0, x1 = cols[1]
s.box(x0, BY0, x1, BY1, '', fill=GREENBG, outline=GREEN, width=3)
s.txt((x0 + x1) // 2, BY0 + 32, 'V   开槽嵌入（首选）', 18, GREEN, bold=True, anchor='mm')
s.d.rectangle([x0 + 60, mid - 46, x1 - 60, mid - 12], fill=EVA, outline=(196, 160, 40), width=3)
s.d.rectangle([x0 + 60, mid + 12, x1 - 60, mid + 46], fill=EVA, outline=(196, 160, 40), width=3)
tube_circle(s.d, (x0 + x1) // 2, mid, 22)
s.txt((x0 + x1) // 2, mid + 80, '压力由泡棉承担', 15, DKGREEN, bold=True, anchor='mm')
s.txt((x0 + x1) // 2, mid + 106, '管子完整不变形', 15, DKGREEN, anchor='mm')
s.txt((x0 + x1) // 2, mid + 142, '垫子边缘缝 5cm 松紧带，像护腰一样套身上', 14, GRAY, anchor='mm')

# --- 对：布环 / 松扎带 ---
x0, x1 = cols[2]
s.box(x0, BY0, x1, BY1, '', fill=GREENBG, outline=GREEN, width=3)
s.txt((x0 + x1) // 2, BY0 + 32, 'V   布环 / 松扎带', 18, GREEN, bold=True, anchor='mm')
s.d.line([x0 + 50, mid, x1 - 50, mid], fill=TUBE, width=12)
for cx in (x0 + 130, x1 - 130):
    s.d.arc([cx - 32, mid - 32, cx + 32, mid + 32], 0, 360, fill=GRAY, width=5)
s.txt((x0 + x1) // 2, mid + 80, '环要比管子松 1~2mm', 15, DKGREEN, anchor='mm')
s.txt((x0 + x1) // 2, mid + 106, '管子能滑动，弯折不被勒', 15, DKGREEN, anchor='mm')
s.txt((x0 + x1) // 2, mid + 142, '适合「先用几天试试」的临时做法', 14, GRAY, anchor='mm')

# ======================================================================
#  ④ 龙骨材料 + 管长预算（底排）
# ======================================================================
s.box(60, 1020, 760, 1170, '', fill=(245, 248, 252), outline=GRAY, width=2)
s.txt(80, 1050, '想做"龙骨"托住的话：材料这样选', 18, BLACK, bold=True)
s.txt(80, 1085, 'PVC 发泡板 3mm（雪弗板）  >  PP 中空板（广告板）', 15, BLACK)
s.txt(80, 1110, '>>  纸箱（出汗就软，背一天就散，还掉渣）', 15, RED, bold=True)
s.txt(80, 1142, '别做平板：热风枪吹到 80~100C 弯出胸/背弧度，否则只有', 14, GRAY)
s.txt(80, 1162, '中间接触、两边翘起，晃起来很硌', 14, GRAY)

s.box(790, 1020, 1480, 1170, '', fill=YELLOW, outline=ORANGE, width=2)
s.txt(810, 1050, '1 米硅胶管能做多大一块？', 18, BLACK, bold=True)
s.txt(810, 1085, '管间距 8cm，1 米 -> 只能走 4 道（每道 25cm）', 15, BLACK)
s.txt(810, 1110, '= 一块 25 x 25cm 的垫子，只够盖住前胸 或 后背之一', 15, BLACK)
s.txt(810, 1142, '想前后都铺，硅胶管要买到 2.5~3 米。硅胶管很便宜，', 15, RED, bold=True)
s.txt(810, 1162, '建议一次买够 3 米，多出来的留着改管路', 15, RED)

s.legend([(TUBE, '硅胶管'), (EVA, 'EVA 泡棉'), (SKIN, '皮肤'), (CLOTH, '速干衣'), (MESH, '网布')],
         x=60, y=H - 22)
s.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig7_wearable.png'))
