# -*- coding: utf-8 -*-
"""
生成 KiCad 旧版（EESchema v4）原理图 + 符号库 —— 嘉立创EDA 可直接导入。

为什么用旧格式：嘉立创EDA 的文件导入文档明确写着
  「仅支持 KiCAD v4.06 及以上版本」，且「v5.1.3 后的版本文件格式有更新，可能会导入失败」。
所以这里生成 v4 的 .sch + .lib，并打成 zip（导入原理图时必须带库文件）。

输出:
    body-cooler.sch / body-cooler.lib / body-cooler-cache.lib / body-cooler-kicad.zip
规则: 每一处点对点连接都带网络标签；同名网络 = 必须手工接的一根线。
"""
import os, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))

SYMS = {}


def S(name, ref, f0, f1, draw, pins):
    SYMS[name] = dict(ref=ref, f0=f0, f1=f1, draw=draw, pins=pins)


# ============================== 符号库 ==============================
S('ESP32-S3-DEVKITC', 'U', (-1000, 1080), (0, -1080),
  ['S -1000 900 1000 -900 0 1 12 f'],
  [('GPIO4', '1',  -1200,  700, 'R', 'B'), ('GPIO1', '2',  -1200,  500, 'R', 'B'),
   ('GPIO10','3',  -1200,  300, 'R', 'B'), ('GPIO11','4',  -1200,  100, 'R', 'B'),
   ('GPIO18','5',  -1200, -100, 'R', 'B'), ('GPIO21','6',  -1200, -300, 'R', 'B'),
   ('GPIO38','7',  -1200, -500, 'R', 'B'), ('GPIO39','8',  -1200, -700, 'R', 'B'),
   ('GPIO5', '9',   1200,  700, 'L', 'B'), ('GPIO6', '10',  1200,  500, 'L', 'B'),
   ('GPIO7', '11',  1200,  300, 'L', 'B'), ('GPIO15','12',  1200,  100, 'L', 'B'),
   ('GPIO16','13',  1200, -100, 'L', 'B'), ('GPIO17','14',  1200, -300, 'L', 'B'),
   ('GPIO48','15',  1200, -500, 'L', 'B'),
   ('GND',   '16',  -400, -1100, 'U', 'W'), ('5V',    '17',     0, -1100, 'U', 'W'),
   ('3V3',   '18',   400, -1100, 'U', 'W')])

S('PWR-MODULE', 'PS', (-700, 700), (0, -700),
  ['S -700 600 700 -600 0 1 12 f'],
  [('VIN+', '1', -900,  400, 'R', 'W'), ('VIN-', '2', -900, -400, 'R', 'W'),
   ('+5V_A','3',  900,  400, 'L', 'w'), ('+5V_B','4',  900,  200, 'L', 'w'),
   ('+3V3', '5',  900,    0, 'L', 'w'), ('GND',  '6',  900, -400, 'L', 'w')])

S('RELAY-5V-LOW', 'K', (-300, 400), (0, -480),
  ['S -300 300 300 -300 0 1 12 f',
   'P 2 0 1 0 -160 60 160 60 N',
   'P 4 0 1 0 -160 -60 -40 60 60 -60 160 60 N',
   'P 2 0 1 0 300 200 200 200 N', 'P 2 0 1 0 300 -200 200 -200 N'],
  [('VCC', '1', -500,  200, 'R', 'W'), ('IN',  '2', -500,    0, 'R', 'I'),
   ('GND', '3', -500, -200, 'R', 'W'), ('COM', '4',  500,  200, 'L', 'P'),
   ('NO',  '5',  500,    0, 'L', 'P'), ('NC',  '6',  500, -200, 'L', 'P')])

S('R', 'R', (80, 0), (0, 160), ['S -40 100 40 -100 0 1 8 N'],
  [('~', '1', 0,  200, 'D', 'P'), ('~', '2', 0, -200, 'U', 'P')])

S('DS18B20', 'T', (-420, 420), (0, -420), ['S -300 300 300 -300 0 1 12 f'],
  [('VDD', '1', -500,  200, 'R', 'W'), ('DQ', '2', -500, 0, 'R', 'B'),
   ('GND', '3', -500, -200, 'R', 'W')])

