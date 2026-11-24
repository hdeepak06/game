import math
import os
import unreal

# ---------------------------------------------------------------------------
# Task 05, Landmark 1: Virupaksha Temple inspired landmark.
# Original low-poly geometry and material instances only. Photographs are
# reference material; no downloaded image is used as a texture.
# ---------------------------------------------------------------------------

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "Task05Audit", "build_virupaksha.txt")
ROOT = "/Game/Environment"
ASSET_ROOT = ROOT + "/Task05/Virupaksha"
MESH_DIR = ASSET_ROOT + "/Meshes"
MI_DIR = ASSET_ROOT + "/Materials"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

lines = []


def w(s=""):
    lines.append(str(s))


eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def ensure_dir(path):
    if not eal.does_directory_exist(path):
        eal.make_directory(path)


def load(path):
    return eal.load_asset(path)


def save(obj):
    if obj:
        eal.save_loaded_asset(obj)


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


def add_box(verts, faces, mat, mn, mx):
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    if x1 <= x0 or y1 <= y0 or z1 <= z0:
        return
    base = len(verts)
    verts.extend([
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ])
    for q in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
              (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        faces.append((mat, tuple(base + i for i in q)))


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


def add_stepped_shikhara(verts, faces, mat, cx, cy, z0, width, levels=3):
    cur_w = width
    z = z0
    for i in range(levels):
        h = width * 0.28
        add_box(verts, faces, mat,
                (cx - cur_w / 2, cy - cur_w / 2, z),
                (cx + cur_w / 2, cy + cur_w / 2, z + h))
        z += h
        cur_w *= 0.68
    add_cylinder(verts, faces, "White", cx, cy, z, z + width * 0.45,
                 max(12.0, width * 0.09), 8, 0.25)


def add_front_niche(verts, faces, x_face, cy, z0, w, h, idx):
    # Decorative recessed panel on an east-facing tower face.
    add_box(verts, faces, "White",
            (x_face, cy - w * 0.62, z0 - h * 0.10),
            (x_face + 26, cy + w * 0.62, z0 + h * 1.10))
    add_box(verts, faces, "StoneDark",
            (x_face + 27, cy - w * 0.45, z0),
            (x_face + 33, cy + w * 0.45, z0 + h))
    add_box(verts, faces, "Ochre" if idx % 2 else "Red",
            (x_face + 34, cy - w * 0.25, z0 + h * 0.18),
            (x_face + 43, cy + w * 0.25, z0 + h * 0.78))
    add_box(verts, faces, "White",
            (x_face + 44, cy - w * 0.10, z0 + h * 0.42),
            (x_face + 50, cy + w * 0.10, z0 + h * 0.64))


def build_static_mesh(name, verts, faces, materials):
    ensure_dir(MESH_DIR)
    path = MESH_DIR + "/" + name
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
        slots[slot_name] = mesh.add_material(mat) if mat else unreal.Name(slot_name)
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
            u, vv = planar_uv(verts[idx], axis)
            desc.set_vertex_instance_uv(vi, unreal.Vector2D(u, vv), 0)
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
    w("MESH_READY %s verts=%d tris=%d slots=%d" % (
        name, desc.get_vertex_count(), tris, len(slots)))
    return mesh


def make_mi(name, parent, tint, roughness=None):
    ensure_dir(MI_DIR)
    path = MI_DIR + "/" + name
    mi = load(path)
    if not mi:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        try:
            factory.set_editor_property("initial_parent", parent)
        except Exception:
            pass
        mi = tools.create_asset(name, MI_DIR, unreal.MaterialInstanceConstant, factory)
    if not mi:
        w("MI_FAILED=%s" % name)
        return None
    try:
        mi.set_editor_property("parent", parent)
    except Exception:
        pass
    try:
        mel.set_material_instance_vector_parameter_value(
            mi, "Tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
    except Exception as e:
        w("MI_TINT_WARN %s %s" % (name, e))
    if roughness is not None:
        try:
            mel.set_material_instance_scalar_parameter_value(mi, "Roughness", float(roughness))
        except Exception:
            pass
    try:
        mel.update_material_instance(mi)
    except Exception:
        pass
    save(mi)
    w("MI_READY %s" % path)
    return mi


def build_materials():
    parents = {
        "granite": load(ROOT + "/Materials/M_HampiGranite_Mobile"),
        "plaster": load(ROOT + "/Materials/M_HampiPlasterWarm_Mobile"),
        "roof": load(ROOT + "/Materials/M_HampiRoofWarm_Mobile"),
        "wood": load(ROOT + "/Materials/M_HampiWood_Mobile"),
        "water": load(ROOT + "/Materials/M_HampiWater_Mobile"),
    }
    for key, parent in parents.items():
        if not parent:
            w("PARENT_MATERIAL_MISSING=%s" % key)
    mats = {}
    specs = [
        ("T05_TempleStone", "granite", (0.96, 0.88, 0.76), 0.95),
        ("T05_TempleStoneDark", "granite", (0.55, 0.51, 0.46), 0.97),
        ("T05_TemplePlaster", "plaster", (1.00, 0.78, 0.55), 0.94),
        ("T05_TempleOchre", "plaster", (1.00, 0.58, 0.28), 0.95),
        ("T05_TempleWhite", "plaster", (1.00, 0.96, 0.86), 0.92),
        ("T05_TempleRed", "plaster", (0.72, 0.22, 0.15), 0.94),
        ("T05_TempleAccent", "plaster", (0.88, 0.52, 0.18), 0.94),
        ("T05_TempleWood", "wood", (0.58, 0.38, 0.25), 0.92),
        ("T05_TempleRoof", "roof", (0.92, 0.78, 0.62), 0.93),
        ("T05_TempleWater", "water", (0.62, 0.88, 1.00), 0.30),
    ]
    for name, parent_key, tint, rough in specs:
        parent = parents.get(parent_key)
        if parent:
            mats[name] = make_mi(name, parent, tint, rough)
    return mats


def gopuram(mats):
    verts, faces = [], []
    # Stone plinth and gate pylons leave a real passage through the tower.
    add_box(verts, faces, "Stone", (2150, -1320, 0), (3300, 1320, 180))
    add_box(verts, faces, "Stone", (2180, -1320, 180), (3260, -360, 1180))
    add_box(verts, faces, "Stone", (2180, 360, 180), (3260, 1320, 1180))
    add_box(verts, faces, "Stone", (2180, -360, 920), (3260, 360, 1180))
    # Framed entrance and lintel.
    add_box(verts, faces, "StoneDark", (3262, -390, 180), (3290, -350, 920))
    add_box(verts, faces, "StoneDark", (3262, 350, 180), (3290, 390, 920))
    add_box(verts, faces, "Ochre", (3265, -470, 920), (3305, 470, 1010))
    add_box(verts, faces, "Red", (3292, -520, 1010), (3325, 520, 1070))

    # Nine tapering storeys, each with a projecting cornice and repetitive niches.
    z = 1180.0
    tier_h = 405.0
    for i in range(9):
        t = i / 8.0
        half_y = 1120.0 - 570.0 * t
        front_x = 3260.0 - 150.0 * t
        back_x = 2220.0 + 110.0 * t
        body_mat = "Plaster" if i % 2 == 0 else "Ochre"
        add_box(verts, faces, body_mat, (back_x, -half_y, z), (front_x, half_y, z + tier_h))
        # Stone bands and coping make the tiers read as separate storeys.
        add_box(verts, faces, "Stone", (back_x - 45, -half_y - 55, z - 34),
                (front_x + 55, half_y + 55, z + 18))
        add_box(verts, faces, "White", (front_x - 10, -half_y - 28, z + tier_h - 34),
                (front_x + 52, half_y + 28, z + tier_h + 20))
        # Pilasters and sculpted niche rows on the east face.
        for k in range(-2, 3):
            cy = k * (half_y * 0.40)
            if abs(cy) > half_y - 120:
                continue
            add_box(verts, faces, "White",
                    (front_x + 8, cy - 24, z + 28),
                    (front_x + 26, cy + 24, z + tier_h - 34))
            add_front_niche(verts, faces, front_x + 27, cy, z + 72,
                            min(150.0, half_y * 0.30), tier_h * 0.58, i * 5 + k + 2)
        # Side niches, simplified for mobile.
        for sy in [-1, 1]:
            y_face = sy * (half_y + 2)
            add_box(verts, faces, "White",
                    (front_x - 300, y_face - 2 if sy > 0 else y_face - 18, z + 60),
                    (front_x - 170, y_face + 18 if sy > 0 else y_face + 2, z + tier_h - 60))
            add_box(verts, faces, "Red",
                    (front_x - 275, y_face + (16 if sy > 0 else -22), z + 100),
                    (front_x - 195, y_face + (24 if sy > 0 else -30), z + tier_h - 90))
        z += tier_h

    # Crown: stepped shikhara and finial.
    add_stepped_shikhara(verts, faces, "Ochre", 2780, 0, z, 520, 4)
    add_box(verts, faces, "White", (2730, -50, z + 700), (2830, 50, z + 790))

    mats_used = [
        ("Stone", mats["T05_TempleStone"]),
        ("StoneDark", mats["T05_TempleStoneDark"]),
        ("Plaster", mats["T05_TemplePlaster"]),
        ("Ochre", mats["T05_TempleOchre"]),
        ("White", mats["T05_TempleWhite"]),
        ("Red", mats["T05_TempleRed"]),
    ]
    return build_static_mesh("SM_T05_VirupakshaGopuram", verts, faces, mats_used)


def mandapa(mats):
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-1250, -900, 0), (1250, 900, 55))
    add_box(verts, faces, "Stone", (-1190, -840, 55), (1190, 840, 95))
    for ix in range(7):
        x = -1030 + ix * 343
        for iy in range(5):
            y = -680 + iy * 340
            add_cylinder(verts, faces, "Stone", x, y, 95, 620, 42, 8, 0.92)
            add_box(verts, faces, "White", (x - 58, y - 58, 600), (x + 58, y + 58, 645))
            add_box(verts, faces, "Ochre", (x - 46, y - 46, 645), (x + 46, y + 46, 685))
    add_box(verts, faces, "Stone", (-1210, -860, 685), (1210, 860, 765))
    add_box(verts, faces, "White", (-1260, -910, 765), (1260, 910, 815))
    for x in [-980, -330, 330, 980]:
        add_stepped_shikhara(verts, faces, "Ochre", x, 0, 815, 250, 2)
    mats_used = [
        ("Stone", mats["T05_TempleStone"]),
        ("White", mats["T05_TempleWhite"]),
        ("Ochre", mats["T05_TempleOchre"]),
    ]
    return build_static_mesh("SM_T05_VirupakshaMandapa", verts, faces, mats_used)


