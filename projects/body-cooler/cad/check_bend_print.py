# -*- coding: utf-8 -*-
"""诊断：旧的 bend_*.stl 躺平打印时底部是什么样。"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_half_bends as MB

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

me = bpy.data.meshes.new('bed'); bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, verts=bm.verts, vec=(240, 120, 2.0))
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, -1.0))
bm.to_mesh(me); bm.free()
bed = bpy.data.objects.new('bed', me); bpy.context.collection.objects.link(bed)

# 旧的：导入 STL，保持原姿态（Z 最低点贴床）
for f, dx in (('bend_180_R25.stl', -60),):
    p = os.path.join(HERE, f)
    bpy.ops.wm.stl_import(filepath=p)
    o = [x for x in sc.objects if x.type == 'MESH' and not x.name.startswith('bed')][-1]
    zmin = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    o.location.z -= zmin
    o.location.x = dx
# 新的：对开半壳
nb = MB.build('new', 25.0, 180.0, 12.0)
nb.location = (60, 0, -(-5.796))

def mat(n, rgb, r=0.45):
    m = bpy.data.materials.new(n); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = r
    return m
mb_, mo, mn = mat('bed', (0.10, 0.11, 0.14), 0.85), mat('old', (0.86, 0.33, 0.28), 0.45), mat('new', (0.24, 0.56, 0.86), 0.40)
for o in sc.objects:
    if o.type != 'MESH': continue
    o.data.materials.clear()
    o.data.materials.append(mb_ if o.name == 'bed' else (mn if o.name == 'new' else mo))

w = bpy.data.worlds.new('W'); sc.world = w
try: w.use_nodes = True
except Exception: pass
w.node_tree.nodes['Background'].inputs[0].default_value = (0.05, 0.06, 0.08, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
for ang, en in (((60, 0, 25), 3.6), ((75, 0, 200), 1.9), ((15, 0, 120), 1.4)):
    ld = bpy.data.lights.new('S', 'SUN'); ld.energy = en
    lo = bpy.data.objects.new('S', ld); bpy.context.collection.objects.link(lo)
    lo.rotation_euler = tuple(math.radians(a) for a in ang)

cd = bpy.data.cameras.new('C'); cd.lens = 55
cam = bpy.data.objects.new('C', cd); bpy.context.collection.objects.link(cam)
tgt = Vector((0, 0, 4))
cam.location = tgt + Vector((10, -175, 26))     # 低机位，专门看底面
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 72; sc.cycles.use_denoising = True
sc.render.resolution_x = 1500; sc.render.resolution_y = 620
sc.render.filepath = os.path.join(HERE, 'preview_bend_problem.png')
bpy.ops.render.render(write_still=True)
print('RENDERED', sc.render.filepath)

# 数值证据：旧件每一层的截面宽度
old = [x for x in sc.objects if x.type == 'MESH' and x.name not in ('bed', 'new')][0]
verts = [old.matrix_world @ v.co for v in old.data.vertices]
z0 = min(v.z for v in verts)
print('--- 旧 bend_180_R25 逐层宽度 ---')
for k in range(6):
    h = z0 + k * 0.2
    xs = [v.x + 0 for v in verts if abs(v.z - h) < 0.11 or True]
    band = [v for v in verts if h <= v.z < h + 0.2]
    if band:
        print('  z=%.1f~%.1f mm  该层顶点 x 跨度 %.2f mm' % (h - z0, h - z0 + 0.2,
              max(v.x for v in band) - min(v.x for v in band)))