S('BUZZER', 'LS', (-330, 330), (0, -330), ['S -250 250 250 -250 0 1 12 f'],
  [('+', '1', -450,  100, 'R', 'I'), ('-', '2', -450, -100, 'R', 'W')])

S('BATTERY-3S', 'BT', (-330, 330), (0, -520), ['S -300 200 300 -200 0 1 12 f'],
  [('+', '1', 0,  400, 'D', 'W'), ('-', '2', 0, -400, 'U', 'W')])

S('FUSE', 'F', (-380, 180), (0, -180), ['S -300 100 300 -100 0 1 12 f'],
  [('~', '1', -500, 0, 'R', 'P'), ('~', '2', 500, 0, 'L', 'P')])

S('D-SCHOTTKY', 'D', (-300, 260), (0, -320),
  ['P 2 0 1 10 120 140 120 -140 N', 'P 3 0 1 10 -120 140 120 0 -120 -140 N'],
  [('A', '1', -500, 0, 'R', 'P'), ('K', '2', 500, 0, 'L', 'P')])

S('PUMP-365', 'M', (-260, 400), (0, -400), ['C -400 0 300 0 1 12 N'],
  [('+', '1', -500, 0, 'R', 'P'), ('-', '2', 500, 0, 'L', 'P')])

S('FLOW-YF-S401', 'FS', (-440, 440), (0, -440), ['S -400 300 400 -300 0 1 12 f'],
  [('VCC', '1', -600,  200, 'R', 'W'), ('GND', '2', -600, -200, 'R', 'W'),
   ('OUT', '3',  600,    0, 'L', 'O')])

for _n in ('SW-LEVER', 'SW-NC', 'SW-PUSH'):
    S(_n, 'SW', (-300, 320), (0, -320), ['S -300 200 300 -200 0 1 12 f'],
      [('~', '1', -500, 0, 'R', 'P'), ('~', '2', 500, 0, 'L', 'P')])

S('CONN-2', 'J', (-300, 420), (0, -420), ['S -300 300 300 -300 0 1 12 f'],
  [('1', '1', -500,  100, 'R', 'P'), ('2', '2', -500, -100, 'R', 'P')])


def lib_text():
    o = ['EESchema-LIBRARY Version 2.4', '#encoding utf-8', '#']
    for name, s in SYMS.items():
        o += ['# ' + name, '#',
              'DEF %s %s 0 40 Y Y 1 F N' % (name, s['ref']),
              'F0 "%s" %d %d 50 H V C CNN' % (s['ref'], s['f0'][0], s['f0'][1]),
              'F1 "%s" %d %d 50 H V C CNN' % (name, s['f1'][0], s['f1'][1]),
              'F2 "" 0 0 50 H V C CNN', 'F3 "" 0 0 50 H V C CNN', 'DRAW']
        o += s['draw']
        for pn, num, px, py, orient, et in s['pins']:
            o.append('X %s %s %d %d 200 %s 50 50 1 1 %s' % (pn, num, px, py, orient, et))
        o += ['ENDDRAW', 'ENDDEF', '#']
    o.append('#End Library')
    return '\n'.join(o) + '\n'


# ============================== 绘图原语 ==============================
ROT = {0: (1, 0, 0, -1), 90: (0, -1, -1, 0), 180: (-1, 0, 0, 1), 270: (0, 1, 1, 0)}
body, PINMAP, REFS, WIRES, LABELS, PINS = [], {}, [], [], [], []


def place(name, ref, value, x, y, rot=0):
    a, b, c, d = ROT[rot]
    s = SYMS[name]
    # ★ 用「工程库名:符号名」的标准写法，并把两个库都写进 LIBS 行
    body.extend(['$Comp', 'L body-cooler:%s %s' % (name, ref),
             'U 1 1 %08X' % (0x5F000000 + len(REFS) * 7 + 1),
             'P %d %d' % (x, y),
             'F 0 "%s" H %d %d 50  0000 C CNN' % (ref, x + 40, y + 70),
             'F 1 "%s" H %d %d 50  0000 C CNN' % (value, x + 40, y + 140),
             'F 2 "" H %d %d 50  0001 C CNN' % (x, y),
             'F 3 "" H %d %d 50  0001 C CNN' % (x, y),
             '\t1    %d %d' % (x, y), '\t%d    %d    %d    %d' % (a, b, c, d), '$EndComp'])
    pm = {}
    for pn, num, px, py, orient, et in s['pins']:
        pos = (x + a * px + b * py, y + c * px + d * py)
        pm[num] = pos
        pm.setdefault(pn, pos)
        PINS.append((pos, '%s.%s' % (ref, pn)))
    PINMAP[ref] = pm
    REFS.append((ref, name, value, x, y, rot))
    return pm


