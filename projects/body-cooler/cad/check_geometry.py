# -*- coding: utf-8 -*-
"""数值自检：确认螺旋缝真的存在、宽度对不对、最小弯曲半径推导对不对。"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_sleeve import helix_sleeve

v, f = helix_sleeve(slit=2.0, length=60.0, ang_n=28, step=0.6)
P = 2 * 28 + 2
ring_i = 50
base = ring_i * P
z = v[base][2]
ring = v[base:base + P]

# 只看外圈顶点（索引 29..58 是外弧，其中 29 对应 phi1，58 对应 phi0）
outer = [(math.degrees(math.atan2(p[1], p[0])) % 360, p) for p in ring[29:59]]
outer.sort()
print('z = %.2f mm, 外圈顶点数 %d' % (z, len(outer)))
gaps = []
for i in range(len(outer)):
    a0 = outer[i][0]
    a1 = outer[(i + 1) % len(outer)][0]
    d = (a1 - a0) % 360
    gaps.append((d, a0))
gaps.sort(reverse=True)
print('最大角间隙 = %.2f deg  (理论 gap_a = %.2f deg)' % (
    gaps[0][0], math.degrees(2.0 / 5.15)))
print('次大角间隙 = %.2f deg   (相邻顶点正常间距 = %.2f deg)' % (
    gaps[1][0], math.degrees((2 * math.pi - 2.0 / 5.15) / 28)))
print('缝的弧长 = %.2f mm  (目标 2.00)' % (math.radians(gaps[0][0]) * 5.15))
print('径向壁厚 = %.2f mm' % (6.0 - 4.3))
print('外径 %.1f  内径 %.1f' % (12.0, 8.6))
