# -*- coding: utf-8 -*-
"""
转角件 —— 可打印版（对开两半，躺着打）

截面和 sleeve_half_* 完全一样（半圆槽 + 削平平底），只是把路径从直线换成圆弧。
所以对开的另一半就是**同一个件翻过来**，打 2 片即可。

所有件平放打印：圆弧在 XY 平面、凹面朝上 -> 底面贴床、零悬垂、不需要支撑。

用法: blender -b --factory-startup --python make_half_bends.py
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_sleeve_half as MH

R_IN, R_OUT, FLAT_Y, N_PROF = MH.R_IN, MH.R_OUT, MH.FLAT_Y, MH.N_PROF


def profile():
    inner, outer = [], []
    lo, hi = math.pi, 2.0 * math.pi
    for k in range(N_PROF + 1):
        t = lo + (hi - lo) * k / N_PROF
        inner.append((R_IN * math.cos(t), R_IN * math.sin(t)))
        outer.append((MH.outer_r(t) * math.cos(t), MH.outer_r(t) * math.sin(t)))
    return inner + outer[::-1]


def path(rc, sweep_deg, leg):
    """平面路径：进料直段 + 圆弧 + 出料直段。返回 [(位置, 径向外向量)]"""
    pts = []
    sw = math.radians(sweep_deg)

    def frame(b):
        return (Vector((rc * math.cos(b), rc * math.sin(b), 0.0)),
                Vector((math.cos(b), math.sin(b), 0.0)),
                Vector((-math.sin(b), math.cos(b), 0.0)))

    if leg > 0:
        p0, rad, tan = frame(0.0)
        n = max(1, int(round(leg / 3.0)))
        for k in range(n + 1):
            pts.append((p0 - tan * (leg * (1.0 - k / n)), rad))
    if sweep_deg > 0:
        n = max(2, int(round(sweep_deg / 3.0)))
        for k in range(n + 1):
            p, rad, _ = frame(sw * k / n)
            pts.append((p, rad))
    if leg > 0:
        pe, rad, tan = frame(sw)
        n = max(1, int(round(leg / 3.0)))
        for k in range(1, n + 1):
            pts.append((pe + tan * (leg * k / n), rad))
    return pts


def build(name, rc, sweep_deg, leg):
    prof = profile()
    P = len(prof)
    up = Vector((0.0, 0.0, 1.0))
    bm = bmesh.new()
    rings = []
    for pos, radial in path(rc, sweep_deg, leg):
        rings.append([bm.verts.new(pos + radial * u + up * v) for (u, v) in prof])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(P):
            j2 = (j + 1) % P
            try: bm.faces.new([a[j], a[j2], b[j2], b[j]])
            except ValueError: pass
    n = N_PROF
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


def export(ob, p):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    try: bpy.ops.wm.stl_export(filepath=p, export_selected_objects=True)
    except TypeError: bpy.ops.wm.stl_export(filepath=p)
    return os.path.getsize(p)


VARIANTS = [
    ('halfbend_180_R25', 25.0, 180.0, 12.0),
    ('halfbend_90_R25',  25.0,  90.0, 12.0),
    ('halfbend_45_R25',  25.0,  45.0, 12.0),
    ('halfbend_180_R18', 18.0, 180.0, 12.0),
]

if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print('%-20s %7s %6s %8s %8s %10s' % ('variant', 'R', 'sweep', 'verts', 'tris', 'STL'))
    made = []
    for name, rc, sw, leg in VARIANTS:
        ob = build(name, rc, sw, leg)
        p = os.path.join(HERE, name + '.stl')
        sz = export(ob, p)
        bb = [Vector(c) for c in ob.bound_box]
        size = (max(v.x for v in bb) - min(v.x for v in bb),
                max(v.y for v in bb) - min(v.y for v in bb),
                max(v.z for v in bb) - min(v.z for v in bb))
        print('%-20s %6.0f %5.0fD %8d %8d %10d   外形 %.0f x %.0f x %.1f mm' % (
            name, rc, sw, len(ob.data.vertices),
            sum(len(f.vertices) - 2 for f in ob.data.polygons), sz, *size))
        made.append(ob)
    # 网格自检
    for ob in made:
        bm = bmesh.new(); bm.from_mesh(ob.data)
        print('CHECK %-20s non_manifold=%d open=%d' % (
            ob.name, len([e for e in bm.edges if not e.is_manifold]),
            len([e for e in bm.edges if len(e.link_faces) < 2])))
        bm.free()
    print('OK ->', HERE)