def wire(x1, y1, x2, y2):
    body.extend(['Wire Wire Line', '\t%d %d %d %d' % (x1, y1, x2, y2)])
    WIRES.append(((x1, y1), (x2, y2)))


def wires(*pts):
    for i in range(len(pts) - 1):
        wire(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])


def label(x, y, text, orient=0):
    body.extend(['Text Label %d %d %d    50   ~ 0' % (x, y, orient), text])
    LABELS.append(((x, y), text))


def junction(x, y):
    body.append('Connection ~ %d %d' % (x, y))


def note(x, y, text, size=60):
    body.extend(['Text Notes %d %d 0    %d   ~ 0' % (x, y, size), text])


def stub(pos, dx, dy, net):
    """从引脚拉一小段线并打网络标签 —— 本项目所有连接都长这样。"""
    x, y = pos
    ex, ey = x + dx, y + dy
    wire(x, y, ex, ey)
    o = 2 if dx < 0 else 0
    label(ex, ey, net, o)
    return (ex, ey)

# ============================== 版面（mil，A2 = 23386 x 16535）==============================
note(700, 620, 'ESP32 全身降温器 —— 接线原理图（控制端 + 输入端）', 90)
note(700, 800, '低电平触发继电器 + 开漏驱动 ／ 不含陶瓷与电解电容 ／ 每一处点对点连接都已标注网络名', 55)
note(700, 950, '规则：两个引脚标着同一个网络名，就表示必须手工接的一根线（同名即相连，不必画成实线）。', 55)

# ---------- 一、12V 电源树 ----------
note(700, 1250, '【一】12V 电源树', 75)
bt1 = place('BATTERY-3S', 'BT1', '3S 锂电 11.1V/12.6V满', 1500, 2300)
f1 = place('FUSE', 'F1', '5A', 2700, 1900)
ps1 = place('PWR-MODULE', 'PS1', '12V -> 5V_A / 5V_B / 3V3', 5900, 2300)
wire(bt1['+'][0], bt1['+'][1], bt1['+'][0], 1900)
wire(bt1['+'][0], 1900, f1['1'][0], f1['1'][1])
label(bt1['+'][0], 1900, '+12V_BAT', 0)
wire(f1['2'][0], f1['2'][1], ps1['VIN+'][0], ps1['VIN+'][1])
label(f1['2'][0] + 300, f1['2'][1], '+12V_F', 0)
wire(bt1['-'][0], bt1['-'][1], bt1['-'][0], ps1['VIN-'][1])
wire(bt1['-'][0], ps1['VIN-'][1], ps1['VIN-'][0], ps1['VIN-'][1])
label(bt1['-'][0], ps1['VIN-'][1], 'GND', 0)
for pn, net in (('+5V_A', '+5V_A'), ('+5V_B', '+5V_B'), ('+3V3', '+3V3'), ('GND', 'GND')):
    stub(ps1[pn], 600, 0, net)

# ---------- 二、ESP32 ----------
note(3900, 3400, '【二】ESP32-S3-DevKitC-1（只画本项目用到的脚）', 75)
note(3900, 3520, '左右两侧都是 500mil 短支线 + 网络标签，靠名字连接', 48)
u1 = place('ESP32-S3-DEVKITC', 'U1', 'ESP32-S3-N16R8', 6200, 5200)
for pn, net in (('GPIO4', 'OW_DQ'), ('GPIO1', 'VBAT_SENSE'), ('GPIO10', 'FLOW_SIG'),
                ('GPIO11', 'LEVEL_SW'), ('GPIO18', 'LEAK_A'), ('GPIO21', 'ESTOP_SW'),
                ('GPIO38', 'BTN_A'), ('GPIO39', 'BTN_B')):
    stub(u1[pn], -700, 0, net)
for pn, net in (('GPIO5', 'K1_IN'), ('GPIO6', 'K2_IN'), ('GPIO7', 'K3_IN'),
                ('GPIO15', 'K4_IN'), ('GPIO16', 'K5_IN'), ('GPIO17', 'BUZZ')):
    stub(u1[pn], 700, 0, net)