def sanctum(mats):
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-720, -720, 0), (720, 720, 90))
    add_box(verts, faces, "Stone", (-650, -650, 90), (650, 650, 980))
    add_box(verts, faces, "StoneDark", (648, -190, 90), (692, 190, 720))
    add_box(verts, faces, "Wood", (694, -170, 110), (720, 170, 690))
    add_box(verts, faces, "Ochre", (620, -230, 720), (735, 230, 820))
    add_box(verts, faces, "Stone", (-720, -720, 980), (720, 720, 1050))
    add_box(verts, faces, "White", (-760, -760, 1050), (760, 760, 1100))
    add_stepped_shikhara(verts, faces, "Ochre", 0, 0, 1100, 820, 4)
    for y in [-520, 520]:
        add_front_niche(verts, faces, 652, y, 300, 150, 260, 3)
    mats_used = [
        ("Stone", mats["T05_TempleStone"]),
        ("StoneDark", mats["T05_TempleStoneDark"]),
        ("Wood", mats["T05_TempleWood"]),
        ("Ochre", mats["T05_TempleOchre"]),
        ("White", mats["T05_TempleWhite"]),
        ("Red", mats["T05_TempleRed"]),
    ]
    return build_static_mesh("SM_T05_VirupakshaSanctum", verts, faces, mats_used)


