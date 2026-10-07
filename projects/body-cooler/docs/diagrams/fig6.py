# -*- coding: utf-8 -*-
"""图 6  端子排实物接线图"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schematic_lib import *

W, H = 2500, 1640
s = Sch(W, H, '图 6   端子排接线图（照着接）')
d = s.d
RD=(205,50,50); BK=(45,45,45); BU=(45,95,200); GN=(30,145,80); YL=(200,150,10); GY=(130,130,130)

# ================= ① 电源输入链 =================
s.txt(90, 106, '①  电源输入链', 19, RD, bold=True)
s.box(110, 140, 330, 290, '3S 锂电池组', fill=YELLOW, fs=16, bold=True,
      sub='11.1V / 12.6V'+chr(10)+'带 BMS 保护板', subfs=13)
s.txt(330, 182, '+', 22, RD, bold=True, anchor='rm')
s.txt(330, 252, '-', 22, BK, bold=True, anchor='rm')
s.wire([(330,182),(392,182)], RD, 5)
s.fuse(410, 160, 522, 204)
s.txt(466, 140, '5A 快熔', 13, ORANGE, bold=True, anchor='mm')
s.wire([(522,182),(562,182)], RD, 5)
s.box(562, 150, 722, 220, '', fill=REDBG, outline=RD, width=2)
d.line([(592,202),(642,202)], fill=BLACK, width=3)
d.line([(642,202),(684,172)], fill=BLACK, width=3)
s.txt(642, 154, '肩带开关 >=10A', 13, RD, bold=True, anchor='mm')
# +12V 落到 X1-1
s.wire([(722,182),(664,182),(664,404)], RD, 5)
s.txt(676, 300, '+12V', 14, RD, bold=True, anchor='lm')
# 电池负极落到 X1-4
s.wire([(330,252),(380,252),(380,332),(1348,332),(1348,404)], BK, 5)
s.txt(600, 318, 'GND  GND  GND  —— 公共地', 13, BK, bold=True, anchor='lm')

# ================= ② X1 电源分配端子排 =================
s.txt(90, 350, '②  X1   电源分配端子排（8 位）', 19, (0,110,190), bold=True)
s.box(520, 382, 2400, 700, '', fill=(246,248,250), outline=(0,110,190), width=2, r=10)
x1 = [('1','+12V',RD,['电池正极','经保险丝+开关']),
      ('2','+12V',RD,['跳线到 1','-> 继电器 COM x5']),
      ('3','+12V',RD,['跳线到 2','-> DC-DC #1/#2 IN+']),
      ('4','GND',BK,['电池负极','公共地起点']),
      ('5','GND',BK,['跳线到 4','-> 继电器/DC-DC/传感器']),
      ('6','5V_A',BU,['DC-DC#1 输出','-> 5 个继电器 VCC']),
      ('7','5V_B',BU,['DC-DC#2 输出','-> ESP32 的 5V 脚']),
      ('8','备用',GY,['预留','以后加风扇/二号泵'])]
for i,(num,name,col,notes) in enumerate(x1):
    x0 = 560 + i*228
    s.box(x0, 420, x0+208, 674, '', fill='white', outline=(180,195,210), width=2, r=8)
    d.rounded_rectangle([x0+12, 434, x0+88, 470], radius=17, fill=col)
    s.txt(x0+50, 452, 'X1-' + num, 15, 'white', bold=True, anchor='mm', mono=True)
    s.txt(x0+98, 452, name, 17, col, bold=True, anchor='lm', mono=True)
    d.line([x0+12, 486, x0+196, 486], fill=(215,222,230), width=1)
    for j,n in enumerate(notes):
        s.txt(x0+14, 512+j*27, n, 12, BLACK)
    if i in (0,1,3):
        xr = x0 + 208
        d.line([(xr+2, 440),(xr+18, 424),(xr+18, 440)], fill=ORANGE, width=3)
        s.txt(xr+22, 424, '跳线', 11, ORANGE, bold=True, anchor='lm')

# ================= ③ X2 ESP32 引脚端子排 =================
s.txt(90, 742, '③  X2   ESP32 引脚端子排（20 位）—— X1-x 和 X2-x 是两组不同的端子，别接混', 19, GN, bold=True)
s.box(90, 774, 2410, 1074, '', fill=(246,250,247), outline=GN, width=2, r=10)
s.box(90, 1112, 2410, 1412, '', fill=(246,250,247), outline=GN, width=2, r=10)
x2a = [('1','3V3',RD,'传感器电源'),('2','GND',BK,'公共地'),
       ('3','IO1',YL,'电池分压中点'),('4','IO4',YL,'DS18B20 的 DQ'),
       ('5','IO8',YL,'OLED 的 SDA'),('6','IO9',YL,'OLED 的 SCL'),
       ('7','IO10',YL,'水流(分压后)'),('8','IO11',YL,'液位开关'),
       ('9','IO18',YL,'漏水检测线'),('10','IO21',YL,'备用')]
x2b = [('11','IO38',YL,'按键 A'),('12','IO39',YL,'按键 B'),
       ('13','IO5',GN,'继电器1 IN'),('14','IO6',GN,'继电器2 IN'),
       ('15','IO7',GN,'继电器3 IN'),('16','IO15',GN,'继电器4 IN'),
       ('17','IO16',GN,'继电器5 IN'),('18','IO17',GN,'蜂鸣器'),
       ('19','5V',BU,'<- 5V_B'),('20','GND',BK,'公共地')]
for cells, y0 in [(x2a, 800), (x2b, 1138)]:
    for i,(num,name,col,note) in enumerate(cells):
        x0 = 118 + i*230
        s.box(x0, y0, x0+206, y0+256, '', fill='white', outline=(190,215,200), width=2, r=8)
        d.rounded_rectangle([x0+10, y0+14, x0+82, y0+46], radius=16, fill=col)
        s.txt(x0+46, y0+30, 'X2-' + num, 14, 'white', bold=True, anchor='mm', mono=True)
        s.txt(x0+90, y0+30, name, 16, col, bold=True, anchor='lm', mono=True)
        d.line([x0+10, y0+58, x0+196, y0+58], fill=(220,225,230), width=1)
        s.txt(x0+103, y0+88, '接 ESP32 的', 12, GY, anchor='mm')
        s.txt(x0+103, y0+116, name, 15, BLACK, bold=True, anchor='mm', mono=True)
        s.txt(x0+103, y0+152, '↓', 15, GY, anchor='mm')
        s.txt(x0+103, y0+196, note, 13, BLACK, anchor='mm')
        s.txt(x0+103, y0+228, '接 ' + note.split(' ')[-1] if False else '', 12, GY, anchor='mm')

# ================= ④ 说明 =================
s.box(90, 1440, 2410, 1610, '', fill=LGRAY, outline=GRAY, width=2)
s.txt(115, 1472, '接线规则', 17, RED, bold=True)
for i,t in enumerate([
    '线色约定：红=+12V   黑=GND   蓝=5V   黄=信号',
    '端子排每格是独立的，同电位的格子要用短跳线并联',
    '一个螺钉端子可以压 2~3 根线，别硬塞',
    '先接 GND，再接电源，最后接信号 —— 这样不会烧东西',
]):
    s.txt(115, 1508 + i*24, t, 14, BLACK)
for i,(c,t) in enumerate([(RD,'+12V'),(BK,'GND'),(BU,'5V'),(YL,'信号')]):
    x = 1180 + i*290
    d.line([x, 1516, x+40, 1516], fill=c, width=6)
    s.txt(x+52, 1516, t, 15, c, bold=True, anchor='lm')
s.txt(1180, 1560, '上电前用万用表通断档确认：+12V 和 GND 之间不能短路', 14, RED, bold=True)
s.txt(1180, 1592, '首次上电先只接电池 + 万用表，确认电压正常再接模块', 14, RED, bold=True)
s.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig6_terminal_wiring.new.png'))