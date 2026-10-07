# -*- coding: utf-8 -*-
"""
防折螺旋护套 (anti-kink helical sleeve) 生成器

问题：6x8 硅胶管一折就瘪，瘪了以后即使泵有推力也撑不开。
原理：
  1) 把软管套进一根"开螺旋缝的硬管"里 -> 径向被硬壳撑住，压不瘪；
  2) 螺旋缝在弯曲时内侧会闭合 -> 自然限制最小弯曲半径 Rmin，
     于是管子永远弯不到会打死折的角度。
     Rmin = 螺距 p * 外径 OD / (2 * 缝宽 g)

纯 Python 生成 + 自己写二进制 STL（不依赖任何第三方库）。
"""
import math, struct, os

OUT = os.path.dirname(os.path.abspath(__file__))


def helix_sleeve(r_in=4.3, r_out=6.0, slit=2.0, pitch=8.0, length=150.0,
                 ang_n=28, step=0.6):
    """C 形截面沿螺旋扫掠 -> 带螺旋缝的套筒。

    r_in   : 内半径 (半) = 管外径 8mm + 0.6 间隙 -> 4.3
    r_out  : 外半径 (半) = 12mm 外径 -> 6.0
    slit   : 螺旋缝宽度 mm
    pitch  : 螺距 mm
    length : 套筒长度 mm
    """
    mid_r = (r_in + r_out) * 0.5
    gap_a = slit / mid_r                 # 缝对应的圆心角
    n_ring = max(2, int(round(length / step)) + 1)
    dz = length / (n_ring - 1)
    span = 2.0 * math.pi - gap_a         # C 形张开的角度

    verts, faces = [], []
    P = 2 * ang_n + 2

    for i in range(n_ring):
        z = i * dz
        theta = 2.0 * math.pi * z / pitch         # 螺旋旋转角
        phi0 = theta + gap_a * 0.5
        ring = []
        # 内弧 φ0 -> φ1
        for k in range(ang_n + 1):
            phi = phi0 + span * k / ang_n
            ring.append((r_in * math.cos(phi), r_in * math.sin(phi), z))
        # 外弧 φ1 -> φ0
        for k in range(ang_n, -1, -1):
            phi = phi0 + span * k / ang_n
            ring.append((r_out * math.cos(phi), r_out * math.sin(phi), z))
        verts.extend(ring)

    for i in range(n_ring - 1):
        a = i * P
        b = (i + 1) * P
        for j in range(P):
            j2 = (j + 1) % P
            faces.append((a + j, a + j2, b + j2, b + j))

    # 两端封盖：内弧和外弧之间铺一圈四边形（不能用凹多边形 n-gon）
    for i, flip in ((0, False), (n_ring - 1, True)):
        base = i * P
        for j in range(ang_n):
            q = (base + j, base + j + 1, base + 2 * ang_n - j, base + 2 * ang_n + 1 - j)
            faces.append(q[::-1] if flip else q)

    return verts, faces


def write_binary_stl(path, verts, faces, name=b'anti-kink sleeve'):
    tris = []
    for f in faces:
        for k in range(1, len(f) - 1):
            tris.append((f[0], f[k], f[k + 1]))
    with open(path, 'wb') as fh:
        fh.write(name.ljust(80, b' ')[:80])
        fh.write(struct.pack('<I', len(tris)))
        for a, b, c in tris:
            v1, v2, v3 = verts[a], verts[b], verts[c]
            ux, uy, uz = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
            vx, vy, vz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            fh.write(struct.pack('<12fH', nx / ln, ny / ln, nz / ln,
                                 v1[0], v1[1], v1[2], v2[0], v2[1], v2[2],
                                 v3[0], v3[1], v3[2], 0))
    return len(tris)


VARIANTS = [
    # 名字            缝宽   长度   说明
    ('sleeve_A_flex',   2.0, 150.0, 'Rmin≈24mm  最软最好盘，贴身用'),
    ('sleeve_B_mid',    1.5, 150.0, 'Rmin≈32mm  折中'),
    ('sleeve_C_rigid',  1.0, 150.0, 'Rmin≈48mm  最硬，管子最不容易瘪'),
    ('sleeve_A_short',  2.0,  60.0, 'Rmin≈24mm  短段，先打印试手感'),
]

if __name__ == '__main__':
    print('%-18s %6s %7s %8s %9s %8s' % ('variant', 'slit', 'len', 'verts', 'tris', 'Rmin'))
    for name, slit, length, desc in VARIANTS:
        v, f = helix_sleeve(slit=slit, length=length)
        p = os.path.join(OUT, name + '.stl')
        n = write_binary_stl(p, v, f, name.encode())
        rmin = 8.0 * 12.0 / (2.0 * slit)
        print('%-18s %6.1f %7.0f %8d %9d %8.1f   %s' % (name, slit, length, len(v), n, rmin, desc))
        print('    ->', p)