def sub_shrine(mats):
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-340, -340, 0), (340, 340, 60))
    add_box(verts, faces, "Stone", (-290, -290, 60), (290, 290, 520))
    add_box(verts, faces, "StoneDark", (288, -110, 60), (315, 110, 400))
    add_box(verts, faces, "Ochre", (-330, -330, 520), (330, 330, 590))
    add_box(verts, faces, "White", (-360, -360, 590), (360, 360, 630))
    add_stepped_shikhara(verts, faces, "Ochre", 0, 0, 630, 430, 3)
    mats_used = [
        ("Stone", mats["T05_TempleStone"]),
        ("StoneDark", mats["T05_TempleStoneDark"]),
        ("Ochre", mats["T05_TempleOchre"]),
        ("White", mats["T05_TempleWhite"]),
    ]
    return build_static_mesh("SM_T05_VirupakshaSubShrine", verts, faces, mats_used)


def cloister(mats):
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-500, -190, 0), (500, 190, 45))
    for x in [-420, -140, 140, 420]:
        add_cylinder(verts, faces, "Stone", x, -95, 45, 390, 33, 8, 0.95)
        add_cylinder(verts, faces, "Stone", x, 95, 45, 390, 33, 8, 0.95)
        add_box(verts, faces, "White", (x - 45, -140, 380), (x + 45, 140, 415))
    add_box(verts, faces, "Stone", (-520, -230, 415), (520, 230, 485))
    add_box(verts, faces, "Ochre", (-540, -250, 485), (540, 250, 525))
    mats_used = [
        ("Stone", mats["T05_TempleStone"]),
        ("White", mats["T05_TempleWhite"]),
        ("Ochre", mats["T05_TempleOchre"]),
    ]
    return build_static_mesh("SM_T05_VirupakshaCloister", verts, faces, mats_used)