stub(u1['GPIO48'], 700, 0, 'NC_WS2812板载')
for pn, net in (('GND', 'GND'), ('5V', '+5V_B'), ('3V3', '+3V3')):
    stub(u1[pn], 0, 600, net)

# ---------- 三、继电器 ----------
note(9600, 1250, '【三】继电器模块 K1~K5（低电平触发）', 75)
note(9600, 1370, 'IN 拉低 = 吸合；释放时 GPIO 变高阻，由 10k 上拉到 5V 才彻底截止', 48)
REL_Y = [1900, 3300, 4700, 6100, 7500]
for i, y in enumerate(REL_Y):
    k = place('RELAY-5V-LOW', 'K%d' % (i + 1), '5V低电平触发', 10400, y)
    stub(k['VCC'], -300, 0, '+5V_A')
    stub(k['GND'], -300, 0, 'GND')
    stub(k['IN'], -600, 0, 'K%d_IN' % (i + 1))
    stub(k['COM'], 300, 0, '+12V_F')
    if i == 0:
        wire(k['NO'][0], k['NO'][1], k['NO'][0] + 300, k['NO'][1])
        label(k['NO'][0] + 300, k['NO'][1], 'PUMP_P', 0)
    else:
        stub(k['NO'], 300, 0, 'K%d_OUT_备用' % (i + 1))
    note(k['NC'][0] + 420, k['NC'][1] + 20, 'NC 不接', 45)

# ---------- 四、泵主回路 ----------
note(13300, 1250, '【四】泵主回路：电池+ -> 保险丝 -> 继电器 COM/NO -> 泵+ -> 泵- -> 电池-', 75)
m1 = place('PUMP-365', 'M1', '365 隔膜泵', 14300, 1900)
wire(PINMAP['K1']['NO'][0] + 300, 1900, m1['+'][0], m1['+'][1])
label(12300, 1900, 'PUMP_P', 0)
stub(m1['-'], 900, 0, 'GND')
d1 = place('D-SCHOTTKY', 'D1', '1N5822 续流', 14300, 2700, rot=180)
wire(d1['K'][0], d1['K'][1], d1['K'][0], m1['+'][1])
junction(d1['K'][0], m1['+'][1])
wire(d1['A'][0], d1['A'][1], d1['A'][0], m1['-'][1])
junction(d1['A'][0], m1['-'][1])
note(13500, 3000, '阴极(有环那一端)朝泵+', 48)

# ---------- 三之二、10k 上拉组 ----------
note(11800, 7900, '【三之二】继电器 IN 的 10k 上拉（5 只：一端 +5V_A，一端 Kn_IN）', 70)
note(11800, 8010, 'ESP32 复位期间 GPIO 是高阻，靠它把 IN 明确拉到 5V，继电器才彻底截止', 48)
for i, x in enumerate((12300, 13300, 14300, 15300, 16300)):
    r = place('R', 'RP%d' % (i + 1), '10k', x, 8800)
    stub(r['1'], 0, -400, '+5V_A')
    stub(r['2'], 0, 400, 'K%d_IN' % (i + 1))

# ---------- 五、输入端 ----------
note(700, 7900, '【五】输入端', 75)

note(700, 8150, '5.1 DS18B20 单总线温度（4.7k 上拉到 3V3，整条总线只加一只）', 65)
r11 = place('R', 'R11', '4.7k', 1300, 9000)
stub(r11['1'], 0, -400, '+3V3')
stub(r11['2'], 0, 400, 'OW_DQ')
for i, y in enumerate((8800, 9800, 10800)):
    t = place('DS18B20', 'T%d' % (i + 1), '防水探头%d' % (i + 1), 3000, y)
    stub(t['VDD'], -500, 0, '+3V3')
    stub(t['DQ'], -500, 0, 'OW_DQ')
    stub(t['GND'], -500, 0, 'GND')
note(1900, 11300, '现只有 3 个防水探头，还缺 2 个；再多就并联到 OW_DQ', 45)

