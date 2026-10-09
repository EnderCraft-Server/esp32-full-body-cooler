# -*- coding: utf-8 -*-
"""
转角导弯件 (bend guide) -- Blender headless 建模 + 导出 STL + 渲染

问题：6x8 硅胶管在转角处一折就瘪，瘪了以后泵有压力也撑不开 -> 憋压 -> 烧泵。
做法：转角**不靠软管自己弯**，而是走一个已经弯好的硬质导槽：

    ┌──────────────────────────────────────┐
    │  剖面（垂直于管路方向）              │
    │                                      │
    │        ┌──── 开口 6.8mm ────┐        │  <- 管子从上面按进去
    │      ╱                       ╲       │
    │     │   内孔 Ø8.6（管 Ø8）    │      │  <- 硬壳撑住管壁，压不瘪
    │     │                         │      │
    │      ╲_______________________╱       │
    │      外径 Ø12，包住 255°             │
    └──────────────────────────────────────┘

  管路走向（俯视，零件平放在打印床上）：
        进 ──┐                          ┌── 出
              │                          │
              └──────  R = 25mm  ───────┘     <- 圆弧是建模出来的，不是弯出来的

用法:  blender -b --factory-startup --python make_bends.py
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
#  参数
# ---------------------------------------------------------------------------
RI      = 4.3    # 内孔半径（Ø8.6 = 8mm 管 + 0.6 装配间隙）
RO      = 6.0    # 外半径（Ø12）
OPEN_W  = 6.8    # 顶部开口宽度，比管子细 -> 按进去能卡住
N_PROF  = 36     # 剖面圆弧分段数


def channel_profile(ri=RI, ro=RO, open_w=OPEN_W, n=N_PROF):
    """导槽剖面：一个开口 255 度的 C 形环。角度 psi 从正上方(+v)起算。"""
    psi0 = math.asin(min(0.995, (open_w * 0.5) / ri))
    span = 2.0 * math.pi - 2.0 * psi0
    outer, inner = [], []
    for k in range(n + 1):
        psi = psi0 + span * k / n
        outer.append((ro * math.sin(psi), ro * math.cos(psi)))
        inner.append((ri * math.sin(psi), ri * math.cos(psi)))
    # 闭合环：外弧 ->(径向)-> 内弧 ->(径向)-> 回到起点
    return outer + inner[::-1], n, math.degrees(psi0)


def bend_path(rc, sweep_deg, leg, step=3.0):
    """平面路径：直线段 + 圆弧 + 直线段。返回 [(位置, 径向外向量)]。

    圆弧中心在原点、位于 XY 平面，所以整个零件平放在打印床上即可打印，不需要支撑。
    """
    pts = []
    sweep = math.radians(sweep_deg)

    def frame(beta):
        p = Vector((rc * math.cos(beta), rc * math.sin(beta), 0.0))
        radial = Vector((math.cos(beta), math.sin(beta), 0.0))   # 剖面 +u 方向
        tangent = Vector((-math.sin(beta), math.cos(beta), 0.0))
        return p, radial, tangent

    # 进料直段
    if leg > 0:
        p0, rad, tan = frame(0.0)
        nseg = max(1, int(round(leg / step)))
        for k in range(nseg + 1):
            pts.append((p0 - tan * (leg * (1.0 - k / nseg)), rad))
    # 圆弧
    if sweep_deg > 0:
        nseg = max(2, int(round(sweep_deg / 3.0)))
        for k in range(nseg + 1):
            p, rad, _ = frame(sweep * k / nseg)
            pts.append((p, rad))
    # 出料直段
    if leg > 0:
        pe, rad, tan = frame(sweep)
        nseg = max(1, int(round(leg / step)))
        for k in range(1, nseg + 1):
            pts.append((pe + tan * (leg * k / nseg), rad))
    return pts


def build_bend(name, rc, sweep_deg, leg):
    prof, n, psi_deg = channel_profile()
    P = len(prof)
    path = bend_path(rc, sweep_deg, leg)
    up = Vector((0.0, 0.0, 1.0))

    bm = bmesh.new()
    rings = []
    for pos, radial in path:
        ring = [bm.verts.new(pos + radial * u + up * v) for (u, v) in prof]
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(P):
            j2 = (j + 1) % P
            try:
                bm.faces.new([a[j], a[j2], b[j2], b[j]])
            except ValueError:
                pass
    # 两端封盖：内弧/外弧之间铺四边形（环形扇区是凹多边形，不能整块 n-gon）
    # 索引：第 k 个外弧点 = k；第 k 个内弧点 = 2n+1-k
    for ring, flip in ((rings[0], False), (rings[-1], True)):
        for j in range(n):
            q = [ring[j], ring[j + 1], ring[2 * n - j], ring[2 * n + 1 - j]]
            try:
                bm.faces.new(q[::-1] if flip else q)
            except ValueError:
                pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob['psi'] = psi_deg
    return ob


def export_stl(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
    except TypeError:
        bpy.ops.wm.stl_export(filepath=path)
    return os.path.getsize(path)


# ---------------------------------------------------------------------------
VARIANTS = [
    # 文件名                    中心半径  转角    端部直段
    ('bend_180_R25',            25.0,    180.0,  15.0),
    ('bend_90_R25',             25.0,     90.0,  15.0),
    ('bend_45_R25',             25.0,     45.0,  15.0),
    ('bend_180_R18',            18.0,    180.0,  15.0),
    ('straight_80',             25.0,      0.0,  40.0),
]

if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print('%-18s %8s %10s %8s %9s %10s' % ('variant', 'sweep', 'R_center', 'verts', 'tris', 'STL bytes'))
    made = []
    for name, rc, sweep, leg in VARIANTS:
        ob = build_bend(name, rc, sweep, leg)
        me = ob.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        p = os.path.join(OUT, name + '.stl')
        sz = export_stl(ob, p)
        made.append(ob)
        print('%-18s %7.0fD %9.1fmm %8d %9d %10d   (开口 %.1fD)' % (
            name, sweep, rc, len(me.vertices), tris, sz, ob['psi']))
    print('OK', len(made), 'parts ->', OUT)
