# -*- coding: utf-8 -*-
"""渲染转角导弯件 + 网格自检。用法:
   blender -b --factory-startup --python render_bends.py
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_bends as MB

bpy.ops.wm.read_factory_settings(use_empty=True)

specs = [
    ('bend_180_R25', 25.0, 180.0, 15.0),
    ('bend_90_R25',  25.0,  90.0, 15.0),
    ('bend_45_R25',  25.0,  45.0, 15.0),
    ('bend_180_R18', 18.0, 180.0, 15.0),
    ('straight_80',  25.0,   0.0, 40.0),
]

objs = []
for name, rc, sweep, leg in specs:
    ob = MB.build_bend(name, rc, sweep, leg)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    print('CHECK %-16s verts=%-6d tris=%-6d non_manifold=%d open=%d' % (
        name, len(ob.data.vertices),
        sum(len(p.vertices) - 2 for p in ob.data.polygons),
        len([e for e in bm.edges if not e.is_manifold]),
        len([e for e in bm.edges if len(e.link_faces) < 2])))
    bm.free()
    objs.append(ob)


def bounds(obs):
    mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
    for o in obs:
        for c in o.bound_box:
            w = Vector(c) + o.location
            mn = Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
            mx = Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
    return mn, mx


# ---- 排成一行 ----
x = 0.0
for ob in objs:
    bb = [Vector(c) for c in ob.bound_box]
    mnx = min(v.x for v in bb); mxx = max(v.x for v in bb)
    ob.location.x = x - mnx
    x += (mxx - mnx) + 20.0
bpy.context.view_layer.update()
MIN, MAX = bounds(objs)
SIZE = MAX - MIN
CTR = (MIN + MAX) * 0.5
print('LAYOUT size = %.0f x %.0f x %.0f mm' % (SIZE.x, SIZE.y, SIZE.z))

# ---- 光 / 材质 ----
w = bpy.data.worlds.new('W'); bpy.context.scene.world = w
try: w.use_nodes = True
except Exception: pass
w.node_tree.nodes['Background'].inputs[0].default_value = (0.045, 0.055, 0.075, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
for ang, en in (((50, 0, 30), 4.2), ((68, 0, 200), 1.7), ((20, 0, 110), 1.3)):
    ld = bpy.data.lights.new('S', 'SUN'); ld.energy = en
    lo = bpy.data.objects.new('S', ld); bpy.context.collection.objects.link(lo)
    lo.rotation_euler = tuple(math.radians(a) for a in ang)
mat = bpy.data.materials.new('M'); mat.use_nodes = True
bs = mat.node_tree.nodes['Principled BSDF']
bs.inputs['Base Color'].default_value = (0.24, 0.56, 0.86, 1)
bs.inputs['Roughness'].default_value = 0.40

cam_d = bpy.data.cameras.new('C')
cam = bpy.data.objects.new('C', cam_d); bpy.context.collection.objects.link(cam)
sc = bpy.context.scene
sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 64; sc.cycles.use_denoising = True


def shoot(path, res, tgt, dirv, lens=50.0, fit=None, ortho=None):
    """按视野宽度解析计算相机距离，避免拍不全。"""
    sc.render.resolution_x, sc.render.resolution_y = res
    if ortho is not None:
        cam_d.type = 'ORTHO'; cam_d.ortho_scale = ortho
    else:
        cam_d.type = 'PERSP'; cam_d.lens = lens
    cam.location = tgt + dirv.normalized() * 100.0
    if ortho is None:
        # 需要覆盖的水平/垂直尺寸
        d = dirv.normalized() * -1.0
        dist = lens * (fit if fit else 100.0) / 36.0
        cam.location = tgt + dirv.normalized() * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print('RENDERED', path)


for ob in objs:
    ob.data.materials.append(mat)

# 全家福：水平方向要装下整个 x 跨度
w_need = SIZE.x + 40.0
shoot(os.path.join(HERE, 'preview_bends.png'), (1600, 640), CTR,
      Vector((0.10, -0.72, 0.69)), lens=48.0, fit=w_need)

# 端面剖面：正交投影，正对轴线
for ob in objs:
    bpy.data.objects.remove(ob, do_unlink=True)
st = MB.build_bend('profile_view', 25.0, 0.0, 40.0)
st.data.materials.append(mat)
bb = [Vector(c) for c in st.bound_box]
st.location = Vector((0, 0, 0)) - (bb[0] + bb[6]) * 0.5
bpy.context.view_layer.update()
shoot(os.path.join(HERE, 'preview_bends_profile.png'), (760, 760), Vector((0, 0, 0)),
      Vector((0.06, -1.0, 0.05)), ortho=19.0)
