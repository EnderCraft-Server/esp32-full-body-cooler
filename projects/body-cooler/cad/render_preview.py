# -*- coding: utf-8 -*-
"""Blender headless：导入护套 STL，检查网格，渲染预览图。
用法: blender -b -P render_preview.py -- <src.stl> <out.png> <view> [len_scale]
view: iso | axial
"""
import bpy, sys, os, math, bmesh
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, DST, VIEW = argv[0], argv[1], argv[2]

bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.wm.stl_import(filepath=SRC)
except Exception:
    bpy.ops.import_mesh.stl(filepath=SRC)

ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
me = ob.data
bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
size = mx - mn
print('SIZE  X=%.2f  Y=%.2f  Z=%.2f' % (size.x, size.y, size.z))
bm = bmesh.new(); bm.from_mesh(me)
print('NON_MANIFOLD %d  OPEN %d' % (
    len([e for e in bm.edges if not e.is_manifold]),
    len([e for e in bm.edges if len(e.link_faces) < 2])))
bm.free()

w = bpy.data.worlds.new('W'); bpy.context.scene.world = w
try: w.use_nodes = True
except Exception: pass
w.node_tree.nodes['Background'].inputs[0].default_value = (0.04, 0.05, 0.07, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.9

for ang, en in (((55, 0, 35), 4.0), ((70, 0, 215), 1.6), ((25, 0, 120), 1.2)):
    ld = bpy.data.lights.new('S', 'SUN'); ld.energy = en
    lo = bpy.data.objects.new('S', ld); bpy.context.collection.objects.link(lo)
    lo.rotation_euler = tuple(math.radians(a) for a in ang)

mat = bpy.data.materials.new('M'); mat.use_nodes = True
b = mat.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.24, 0.56, 0.86, 1)
b.inputs['Roughness'].default_value = 0.42
ob.data.materials.append(mat)

ctr = (mn + mx) * 0.5
cam_d = bpy.data.cameras.new('C'); cam_d.lens = 70
cam = bpy.data.objects.new('C', cam_d); bpy.context.collection.objects.link(cam)
if VIEW == 'axial':
    cam.location = ctr + Vector((0, 0, size.length * 1.9))
    cam.rotation_euler = (0, 0, 0)
    cam_d.lens = 85
else:
    d = size.length * 2.1
    cam.location = ctr + Vector((d * 0.60, -d * 0.68, d * 0.42))
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.resolution_x = 900; sc.render.resolution_y = 700
sc.render.filepath = DST
bpy.ops.render.render(write_still=True)
print('RENDERED', DST)
