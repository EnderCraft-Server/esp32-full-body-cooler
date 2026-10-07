# -*- coding: utf-8 -*-
"""原理图绘制公共库（Pillow）"""
from PIL import Image, ImageDraw, ImageFont
import os

FONT_DIR = 'C:/Windows/Fonts'
def F(size, bold=False, mono=False):
    name = 'consola.ttf' if mono else ('msyhbd.ttc' if bold else 'msyh.ttc')
    p = os.path.join(FONT_DIR, name)
    if not os.path.exists(p):
        p = os.path.join(FONT_DIR, 'msyh.ttc')
    return ImageFont.truetype(p, size)

BLACK=(20,20,20); RED=(200,30,30); BLUE=(20,70,190); GREEN=(0,130,60)
ORANGE=(220,120,0); GRAY=(120,120,120); LGRAY=(225,228,232)
YELLOW=(255,246,214); CYANBG=(222,240,250); GREENBG=(226,246,230); REDBG=(253,232,232)
PURPLE=(120,50,160)

class Sch:
    def __init__(self, w, h, title):
        self.img = Image.new('RGB', (w, h), 'white')
        self.d = ImageDraw.Draw(self.img)
        self.w, self.h = w, h
        self.d.rectangle([0,0,w-1,h-1], outline=(180,180,180), width=2)
        self.d.text((w//2, 34), title, font=F(30, True), fill=BLACK, anchor='mm')
        self.d.line([40, 62, w-40, 62], fill=(200,200,200), width=2)

    def box(self, x0, y0, x1, y1, text='', fill=None, outline=BLACK, width=2, r=9,
            fs=19, bold=False, tcolor=None, sub=None, subfs=15, subsize=None):
        if fill: self.d.rounded_rectangle([x0,y0,x1,y1], radius=r, fill=fill, outline=outline, width=width)
        else:    self.d.rounded_rectangle([x0,y0,x1,y1], radius=r, outline=outline, width=width)
        cx, cy = (x0+x1)//2, (y0+y1)//2
        lines = text.split(chr(10)) if text else []
        if sub:
            lines = lines + sub.split(chr(10))
        if lines:
            lh = fs + 6
            total = lh*len(lines)
            y = cy - total//2 + lh//2
            for i, ln in enumerate(lines):
                is_sub = sub is not None and i >= len(text.split(chr(10))) if text else (sub is not None)
                fnt = F(subfs) if is_sub else F(fs, bold)
                col = GRAY if is_sub else (tcolor or BLACK)
                self.d.text((cx, y), ln, font=fnt, fill=col, anchor='mm')
                y += lh
        return (x0,y0,x1,y1)

    def wire(self, pts, color=RED, width=3, dash=False):
        for i in range(len(pts)-1):
            if dash: self._dline(pts[i], pts[i+1], color, width)
            else: self.d.line([pts[i], pts[i+1]], fill=color, width=width)

    def _dline(self, a, b, color, width, seg=14, gap=9):
        import math
        x0,y0=a; x1,y1=b; L=math.hypot(x1-x0,y1-y0)
        if L==0: return
        ux,uy=(x1-x0)/L,(y1-y0)/L; t=0
        while t < L:
            t2=min(t+seg,L)
            self.d.line([(x0+ux*t,y0+uy*t),(x0+ux*t2,y0+uy*t2)], fill=color, width=width)
            t=t2+gap

    def dot(self, x, y, color=RED, r=6):
        self.d.ellipse([x-r,y-r,x+r,y+r], fill=color)

    def txt(self, x, y, s, fs=17, color=BLACK, bold=False, anchor='lm', mono=False):
        self.d.text((x,y), s, font=F(fs,bold,mono), fill=color, anchor=anchor)

    def gnd(self, x, y, color=BLACK, label=True):
        self.d.line([x,y,x,y+16], fill=color, width=3)
        for i,w in enumerate([34,22,10]):
            self.d.line([x-w//2, y+16+i*9, x+w//2, y+16+i*9], fill=color, width=3)
        if label: self.txt(x, y+56, 'GND', 14, GRAY, anchor='mm')

    def fuse(self, x0, y0, x1, y1, color=BLACK):
        self.d.rounded_rectangle([x0,y0,x1,y1], radius=6, outline=color, width=2)
        cy=(y0+y1)//2
        self.d.line([x0, cy, x1, cy], fill=color, width=3)
        self.d.line([x0+8, cy-8, x1-8, cy+8], fill=color, width=2)

    def diode(self, cx, cy, size=26, color=BLACK, points_left=True):
        s=size
        if points_left:
            self.d.polygon([(cx+s,cy-s),(cx+s,cy+s),(cx-s,cy)], fill=color)
            self.d.line([cx-s, cy-s, cx-s, cy+s], fill=color, width=4)
        else:
            self.d.polygon([(cx-s,cy-s),(cx-s,cy+s),(cx+s,cy)], fill=color)
            self.d.line([cx+s, cy-s, cx+s, cy+s], fill=color, width=4)

    def motor(self, cx, cy, r=46, color=BLACK, label='M'):
        self.d.ellipse([cx-r,cy-r,cx+r,cy+r], outline=color, width=3, fill='white')
        self.d.text((cx,cy), label, font=F(30,True), fill=color, anchor='mm')

    def res_h(self, x0, y, x1, color=BLACK):
        self.d.line([x0,y,x1,y], fill=color, width=3)
        n=6; w=(x1-x0)/n; h=13
        pts=[]
        for i in range(n):
            pts.append((x0+w*i+w/2, y-h if i%2==0 else y+h))
        self.d.line(pts, fill=color, width=3, joint='curve')

    def cap(self, x, y, color=BLACK, w=26):
        self.d.line([x-w,y-12,x+w,y-12], fill=color, width=4)
        self.d.line([x-w,y+12,x+w,y+12], fill=color, width=4)
        self.d.line([x,y-30,x,y-12], fill=color, width=3)
        self.d.line([x,y+12,x,y+30], fill=color, width=3)

    def res_v(self, x, y0, y1, color=BLACK):
        n=6; h=(y1-y0)/n; w=13
        pts=[(x,y0)]
        for i in range(n):
            pts.append((x-w if i%2==0 else x+w, y0+h*i+h/2))
        pts.append((x,y1))
        self.d.line(pts, fill=color, width=3, joint='curve')

    def netlabel(self, x, y, text, color=BLUE, fs=15):
        fnt = F(fs, True)
        tw = self.d.textlength(text, font=fnt)
        self.d.rounded_rectangle([x-tw/2-10, y-14, x+tw/2+10, y+14], radius=7,
                                 fill=(240,246,255), outline=color, width=2)
        self.d.text((x, y), text, font=fnt, fill=color, anchor='mm')

    def save(self, path):
        self.img.save(path)
        print('wrote', path, self.img.size)

    def legend(self, items, x=60, y=None):
        if y is None: y = self.h-40
        cx = x
        for col, label in items:
            self.d.line([cx, y, cx+34, y], fill=col, width=3)
            self.txt(cx+42, y, label, 15, GRAY)
            cx += 42 + 12*len(label) + 30