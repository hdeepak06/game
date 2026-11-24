import unreal
import math
import os
import random
import struct
import zlib

# ---------------------------------------------------------------------------
# Task 04 full environment - original asset library only.
# Generates original procedural textures and low-poly static meshes with
# Unreal-native StaticMeshDescription; no downloaded or copyrighted content.
# ---------------------------------------------------------------------------

PROJECT = r"C:\UnrealProjects\Battleground"
INTERMEDIATE = os.path.join(PROJECT, "Saved", "Task04FullIntermediate")
OUT = os.path.join(PROJECT, "Saved", "Task04FullAudit", "content_build.txt")
ROOT = "/Game/Environment"
os.makedirs(INTERMEDIATE, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

lines = []
DEFAULT_SLOT_MATERIALS = {}


def w(s=""):
    lines.append(str(s))


def clamp(v, a, b):
    return max(a, min(b, v))


def lerp(a, b, t):
    return a + (b - a) * t


def hash2(ix, iy, seed):
    n = (int(ix) * 374761393 + int(iy) * 668265263 + int(seed) * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 4294967295.0


def tile_noise(u, v, period, seed):
    x = u * period
    y = v * period
    xi = int(math.floor(x))
    yi = int(math.floor(y))
    xf = x - xi
    yf = y - yi
    x0 = xi % period
    y0 = yi % period
    x1 = (x0 + 1) % period
    y1 = (y0 + 1) % period
    a = hash2(x0, y0, seed)
    b = hash2(x1, y0, seed)
    c = hash2(x0, y1, seed)
    d = hash2(x1, y1, seed)
    sx = xf * xf * (3.0 - 2.0 * xf)
    sy = yf * yf * (3.0 - 2.0 * yf)
    return lerp(lerp(a, b, sx), lerp(c, d, sx), sy)


def fbm(u, v, seed, periods=(4, 8, 16, 32), weights=(0.42, 0.28, 0.18, 0.12)):
    total = 0.0
    wsum = 0.0
    for p, wt in zip(periods, weights):
        total += tile_noise(u, v, p, seed + p) * wt
        wsum += wt
    return total / wsum


def png_chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def write_png(path, width, height, pixels):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        start = y * width * 4
        raw.extend(pixels[start:start + width * 4])
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def rgb_bytes(r, g, b):
    return (int(clamp(r, 0.0, 1.0) * 255.0 + 0.5),
            int(clamp(g, 0.0, 1.0) * 255.0 + 0.5),
            int(clamp(b, 0.0, 1.0) * 255.0 + 0.5), 255)


def generate_textures():
    specs = {
        "road": (256, 9),
        "sand": (256, 19),
        "grass": (128, 29),
        "leaf": (128, 37),
        "water": (256, 43),
        "concrete": (256, 53),
    }
    paths = {}
    for kind, (size, seed) in specs.items():
        px = bytearray(size * size * 4)
        for y in range(size):
            for x in range(size):
                u = x / float(size)
                v = y / float(size)
                n = fbm(u, v, seed)
                grain = hash2(x, y, seed + 101)
                if kind == "road":
                    r = 0.36 + 0.19 * n + 0.05 * grain
                    g = 0.25 + 0.14 * n + 0.04 * grain
                    b = 0.17 + 0.09 * n + 0.03 * grain
                elif kind == "sand":
                    r = 0.62 + 0.18 * n + 0.04 * grain
                    g = 0.49 + 0.15 * n + 0.04 * grain
                    b = 0.31 + 0.11 * n + 0.03 * grain
                elif kind == "grass":
                    r = 0.20 + 0.20 * n
                    g = 0.34 + 0.26 * n
                    b = 0.13 + 0.12 * n
                elif kind == "leaf":
                    r = 0.16 + 0.17 * n
                    g = 0.32 + 0.27 * n
                    b = 0.11 + 0.10 * n
                elif kind == "water":
                    wave = 0.5 + 0.5 * math.sin(2 * math.pi * (u * 5.0 + v * 2.0) + n * 3.0)
                    r = 0.10 + 0.08 * wave + 0.03 * n
                    g = 0.30 + 0.16 * wave + 0.04 * n
                    b = 0.36 + 0.18 * wave + 0.05 * n
                else:  # concrete
                    r = 0.40 + 0.13 * n + 0.05 * grain
                    g = 0.39 + 0.12 * n + 0.05 * grain
                    b = 0.36 + 0.11 * n + 0.04 * grain
                off = (y * size + x) * 4
                px[off:off + 4] = rgb_bytes(r, g, b)
        path = os.path.join(INTERMEDIATE, "T_Hampi%s_Albedo.png" % kind.capitalize())
        write_png(path, size, size, px)
        paths[kind] = path
    w("TEXTURES_GENERATED=%d" % len(paths))
    return paths


eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def ensure_dir(path):
    if not eal.does_directory_exist(path):
        eal.make_directory(path)


def load(path):
    return eal.load_asset(path)


def save(obj):
    if obj:
        eal.save_loaded_asset(obj)


def import_texture(png_path, name, srgb=True, compression=unreal.TextureCompressionSettings.TC_DEFAULT):
    dest = ROOT + "/Terrain"
    ensure_dir(dest)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", png_path)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    tools.import_asset_tasks([task])
    tex = load(dest + "/" + name)
    if tex:
        try:
            tex.set_editor_property("srgb", srgb)
            tex.set_editor_property("compression_settings", compression)
        except Exception:
            pass
        save(tex)
    w("TEXTURE_IMPORT %s=%s" % (name, bool(tex)))
    return tex


def connect_expr(src, src_outputs, dst, dst_inputs):
    for out in src_outputs:
        for inp in dst_inputs:
            try:
                if mel.connect_material_expressions(src, out, dst, inp):
                    return True
            except Exception:
                continue
    w("CONNECT_WARN %s -> %s" % (src.get_name(), dst.get_name()))
    return False


def create_textured_material(name, texture, tint, roughness=0.94, specular=0.12,
                             tiling=1.0, two_sided=False):
    dest = ROOT + "/Materials"
    ensure_dir(dest)
    path = dest + "/" + name
    mat = load(path)
    if not mat:
        mat = tools.create_asset(name, dest, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        w("MATERIAL_CREATE_FAILED=%s" % name)
        return None
    mel.delete_all_material_expressions(mat)
    try:
        mat.set_editor_property("two_sided", two_sided)
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception:
        pass
    for usage_prop in ["used_with_instanced_static_meshes", "used_with_instanced_static_mesh"]:
        try:
            mat.set_editor_property(usage_prop, True)
            w("MATERIAL_HISM_FLAG %s via %s" % (name, usage_prop))
            break
        except Exception:
            continue

    uv_scale = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -620, -260)
    uv_scale.set_editor_property("parameter_name", "UVScale")
    uv_scale.set_editor_property("default_value", float(tiling))
    uv_coord = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -620, -180)
    uv_mult = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -420, -180)
    connect_expr(uv_coord, ["", "Output"], uv_mult, ["A"])
    connect_expr(uv_scale, ["", "Output"], uv_mult, ["B"])
    ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -620, -40)
    ts.set_editor_property("parameter_name", "Albedo")
    ts.set_editor_property("texture", texture)
    connect_expr(uv_mult, ["", "Output"], ts, ["UVs", "Coordinates"])
    tint_expr = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -420, 100)
    tint_expr.set_editor_property("parameter_name", "Tint")
    tint_expr.set_editor_property("default_value", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
    base = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -160, -20)
    connect_expr(ts, ["", "RGB"], base, ["A"])
    connect_expr(tint_expr, ["", "RGB", "Output"], base, ["B"])
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -160, 180)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", float(roughness))
    spec = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -160, 280)
    spec.set_editor_property("parameter_name", "Specular")
    spec.set_editor_property("default_value", float(specular))
    for out in ["", "Output", "RGB"]:
        try:
            if mel.connect_material_property(base, out, unreal.MaterialProperty.MP_BASE_COLOR):
                break
        except Exception:
            continue
    for out in ["", "Output"]:
        try:
            if mel.connect_material_property(rough, out, unreal.MaterialProperty.MP_ROUGHNESS):
                break
        except Exception:
            continue
    for out in ["", "Output"]:
        try:
            if mel.connect_material_property(spec, out, unreal.MaterialProperty.MP_SPECULAR):
                break
        except Exception:
            continue
    mel.recompile_material(mat)
    save(mat)
    w("MATERIAL_READY %s" % path)
    return mat


