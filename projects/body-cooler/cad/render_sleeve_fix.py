# -*- coding: utf-8 -*-
"""对比渲染：旧的竖打护套 vs 新的躺打半壳。带打印床平面，直观看接触面积。"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_sleeve_half as MH

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
BED = 2.0

# ---- 打印床 ----
me = bpy.data.meshes.new('bed')
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bmesh.ops.scale(bm, verts=bm.verts, vec=(300, 160, BED))
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, -BED / 2))
bm.to_mesh(me); bm.free()
bed = bpy.data.objects.new('bed', me); bpy.context.collection.objects.link(bed)

# ---- 旧的竖打护套（导入 STL，竖着放）----
old = os.path.join(HERE, 'sleeve_A_short.stl')
if os.path.exists(old):
    bpy.ops.wm.stl_import(filepath=old)
    o = [x for x in sc.objects if x.type == 'MESH' and x.name != 'bed'][-1]
    o.location = (-70, 0, 0)

# ---- 新的躺打半壳 x2 ----
for i, x in enumerate((30, 130)):          # 75mm 长，两件错开不能叠
    ob = MH.build('half%d' % i, 75.0)
    ob.location = (x, 0, -MH.FLAT_Y)          # 平底贴床
    ob.rotation_euler = (0, 0, 0)

# ---- 材质 ----
def mat(name, rgb, rough=0.45):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    return m
mb = mat('bed', (0.10, 0.11, 0.14), 0.85)
mp = mat('part', (0.24, 0.56, 0.86), 0.40)
mo = mat('old', (0.85, 0.36, 0.30), 0.45)
for o in sc.objects:
    if o.type != 'MESH': continue
    d = o.data
    d.materials.clear()
    d.materials.append(mb if o.name == 'bed' else (mp if o.name.startswith('half') else mo))

# ---- 光 ----
w = bpy.data.worlds.new('W'); sc.world = w
try: w.use_nodes = True
except Exception: pass
w.node_tree.nodes['Background'].inputs[0].default_value = (0.045, 0.055, 0.075, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
for ang, en in (((52, 0, 28), 4.0), ((70, 0, 205), 1.8), ((22, 0, 115), 1.2)):
    ld = bpy.data.lights.new('S', 'SUN'); ld.energy = en
    lo = bpy.data.objects.new('S', ld); bpy.context.collection.objects.link(lo)
    lo.rotation_euler = tuple(math.radians(a) for a in ang)

cam_d = bpy.data.cameras.new('C'); cam_d.lens = 42
cam = bpy.data.objects.new('C', cam_d); bpy.context.collection.objects.link(cam)
tgt = Vector((45, 0, 4))
cam.location = tgt + Vector((0, -330, 230))    # 抬高机位，能看见槽口朝上
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = 64; sc.cycles.use_denoising = True
sc.render.resolution_x = 1400; sc.render.resolution_y = 620
sc.render.filepath = os.path.join(HERE, 'preview_sleeve_fix.png')
bpy.ops.render.render(write_still=True)
print('RENDERED', sc.render.filepath)

# ---- 网格自检 ----
for nm in ('half0', 'half1'):
    o = sc.objects[nm]
    bm2 = bmesh.new(); bm2.from_mesh(o.data)
    print('CHECK %-8s verts=%-6d non_manifold=%d open=%d' % (
        nm, len(o.data.vertices),
        len([e for e in bm2.edges if not e.is_manifold]),
        len([e for e in bm2.edges if len(e.link_faces) < 2])))
    bm2.free()
