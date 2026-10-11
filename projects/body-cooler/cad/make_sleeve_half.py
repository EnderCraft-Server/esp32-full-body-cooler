# -*- coding: utf-8 -*-
"""
防折护套 —— 可打印版（对开两半，躺平打）

为什么改：
  上一版是 Ø12 x 150mm 竖着打的螺旋管，接触面积只有 ~55mm²，高宽比 12.5:1，
  而且整件是一条连续螺旋带（弹性件），喷嘴一碰就倒 -> 炒面。

改成对开两半后：
  * 每半截面是"槽"形，凹面朝上 -> 弯底是凹面（材料在下），**没有任何悬垂**
  * 底面特意削平（±15° 弧段拉成弦），接触面积 = 3.1 x 150 = 465 mm²，是原来的 8 倍
  * 零件高度只有 5.8mm -> 不存在细高件倒塌问题
  * 打印时长也短得多

用法: blender -b --factory-startup --python make_sleeve_half.py
"""
import bpy, bmesh, math, os

OUT = os.path.dirname(os.path.abspath(__file__))

R_IN   = 4.3      # 内孔半径（管 Ø8 + 0.6 间隙）
R_OUT  = 6.0      # 外半径（Ø12）
FLAT_Y = -5.796   # 削平后的底面高度（对应 ±15° 弧段）
N_PROF = 48       # 半圆弧分段数


def outer_r(theta):
    """外轮廓半径：±15° 范围内拉成弦，得到 3.1mm 宽的平底"""
    s = abs(math.sin(theta))
    r_flat = abs(FLAT_Y)
    return r_flat / s if (s > r_flat / R_OUT) else R_OUT


def half_profile(n=N_PROF):
    """对开半壳的截面：内半圆（凹面朝上）+ 削平的外半圆。"""
    lo, hi = math.pi, 2.0 * math.pi          # 180° -> 360°（下半圈）
    inner, outer = [], []
    for k in range(n + 1):
        t = lo + (hi - lo) * k / n
        inner.append((R_IN * math.cos(t), R_IN * math.sin(t)))
        outer.append((outer_r(t) * math.cos(t), outer_r(t) * math.sin(t)))
    return inner + outer[::-1], n


def build(name, length):
    prof, n = half_profile()
    P = len(prof)
    bm = bmesh.new()
    rings = []
    # 沿 X 轴扫掠；截面在 YZ 平面（凹面朝上 = +Z），躺平打不需要支撑
    steps = max(2, int(length / 2.0))
    for i in range(steps + 1):
        x = length * i / steps
        ring = [bm.verts.new((x, u, v)) for (u, v) in prof]
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(P):
            j2 = (j + 1) % P
            try: bm.faces.new([a[j], a[j2], b[j2], b[j]])
            except ValueError: pass
    # 两端封盖：内弧点与对应的外弧点之间铺四边形（索引 j 与 2n+1-j 配对）
    for ring, flip in ((rings[0], False), (rings[-1], True)):
        for j in range(n):
            q = [ring[j], ring[j + 1], ring[2 * n - j], ring[2 * n + 1 - j]]
            try: bm.faces.new(q[::-1] if flip else q)
            except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def export(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    try: bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
    except TypeError: bpy.ops.wm.stl_export(filepath=path)
    return os.path.getsize(path)


VARIANTS = [('sleeve_half_150', 150.0), ('sleeve_half_075', 75.0), ('sleeve_half_050', 50.0)]

if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print('%-20s %8s %8s %8s %10s' % ('variant', 'len', 'verts', 'tris', 'STL bytes'))
    for name, L in VARIANTS:
        ob = build(name, L)
        me = ob.data
        p = os.path.join(OUT, name + '.stl')
        sz = export(ob, p)
        print('%-20s %7.0f %8d %8d %10d' % (name, L, len(me.vertices),
              sum(len(f.vertices) - 2 for f in me.polygons), sz))
    print('OK ->', OUT)