def create_instance(name, parent, tint=None, scalar_values=None):
    dest = ROOT + "/Materials"
    path = dest + "/" + name
    mi = load(path)
    if not mi:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        try:
            factory.set_editor_property("initial_parent", parent)
        except Exception:
            pass
        mi = tools.create_asset(name, dest, unreal.MaterialInstanceConstant, factory)
    if not mi:
        w("MI_FAILED=%s" % name)
        return None
    try:
        mi.set_editor_property("parent", parent)
    except Exception:
        pass
    if tint:
        mel.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
    for k, v in (scalar_values or {}).items():
        mel.set_material_instance_scalar_parameter_value(mi, k, float(v))
    mel.update_material_instance(mi)
    save(mi)
    w("MI_READY %s" % path)
    return mi


def cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def planar_uv(p, axis):
    scale = 1.0 / 160.0
    if axis == 2:
        return p[0] * scale, p[1] * scale
    if axis == 0:
        return p[1] * scale, p[2] * scale
    return p[0] * scale, p[2] * scale


def add_box(verts, faces, mat, mn, mx):
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    base = len(verts)
    verts.extend([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ])
    for q in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
              (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        faces.append((mat, tuple(base + i for i in q)))


def add_prism(verts, faces, mat, top_quad, thickness):
    base = len(verts)
    for p in top_quad:
        verts.append(p)
    for p in top_quad:
        verts.append((p[0], p[1], p[2] - thickness))
    faces.append((mat, (base + 0, base + 1, base + 2, base + 3)))
    faces.append((mat, (base + 7, base + 6, base + 5, base + 4)))
    faces.append((mat, (base + 0, base + 4, base + 5, base + 1)))
    faces.append((mat, (base + 1, base + 5, base + 6, base + 2)))
    faces.append((mat, (base + 2, base + 6, base + 7, base + 3)))
    faces.append((mat, (base + 3, base + 7, base + 4, base + 0)))


def add_gable_roof(verts, faces, mat, w, d, z, roof_h, eave=45.0):
    hw = w / 2.0 + eave
    hd = d / 2.0 + eave
    base = len(verts)
    verts.extend([
        (-hw, -hd, z), (0.0, -hd, z + roof_h), (hw, -hd, z),
        (-hw, hd, z), (0.0, hd, z + roof_h), (hw, hd, z),
    ])
    faces.append((mat, (base + 0, base + 2, base + 1)))
    faces.append((mat, (base + 3, base + 4, base + 5)))
    faces.append((mat, (base + 0, base + 1, base + 4, base + 3)))
    faces.append((mat, (base + 2, base + 5, base + 4, base + 1)))
    faces.append((mat, (base + 0, base + 3, base + 5, base + 2)))


def add_cylinder(verts, faces, mat, cx, cy, z0, z1, radius, segs=8, taper=1.0):
    base = len(verts)
    for z, rad in [(z0, radius), (z1, radius * taper)]:
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            verts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad, z))
    top_center = len(verts)
    verts.append((cx, cy, z1))
    bot_center = len(verts)
    verts.append((cx, cy, z0))
    for i in range(segs):
        j = (i + 1) % segs
        b0, b1 = base + i, base + j
        t0, t1 = base + segs + i, base + segs + j
        faces.append((mat, (b0, b1, t1, t0)))
        faces.append((mat, (t0, t1, top_center)))
        faces.append((mat, (b0, bot_center, b1)))


