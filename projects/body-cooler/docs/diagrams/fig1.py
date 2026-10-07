# -*- coding: utf-8 -*-
"""图 1  电源分配与水泵主回路"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schematic_lib import *

W, H = 1800, 1380
s = Sch(W, H, '图 1   电源分配与水泵主回路（rev2）')
d = s.d

# ============ 电池 ============
s.box(70, 640, 310, 800, '3S 锂电池组', fill=YELLOW, fs=20, bold=True,
      sub='11.1V 标称 / 12.6V 满电'+chr(10)+'9.0V 放空'+chr(10)+'(必须带 BMS 保护板)', subfs=15)
s.txt(310, 690, '+', 26, RED, bold=True, anchor='rm')
s.txt(310, 760, '-', 26, BLACK, bold=True, anchor='rm')

# ============ 保险丝 ============
s.wire([(310,690),(375,690)], RED)
s.fuse(395, 668, 520, 712)
s.txt(457, 640, '5A 快熔 F5A', 17, ORANGE, bold=True, anchor='mm')
s.wire([(520,690),(580,690)], RED)
s.dot(580, 690)

# ============ +12V 母线 ============
s.wire([(580,240),(580,1010)], RED, 4)
s.txt(600, 200, '+12V 母线', 19, RED, bold=True)

# ============ 主回路：急停 -> 继电器 -> 泵 ============
s.dot(580, 240)
s.wire([(580,240),(650,240)], RED, 4)
s.box(650, 178, 800, 300, '急停按钮', fill=REDBG, fs=18, bold=True,
      sub='LAY37-11ZS'+chr(10)+'常闭 NC 触点', subfs=14)
s.wire([(800,240),(865,240)], RED, 4)

s.box(865, 120, 1105, 360, '', fill=CYANBG)
s.txt(985, 152, '5V 光耦继电器模块 1', 19, BLACK, bold=True, anchor='mm')
s.txt(985, 178, '(10A 触点，可跳线选高/低电平触发)', 14, GRAY, anchor='mm')
# 内部触点示意
d.line([(905,240),(1000,240)], fill=GRAY, width=3)
d.line([(1000,240),(1060,205)], fill=GRAY, width=3)
d.line([(1060,215),(1060,258)], fill=GRAY, width=3)
d.line([(1035,285),(1085,285)], fill=GRAY, width=3)
d.rounded_rectangle([(1035,270),(1085,300)], radius=4, outline=GRAY, width=2)
s.txt(1060, 320, '线圈', 13, GRAY, anchor='mm')
s.txt(890, 240, 'COM', 15, BLACK, anchor='lm')
s.txt(1085, 240, 'NO', 15, BLACK, anchor='rm')
s.txt(880, 336, 'VCC', 13, GRAY, anchor='lm')
s.txt(935, 336, 'GND', 13, GRAY, anchor='lm')
s.txt(1010, 336, 'IN', 13, GRAY, anchor='lm')

s.wire([(1105,240),(1190,240)], RED, 4)
s.dot(1140, 240)

# ============ 泵 ============
s.motor(1245, 240, 52, BLACK, 'M')
s.txt(1245, 345, '365 隔膜泵', 20, BLACK, bold=True, anchor='mm')
s.txt(1245, 372, '12V / 450mA  启动峰值约 2A', 15, GRAY, anchor='mm')
s.wire([(1297,240),(1450,240)], RED, 4)
s.wire([(1450,240),(1450,1240)], BLACK, 4)

# ============ 续流二极管 ============
s.wire([(1140,240),(1140,145)], BLUE, 3)
s.wire([(1140,145),(1218,145)], BLUE, 3)
s.diode(1245, 145, 26, BLUE, points_left=True)
s.wire([(1272,145),(1360,145)], BLUE, 3)
s.wire([(1360,145),(1360,240)], BLUE, 3)
s.dot(1360, 240)
s.box(1050, 78, 1460, 122, '', fill=(235,242,255), outline=BLUE, width=2)
s.txt(1255, 100, '1N5822 续流二极管（阴极/有环端朝 +12V）', 16, BLUE, bold=True, anchor='mm')

# ============ 继电器控制脚 ============
for x, lab, col in [(905,'5V_A', BLUE), (960,'GND', BLACK), (1040,'ESP32 GPIO5', GREEN)]:
    s.wire([(x,360),(x,412)], col, 3, dash=(col is GREEN))
    s.txt(x, 430, lab, 15, col, bold=True, anchor='mm')

# ============ DC-DC 1 ============
s.dot(580, 745)
s.wire([(580,745),(640,745)], RED, 4)
s.box(640, 700, 910, 845, 'DC-DC #1   XL4015E1', fill=GREENBG, fs=18, bold=True,
      sub='12V -> 5V / 5A 可调'+chr(10)+'只给继电器模块供电', subfs=14)
s.wire([(640,795),(608,795)], BLACK, 3)
s.wire([(608,795),(608,1240)], BLACK, 3)
s.wire([(910,745),(1000,745)], BLUE, 3)
s.box(1005, 712, 1270, 780, '5V_A 电源轨', fill=(235,242,255), outline=BLUE, fs=17, bold=True,
      sub='>= 2A，继电器线圈用', subfs=13, tcolor=BLUE)
s.wire([(910,795),(1040,795)], BLACK, 3)
s.wire([(1040,795),(1040,1240)], BLACK, 3)

# ============ DC-DC 2 ============
s.dot(580, 945)
s.wire([(580,945),(640,945)], RED, 4)
s.box(640, 900, 910, 1045, 'DC-DC #2   MP1584EN', fill=GREENBG, fs=18, bold=True,
      sub='12V -> 5V / 3A'+chr(10)+'只给 ESP32 + 探头供电（干净电源）', subfs=14)
s.wire([(640,995),(608,995)], BLACK, 3)
s.wire([(608,995),(608,1240)], BLACK, 3)
s.dot(608, 995)
s.dot(608, 1240)
s.wire([(910,945),(1000,945)], BLUE, 3)
s.box(1005, 912, 1270, 980, '5V_B 电源轨', fill=(235,242,255), outline=BLUE, fs=17, bold=True,
      sub='>= 1A，主控与传感器用', subfs=13, tcolor=BLUE)
s.wire([(910,995),(1080,995)], BLACK, 3)
s.wire([(1080,995),(1080,1240)], BLACK, 3)

# ============ GND 母线 ============
s.wire([(310,760),(340,760)], BLACK, 4)
s.wire([(340,760),(340,1240)], BLACK, 4)
s.dot(340, 1240)
s.wire([(340,1240),(1450,1240)], BLACK, 4)
s.dot(608, 1240); s.dot(1040, 1240); s.dot(1080, 1240)
s.gnd(1560, 1240)
s.wire([(1450,1240),(1560,1240)], BLACK, 4)
s.txt(700, 1288, 'GND 母线 —— 电池负极 / DC-DC / 继电器模块 / ESP32 全部必须共地', 17, BLACK, bold=True)

# ============ 说明框 ============
s.box(1320, 480, 1740, 700, '', fill=LGRAY, outline=GRAY, width=2)
s.txt(1340, 512, '接线要点', 19, RED, bold=True)
for i, t in enumerate([
    '1. 泵正极走继电器 NO 触点（常开）',
    '   断电时泵绝对不转',
    '2. 续流二极管阴极朝 +12V，接反 =',
    '   直接短路，会烧保险丝',
    '3. 急停常闭触点串在 12V 硬回路里',
    '   不依赖单片机，按下去就断',
    '4. 两个 DC-DC 分开：泵的大电流',
    '   不会污染主控的 5V',
    '5. 电池正极出口先过保险丝再分流',
]):
    s.txt(1340, 545 + i*19, t, 14, BLACK if t[0] != ' ' else GRAY)

# ============ 图例 ============
s.legend([(RED,'+12V 主回路'), (BLUE,'5V / 信号'), (BLACK,'GND / 负极线'), (GREEN,'MCU 控制线')], x=70, y=1330)

s.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig1_power_pump.png'))