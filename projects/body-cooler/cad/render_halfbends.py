# -*- coding: utf-8 -*-
"""转角件（对开半壳）预览：全部平放，凹面朝上。"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_sleeve_half as MH
import make_half_bends as MB

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

me = bpy.data.meshes.new('bed'); bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, verts=bm.verts, vec=(320, 150, 2.0))
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, -1.0))
bm.to_mesh(me); bm.free()
bed = bpy.data.objects.new('bed', me); bpy.context.collection.objects.link(bed)

specs = [('halfbend_180_R25', 25.0, 180.0, 12.0, (-78, 0)),
         ('halfbend_90_R25',  25.0,  90.0, 12.0, (0, 32)),
         ('halfbend_45_R25',  25.0,  45.0, 12.0, (46, 26)),
         ('halfbend_180_R18', 18.0, 180.0, 12.0, (110, -10))]
for name, rc, sw, leg, (px, py) in specs:
    ob = MB.build(name, rc, sw, leg)
    ob.location = (px, py, -MH.FLAT_Y)     # 平底贴床
ob = MH.build('straight', 75.0)
ob.location = (10, -46, -MH.FLAT_Y)

def mat(n, rgb, r=0.45):
    m = bpy.data.materials.new(n); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = r
    return m
mb_, mp = mat('bed', (0.10, 0.11, 0.14), 0.85), mat('p', (0.24, 0.56, 0.86), 0.40)
for o in sc.objects:
    if o.type != 'MESH': continue
    o.data.materials.clear()
    o.data.materials.append(mb_ if o.name == 'bed' else mp)

w = bpy.data.worlds.new('W'); sc.world = w
try: w.use_nodes = True
except Exception: pass
w.node_tree.nodes['Background'].inputs[0].default_value = (0.045, 0.055, 0.075, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
for ang, en in (((52, 0, 28), 4.0), ((70, 0, 205), 1.8), ((22, 0, 115), 1.2)):
    ld = bpy.data.lights.new('S', 'SUN'); ld.energy = en
    lo = bpy.data.objects.new('S', ld); bpy.context.collection.objects.link(lo)
    lo.rotation_euler = tuple(math.radians(a) for a in ang)

cd = bpy.data.cameras.new('C'); cd.lens = 45
cam = bpy.data.objects.new('C', cd); bpy.context.collection.objects.link(cam)
tgt = Vector((10, 0, 3))
cam.location = tgt + Vector((0, -320, 210))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.resolution_x = 1500; sc.render.resolution_y = 700
sc.render.filepath = os.path.join(HERE, 'preview_halfbends.png')
bpy.ops.render.render(write_still=True)
print('RENDERED', sc.render.filepath)