def add_ellipsoid(verts, faces, mat, center, radii, segs=8, rings=5, seed=0):
    cx, cy, cz = center
    rx, ry, rz = radii
    base = len(verts)
    verts.append((cx, cy, cz + rz))
    for ring in range(1, rings):
        theta = math.pi * ring / float(rings)
        for seg in range(segs):
            phi = 2.0 * math.pi * seg / float(segs)
            jitter = 1.0 + 0.06 * math.sin(3.0 * phi + seed) * math.sin(2.0 * theta)
            verts.append((cx + math.cos(phi) * math.sin(theta) * rx * jitter,
                          cy + math.sin(phi) * math.sin(theta) * ry * jitter,
                          cz + math.cos(theta) * rz * jitter))
    bottom = len(verts)
    verts.append((cx, cy, cz - rz))
    for seg in range(segs):
        nxt = (seg + 1) % segs
        faces.append((mat, (base, base + 1 + seg, base + 1 + nxt)))
    for ring in range(rings - 2):
        top = base + 1 + ring * segs
        bot = base + 1 + (ring + 1) * segs
        for seg in range(segs):
            nxt = (seg + 1) % segs
            faces.append((mat, (top + seg, bot + seg, bot + nxt, top + nxt)))
    last = base + 1 + (rings - 2) * segs
    for seg in range(segs):
        nxt = (seg + 1) % segs
        faces.append((mat, (bottom, last + nxt, last + seg)))


