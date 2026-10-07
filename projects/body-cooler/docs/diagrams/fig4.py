# -*- coding: utf-8 -*-
"""图 4  三种搭建方式（不需要画 PCB）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schematic_lib import *

W, H = 1800, 920
s = Sch(W, H, '图 4   三种搭建方式 —— 你不需要画电路板')
d = s.d

def panel(x0, x1, title, num, col):
    s.box(x0, 110, x1, 800, '', fill='white', outline=(215,215,215), width=2, r=14)
    d.ellipse([x0+28, 138, x0+62, 172], fill=col)
    s.txt(x0+45, 155, num, 18, 'white', bold=True, anchor='mm')
    s.txt(x0+76, 155, title, 20, BLACK, bold=True, anchor='lm')

# ============ 面板 1：面包板 ============
panel(60, 580, '桌面验证阶段', '1', (60,130,200))
d.rounded_rectangle([100,230,540,650], radius=8, fill=(238,238,234), outline=(170,170,165), width=2)
for r in range(9):
    for c in range(16):
        d.ellipse([118+c*26-2, 250+r*22-2, 118+c*26+2, 250+r*22+2], fill=(200,200,196))
for c in range(16):
    d.ellipse([118+c*26-2, 452-2, 118+c*26+2, 452+2], fill=(255,255,255))
d.line([105, 448, 535, 448], fill=(215,215,210), width=6)
d.rounded_rectangle([160,268,480,410], radius=8, fill=(35,65,100), outline=BLACK, width=2)
s.txt(320, 315, 'ESP32-S3', 20, 'white', bold=True, anchor='mm')
s.txt(320, 345, '开发板', 16, (170,200,230), anchor='mm')
s.txt(320, 385, '（这就是你的电路板）', 13, (140,175,210), anchor='mm')
d.line([190,410,190,500], fill=(210,80,80), width=3)
d.line([450,410,450,500], fill=(60,60,60), width=3)
d.rounded_rectangle([120,500,320,560], radius=6, fill=(225,240,250), outline=(60,110,170), width=2)
s.txt(220, 530, '继电器模块', 15, BLACK, anchor='mm')
d.rounded_rectangle([340,500,530,560], radius=6, fill=(226,246,230), outline=GREEN, width=2)
s.txt(435, 530, 'DC-DC 模块', 15, BLACK, anchor='mm')
d.line([190,500,190,530], fill=(210,80,80), width=3)
d.line([190,530,150,530], fill=(60,60,60), width=3)
s.txt(320, 690, '面包板 830 孔 约 8 元 + 杜邦线', 15, BLACK, anchor='mm')
s.txt(320, 720, '插上就能跑，改线不用焊', 14, GRAY, anchor='mm')
s.txt(320, 752, '缺点：振动会松，不能上身', 14, RED, anchor='mm')

# ============ 面板 2：免板焊接 ============
panel(620, 1180, '免板方案（推荐）', '2', (0,140,70))
s.txt(900, 205, '全项目 P0 只需焊 6 个电阻', 17, GREEN, bold=True, anchor='mm')
# 继电器模块特写
d.rounded_rectangle([670,240,940,420], radius=8, fill=(225,240,250), outline=(60,110,170), width=2)
s.txt(805, 272, '继电器模块', 17, BLACK, bold=True, anchor='mm')
d.ellipse([700,330,730,360], outline=GRAY, width=2)
d.ellipse([880,330,910,360], outline=GRAY, width=2)
s.txt(805, 345, '线圈 + 触点', 13, GRAY, anchor='mm')
for x, lab in [(700,'VCC'), (780,'GND'), (880,'IN')]:
    d.ellipse([x-5,415,x+5,425], fill=BLACK)
    s.txt(x, 445, lab, 13, BLACK, anchor='mm')
d.line([780,425,780,485], fill=BLACK, width=3)
d.line([880,425,880,485], fill=BLACK, width=3)
s.res_h(800, 485, 860, BLACK)
d.line([780,485,800,485], fill=BLACK, width=3)
d.line([860,485,880,485], fill=BLACK, width=3)
s.txt(830, 515, '10k 直接焊在模块背面', 14, RED, bold=True, anchor='mm')
s.txt(830, 540, 'GND 和 IN 两个焊盘之间', 13, GRAY, anchor='mm')
# DS18B20 特写
d.rounded_rectangle([670,580,940,760], radius=8, fill='white', outline=(150,190,225), width=2)
s.txt(805, 608, 'DS18B20 三个线头', 15, BLACK, bold=True, anchor='mm')
cols = [(700,(210,60,60),'VDD'), (790,(200,170,40),'DQ'), (880,(60,60,60),'GND')]
for x, c, lab in cols:
    d.line([x, 640, x, 720], fill=c, width=4)
    s.txt(x, 740, lab, 12, c, bold=True, anchor='mm')
s.res_h(700, 665, 790, BLACK)
s.txt(805, 660, '4.7k', 14, RED, bold=True, anchor='lm')
d.line([700,640,700,665], fill=(210,60,60), width=3)
d.line([700,665,700,640], fill=(210,60,60), width=3)
d.line([790,640,790,665], fill=(210,60,60), width=3)
s.txt(805, 700, '焊在 VDD 和 DQ 之间', 13, GRAY, anchor='lm')
s.txt(900, 790, '焊完套热缩管，不需要任何电路板', 15, GREEN, bold=True, anchor='mm')

# ============ 面板 3：洞洞板 ============
panel(1220, 1740, '定型方案', '3', (190,110,0))
d.rounded_rectangle([1260,230,1700,650], radius=6, fill=(232,222,196), outline=(150,130,90), width=2)
for r in range(17):
    for c in range(18):
        d.ellipse([1278+c*23-3, 250+r*23-3, 1278+c*23+3, 250+r*23+3], outline=(170,155,120))
# ESP32 插在排母上
d.rounded_rectangle([1310,270,1600,410], radius=6, fill=(35,65,100), outline=BLACK, width=2)
s.txt(1455, 330, 'ESP32-S3', 17, 'white', bold=True, anchor='mm')
s.txt(1455, 360, '（插在排母上，可拆）', 12, (170,200,230), anchor='mm')
for y in range(280, 405, 20):
    d.ellipse([1302, y-4, 1310, y+4], fill=(220,190,60))
    d.ellipse([1600, y-4, 1608, y+4], fill=(220,190,60))
# 电阻
for i, x in enumerate([1300, 1360, 1420, 1480, 1540]):
    s.res_v(x, 450, 510, BLACK)
s.txt(1455, 535, '6 个电阻焊在板上', 13, BLACK, anchor='mm')
# 接线端子
for i, x in enumerate([1290, 1390, 1490, 1590]):
    d.rounded_rectangle([x-38,575,x+38,625], radius=4, fill=(60,150,90), outline=(30,90,50), width=2)
    d.ellipse([x-8,592,x+8,608], fill=(230,230,230))
s.txt(1480, 655, '螺钉接线端子', 13, BLACK, anchor='mm')
s.txt(1480, 700, '7x9cm 双面镀锡洞洞板 约 3 元', 15, BLACK, anchor='mm')
s.txt(1480, 730, '排母 + 螺钉端子 + 洞洞板 合计约 15 元', 14, GRAY, anchor='mm')
s.txt(1480, 762, '焊一次，以后不松动', 14, ORANGE, anchor='mm')

# ============ 底部说明 ============
s.box(60, 815, 1740, 890, '', fill=(240,246,255), outline=BLUE, width=2)
s.txt(90, 852, '三条路可以叠加：', 16, BLUE, bold=True, anchor='lm')
s.txt(240, 852, '先用面包板把电路调通  ->  再花 10 分钟焊 6 个电阻装进防水盒  ->  硬件完全定型后再考虑打 PCB（嘉立创 5 元打样 5 片，现在没必要）', 15, BLACK, anchor='lm')
s.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig4_build_methods.png'))