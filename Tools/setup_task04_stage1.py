import unreal
import math
import os
import random
import struct
import traceback
import zlib

# ---------------------------------------------------------------------------
# Hampi Battleground - Task 04, Stage 1
# Soil material + original granite boulders + one small traditional house.
# No copyrighted reference images are imported or used as textures.
# ---------------------------------------------------------------------------

PROJECT = r"C:\UnrealProjects\Battleground"
INTERMEDIATE = os.path.join(PROJECT, "Saved", "Task04Stage1Intermediate")
OUT = r"C:\Users\HP\AppData\Local\Temp\opencode\task04_stage1_output.txt"
MAP_PATH = "/Game/Maps/LV_HampiBattleground"
ROOT = "/Game/Environment"

lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def flush():
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def clamp(v, a, b):
    return max(a, min(b, v))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_rgb(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def smoothstep(e0, e1, x):
    if e1 == e0:
        return 0.0
    t = clamp((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


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


def fbm(u, v, seed, periods=(4, 8, 16, 32), weights=(0.45, 0.28, 0.17, 0.10)):
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


def color_to_bytes(c):
    return tuple(int(clamp(v, 0.0, 1.0) * 255.0 + 0.5) for v in c) + (255,)


def generate_textures():
    os.makedirs(INTERMEDIATE, exist_ok=True)
    paths = {}

    # 256x256 tileable Hampi soil: red-brown earth, sandy patches, granite flecks.
    size = 256
    px = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            u = x / float(size)
            v = y / float(size)
            n_broad = fbm(u, v, 11, (3, 6, 12), (0.50, 0.32, 0.18))
            n_patch = fbm(u, v, 23, (4, 9, 18, 36), (0.42, 0.28, 0.20, 0.10))
            grain = hash2(x, y, 71)
            col = lerp_rgb((0.31, 0.17, 0.10), (0.52, 0.31, 0.18), n_broad)
            sand_t = smoothstep(0.53, 0.79, n_patch)
            col = lerp_rgb(col, (0.64, 0.50, 0.33), sand_t * 0.72)
            rock_t = 1.0 - smoothstep(0.14, 0.38, n_broad)
            col = lerp_rgb(col, (0.43, 0.40, 0.36), rock_t * 0.48)
            if n_patch > 0.74 and n_broad < 0.58:
                g = smoothstep(0.74, 0.94, n_patch)
                col = lerp_rgb(col, (0.25, 0.31, 0.15), g * 0.50)
            speck = (grain - 0.5) * 0.075
            col = (col[0] + speck, col[1] + speck * 0.85, col[2] + speck * 0.7)
            idx = (y * size + x) * 4
            px[idx:idx + 4] = bytes(color_to_bytes(col))
    paths["soil"] = os.path.join(INTERMEDIATE, "T_HampiSoil_Albedo.png")
    write_png(paths["soil"], size, size, px)

    # Granite: grey-pink speckled local stone.
    px = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            u = x / float(size)
            v = y / float(size)
            broad = fbm(u, v, 41, (4, 12, 32), (0.50, 0.30, 0.20))
            fine = hash2(x, y, 97)
            col = lerp_rgb((0.38, 0.36, 0.34), (0.58, 0.53, 0.49), broad)
            if broad > 0.62:
                col = lerp_rgb(col, (0.60, 0.42, 0.37), (broad - 0.62) * 1.4)
            if fine > 0.91:
                col = (0.18, 0.17, 0.16)
            elif fine < 0.07:
                col = (0.72, 0.68, 0.63)
            idx = (y * size + x) * 4
            px[idx:idx + 4] = bytes(color_to_bytes(col))
    paths["granite"] = os.path.join(INTERMEDIATE, "T_HampiGranite_Albedo.png")
    write_png(paths["granite"], size, size, px)

    # Mud plaster: warm village wall with soft mottling.
    px = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            u = x / float(size)
            v = y / float(size)
            n = fbm(u, v, 59, (5, 13, 31), (0.48, 0.32, 0.20))
            grain = hash2(x, y, 131)
            col = lerp_rgb((0.53, 0.42, 0.29), (0.72, 0.60, 0.43), n)
            col = lerp_rgb(col, (0.45, 0.34, 0.23), (1.0 - n) * 0.22)
            col = (col[0] + (grain - 0.5) * 0.035,
                   col[1] + (grain - 0.5) * 0.030,
                   col[2] + (grain - 0.5) * 0.025)
            idx = (y * size + x) * 4
            px[idx:idx + 4] = bytes(color_to_bytes(col))
    paths["mud"] = os.path.join(INTERMEDIATE, "T_HampiMudPlaster_Albedo.png")
    write_png(paths["mud"], size, size, px)

    # Clay roof tiles: staggered red tiles with darker joints.
    px = bytearray(size * size * 4)
    cols = 8
    rows = 8
    for y in range(size):
        for x in range(size):
            u = x / float(size)
            v = y / float(size)
            row = int(v * rows) % rows
            tu = (u * cols + (0.5 if row % 2 else 0.0)) % 1.0
            tv = (v * rows) % 1.0
            tile_variation = hash2(int((u * cols + (0.5 if row % 2 else 0.0))), row, 151)
            col = lerp_rgb((0.50, 0.17, 0.10), (0.70, 0.31, 0.17), tile_variation)
            if tu < 0.055 or tv < 0.085:
                col = (0.27, 0.11, 0.07)
            elif tu > 0.93:
                col = lerp_rgb(col, (0.34, 0.13, 0.08), 0.55)
            shade = 0.88 + 0.12 * math.sin(tv * math.pi)
            col = (col[0] * shade, col[1] * shade, col[2] * shade)
            idx = (y * size + x) * 4
            px[idx:idx + 4] = bytes(color_to_bytes(col))
    paths["roof"] = os.path.join(INTERMEDIATE, "T_HampiClayRoof_Albedo.png")
    write_png(paths["roof"], size, size, px)

    # Dark wood: vertical grain for doors, windows and veranda posts.
    wsize = 128
    px = bytearray(wsize * wsize * 4)
    for y in range(wsize):
        for x in range(wsize):
            u = x / float(wsize)
            v = y / float(wsize)
            warp = fbm(u, v, 17, (4, 12), (0.65, 0.35))
            grain = 0.5 + 0.5 * math.sin((u * 17.0 + warp * 2.2) * math.pi * 2.0)
            col = lerp_rgb((0.15, 0.08, 0.045), (0.29, 0.17, 0.09), grain)
            idx = (y * wsize + x) * 4
            px[idx:idx + 4] = bytes(color_to_bytes(col))
    paths["wood"] = os.path.join(INTERMEDIATE, "T_HampiWood_Albedo.png")
    write_png(paths["wood"], wsize, wsize, px)

    w("TEXTURES_GENERATED=%d" % len(paths))
    return paths


def write_obj(path, verts, faces, mtl_file=None):
    with open(path, "w", encoding="ascii") as f:
        f.write("# Original procedural mesh generated for Hampi Battleground Task 04\n")
        if mtl_file:
            f.write("mtllib %s\n" % mtl_file)
        for v in verts:
            f.write("v %.4f %.4f %.4f\n" % (v[0], v[1], v[2]))
        current = None
        for mat, face in faces:
            if mat != current:
                f.write("usemtl %s\n" % mat)
                current = mat
            f.write("f %s\n" % " ".join(str(i + 1) for i in face))


def add_box(verts, faces, mat, mn, mx):
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    base = len(verts)
    verts.extend([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ])
    quads = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    for q in quads:
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


def generate_rock_meshes():
    os.makedirs(INTERMEDIATE, exist_ok=True)
    result = []
    for variant in range(5):
        rnd = random.Random(4000 + variant)
        radius = 190.0 + variant * 34.0
        segs = 10
        rings = 6
        xs = 1.08 + (variant % 3) * 0.12
        ys = 0.83 + (variant % 2) * 0.18
        zs = 0.62 + (variant % 4) * 0.07
        seed = 500 + variant * 17
        verts = []
        for ring in range(rings + 1):
            theta = math.pi * ring / float(rings)
            for seg in range(segs):
                phi = 2.0 * math.pi * seg / float(segs)
                if ring == 0:
                    z = radius * zs
                    x = y = 0.0
                elif ring == rings:
                    z = -radius * zs
                    x = y = 0.0
                else:
                    radial = (1.0
                              + 0.17 * math.sin(3.0 * phi + seed * 0.13 + theta * 2.0)
                              + 0.11 * math.cos(5.0 * theta + 2.0 * phi + seed * 0.07)
                              + 0.09 * (rnd.random() - 0.5))
                    x = math.cos(phi) * math.sin(theta) * radius * radial * xs
                    y = math.sin(phi) * math.sin(theta) * radius * radial * ys
                    z = math.cos(theta) * radius * radial * zs
                    if z < -0.48 * radius:
                        z = -0.48 * radius + (z + 0.48 * radius) * 0.12
                verts.append((x, y, z))
        min_z = min(v[2] for v in verts)
        verts = [(x, y, z - min_z) for x, y, z in verts]
        faces = []
        for seg in range(segs):
            faces.append(("Granite", (0, 1 + seg, 1 + ((seg + 1) % segs))))
        for ring in range(1, rings):
            top = ring * segs
            bot = (ring + 1) * segs
            for seg in range(segs):
                seg2 = (seg + 1) % segs
                faces.append(("Granite", (top + seg, bot + seg, bot + seg2, top + seg2)))
        bottom_center = rings * segs
        prev = (rings - 1) * segs
        for seg in range(segs):
            seg2 = (seg + 1) % segs
            faces.append(("Granite", (bottom_center, prev + seg2, prev + seg)))
        path = os.path.join(INTERMEDIATE, "SM_HampiBoulder_%02d.obj" % (variant + 1))
        write_obj(path, verts, faces)
        result.append((variant, path, verts, faces))
    w("ROCK_MESHES_GENERATED=%d" % len(result))
    return result


def generate_house_mesh():
    os.makedirs(INTERMEDIATE, exist_ok=True)
    verts = []
    faces = []

    # Stone plinth and veranda floor.
    add_box(verts, faces, "StoneBase", (-470, -370, 0), (470, 370, 60))
    add_box(verts, faces, "StoneBase", (-470, -530, 55), (470, -350, 70))

    # Mud-plastered walls with a simple front door opening.
    add_box(verts, faces, "MudPlaster", (-450, 328, 60), (450, 350, 450))
    add_box(verts, faces, "MudPlaster", (-450, -350, 60), (-428, 350, 450))
    add_box(verts, faces, "MudPlaster", (428, -350, 60), (450, 350, 450))
    add_box(verts, faces, "MudPlaster", (-450, -350, 60), (-90, -328, 450))
    add_box(verts, faces, "MudPlaster", (90, -350, 60), (450, -328, 450))
    add_box(verts, faces, "MudPlaster", (-90, -350, 330), (90, -328, 450))

    # Wooden door and small shuttered windows.
    add_box(verts, faces, "DarkWood", (-86, -357, 62), (86, -348, 330))
    add_box(verts, faces, "DarkWood", (-332, -358, 180), (-220, -349, 272))
    add_box(verts, faces, "DarkWood", (220, -358, 180), (332, -349, 272))
    add_box(verts, faces, "DarkWood", (-338, -362, 174), (-214, -349, 278))
    add_box(verts, faces, "DarkWood", (214, -362, 174), (338, -349, 278))

    # Veranda posts and beam.
    add_box(verts, faces, "DarkWood", (-372, -515, 70), (-344, -487, 356))
    add_box(verts, faces, "DarkWood", (344, -515, 70), (372, -487, 356))
    add_box(verts, faces, "DarkWood", (-430, -515, 348), (430, -487, 372))

    # Gabled clay roof, ridge cap and front veranda awning.
    add_prism(verts, faces, "ClayRoof",
              [(-480, 0, 650), (480, 0, 650), (480, 380, 440), (-480, 380, 440)], 18)
    add_prism(verts, faces, "ClayRoof",
              [(480, 0, 650), (-480, 0, 650), (-480, -380, 440), (480, -380, 440)], 18)
    add_box(verts, faces, "ClayRoof", (-500, -25, 642), (500, 25, 668))
    add_prism(verts, faces, "ClayRoof",
              [(430, -350, 440), (-430, -350, 440), (-430, -530, 352), (430, -530, 352)], 12)

    # Low courtyard walls, leaving a front opening.
    add_box(verts, faces, "StoneBase", (-470, -545, 0), (-110, -525, 55))
    add_box(verts, faces, "StoneBase", (110, -545, 0), (470, -525, 55))
    add_box(verts, faces, "StoneBase", (-470, -525, 0), (-450, -350, 55))
    add_box(verts, faces, "StoneBase", (450, -525, 0), (470, -350, 55))

    obj_path = os.path.join(INTERMEDIATE, "SM_KamalapurHouse_Small.obj")
    mtl_path = os.path.join(INTERMEDIATE, "HampiHouse.mtl")
    with open(mtl_path, "w", encoding="ascii") as f:
        f.write("newmtl MudPlaster\nKd 0.65 0.52 0.37\n\n")
        f.write("newmtl ClayRoof\nKd 0.62 0.25 0.14\n\n")
        f.write("newmtl DarkWood\nKd 0.22 0.12 0.07\n\n")
        f.write("newmtl StoneBase\nKd 0.45 0.43 0.39\n\n")
    write_obj(obj_path, verts, faces, "HampiHouse.mtl")
    w("HOUSE_MESH_GENERATED verts=%d faces=%d" % (len(verts), len(faces)))
    return verts, faces, obj_path


# ---------------------------------------------------------------------------
# Unreal asset helpers
# ---------------------------------------------------------------------------

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary


def ensure_dir(path):
    if not eal.does_directory_exist(path):
        eal.make_directory(path)


def load(path):
    return eal.load_asset(path)


def save(obj):
    if obj:
        eal.save_loaded_asset(obj)


def import_texture(png_path, dest_path, name):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", png_path)
    task.set_editor_property("destination_path", dest_path)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    tools.import_asset_tasks([task])
    obj = load(dest_path + "/" + name)
    if obj:
        try:
            obj.set_editor_property("srgb", True)
        except Exception:
            pass
        try:
            obj.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
        except Exception:
            pass
        save(obj)
    w("TEXTURE_IMPORT %s = %s" % (name, bool(obj)))
    return obj


def create_textured_material(name, texture, tint, roughness=0.92, specular=0.15, world_uv=False):
    dest = ROOT + "/Materials"
    ensure_dir(dest)
    path = dest + "/" + name
    mat = load(path)
    if not mat:
        mat = tools.create_asset(name, dest, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        w("MATERIAL_CREATE_FAILED %s" % name)
        return None
    mel.delete_all_material_expressions(mat)

    try:
        mat.set_editor_property("two_sided", False)
    except Exception:
        pass
    try:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    except Exception:
        pass
    try:
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    except Exception:
        pass

    ts = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -380, 40)
    ts.set_editor_property("parameter_name", "BaseTexture")
    if texture:
        ts.set_editor_property("texture", texture)

    tint_expr = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -380, 260)
    tint_expr.set_editor_property("parameter_name", "Tint")
    tint_expr.set_editor_property("default_value", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))

    mult = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -80, 100)

    if world_uv:
        world = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -820, -120)
        mask = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -640, -120)
        for prop in ("r", "g", "b", "a"):
            mask.set_editor_property(prop, prop in ("r", "g"))
        tiling = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -640, 120)
        tiling.set_editor_property("parameter_name", "Tiling")
        tiling.set_editor_property("default_value", 0.0045)
        uv_mult = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -420, -80)
        # ComponentMask's first input pin is reported as "None" by UE 5.4; an
        # empty string is accepted as "use first input". The previous "Input"
        # name compiled into an unconnected mask and broke the soil material.
        connect_expr(world, ["", "XYZ", "RGB"], mask, ["", "None"])
        connect_expr(mask, ["", "RGB", "RG"], uv_mult, ["A"])
        connect_expr(tiling, ["", "Output"], uv_mult, ["B"])
        connect_expr(uv_mult, ["", "Output"], ts, ["UVs", "Coordinates"])
    connect_expr(ts, ["RGB", "RGBA", ""], mult, ["A"])
    connect_expr(tint_expr, ["", "RGB"], mult, ["B"])

    for out in ["", "RGB", "RGBA"]:
        try:
            mel.connect_material_property(mult, out, unreal.MaterialProperty.MP_BASE_COLOR)
            break
        except Exception:
            continue

    rough = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -80, 300)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", roughness)
    for out in ["", "Output"]:
        try:
            mel.connect_material_property(rough, out, unreal.MaterialProperty.MP_ROUGHNESS)
            break
        except Exception:
            continue

    spec = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -80, 460)
    spec.set_editor_property("parameter_name", "Specular")
    spec.set_editor_property("default_value", specular)
    for out in ["", "Output"]:
        try:
            mel.connect_material_property(spec, out, unreal.MaterialProperty.MP_SPECULAR)
            break
        except Exception:
            continue

    mel.recompile_material(mat)
    save(mat)
    w("MATERIAL_READY %s" % path)
    return mat