def add_leaf_blade(verts, faces, mat, base, tip, width, drop=0.0):
    bx, by, bz = base
    tx, ty, tz = tip
    dx, dy = tx - bx, ty - by
    length = max(0.001, math.sqrt(dx * dx + dy * dy))
    px, py = -dy / length, dx / length
    hx, hy = px * width / 2.0, py * width / 2.0
    mx, my, mz = bx + dx * 0.5, by + dy * 0.5, bz + (tz - bz) * 0.55 + drop
    b = len(verts)
    verts.extend([
        (bx - hx, by - hy, bz), (bx + hx, by + hy, bz),
        (mx - hx * 0.9, my - hy * 0.9, mz), (mx + hx * 0.9, my + hy * 0.9, mz),
        (tx, ty, tz), (tx, ty, tz - 5.0),
    ])
    faces.append((mat, (b + 0, b + 2, b + 4)))
    faces.append((mat, (b + 1, b + 5, b + 3)))
    faces.append((mat, (b + 0, b + 4, b + 5, b + 1)))
    faces.append((mat, (b + 2, b + 3, b + 5, b + 4)))


def add_grass_blade(verts, faces, mat, x, y, z, height, width):
    b = len(verts)
    verts.extend([
        (x - width, y, z), (x + width, y, z),
        (x + width * 0.35, y, z + height), (x - width * 0.35, y, z + height),
        (x, y - width, z), (x, y + width, z),
        (x, y + width * 0.35, z + height * 0.9), (x, y - width * 0.35, z + height * 0.9),
    ])
    faces.append((mat, (b + 0, b + 1, b + 2, b + 3)))
    faces.append((mat, (b + 4, b + 5, b + 6, b + 7)))


def build_static_mesh(name, dest_path, verts, faces, materials):
    dest_path = ROOT + "/" + dest_path
    ensure_dir(dest_path)
    path = dest_path + "/" + name
    mesh = load(path)
    if not mesh:
        mesh = eal.duplicate_asset("/Engine/BasicShapes/Cube", path)
    if not mesh:
        w("MESH_CREATE_FAILED=%s" % name)
        return None
    try:
        mesh.set_editor_property("static_materials", [])
    except Exception:
        pass
    slots = {}
    for slot_name, mat in materials:
        resolved = mat if mat else DEFAULT_SLOT_MATERIALS.get(slot_name)
        slots[slot_name] = mesh.add_material(resolved) if resolved else unreal.Name(slot_name)
    desc = mesh.create_static_mesh_description(mesh)
    desc.empty()
    vids = []
    for p in verts:
        vid = desc.create_vertex()
        desc.set_vertex_position(vid, unreal.Vector(float(p[0]), float(p[1]), float(p[2])))
        vids.append(vid)
    groups = {}
    for slot_name in slots:
        pg = desc.create_polygon_group()
        desc.set_polygon_group_material_slot_name(pg, slots[slot_name])
        groups[slot_name] = pg
    for mat_name, face in faces:
        pg = groups.get(mat_name)
        if pg is None or len(face) < 3:
            continue
        p0, p1, p2 = verts[face[0]], verts[face[1]], verts[face[2]]
        n = cross3((p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]),
                   (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]))
        axis = max(range(3), key=lambda i: abs(n[i]))
        vis = []
        for idx in face:
            vi = desc.create_vertex_instance(vids[idx])
            u, v = planar_uv(verts[idx], axis)
            desc.set_vertex_instance_uv(vi, unreal.Vector2D(u, v), 0)
            vis.append(vi)
        for i in range(1, len(vis) - 1):
            desc.create_triangle(pg, [vis[0], vis[i], vis[i + 1]])
    tris = desc.get_triangle_count()
    if tris == 0:
        w("MESH_EMPTY=%s" % name)
        return None
    mesh.build_from_static_mesh_descriptions([desc], True, True)
    try:
        ns = mesh.get_editor_property("nanite_settings")
        ns.enabled = False
        mesh.set_editor_property("nanite_settings", ns)
    except Exception:
        pass
    save(mesh)
    w("MESH_READY %s verts=%d tris=%d slots=%d" % (name, desc.get_vertex_count(), tris, len(slots)))
    return mesh


