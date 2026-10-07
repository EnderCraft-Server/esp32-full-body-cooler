# -*- coding: utf-8 -*-
"""图 5  整机系统原理图（电源 + 主回路 + 主控 + 传感器互联）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schematic_lib import *

W, H = 2300, 1560
s = Sch(W, H, '图 5   整机系统原理图')
d = s.d

# ============================================================
#  A  电源输入链
# ============================================================
s.txt(90, 105, 'A  电源输入与分配', 20, RED, bold=True)
s.box(90, 140, 310, 300, '3S 锂电池组', fill=YELLOW, fs=17, bold=True,
      sub='11.1V 标称'+chr(10)+'12.6V 满电'+chr(10)+'带 BMS 保护板', subfs=13)
s.txt(310, 180, '+', 22, RED, bold=True, anchor='rm')
s.txt(310, 250, '-', 22, BLACK, bold=True, anchor='rm')
s.wire([(310,180),(360,180)], RED, 4)
s.fuse(378, 158, 490, 202)
s.txt(434, 138, '5A 快熔', 14, ORANGE, bold=True, anchor='mm')
s.wire([(490,180),(530,180)], RED, 4)
s.box(530, 145, 690, 218, '', fill=REDBG, outline=RED, width=2)
d.line([(560,200),(610,200)], fill=BLACK, width=3)
d.line([(610,200),(650,168)], fill=BLACK, width=3)
d.ellipse([(556,196),(564,204)], fill=BLACK); d.ellipse([(646,164),(654,172)], fill=BLACK)
s.txt(610, 148, '肩带开关 >=10A', 13, RED, bold=True, anchor='mm')
s.wire([(690,180),(750,180)], RED, 5)
s.wire([(750,180),(2210,180)], RED, 6)
s.txt(770, 148, '+12V 母线', 17, RED, bold=True)
s.txt(2210, 205, '', 12, GRAY, anchor='rm')

# ---- 主回路分支 ----
s.dot(870, 180)
s.wire([(870,180),(870,300)], RED, 4)
s.box(760, 300, 1070, 510, '', fill=CYANBG, outline=BLACK, width=2)
s.txt(915, 330, '5V 光耦继电器模块 x5', 17, BLACK, bold=True, anchor='mm')
s.txt(915, 355, '(通道 1 驱动水泵)', 13, GRAY, anchor='mm')
d.line([(820,410),(940,410)], fill=GRAY, width=3)
d.line([(940,410),(990,378)], fill=GRAY, width=3)
s.txt(790, 410, 'COM', 13, BLACK, anchor='lm')
s.txt(1045, 410, 'NO', 13, BLACK, anchor='rm')
s.txt(846, 490, 'VCC', 12, GRAY, anchor='mm'); s.txt(931, 490, 'GND', 12, GRAY, anchor='mm'); s.txt(1016, 490, 'IN', 12, GRAY, anchor='mm')
for x, lab, col in [(846,'5V_A',BLUE),(931,'GND',BLACK),(1016,'ESP32 GPIO5',GREEN)]:
    s.wire([(x,510),(x,556)], col, 3, dash=(col is GREEN))
    s.txt(x, 574, lab, 13, col, bold=True, anchor='mm')
# 泵
s.wire([(1070,410),(1155,410)], RED, 4)
s.dot(1110, 410)
s.motor(1210, 410, 52, BLACK, 'M')
s.txt(1210, 492, '365 泵', 15, BLACK, bold=True, anchor='mm')
s.wire([(1262,410),(1420,410)], RED, 4)
s.wire([(1420,410),(1420,560)], BLACK, 3)
s.txt(1420, 578, 'GND', 13, BLACK, bold=True, anchor='mm')
# 续流二极管
s.wire([(1110,410),(1110,300)], BLUE, 3)
s.wire([(1110,300),(1185,300)], BLUE, 3)
s.diode(1210, 300, 24, BLUE, points_left=True)
s.wire([(1235,300),(1330,300)], BLUE, 3)
s.wire([(1330,300),(1330,410)], BLUE, 3)
s.dot(1330, 410)
s.box(1040, 232, 1390, 274, '', fill=(235,242,255), outline=BLUE, width=2)
s.txt(1215, 253, '1N5822 续流二极管（阴极朝 +12V）', 14, BLUE, bold=True, anchor='mm')

# ---- DC-DC 分支 ----
s.dot(1660, 180)
s.wire([(1660,180),(1660,300)], RED, 4)
s.box(1540, 300, 1870, 435, 'DC-DC #1', fill=GREENBG, outline=GREEN, fs=16, bold=True,
      sub='XL4015E1  12V -> 5V / 5A'+chr(10)+'只给继电器模块', subfs=13)
s.wire([(1705,435),(1705,486)], BLUE, 3)
s.netlabel(1705, 505, '5V_A', BLUE, 14)
s.dot(2070, 180)
s.wire([(2070,180),(2070,300)], RED, 4)
s.box(1950, 300, 2280, 435, 'DC-DC #2', fill=GREENBG, outline=GREEN, fs=16, bold=True,
      sub='MP1584EN  12V -> 5V / 3A'+chr(10)+'只给 ESP32 + 探头', subfs=13)
s.wire([(2115,435),(2115,486)], BLUE, 3)
s.netlabel(2115, 505, '5V_B', BLUE, 14)

# ============================================================
#  B  ESP32 主控
# ============================================================
s.txt(90, 660, 'B  ESP32-S3 主控', 20, BLUE, bold=True)
s.box(90, 695, 900, 1300, '', fill=(249,251,253), outline=BLACK, width=3, r=14)
s.txt(495, 728, 'ESP32-S3 DevKitC-1', 21, BLACK, bold=True, anchor='mm')
s.txt(495, 754, 'N16R8   16MB Flash   8MB PSRAM', 13, GRAY, anchor='mm')
d.line([115, 772, 875, 772], fill=(200,200,200), width=2)
s.txt(130, 800, '输入信号', 16, GREEN, bold=True)
s.txt(520, 800, '输出信号', 16, RED, bold=True)
lin = [('GPIO1','电池分压采样'),('GPIO4','DS18B20 x5 单总线'),('GPIO8','I2C SDA'),
       ('GPIO9','I2C SCL'),('GPIO10','水流传感器'),('GPIO11','液位开关'),
       ('GPIO18','漏水检测'),('GPIO21','(空闲)'),('GPIO38','按键 A'),('GPIO39','按键 B')]
lout = [('GPIO5','继电器1  水泵'),('GPIO6','继电器2  备用'),('GPIO7','继电器3  备用'),
        ('GPIO15','继电器4  备用'),('GPIO16','继电器5  备用'),('GPIO17','蜂鸣器'),
        ('GPIO48','WS2812 状态灯')]
for i,(p,u) in enumerate(lin):
    y = 840 + i*43
    s.txt(135, y, p, 15, BLACK, bold=True, mono=True)
    s.txt(240, y, u, 14, GRAY)
for i,(p,u) in enumerate(lout):
    y = 840 + i*43
    s.txt(525, y, p, 15, BLACK, bold=True, mono=True)
    s.txt(630, y, u, 14, GRAY)
s.box(130, 1180, 860, 1278, '', fill=(240,246,255), outline=BLUE, width=2)
s.txt(150, 1208, '3V3  ->  DS18B20 / I2C 上拉 / OLED', 14, RED)
s.txt(150, 1240, '5V_B <-  DC-DC #2 接到开发板的 5V(VIN) 脚，不要动 3V3 脚', 14, BLUE)

# ============================================================
#  C  传感器与调理电路
# ============================================================
s.txt(960, 660, 'C  传感器与调理电路', 20, PURPLE, bold=True)
cells = [
 (960, 695, 1600, 830, 'DS18B20 防水探头 x5', (226,240,250), [
    '接 GPIO4 单总线，5 个全部并联',
    '电源 3V3 + GND',
    '★ 整条总线只加 1 个 4.7k 上拉到 3V3（不是 5V）']),
 (1640, 695, 2280, 830, '电池电压采样', (255,246,214), [
    '接 GPIO1  (必须 ADC1)',
    'BAT+ ->[100k]-> 节点 ->[18k]-> GND',
    '节点 -> GPIO1，18k 上并 100nF']),
 (960, 860, 1600, 995, 'YF-S401 水流传感器', (226,240,250), [
    '接 GPIO10，5V 供电',
    '★ 信号线要电平转换：',
    '5V -[2.2k]-+->[10k]-> GPIO10，10k 后 20k 到 GND']),
 (1640, 860, 2280, 995, '液位开关 / 漏水检测', (226,246,230), [
    '液位 -> GPIO11   漏水 -> GPIO18',
    '都用 MCU 内部上拉，另一端接 GND',
    '不需要外部电阻']),
 (960, 1025, 1600, 1160, '按键 A / B', (235,235,235), [
    'A -> GPIO38    B -> GPIO39',
    '轻触开关，一端接引脚一端接 GND',
    '用内部上拉，不需要外部电阻']),
 (1640, 1025, 2280, 1160, 'OLED 显示屏', (226,240,250), [
    'SDA -> GPIO8    SCL -> GPIO9',
    '3V3 供电，SSD1306 驱动',
    'I2C 上拉 4.7k x2 多数模块板上自带']),
]
for x0,y0,x1,y1,t,fill,notes in cells:
    s.box(x0, y0, x1, y1, '', fill=fill)
    d.line([x0+12, y0+38, x1-12, y0+38], fill=(190,190,190), width=1)
    s.txt(x0+16, y0+20, t, 16, BLACK, bold=True)
    for i,n in enumerate(notes):
        s.txt(x0+16, y0+60+i*22, n, 13, RED if n.startswith(chr(0x2605)) else BLACK)

# ============================================================
#  D  说明
# ============================================================
s.box(90, 1330, 2280, 1520, '', fill=LGRAY, outline=GRAY, width=2)
s.txt(115, 1362, '接线要点', 17, RED, bold=True)
for i, t in enumerate([
    '1. 电池正极出口先过 5A 保险丝再分流；所有 GND 单点共地',
    '2. 续流二极管阴极（有环端）朝 +12V，接反 = 直接短路',
    '3. 5 个继电器模块的 IN 引脚每个都要加 10k 下拉到 GND',
    '4. DS18B20 的 4.7k 上拉接 3V3，绝不能接 5V',
    '5. 泵的电源线不要和 DS18B20 单总线捆在一起走',
    '6. ESP32 用 DC-DC #2 的 5V 接开发板 5V 脚，USB 供电时不要同时接',
]):
    s.txt(115 + (i%3)*715, 1398 + (i//3)*34, t, 14, BLACK)
s.txt(115, 1480, '可选输入（电池/水流/液位/急停/漏水）在固件里默认关闭 —— 接好一根、验证过读数，再把 config.h 里对应的 ENABLE_xxx 改成 1', 13, BLUE, bold=True)
s.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig5_system_schematic.png'))