def connect_expr(src, src_outputs, dst, dst_inputs):
    for out in src_outputs:
        for inp in dst_inputs:
            try:
                if mel.connect_material_expressions(src, out, dst, inp):
                    return True
            except Exception:
                continue
    w("CONNECT_WARN src=%s dst=%s out=%s in=%s" % (
        src.get_name(), dst.get_name(), src_outputs, dst_inputs))
    return False


def create_material_instance(name, parent, tint):
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
        w("MI_CREATE_FAILED %s" % name)
        return None
    try:
        mi.set_editor_property("parent", parent)
    except Exception:
        pass
    mel.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
    save(mi)
    w("MATERIAL_INSTANCE_READY %s" % path)
    return mi


def import_mesh(obj_path, dest_path, name, collision=True):
    ensure_dir(dest_path)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", obj_path)
    task.set_editor_property("destination_path", dest_path)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)

    # Let the engine's FbxFactory handle OBJ with its default static-mesh import
    # settings. Explicit FbxImportUI objects are not assignable to the factory's
    # automated-import-data slot through the Python API.
    factory = unreal.FbxFactory()
    task.set_editor_property("factory", factory)

    tools.import_asset_tasks([task])
    mesh = load(dest_path + "/" + name)
    if mesh:
        save(mesh)
    w("MESH_IMPORT %s = %s" % (name, bool(mesh)))
    return mesh


def cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def planar_uv(p, axis):
    scale = 1.0 / 180.0
    if axis == 2:
        return p[0] * scale, p[1] * scale
    if axis == 0:
        return p[1] * scale, p[2] * scale
    return p[0] * scale, p[2] * scale


def build_static_mesh(name, dest_path, verts, faces, materials):
    """Build a real static-mesh asset from original vertex/face data."""
    path = dest_path + "/" + name
    ensure_dir(dest_path)
    mesh = load(path)
    if not mesh:
        mesh = eal.duplicate_asset("/Engine/BasicShapes/Cube", path)
    if not mesh:
        w("STATIC_MESH_CREATE_FAILED=%s" % name)
        return None

    try:
        mesh.set_editor_property("static_materials", [])
    except Exception as e:
        w("STATIC_MESH_CLEAR_SLOTS_WARN=%s %s" % (name, e))

    slot_names = {}
    for mat_name, mat in materials:
        if mat:
            slot_names[mat_name] = mesh.add_material(mat)
        else:
            slot_names[mat_name] = unreal.Name(mat_name)

    desc = mesh.create_static_mesh_description(mesh)
    desc.empty()

    vertex_ids = []
    for p in verts:
        vid = desc.create_vertex()
        desc.set_vertex_position(vid, unreal.Vector(float(p[0]), float(p[1]), float(p[2])))
        vertex_ids.append(vid)

    groups = {}
    for mat_name in slot_names:
        pg = desc.create_polygon_group()
        desc.set_polygon_group_material_slot_name(pg, slot_names[mat_name])
        groups[mat_name] = pg

    for mat_name, face in faces:
        pg = groups.get(mat_name)
        if pg is None or len(face) < 3:
            continue
        p0 = verts[face[0]]
        p1 = verts[face[1]]
        p2 = verts[face[2]]
        n = cross3((p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]),
                   (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]))
        axis = max(range(3), key=lambda i: abs(n[i]))
        vis = []
        for idx in face:
            vi = desc.create_vertex_instance(vertex_ids[idx])
            u, v = planar_uv(verts[idx], axis)
            desc.set_vertex_instance_uv(vi, unreal.Vector2D(u, v), 0)
            vis.append(vi)
        for i in range(1, len(vis) - 1):
            desc.create_triangle(pg, [vis[0], vis[i], vis[i + 1]])

    tris = desc.get_triangle_count()
    w("STATIC_MESH_BUILD %s verts=%d triangles=%d slots=%d" % (
        name, desc.get_vertex_count(), tris, len(slot_names)))
    if tris == 0:
        w("STATIC_MESH_BUILD_FAILED_EMPTY=%s" % name)
        return None

    mesh.build_from_static_mesh_descriptions([desc], True, True)
    for mat_name, mat in materials:
        if mat:
            try:
                idx = mesh.get_material_index(slot_names[mat_name])
                mesh.set_material(idx, mat)
            except Exception:
                pass
    save(mesh)
    w("STATIC_MESH_READY %s" % path)
    return mesh