def make_house(mesh_name, w, d, h, roof_h, wall_slot, roof_slot, stone_slot,
               windows=2, shop=False, flat=False):
    verts, faces = [], []
    add_box(verts, faces, stone_slot, (-w / 2, -d / 2, 0), (w / 2, d / 2, 28))
    if shop:
        add_box(verts, faces, wall_slot, (-w / 2, -d / 2, 28), (w / 2, d / 2 - 18, h))
        add_box(verts, faces, wall_slot, (-w / 2, d / 2 - 18, 28), (w / 2, d / 2, 150))
        add_box(verts, faces, "Wood", (-w / 2 + 25, d / 2 - 22, 150), (w / 2 - 25, d / 2 - 8, 285))
        add_box(verts, faces, roof_slot, (-w / 2 - 70, d / 2 - 10, h - 40), (w / 2 + 70, d / 2 + 150, h - 12))
    else:
        add_box(verts, faces, wall_slot, (-w / 2, -d / 2, 28), (w / 2, d / 2, h))
        add_box(verts, faces, "Wood", (-78, -d / 2 - 8, 28), (78, -d / 2 + 2, min(h - 30, 330)))
        for i in range(windows):
            x = -w / 2 + (i + 1) * w / (windows + 1)
            add_box(verts, faces, "Wood", (x - 55, -d / 2 - 9, 170), (x + 55, -d / 2 + 2, 270))
            add_box(verts, faces, stone_slot, (x - 62, -d / 2 - 11, 160), (x + 62, -d / 2 - 8, 280))
    if flat:
        add_box(verts, faces, roof_slot, (-w / 2 - 30, -d / 2 - 30, h), (w / 2 + 30, d / 2 + 30, h + 38))
        add_box(verts, faces, stone_slot, (-w / 2 - 38, -d / 2 - 38, h + 38), (w / 2 + 38, d / 2 + 38, h + 58))
    else:
        add_gable_roof(verts, faces, roof_slot, w, d, h, roof_h)
    mats = [("Stone", stone_slot), ("Wall", wall_slot), ("Roof", roof_slot), ("Wood", None)]
    return build_static_mesh(mesh_name, "Houses", verts, faces, mats)


def make_water_tank():
    verts, faces = [], []
    for x in [-140, 140]:
        for y in [-140, 140]:
            add_box(verts, faces, "Wood", (x - 16, y - 16, 0), (x + 16, y + 16, 430))
    add_cylinder(verts, faces, "Stone", 0, 0, 430, 700, 235, 12, 1.0)
    add_cylinder(verts, faces, "Roof", 0, 0, 700, 750, 250, 12, 0.55)
    return build_static_mesh("SM_KamalapurWaterTank", "Props", verts, faces,
                             [("Stone", None), ("Roof", None), ("Wood", None)])


def make_compound_wall():
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-320, -28, 0), (320, 28, 35))
    add_box(verts, faces, "Wall", (-300, -22, 35), (300, 22, 190))
    add_box(verts, faces, "Roof", (-320, -34, 190), (320, 34, 215))
    return build_static_mesh("SM_KamalapurCompoundWall", "Props", verts, faces,
                             [("Stone", None), ("Wall", None), ("Roof", None)])


def make_fence():
    verts, faces = [], []
    for x in [-260, 0, 260]:
        add_box(verts, faces, "Wood", (x - 11, -12, 0), (x + 11, 12, 165))
    add_box(verts, faces, "Wood", (-280, -12, 55), (280, 12, 78))
    add_box(verts, faces, "Wood", (-280, -12, 125), (280, 12, 148))
    return build_static_mesh("SM_VillageFence", "Props", verts, faces, [("Wood", None)])


def make_gate():
    verts, faces = [], []
    for x in [-210, 210]:
        add_box(verts, faces, "Wood", (x - 20, -22, 0), (x + 20, 22, 310))
    add_box(verts, faces, "Wood", (-240, -24, 285), (240, 24, 330))
    add_box(verts, faces, "Roof", (-255, -40, 330), (255, 40, 365))
    return build_static_mesh("SM_VillageGate", "Props", verts, faces, [("Wood", None), ("Roof", None)])


def make_ruin():
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-360, -260, 0), (360, 260, 55))
    for x in [-285, 285]:
        for y in [-190, 190]:
            add_cylinder(verts, faces, "Stone", x, y, 55, 360, 38, 8, 0.92)
    add_box(verts, faces, "Stone", (-350, -240, 360), (350, 240, 425))
    add_box(verts, faces, "Stone", (-360, -250, 425), (360, 250, 460))
    add_box(verts, faces, "Stone", (-330, -230, 55), (-250, 230, 270))
    return build_static_mesh("SM_HampiStoneRuin", "Temples", verts, faces, [("Stone", None)])


def make_stone_wall():
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-300, -35, 0), (300, 35, 45))
    add_box(verts, faces, "Stone", (-280, -28, 45), (280, 28, 175))
    add_box(verts, faces, "Stone", (-300, -40, 175), (300, 40, 205))
    return build_static_mesh("SM_HampiStoneWall", "Temples", verts, faces, [("Stone", None)])


