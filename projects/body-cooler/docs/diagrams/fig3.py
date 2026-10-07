# -*- coding: utf-8 -*-
"""图 3  水路走向与保温结构"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schematic_lib import *

W, H = 1800, 1300
s = Sch(W, H, '图 3   水路走向与保温结构')
d = s.d
COLD = (35,105,190); WARM = (215,105,35)
def blend(c1,c2,t): return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))

# ---------- 背包 ----------
s.box(70, 130, 660, 980, '', fill=(249,247,242), outline=(150,140,120), width=3, r=18)
s.txt(365, 162, '背  包', 23, (120,105,80), bold=True, anchor='mm')
s.box(110, 190, 620, 300, '锂电池防水盒', fill=(255,232,232), outline=RED, fs=18, bold=True,
      sub='3S 组 + BMS + 5A 保险丝   放最上层，和水路隔开', subfs=13)
# 冷罐
s.box(130, 560, 470, 830, '', fill=(226,240,250), outline=COLD, width=3)
s.txt(300, 596, 'PET 冷罐 500mL', 20, (25,75,145), bold=True, anchor='mm')
s.txt(300, 622, '(外面套保温套)', 14, GRAY, anchor='mm')
s.box(165, 650, 435, 725, '自吸水冰袋', fill='white', outline=(150,190,225), fs=16, bold=True)
d.line([138, 765, 462, 765], fill=COLD, width=2)
s.txt(300, 786, '液面（留 15~20% 空气）', 13, COLD, anchor='mm')
s.txt(300, 545, '防水透气阀 / 疏水膜', 13, COLD, bold=True, anchor='mm')
d.line([300, 553, 300, 564], fill=COLD, width=3)
d.line([215, 760, 215, 822], fill=COLD, width=5)
s.txt(226, 812, '吸水管离底 5~10mm + 滤网', 12, COLD)
# 泵
s.box(490, 860, 630, 950, '365 泵', fill=(235,245,235), outline=GREEN, fs=18, bold=True, sub='低于液面', subfs=12)

# ---------- 出水：罐 -> 泵 ----------
s.wire([(470,650),(530,650),(530,860)], COLD, 5)
# ---------- 泵 -> 出背包 ----------
s.wire([(630,905),(690,905),(690,520),(900,520)], COLD, 5)
# 暴露段保温
d.line([(690,520),(900,520)], fill=(228,228,228), width=17)
d.line([(690,520),(900,520)], fill=COLD, width=5)
s.txt(795, 478, '暴露段（套保温管）', 15, (90,90,90), bold=True, anchor='mm')
s.txt(795, 566, '内径 12 x 壁厚 13~14 橡塑保温管', 14, GRAY, anchor='mm')

# ---------- 人体 ----------
s.box(900, 380, 1420, 860, '', fill=(252,250,247), outline=(190,175,160), width=3, r=22)
s.txt(1160, 412, '贴身速干衣内侧', 18, (150,130,110), bold=True, anchor='mm')
pts=[(900,500),(1380,500),(1380,590),(940,590),(940,680),(1380,680),(1380,770),(900,770)]
for i in range(len(pts)-1):
    d.line([pts[i],pts[i+1]], fill=blend(COLD,WARM,i/(len(pts)-2)), width=7)
s.txt(1160, 822, '贴身段：不保温', 16, (90,90,90), bold=True, anchor='mm')
s.txt(872, 480, '冷水进', 14, COLD, bold=True, anchor='rm')
s.txt(872, 736, '温水回', 14, WARM, bold=True, anchor='rm')
# ---------- 回水：人体 -> 罐 ----------
s.wire([(880,720),(850,720),(850,1040),(440,1040),(440,832)], WARM, 5)

# ---------- 探头 ----------
def probe(x, y, label, col, anchor='lm'):
    d.ellipse([x-8,y-8,x+8,y+8], fill=col, outline='white', width=2)
    s.txt(x+(16 if anchor=='lm' else -16), y, label, 14, col, bold=True, anchor=anchor)
probe(530, 730, 'WATER_OUT  出水温（最冷点）', COLD)
probe(730, 1040, 'WATER_RET  回水温（最热点）', WARM)
probe(1380, 500, 'SKIN_CHEST', (200,55,55))
probe(1380, 680, 'SKIN_BACK', (200,55,55))
probe(600, 430, 'AMBIENT 背包内环境', (120,120,120))

# ---------- 说明 ----------
s.box(70, 1090, 1740, 1250, '', fill=LGRAY, outline=GRAY, width=2)
s.txt(95, 1122, '要点', 17, RED, bold=True)
for i,t in enumerate([
    '1. 软管从 10m 裁到 4~5m，暴露段压到 1~1.5m',
    '2. 暴露段套 13~14mm 保温管（防结露 + 减冷损）',
    '3. 贴身段不保温 —— 那一段本来就是要换热的',
    '4. 罐子放背包最下层，软管从底部直接穿进衣服',
    '5. 罐内留 15~20% 空气并加透气阀，防薄壁罐被吸瘪',
    '6. 泵必须低于液面，初次先灌引水，绝不允许干转',
    '7. 背包内衬防水，底部留一个朝下的排水口',
    '8. 走管避开腋下 / 腹股沟 / 颈前',
]):
    s.txt(95 + (i//4)*840, 1156 + (i%4)*24, t, 14, BLACK)
s.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig3_water_loop.png'))