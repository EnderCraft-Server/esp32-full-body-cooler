# -*- coding: utf-8 -*-
"""
对接护套 / 转角件 —— 可打印版截面（方底 + 顶面半圆槽）

上一版失败原因：平底只有 3.1mm 宽（半圆在底部相切），实机上粘不住床，打一半就飞。

这一版截面：
   ┌──────────────────────────┐   ← 顶面（平的），槽口在这一层敞开
   │  ╭────────────────────╮  │
   │ ╱                        ╲ │   ← 半圆槽 Ø8.6，从顶面往下挖 4.3
   │ ╰───────────────────────╯ │
   │                          │
   ╰──────────────────────────╯   ← 全宽 12mm 平底贴床（四角 R0.8 小圆角）

尺寸：全宽 12.0 / 全高 7.0 / 槽 R4.3（Ø8.6）/ 圆角 R0.8
      -> 侧壁 1.7mm，槽底剩 2.7mm 实心

打印性：
  * 底面 12 x L 全平 -> 贴床牢
  * 外壁垂直、顶面平的 -> 无悬垂
  * 槽是"往上张开的" -> 也没有悬垂
  整件零支撑。
"""
import bpy, bmesh, math, os

OUT = os.path.dirname(os.path.abspath(__file__))

W      = 12.0     # 全宽
H      = 7.0      # 全高
R_G    = 4.3      # 半圆槽半径（管 Ø8 + 0.6 间隙）
CR     = 0.8      # 四角圆角半径（不宜过大）
N_PROF = 40       # 槽圆弧分段
FLAT_Y = 0.0      # 底面在 v=0（旧脚本兼容用）


def half_profile(n=N_PROF):
    """方底 + 顶面半圆槽的闭合截面环（逆时针）。"""
    hw = W / 2.0

    def C(cx, cz, deg):
        a = math.radians(deg)
        return (cx + CR * math.cos(a), cz + CR * math.sin(a))

    pts = [(-(hw - CR), 0.0), (hw - CR, 0.0)]                    # 底边
    pts += [C(hw - CR, CR, -90.0 + 90.0 * k / 5) for k in range(1, 6)]      # 右下角
    pts.append((hw, H - CR))                                     # 右壁
    pts += [C(hw - CR, H - CR, 0.0 + 90.0 * k / 5) for k in range(1, 6)]    # 右上角
    pts.append((R_G, H))                                         # 顶面右段
    pts += [(R_G * math.cos(math.radians(-180.0 * k / n)),
             H + R_G * math.sin(math.radians(-180.0 * k / n))) for k in range(1, n + 1)]
    pts.append((-(hw - CR), H))                                  # 顶面左段
    pts += [C(-(hw - CR), H - CR, 90.0 + 90.0 * k / 5) for k in range(1, 6)]  # 左上角
    pts.append((-hw, CR))                                        # 左壁
    pts += [C(-(hw - CR), CR, 180.0 + 90.0 * k / 5) for k in range(1, 6)]     # 左下角
    # 左下圆弧的终点正好等于起点，去掉避免零长度边（会让三角剖分卡死）
    if len(pts) > 1 and abs(pts[-1][0] - pts[0][0]) < 1e-9 and abs(pts[-1][1] - pts[0][1]) < 1e-9:
        pts.pop()
    return pts


def ear_clip(pts):
    """简单多边形三角剖分（耳切法）—— 用于两端封盖。凹形截面不能用整块 n-gon。"""
    n = len(pts)
    idx = list(range(n))
    def area2(seq):
        return sum(pts[seq[i]][0] * pts[seq[(i + 1) % len(seq)]][1]
                   - pts[seq[(i + 1) % len(seq)]][0] * pts[seq[i]][1] for i in range(len(seq)))
    if area2(idx) < 0:
        idx.reverse()
    tris, guard = [], 0
    while len(idx) > 3 and guard < 20000:
        guard += 1
        found = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]) <= 1e-9:
                continue
            inside = False
            for m in idx:
                if m in (i0, i1, i2):
                    continue
                p = pts[m]
                d1 = (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0])
                d2 = (c[0]-b[0])*(p[1]-b[1]) - (c[1]-b[1])*(p[0]-b[0])
                d3 = (a[0]-c[0])*(p[1]-c[1]) - (a[1]-c[1])*(p[0]-c[0])
                if d1 >= 0 and d2 >= 0 and d3 >= 0:
                    inside = True
                    break
            if inside:
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            found = True
            break
        if not found:
            break
    if len(idx) == 3:
        tris.append((idx[0], idx[1], idx[2]))
    return tris


def build(name, length):
    prof = half_profile()
    P = len(prof)
    bm = bmesh.new()
    rings = []
    steps = max(2, int(round(length / 2.0)))
    for i in range(steps + 1):
        x = length * i / steps
        rings.append([bm.verts.new((x, u, v)) for (u, v) in prof])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(P):
            j2 = (j + 1) % P
            try: bm.faces.new([a[j], a[j2], b[j2], b[j]])
            except ValueError: pass
    # 两端封盖：耳切法三角化（截面是凹的，不能用整块 n-gon）
    tris = ear_clip(prof)
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        for (i0, i1, i2) in tris:
            try: bm.faces.new([ring[i0], ring[i1], ring[i2]][::-1] if flip else [ring[i0], ring[i1], ring[i2]])
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


VARIANTS = [('sleeve_half_150', 150.0), ('sleeve_half_075', 75.0), ('sleeve_half_050', 50.0)]

if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print('%-20s %8s %8s %10s' % ('variant', 'len', 'verts', 'STL'))
    for name, L in VARIANTS:
        ob = build(name, L)
        p = os.path.join(OUT, name + '.stl')
        sz = export(ob, p)
        bm = bmesh.new(); bm.from_mesh(ob.data)
        print('%-20s %7.0f %8d %10d   non_manifold=%d open=%d' % (
            name, L, len(ob.data.vertices), sz,
            len([e for e in bm.edges if not e.is_manifold]),
            len([e for e in bm.edges if len(e.link_faces) < 2])))
        bm.free()
    print('OK ->', OUT)