def make_warehouse():
    verts, faces = [], []
    add_box(verts, faces, "Wall", (-620, -420, 0), (620, 420, 430))
    add_box(verts, faces, "Wood", (-160, -430, 0), (160, -420, 330))
    add_gable_roof(verts, faces, "Roof", 1240, 840, 430, 190, 30)
    return build_static_mesh("SM_HosapeteWarehouse", "Houses", verts, faces,
                             [("Wall", None), ("Roof", None), ("Wood", None)])


def make_barracks():
    verts, faces = [], []
    add_box(verts, faces, "Wall", (-520, -280, 0), (520, 280, 360))
    for x in [-340, -110, 120, 350]:
        add_box(verts, faces, "Wood", (x - 45, -290, 150), (x + 45, -280, 245))
    add_box(verts, faces, "Roof", (-560, -320, 360), (560, 320, 395))
    return build_static_mesh("SM_MilitaryBarracks", "Houses", verts, faces,
                             [("Wall", None), ("Roof", None), ("Wood", None)])


def make_watchtower():
    verts, faces = [], []
    for x in [-150, 150]:
        for y in [-150, 150]:
            add_box(verts, faces, "Wood", (x - 15, y - 15, 0), (x + 15, y + 15, 620))
    add_box(verts, faces, "Wood", (-230, -230, 620), (230, 230, 660))
    for x in [-230, 230]:
        add_box(verts, faces, "Wood", (x - 12, -230, 660), (x + 12, 230, 780))
    for y in [-230, 230]:
        add_box(verts, faces, "Wood", (-230, y - 12, 660), (230, y + 12, 780))
    add_box(verts, faces, "Roof", (-260, -260, 780), (260, 260, 825))
    return build_static_mesh("SM_MilitaryWatchtower", "Props", verts, faces,
                             [("Wood", None), ("Roof", None)])


def make_sandbag():
    verts, faces = [], []
    add_ellipsoid(verts, faces, "Stone", (0, 0, 28), (75, 42, 28), 8, 4, 3)
    return build_static_mesh("SM_Sandbag", "Props", verts, faces, [("Stone", None)])


def make_target():
    verts, faces = [], []
    for x in [-90, 90]:
        add_box(verts, faces, "Wood", (x - 10, -10, 0), (x + 10, 10, 300))
    add_box(verts, faces, "Wall", (-110, -12, 170), (110, 12, 280))
    return build_static_mesh("SM_TargetFrame", "Props", verts, faces, [("Wood", None), ("Wall", None)])


def make_small_stone():
    verts, faces = [], []
    add_ellipsoid(verts, faces, "Stone", (0, 0, 28), (70, 55, 28), 8, 4, 7)
    return build_static_mesh("SM_SmallGraniteStone", "Rocks", verts, faces, [("Stone", None)])


def make_slab():
    verts, faces = [], []
    add_ellipsoid(verts, faces, "Stone", (0, 0, 80), (420, 300, 80), 10, 4, 11)
    return build_static_mesh("SM_GraniteSlab", "Rocks", verts, faces, [("Stone", None)])


def make_palm(kind):
    verts, faces = [], []
    height = 760 if kind == "coconut" else 620
    segs = 7
    for i in range(segs):
        z0 = i * height / segs
        z1 = (i + 1) * height / segs
        r0 = 30 - i * 2.3
        r1 = 30 - (i + 1) * 2.3
        add_cylinder(verts, faces, "Bark", 0, 0, z0, z1, r0, 8, r1 / r0)
    count = 9 if kind == "coconut" else 7
    for i in range(count):
        a = 2.0 * math.pi * i / count
        length = 300 if kind == "coconut" else 230
        tip = (math.cos(a) * length, math.sin(a) * length, height - 40 - (50 if kind == "date" else 0))
        add_leaf_blade(verts, faces, "Leaf", (0, 0, height), tip, 58 if kind == "coconut" else 34, -35)
    mats = [("Bark", None), ("Leaf", None)]
    return build_static_mesh("SM_CoconutPalm" if kind == "coconut" else "SM_DatePalm", "Vegetation", verts, faces, mats)


def make_tree(name, trunk_h, trunk_r, canopy_centers, canopy_radii, seed, extra_roots=False):
    verts, faces = [], []
    add_cylinder(verts, faces, "Bark", 0, 0, 0, trunk_h, trunk_r, 8, 0.72)
    for i, (c, r) in enumerate(zip(canopy_centers, canopy_radii)):
        add_ellipsoid(verts, faces, "Leaf", c, r, 8, 5, seed + i * 7)
    if extra_roots:
        for i in range(6):
            a = 2.0 * math.pi * i / 6
            x, y = math.cos(a) * 75, math.sin(a) * 75
            add_cylinder(verts, faces, "Bark", x, y, 0, trunk_h * 0.62, 8, 6, 0.6)
    return build_static_mesh(name, "Vegetation", verts, faces, [("Bark", None), ("Leaf", None)])