note(4500, 8150, '5.2 电池电压采样（100k / 18k = 6.556:1，必须走 ADC1）', 65)
r6 = place('R', 'R6', '100k', 5000, 9000)
r7 = place('R', 'R7', '18k', 5000, 9800)
stub(r6['1'], 0, -400, '+12V_F')
wire(r6['2'][0], r6['2'][1], r7['1'][0], r7['1'][1])
wire(r6['2'][0], r6['2'][1], r6['2'][0] + 700, r6['2'][1])
label(r6['2'][0] + 700, r6['2'][1], 'VBAT_SENSE', 0)
junction(r6['2'][0], r6['2'][1])
stub(r7['2'], 0, 400, 'GND')

note(6700, 8150, '5.3 水流传感器（5V 方波经 2.2k+10k/20k 分压到 3.11V 进 GPIO10）', 65)
r8 = place('R', 'R8', '2.2k', 7000, 9000)
r9 = place('R', 'R9', '10k', 7000, 9800)
r10 = place('R', 'R10', '20k', 7000, 10600)
fs1 = place('FLOW-YF-S401', 'FS1', 'YF-S401', 8900, 9400, rot=180)
stub(r8['1'], 0, -400, '+5V_A')
wire(r8['2'][0], r8['2'][1], r9['1'][0], r9['1'][1])
wire(r8['2'][0], r8['2'][1], fs1['OUT'][0], fs1['OUT'][1])
label(7500, r8['2'][1], 'FLOW_PU', 0)
junction(r8['2'][0], r8['2'][1])
wire(r9['2'][0], r9['2'][1], r10['1'][0], r10['1'][1])
wire(r9['2'][0], r9['2'][1], r9['2'][0] + 700, r9['2'][1])
label(r9['2'][0] + 700, r9['2'][1], 'FLOW_SIG', 0)
junction(r9['2'][0], r9['2'][1])
stub(r10['2'], 0, 400, 'GND')
stub(fs1['VCC'], 500, 0, '+5V_A')
stub(fs1['GND'], 500, 0, 'GND')