def ground_z(world, x, y, fallback=100.0):
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            unreal.Vector(x, y, 30000.0),
            unreal.Vector(x, y, -5000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True, [], unreal.DrawDebugTrace.NONE, True)
        if hit:
            return float(hit.to_tuple()[4].z)
    except Exception as e:
        w("GROUND_TRACE_WARN %s,%s %s" % (x, y, e))
    return fallback


def spawn_static_mesh(world, mesh, label, location, rotation, scale, folder="Hampi/Task04/Stage1", material=None):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(location[0], location[1], location[2]),
        # unreal.Rotator Python constructor order is roll, pitch, yaw.
        unreal.Rotator(rotation[2], rotation[0], rotation[1]))
    if not actor:
        w("SPAWN_FAILED %s" % label)
        return None
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_editor_property("static_mesh", mesh)
        comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        if material:
            try:
                comp.set_material(0, material)
            except Exception:
                try:
                    comp.set_editor_property("override_materials", [material])
                except Exception:
                    pass
    actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    try:
        actor.set_actor_label(label)
    except Exception:
        pass
    try:
        actor.set_folder_path(unreal.Name(folder))
    except Exception:
        pass
    try:
        actor.set_editor_property("tags", [unreal.Name("Task04_Stage1")])
    except Exception:
        pass
    return actor


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