def courtyard_wall(mats):
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-500, -75, 0), (500, 75, 50))
    add_box(verts, faces, "Stone", (-480, -55, 50), (480, 55, 420))
    add_box(verts, faces, "White", (-500, -85, 420), (500, 85, 465))
    for x in [-330, 0, 330]:
        add_box(verts, faces, "StoneDark", (x - 55, 52, 140), (x + 55, 62, 330))
        add_box(verts, faces, "Ochre", (x - 40, 63, 170), (x + 40, 70, 300))
    mats_used = [
        ("Stone", mats["T05_TempleStone"]),
        ("StoneDark", mats["T05_TempleStoneDark"]),
        ("White", mats["T05_TempleWhite"]),
        ("Ochre", mats["T05_TempleOchre"]),
    ]
    return build_static_mesh("SM_T05_VirupakshaCourtyardWall", verts, faces, mats_used)


def temple_tank(mats):
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-900, -650, 0), (900, 650, 40))
    add_box(verts, faces, "Stone", (-900, -650, 40), (-780, 650, 190))
    add_box(verts, faces, "Stone", (780, -650, 40), (900, 650, 190))
    add_box(verts, faces, "Stone", (-780, -650, 40), (780, -530, 190))
    add_box(verts, faces, "Stone", (-780, 530, 40), (780, 650, 190))
    for i in range(5):
        y = -430 + i * 215
        add_box(verts, faces, "White", (-760, y, 45 + i * 22), (760, y + 35, 70 + i * 22))
    add_box(verts, faces, "Water", (-770, -520, 145), (770, 520, 152))
    mats_used = [
        ("Stone", mats["T05_TempleStone"]),
        ("White", mats["T05_TempleWhite"]),
        ("Water", mats["T05_TempleWater"]),
    ]
    return build_static_mesh("SM_T05_VirupakshaTank", verts, faces, mats_used)


def bazaar_shop(mats):
    verts, faces = [], []
    add_box(verts, faces, "Stone", (-320, -260, 0), (320, 260, 45))
    add_box(verts, faces, "Plaster", (-300, -240, 45), (300, 240, 430))
    add_box(verts, faces, "StoneDark", (-180, -252, 45), (180, -235, 360))
    add_box(verts, faces, "Wood", (-160, -265, 60), (160, -248, 330))
    add_box(verts, faces, "Stone", (-350, -290, 430), (350, 290, 490))
    add_box(verts, faces, "Ochre", (-360, -300, 490), (360, 300, 525))
    for x in [-285, 285]:
        add_cylinder(verts, faces, "Wood", x, -320, 45, 390, 24, 8, 1.0)
    add_box(verts, faces, "Red", (-330, -345, 390), (330, -320, 435))
    mats_used = [
        ("Stone", mats["T05_TempleStone"]),
        ("StoneDark", mats["T05_TempleStoneDark"]),
        ("Plaster", mats["T05_TemplePlaster"]),
        ("Wood", mats["T05_TempleWood"]),
        ("Ochre", mats["T05_TempleOchre"]),
        ("Red", mats["T05_TempleRed"]),
    ]
    return build_static_mesh("SM_T05_HampiBazaarShop", verts, faces, mats_used)


def main():
    ensure_dir(ASSET_ROOT)
    ensure_dir(MESH_DIR)
    ensure_dir(MI_DIR)
    mats = build_materials()
    w("MATERIALS_READY=%d" % len([m for m in mats.values() if m]))
    gopuram(mats)
    mandapa(mats)
    sanctum(mats)
    sub_shrine(mats)
    cloister(mats)
    courtyard_wall(mats)
    temple_tank(mats)
    bazaar_shop(mats)
    w("VIRUPAKSHA_BUILD_DONE")


try:
    main()
except Exception as e:
    w("VIRUPAKSHA_BUILD_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK05_VIRUPAKSHA_BUILD_WRITTEN")