note(700, 12000, '5.4 开关量（全部用 MCU 内部上拉：引脚 — 开关 — GND）', 65)
for i, (sym, ref, val, net) in enumerate([
        ('SW-LEVER', 'SW1', '浮子液位(常开)', 'LEVEL_SW'),
        ('SW-NC', 'SW2', '急停/总电源(常闭)', 'ESTOP_SW'),
        ('SW-PUSH', 'SW3', '按键A', 'BTN_A'),
        ('SW-PUSH', 'SW4', '按键B', 'BTN_B')]):
    x = 2100 + (i % 2) * 3000
    y = 12500 + (i // 2) * 1500
    sw = place(sym, ref, val, x, y)
    stub(sw['1'], -600, 0, net)
    stub(sw['2'], 600, 0, 'GND')
j1 = place('CONN-2', 'J1', '漏水探针', 6300, 13000)
stub(j1['1'], -600, 0, 'LEAK_A')
stub(j1['2'], -600, 0, 'GND')
note(5400, 13500, 'J1 两根裸铜线相距 2~3mm，遇水导通', 45)

note(8300, 12000, '5.5 蜂鸣器（可选）', 65)
ls1 = place('BUZZER', 'LS1', '有源蜂鸣器', 9200, 12500)
stub(ls1['+'], -600, 0, 'BUZZ')
stub(ls1['-'], -600, 0, 'GND')

note(11800, 10600, '图例 / 网络名含义', 75)
for i, s in enumerate([
        '+12V_BAT   电池正极（保险丝之前）',
        '+12V_F     保险丝之后的 12V 母线',
        '+5V_A      只给 5 个继电器线圈的 5V 轨',
        '+5V_B      只给 ESP32 的 5V 轨',
        '+3V3       ESP32 的 3.3V（DS18B20 上拉）',
        'GND        单点星形接地的公共地',
        'K1_IN ~ K5_IN   GPIO5/6/7/15/16 -> 继电器线圈 IN',
        'PUMP_P     继电器1 的 NO 触点 -> 泵正极',
        'K2_OUT ~ K5_OUT_备用   备用继电器输出',
        'OW_DQ      DS18B20 单总线',
        'VBAT_SENSE / FLOW_SIG   分压中点 -> ADC',
        'LEVEL_SW / ESTOP_SW / LEAK_A / BTN_A / BTN_B   开关量输入']):
    note(11800, 10770 + i * 110, s, 45)
note(11800, 12300, '同名网络 = 必须手工接的一根线', 52)
note(11800, 12440, '本图按你要求不含任何陶瓷电容与电解电容', 52)
note(11800, 12580, '继电器模块必须和 ESP32 共地，否则改极性也没用', 52)

# ============================== 输出 + 自检 ==============================
def schematic_text():
    head = ['EESchema Schematic File Version 4', 'LIBS:body-cooler body-cooler-cache',
            'EELAYER 29 0', 'EELAYER END', '$Descr A2 23386 16535', 'Sheet 1 1',
            'Title "ESP32 全身降温器 接线原理图"', 'Date "2026-02-14"', 'Rev "1"',
            'Comp "EnderCraft-Server"',
            'Comment1 "控制端 + 输入端，每处点对点连接都已标注网络名"',
            'Comment2 "低电平触发继电器 / 开漏驱动 / 不含陶瓷与电解电容"',
            'Comment3 ""', 'Comment4 ""', '$EndDescr']
    return '\n'.join(head) + '\n' + '\n'.join(body) + '\n$EndSCHEMATC\n'


def on_seg(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    if ax == bx:
        return px == ax and min(ay, by) < py < max(ay, by)
    if ay == by:
        return py == ay and min(ax, bx) < px < max(ax, bx)
    return False


def seg_cross(a, b, c, d):
    """两条正交线段是否在内部交叉（交叉不算连接，但要看会不会被误读）"""
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = a, b, c, d
    if ax == bx and cy == dy:
        return min(ay, by) < cy < max(ay, by) and min(cx, dx) < ax < max(cx, dx)
    if ay == by and cx == dx:
        return min(ax, bx) < cx < max(ax, bx) and min(cy, dy) < ay < max(cy, dy)
    return False


def validate():
    pinset = {}
    for pos, who in PINS:
        pinset.setdefault(pos, []).append(who)
    labset = set(p for p, _ in LABELS)
    ends = {}
    for a, b in WIRES:
        ends[a] = ends.get(a, 0) + 1
        ends[b] = ends.get(b, 0) + 1
    bad, tees = [], []
    for a, b in WIRES:
        for p in (a, b):
            hit = [w for w in WIRES if on_seg(p, w[0], w[1])]
            if not ((p in pinset) or (p in labset) or (ends.get(p, 0) >= 2) or hit):
                bad.append((p, 'dangling'))
            elif hit and p not in pinset and ends.get(p, 0) < 2 and p not in labset:
                tees.append(p)
    orphan = [w for pos, w in PINS if pos not in ends]
    cross = []
    for i in range(len(WIRES)):
        for j in range(i + 1, len(WIRES)):
            if seg_cross(WIRES[i][0], WIRES[i][1], WIRES[j][0], WIRES[j][1]):
                cross.append((WIRES[i], WIRES[j]))
    return bad, tees, orphan, cross


def main():
    lib = lib_text()
    for fn in ('body-cooler.lib', 'body-cooler-cache.lib'):
        open(os.path.join(HERE, fn), 'w', encoding='utf-8').write(lib)
    sch = schematic_text()
    open(os.path.join(HERE, 'body-cooler.sch'), 'w', encoding='utf-8').write(sch)
    with zipfile.ZipFile(os.path.join(HERE, 'body-cooler-kicad.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for fn in ('body-cooler.sch', 'body-cooler.lib', 'body-cooler-cache.lib'):
            z.write(os.path.join(HERE, fn), 'body-cooler/' + fn)
    bad, tees, orphan, cross = validate()
    print('符号 %d  元件 %d  导线 %d  标签 %d  引脚 %d' %
          (len(SYMS), len(REFS), len(WIRES), len(LABELS), len(PINS)))
    print('悬空导线端点 %d %s' % (len(bad), bad[:8]))
    print('未标注的 T 形接点 %d %s' % (len(tees), tees[:8]))
    print('未接线引脚 %d %s' % (len(orphan), orphan[:14]))
    print('交叉(不相连) %d %s' % (len(cross), cross[:6]))
    for f in ('body-cooler.lib', 'body-cooler-cache.lib', 'body-cooler.sch', 'body-cooler-kicad.zip'):
        print('  %-24s %8d bytes' % (f, os.path.getsize(os.path.join(HERE, f))))


if __name__ == '__main__':
    main()
