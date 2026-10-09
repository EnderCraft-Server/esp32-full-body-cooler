# -*- coding: utf-8 -*-
"""把 make_schematic 的版面数据画成 PNG，用来肉眼检查有没有重叠/错位。"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import make_schematic as M

S = 0.115                                   # mil -> px
W = int(23386 * S); H = int(16535 * S)
img = Image.new('RGB', (W, H), (252, 252, 250))
d = ImageDraw.Draw(img)
FONT = 'C:/Windows/Fonts/msyh.ttc'
def font(sz): return ImageFont.truetype(FONT, sz)

INK = (30, 34, 42); WIRE = (0, 110, 60); LBLC = (170, 40, 40)
BODY = (60, 90, 170); PIN = (120, 120, 130)

def P(x, y): return (x * S, y * S)

# --- 元件 ---
for ref, name, value, x, y, rot in M.REFS:
    sym = M.SYMS[name]
    a, b, c, e = M.ROT[rot]
    # 外框
    body_rect = None
    for line in sym['draw']:
        if line.startswith('S '):
            p = line.split()
            x0, y0, x1, y1 = float(p[1]), float(p[2]), float(p[3]), float(p[4])
            pts = []
            for (px, py) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                pts.append(P(x + a*px + b*py, y + c*px + e*py))
            d.polygon(pts, outline=BODY)
            d.line(pts + [pts[0]], fill=BODY, width=2)
            body_rect = (min(q[0] for q in pts), min(q[1] for q in pts),
                         max(q[0] for q in pts), max(q[1] for q in pts))
        elif line.startswith('C '):
            p = line.split()
            cx, cy, r = float(p[1]), float(p[2]), float(p[3])
            q = P(x + a*cx + b*cy, y + c*cx + e*cy)
            rr = r * S
            d.ellipse([q[0]-rr, q[1]-rr, q[0]+rr, q[1]+rr], outline=BODY, width=2)
            body_rect = (q[0]-rr, q[1]-rr, q[0]+rr, q[1]+rr)
    # 引脚
    for pn, num, px, py, orient, et in sym['pins']:
        q = P(x + a*px + b*py, y + c*px + e*py)
        dv = {'R': (200, 0), 'L': (-200, 0), 'U': (0, -200), 'D': (0, 200)}[orient]
        q2 = P(x + a*(px+dv[0]) + b*(py+dv[1]), y + c*(px+dv[0]) + e*(py+dv[1]))
        d.line([q, q2], fill=PIN, width=2)
        d.ellipse([q[0]-3, q[1]-3, q[0]+3, q[1]+3], fill=(200, 60, 60))
        if pn != '~':
            tx = q[0] + (6 if dv[0] >= 0 else -6)
            d.text((tx, q[1]), pn, font=font(9), fill=(90, 96, 108),
                   anchor='lm' if dv[0] >= 0 else 'rm')
    # 位号 / 值
    d.text(P(x, y), '%s\n%s' % (ref, value), font=font(11), fill=INK, anchor='mm',
           align='center', spacing=2)

# --- 导线 ---
for (x1, y1), (x2, y2) in M.WIRES:
    d.line([P(x1, y1), P(x2, y2)], fill=WIRE, width=2)

# --- 接点 ---
for line in M.body:
    if line.startswith('Connection ~'):
        p = line.split()
        x, y = P(float(p[2]), float(p[3]))
        d.ellipse([x-4, y-4, x+4, y+4], fill=WIRE)

# --- 网络标签 ---
for (x, y), text in M.LABELS:
    tx, ty = P(x, y)
    d.text((tx + 3, ty - 8), text, font=font(11), fill=LBLC, anchor='lb')

# --- 注释文字 ---
i = 0
while i < len(M.body):
    if M.body[i].startswith('Text Notes'):
        p = M.body[i].split()
        x, y = P(float(p[2]), float(p[3]))
        size = max(9, int(float(p[4]) * 0.24))
        d.text((x, y), M.body[i+1], font=font(size), fill=(40, 44, 54))
        i += 2
    else:
        i += 1

img.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preview_schematic.png'))
print('wrote preview_schematic.png', img.size)