def make_dry_tree():
    verts, faces = [], []
    add_cylinder(verts, faces, "Bark", 0, 0, 0, 430, 32, 7, 0.55)
    for i in range(5):
        a = 2.0 * math.pi * i / 5
        add_box(verts, faces, "Bark",
                (0, 0, 300 + i * 12),
                (math.cos(a) * 210, math.sin(a) * 210, 330 + i * 18))
    return build_static_mesh("SM_DryRegionTree", "Vegetation", verts, faces, [("Bark", None)])


def make_bush(name, leaf_slot="Leaf", seed=0):
    verts, faces = [], []
    rnd = random.Random(seed)
    for i in range(5):
        cx = rnd.uniform(-80, 80)
        cy = rnd.uniform(-80, 80)
        cz = rnd.uniform(45, 85)
        add_ellipsoid(verts, faces, leaf_slot, (cx, cy, cz), (rnd.uniform(55, 95), rnd.uniform(50, 85), rnd.uniform(45, 75)), 7, 4, seed + i)
    return build_static_mesh(name, "Vegetation", verts, faces, [(leaf_slot, None)])


def make_grass(name, leaf_slot="Leaf"):
    verts, faces = [], []
    rnd = random.Random(41 if leaf_slot == "DryLeaf" else 11)
    for i in range(7):
        x = rnd.uniform(-70, 70)
        y = rnd.uniform(-70, 70)
        add_grass_blade(verts, faces, leaf_slot, x, y, 0, rnd.uniform(55, 120), rnd.uniform(7, 13))
    return build_static_mesh(name, "Vegetation", verts, faces, [(leaf_slot, None)])


def make_reeds():
    verts, faces = [], []
    rnd = random.Random(77)
    for i in range(9):
        x = rnd.uniform(-90, 90)
        y = rnd.uniform(-90, 90)
        add_grass_blade(verts, faces, "Leaf", x, y, 0, rnd.uniform(110, 210), rnd.uniform(5, 10))
    return build_static_mesh("SM_RiversideReeds", "Vegetation", verts, faces, [("Leaf", None)])