try:
    ensure_dir(ROOT)
    for sub in ["Terrain", "Houses", "Temples", "Rocks", "Vegetation", "Props", "Materials"]:
        ensure_dir(ROOT + "/" + sub)

    tex_paths = generate_textures()
    tex = {
        "soil": import_texture(tex_paths["soil"], ROOT + "/Terrain", "T_HampiSoil_Albedo"),
        "granite": import_texture(tex_paths["granite"], ROOT + "/Terrain", "T_HampiGranite_Albedo"),
        "mud": import_texture(tex_paths["mud"], ROOT + "/Terrain", "T_HampiMudPlaster_Albedo"),
        "roof": import_texture(tex_paths["roof"], ROOT + "/Terrain", "T_HampiClayRoof_Albedo"),
        "wood": import_texture(tex_paths["wood"], ROOT + "/Terrain", "T_HampiWood_Albedo"),
    }

    soil_mat = create_textured_material("M_HampiSoil_Mobile", tex["soil"], (1.0, 1.0, 1.0), 0.96, 0.10, True)
    granite_mat = create_textured_material("M_HampiGranite_Mobile", tex["granite"], (1.0, 1.0, 1.0), 0.91, 0.13, False)
    mud_mat = create_textured_material("M_HampiMudPlaster_Mobile", tex["mud"], (1.0, 1.0, 1.0), 0.94, 0.11, False)
    roof_mat = create_textured_material("M_HampiClayRoof_Mobile", tex["roof"], (1.0, 1.0, 1.0), 0.90, 0.12, False)
    wood_mat = create_textured_material("M_HampiWoodDark_Mobile", tex["wood"], (1.0, 1.0, 1.0), 0.88, 0.12, False)

    rock_mis = [
        create_material_instance("MI_HampiGranite_Grey", granite_mat, (0.90, 0.89, 0.87)),
        create_material_instance("MI_HampiGranite_Warm", granite_mat, (1.02, 0.93, 0.86)),
        create_material_instance("MI_HampiGranite_Dark", granite_mat, (0.72, 0.72, 0.72)),
    ]

    rock_files = generate_rock_meshes()
    rock_meshes = []
    for variant, path, verts, faces in rock_files:
        name = "SM_HampiBoulder_%02d" % (variant + 1)
        mi = rock_mis[variant % len(rock_mis)]
        mesh = build_static_mesh(name, ROOT + "/Rocks", verts, faces, [("Granite", mi)])
        if mesh:
            rock_meshes.append(mesh)
    w("ROCK_MESHES_BUILT=%d" % len(rock_meshes))

    house_verts, house_faces, house_path = generate_house_mesh()
    house_materials = [
        ("MudPlaster", mud_mat),
        ("ClayRoof", roof_mat),
        ("DarkWood", wood_mat),
        ("StoneBase", granite_mat),
    ]
    house_mesh = build_static_mesh("SM_KamalapurHouse_Small", ROOT + "/Houses",
                                   house_verts, house_faces, house_materials)

    # Load and modify the existing level. No new level asset is created.
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError("Could not load " + MAP_PATH)

    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    # Idempotency: remove only this script's previously tagged Stage 1 actors.
    old_stage1 = []
    for a in actors:
        try:
            if unreal.Name("Task04_Stage1") in list(a.get_editor_property("tags")):
                old_stage1.append(a)
        except Exception:
            pass
    for a in old_stage1:
        unreal.EditorLevelLibrary.destroy_actor(a)
    w("OLD_STAGE1_ACTORS_REMOVED=%d" % len(old_stage1))
    if old_stage1:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()

    landscape = next((a for a in actors if isinstance(a, unreal.Landscape)), None)
    if not landscape:
        raise RuntimeError("Landscape not found in " + MAP_PATH)
    if soil_mat:
        landscape.set_editor_property("landscape_material", soil_mat)
        w("LANDSCAPE_MATERIAL_SET=%s" % soil_mat.get_path_name())

    hx, hy = -29450.0, 0.0
    hz = ground_z(world, hx, hy, 496.87) + 2.0
    house = spawn_static_mesh(
        world, house_mesh, "Hampi_Task04_KamalapurHouse_Small",
        (hx, hy, hz), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    w("HOUSE_PLACED=%s at (%.1f,%.1f,%.1f)" % (bool(house), hx, hy, hz))

    rock_offsets = [
        (-31500, -2300), (-27600, -1900), (-32300, 1500), (-26600, 2100),
        (-30600, 3300), (-28200, -3400), (-33700, -400), (-25400, 500),
        (-30000, 4200), (-27200, 3800),
    ]
    placed = 0
    for idx, (rx, ry) in enumerate(rock_offsets):
        if not rock_meshes:
            break
        mesh = rock_meshes[idx % len(rock_meshes)]
        mi = rock_mis[idx % len(rock_mis)]
        rz = ground_z(world, rx, ry, 100.0) + 2.0
        rnd = random.Random(9000 + idx)
        scale = 0.62 + rnd.random() * 0.72
        actor = spawn_static_mesh(
            world, mesh, "Hampi_Task04_Boulder_%02d" % (idx + 1),
            (rx, ry, rz),
            (rnd.uniform(-5, 5), rnd.uniform(0, 360), rnd.uniform(-5, 5)),
            (scale, scale * (0.85 + rnd.random() * 0.30), scale * (0.75 + rnd.random() * 0.35)),
            material=mi)
        if actor:
            placed += 1
    w("ROCKS_PLACED=%d" % placed)

    try:
        camera_loc = unreal.Vector(-29450.0, -4200.0, 1600.0)
        camera_rot = unreal.Rotator(0.0, -12.0, 90.0)
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_loc, camera_rot)
        world_for_cmds = unreal.EditorLevelLibrary.get_editor_world()
        for cmd in ["VIEWMODE LIT", "SHOWFLAG Lighting 1", "SHOWFLAG Landscape 1",
                    "SHOWFLAG PostProcessing 1", "SHOWFLAG Fog 1"]:
            unreal.SystemLibrary.execute_console_command(world_for_cmds, cmd)
        w("VIEWPORT_CAMERA_SET")
    except Exception as e:
        w("VIEWPORT_CAMERA_WARN=%s" % e)

    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    w("LEVEL_SAVED=%s" % saved)

    mapcheck = unreal.SystemLibrary.execute_console_command(
        unreal.EditorLevelLibrary.get_editor_world(), "MAP CHECK")
    w("MAPCHECK_CMD_SENT=%s" % mapcheck)

    w("STAGE1_DONE")
except Exception:
    w("FATAL:\n" + traceback.format_exc())
finally:
    flush()
    print("TASK04_STAGE1_WRITTEN", OUT)
