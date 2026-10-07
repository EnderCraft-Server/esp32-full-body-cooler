# -*- coding: utf-8 -*-
"""图 2  ESP32-S3 控制与传感器接线（rev2）"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schematic_lib import *

W, H = 2300, 1950
s = Sch(W, H, '图 2   ESP32-S3 控制与传感器接线（rev2）')
d = s.d
EX0, EX1, EY0, EY1 = 900, 1460, 150, 1600

# ---------------- ESP32 主机 ----------------
s.box(EX0, EY0, EX1, EY1, '', fill=(249,251,253), outline=BLACK, width=3, r=14)
s.txt((EX0+EX1)//2, 195, 'ESP32-S3 DevKitC-1', 27, BLACK, bold=True, anchor='mm')
s.txt((EX0+EX1)//2, 226, 'N16R8   16MB Flash   8MB PSRAM', 15, GRAY, anchor='mm')
d.line([EX0+20, 248, EX1-20, 248], fill=(190,190,190), width=2)

LP = [('GPIO1',300,'电池电压'),('GPIO4',430,'DS18B20 总线'),('GPIO8',560,'I2C SDA'),
      ('GPIO9',690,'I2C SCL'),('GPIO10',820,'水流传感器'),('GPIO11',950,'液位开关'),
      ('GPIO18',1080,'漏水检测'),('GPIO21',1210,'急停按钮'),('GPIO38',1340,'按键 A'),
      ('GPIO39',1470,'按键 B')]
RP = [('GPIO5',300,'继电器 1'),('GPIO6',480,'继电器 2'),('GPIO7',660,'继电器 3'),
      ('GPIO15',840,'继电器 4'),('GPIO16',1020,'继电器 5'),('GPIO17',1200,'蜂鸣器'),
      ('GPIO48',1380,'状态灯')]
for n,y,u in LP:
    d.ellipse([EX0-7,y-7,EX0+7,y+7], fill=BLACK)
    s.txt(EX0+18, y, n, 18, BLACK, bold=True, anchor='lm', mono=True)
    s.txt(EX0+130, y, u, 15, GRAY, anchor='lm')
for n,y,u in RP:
    d.ellipse([EX1-7,y-7,EX1+7,y+7], fill=BLACK)
    s.txt(EX1-18, y, n, 18, BLACK, bold=True, anchor='rm', mono=True)
    s.txt(EX1-130, y, u, 15, GRAY, anchor='rm')

def lblock(y0, y1, t, sub, fill=CYANBG, fs=19):
    s.box(150, y0, 600, y1, t, fill=fill, fs=fs, bold=True, sub=sub, subfs=14)

# ---------------- 电池分压 ----------------
lblock(240, 360, '电池电压采样', '3S: 12.6V 满 / 11.1V 标称 / 9.0V 空', YELLOW)
s.netlabel(660, 150, 'BAT+ 12.6V', RED, 14)
s.wire([(660,165),(660,190)], RED, 3)
s.res_v(660, 190, 255, BLACK)
s.txt(686, 222, 'R1  100k 1%', 15, BLACK)
s.dot(660, 300)
s.wire([(660,255),(660,300)], BLACK, 3)
s.wire([(660,300),(EX0,300)], GREEN, 3)
s.wire([(660,300),(660,325)], BLACK, 3)
s.res_v(660, 325, 390, BLACK)
s.txt(686, 357, 'R2  18k 1%', 15, BLACK)
s.gnd(660, 390, label=False)
s.wire([(660,300),(745,300)], BLUE, 3)
s.cap(745, 330, BLUE)
s.wire([(745,360),(745,392)], BLACK, 3)
s.gnd(745, 392, label=False)
s.txt(772, 320, '100nF', 14, BLUE)
s.txt(890, 228, '分压比 6.556', 14, GRAY, anchor='rm')
s.txt(890, 250, '12.6V -> 1.92V', 14, GRAY, anchor='rm')

# ---------------- DS18B20 ----------------
lblock(370, 490, 'DS18B20 防水探头 x5', 'VDD(红)->3V3   GND(黑)->GND' + chr(10) + 'DQ(黄) 五个并联 -> GPIO4')
s.wire([(600,430),(EX0,430)], GREEN, 3)
s.dot(790, 430)
s.res_v(790, 380, 430, BLACK)
s.txt(812, 405, '4.7k', 15, RED, bold=True)
s.netlabel(790, 358, '3V3', RED, 14)

# ---------------- OLED I2C ----------------
lblock(500, 750, '0.96 寸 OLED  (SSD1306)', 'SDA -> GPIO8      SCL -> GPIO9' + chr(10) + 'I2C 地址通常 0x3C')
s.wire([(600,560),(EX0,560)], GREEN, 3)
s.wire([(600,690),(EX0,690)], GREEN, 3)
s.dot(730, 560)
s.res_v(730, 505, 560, BLACK)
s.txt(752, 532, '4.7k', 15, RED, bold=True)
s.netlabel(730, 483, '3V3', RED, 14)
s.dot(830, 690)
s.res_v(830, 635, 690, BLACK)
s.txt(852, 662, '4.7k', 15, RED, bold=True)
s.netlabel(830, 613, '3V3', RED, 14)

# ---------------- 水流传感器 ----------------
lblock(760, 880, 'YF-S401 水流传感器', '5V 供电，输出 5V 方波' + chr(10) + '5880 脉冲/升（可用 flowcal 标定）')
s.netlabel(650, 640, '5V', BLUE, 14)
s.wire([(650,655),(650,690)], BLUE, 3)
s.res_v(650, 690, 745, BLACK)
s.txt(672, 712, '2.2k', 14, BLUE, bold=True)
s.wire([(650,745),(650,820)], BLUE, 3)
s.dot(650, 820)
s.wire([(600,820),(650,820)], GREEN, 3)
s.wire([(650,820),(700,820)], GREEN, 3)
s.res_h(700, 820, 790, BLACK)
s.txt(745, 798, '10k', 15, BLACK)
s.wire([(790,820),(858,820)], GREEN, 3)
s.dot(858, 820)
s.wire([(858,820),(EX0,820)], GREEN, 3)
s.res_v(858, 820, 880, BLACK)
s.txt(880, 850, '20k', 15, BLACK)
s.gnd(858, 880, label=False)
s.box(660, 900, 900, 950, '', fill=(255,248,225), outline=ORANGE, width=2)
s.txt(780, 925, 'GPIO 高电平 3.11V', 15, ORANGE, bold=True, anchor='mm')

# ---------------- 其余输入 ----------------
lblock(890, 1010, '液位开关（浮子，常开 NO）', '一端接 GND，另一端 GPIO11' + chr(10) + '装在罐底上方约 10mm' + chr(10) + '用 MCU 内部上拉', GREENBG, 18)
s.wire([(600,950),(EX0,950)], GREEN, 3)
lblock(1020, 1140, '漏水检测线', '两根裸铜线，间距 2~3mm' + chr(10) + '铺在背包底部（电池盒外围）' + chr(10) + '用 MCU 内部上拉', GREENBG, 18)
s.wire([(600,1080),(EX0,1080)], GREEN, 3)
lblock(1150, 1270, '急停按钮 LAY37-11ZS', '常闭 NC：不按时接通 GND' + chr(10) + '按下或线断 = 被上拉拉高（失效安全）' + chr(10) + '用 MCU 内部上拉', REDBG, 18)
s.wire([(600,1210),(EX0,1210)], GREEN, 3)
lblock(1280, 1530, '按键 A / B', '轻触开关，一端接 GND' + chr(10) + 'A = 模式切换 / 配网' + chr(10) + 'B = 手动强制降温' + chr(10) + '用 MCU 内部上拉', LGRAY, 18)
s.wire([(600,1340),(EX0,1340)], GREEN, 3)
s.wire([(600,1470),(EX0,1470)], GREEN, 3)

# ---------------- 右侧输出 ----------------
relays = [(300,'继电器 1','365 水泵（主输出）   COM/NO 串在 12V 泵回路', REDBG),
          (480,'继电器 2','备用 / 风扇   aux 1', CYANBG),
          (660,'继电器 3','备用   aux 2', CYANBG),
          (840,'继电器 4','备用   aux 3', CYANBG),
          (1020,'继电器 5','备用 / 主电源总闸   aux 4', CYANBG)]
for y,t,u,c in relays:
    s.box(1520, y-58, 2050, y+58, t, fill=c, fs=19, bold=True, sub=u, subfs=14)
    s.wire([(EX1,y),(1520,y)], GREEN, 3)
s.box(1520, 1142, 2050, 1258, '有源蜂鸣器（可选）', fill=LGRAY, fs=18, bold=True, sub='正极 -> GPIO17，负极 -> GND', subfs=14)
s.wire([(EX1,1200),(1520,1200)], GREEN, 3)
s.box(1520, 1322, 2050, 1438, '板载 WS2812 状态灯', fill=LGRAY, fs=18, bold=True, sub='GPIO48，板上自带，无需外接', subfs=14)
s.wire([(EX1,1380),(1520,1380)], GREEN, 3)
s.box(1520, 1480, 2050, 1600, '', fill=(255,244,230), outline=ORANGE, width=2)
s.txt(1785, 1516, '5 个继电器模块的 IN 引脚', 18, ORANGE, bold=True, anchor='mm')
s.txt(1785, 1548, '每个都要加 10k 下拉到 GND', 18, ORANGE, bold=True, anchor='mm')
s.txt(1785, 1576, '防止 ESP32 复位瞬间水泵误启动', 13, GRAY, anchor='mm')

# ---------------- ESP32 底部电源脚 ----------------
for x,n,c in [(1000,'3V3',RED),(1160,'GND',BLACK),(1320,'5V',BLUE)]:
    d.ellipse([x-7,EY1-7,x+7,EY1+7], fill=c)
    s.txt(x, EY1+28, n, 18, c, bold=True, anchor='mm', mono=True)
s.wire([(1000,EY1),(1000,1660)], RED, 3)
s.netlabel(1000, 1660, '3V3', RED, 16)
s.wire([(1320,EY1),(1320,1660)], BLUE, 3)
s.netlabel(1320, 1660, '5V_B', BLUE, 16)
s.wire([(1160,EY1),(1160,1660)], BLACK, 3)
s.gnd(1160, 1660, label=False)
s.txt(1160, 1716, 'GND', 15, BLACK, bold=True, anchor='mm')

# ---------------- 注意事项 ----------------
s.box(150, 1570, 900, 1850, '', fill=LGRAY, outline=GRAY, width=2)
s.txt(172, 1600, '接线注意事项', 19, RED, bold=True)
for i,t in enumerate([
    '* DS18B20 的 4.7k 上拉必须接 3V3，接 5V 会烧 GPIO',
    '* 水流传感器信号线必须 2.2k 上拉 + 10k/20k 分压',
    '* 5 个探头并联在一条总线上，用 map 绑定角色后 save',
    '* 所有 GND 必须共地（含探头屏蔽层）',
    '* 泵的电源线不要和单总线捆在一起走',
    '* 电池分压的 100k/18k 不能用 10k 代替（会烧引脚）',
    '* 3V3 / 5V_B 都从 DC-DC 来，不要用开发板 5V 带继电器',
]):
    s.txt(172, 1636 + i*28, t, 15, BLACK)
s.box(960, 1760, 1780, 1860, '', fill=(240,246,255), outline=BLUE, width=2)
s.txt(990, 1790, '3V3  ->  DS18B20 / I2C 上拉 / OLED', 15, RED)
s.txt(990, 1822, '5V_B <-  DC-DC #2（主控与传感器专用，要干净）', 15, BLUE)
s.legend([(RED,'3V3'),(BLUE,'5V'),(BLACK,'GND'),(GREEN,'信号线')], x=150, y=1910)
s.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig2_esp32_wiring.png'))