def main():
    textures = generate_textures()
    tex = {
        "road": import_texture(textures["road"], "T_HampiRoad_Albedo"),
        "sand": import_texture(textures["sand"], "T_HampiSand_Albedo"),
        "grass": import_texture(textures["grass"], "T_HampiGrass_Albedo"),
        "leaf": import_texture(textures["leaf"], "T_HampiLeaf_Albedo"),
        "water": import_texture(textures["water"], "T_HampiWater_Albedo"),
        "concrete": import_texture(textures["concrete"], "T_HampiConcrete_Albedo"),
    }
    existing = {
        "granite": load(ROOT + "/Terrain/T_HampiGranite_Albedo"),
        "plaster": load(ROOT + "/Terrain/T_HampiMudPlaster_Albedo"),
        "roof": load(ROOT + "/Terrain/T_HampiClayRoof_Albedo"),
        "wood": load(ROOT + "/Terrain/T_HampiWood_Albedo"),
    }
    mats = {}
    mats["road"] = create_textured_material("M_HampiDirtRoad_Mobile", tex["road"], (1.0, 0.94, 0.86), 0.97, 0.08, 0.008)
    mats["gravel"] = create_textured_material("M_HampiGravelRoad_Mobile", existing["granite"], (1.0, 0.93, 0.82), 0.98, 0.08, 0.006)
    mats["sand"] = create_textured_material("M_HampiSand_Mobile", tex["sand"], (1.0, 0.98, 0.92), 0.98, 0.06, 0.006)
    mats["water"] = create_textured_material("M_HampiWater_Mobile", tex["water"], (0.68, 0.95, 1.0), 0.32, 0.55, 0.0035)
    mats["grass"] = create_textured_material("M_HampiGrass_Mobile", tex["grass"], (0.75, 1.0, 0.62), 0.96, 0.05, 0.01, True)
    mats["drygrass"] = create_textured_material("M_HampiDryGrass_Mobile", tex["grass"], (1.0, 0.82, 0.48), 0.97, 0.05, 0.01, True)
    mats["leaf"] = create_textured_material("M_HampiLeaf_Mobile", tex["leaf"], (0.78, 1.0, 0.68), 0.92, 0.06, 0.008, True)
    mats["leafdry"] = create_textured_material("M_HampiLeafDry_Mobile", tex["leaf"], (1.0, 0.75, 0.42), 0.95, 0.05, 0.008, True)
    mats["bark"] = create_textured_material("M_HampiBark_Mobile", existing["wood"], (0.78, 0.63, 0.46), 0.98, 0.04, 0.012)
    mats["stone"] = create_textured_material("M_HampiStoneWall_Mobile", existing["granite"], (1.0, 0.92, 0.80), 0.97, 0.07, 0.008)
    mats["concrete"] = create_textured_material("M_HampiConcrete_Mobile", tex["concrete"], (0.93, 0.92, 0.88), 0.95, 0.08, 0.008)
    mats["metal"] = create_textured_material("M_HampiMetal_Mobile", tex["concrete"], (0.48, 0.55, 0.58), 0.62, 0.28, 0.008)
    mats["plaster"] = create_textured_material("M_HampiPlasterWarm_Mobile", existing["plaster"], (1.0, 0.94, 0.84), 0.96, 0.06, 0.008)
    mats["roof"] = create_textured_material("M_HampiRoofWarm_Mobile", existing["roof"], (1.0, 0.90, 0.76), 0.93, 0.08, 0.009)
    mats["wood"] = create_textured_material("M_HampiWood_Mobile", existing["wood"], (0.62, 0.44, 0.30), 0.94, 0.07, 0.01)
    DEFAULT_SLOT_MATERIALS.update({
        "Stone": mats["stone"],
        "Wall": mats["plaster"],
        "Roof": mats["roof"],
        "Wood": mats["wood"],
        "Bark": mats["bark"],
        "Leaf": mats["leaf"],
        "DryLeaf": mats["drygrass"],
    })
    make_house("SM_KamalapurHouse_A", 920, 760, 430, 210, mats["plaster"], mats["roof"], mats["stone"], 2)
    make_house("SM_KamalapurHouse_B", 760, 900, 390, 180, mats["plaster"], mats["roof"], mats["stone"], 2)
    make_house("SM_KamalapurHouse_C", 1120, 680, 360, 150, mats["plaster"], mats["roof"], mats["stone"], 3, flat=True)
    make_house("SM_KamalapurShop_A", 860, 620, 350, 160, mats["plaster"], mats["roof"], mats["stone"], 0, shop=True)
    make_house("SM_HosapeteHouse_A", 980, 820, 470, 190, mats["concrete"], mats["roof"], mats["stone"], 2)
    make_house("SM_HampiStoneHouse_A", 820, 740, 400, 0, mats["stone"], mats["stone"], mats["stone"], 2, flat=True)
    make_warehouse()
    make_barracks()

    make_water_tank()
    make_compound_wall()
    make_fence()
    make_gate()
    make_ruin()
    make_stone_wall()
    make_watchtower()
    make_sandbag()
    make_target()
    make_small_stone()
    make_slab()

    make_palm("coconut")
    make_palm("date")
    make_tree("SM_NeemTree", 470, 45,
              [(0, 0, 620), (-150, 40, 560), (140, -60, 570), (20, 150, 520)],
              [(230, 210, 135), (180, 165, 110), (175, 160, 105), (155, 150, 95)], 3)
    make_tree("SM_BanyanTree", 530, 80,
              [(0, 0, 700), (-220, 60, 620), (210, -80, 630), (60, 210, 600)],
              [(310, 280, 150), (220, 200, 115), (220, 205, 115), (195, 190, 105)], 9, True)
    make_tree("SM_TamarindTree", 430, 55,
              [(0, 0, 580), (-170, -70, 520), (170, 80, 530)],
              [(275, 250, 135), (190, 175, 105), (190, 180, 105)], 15)
    make_tree("SM_AcaciaTree", 390, 42,
              [(0, 0, 540), (-190, 0, 505), (190, 0, 505)],
              [(300, 230, 75), (190, 150, 60), (190, 150, 60)], 21)
    make_dry_tree()
    make_bush("SM_GreenBush", "Leaf", 31)
    make_bush("SM_DryShrub", "DryLeaf", 41)
    make_grass("SM_GrassTuft", "Leaf")
    make_grass("SM_DryGrassTuft", "DryLeaf")
    make_reeds()

    w("CONTENT_BUILD_DONE")


try:
    main()
except Exception as e:
    w("CONTENT_BUILD_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK04_CONTENT_BUILD_WRITTEN")
