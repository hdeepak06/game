import math
import os
import unreal

# ---------------------------------------------------------------------------
# Task 05, Landmark 1: place the Virupaksha-inspired complex in the existing
# Hampi region. Only actors tagged Task05_Virupaksha are removed on rerun.
# ---------------------------------------------------------------------------

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "Task05Audit", "place_virupaksha.txt")
MAP = "/Game/Maps/LV_HampiBattleground"
ROOT = "/Game/Environment"
MESH_DIR = ROOT + "/Task05/Virupaksha/Meshes"
TAG = "Task05_Virupaksha"
FOLDER = "Hampi/Task05/Virupaksha"
CENTER = (-43800.0, 13500.0)
lines = []


def w(s=""):
    lines.append(str(s))


eal = unreal.EditorAssetLibrary


def load(path):
    return eal.load_asset(path)


def ground_z(world, x, y, fallback=100.0):
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            unreal.Vector(float(x), float(y), 30000.0),
            unreal.Vector(float(x), float(y), -5000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True, [], unreal.DrawDebugTrace.NONE, True)
        if hit:
            return float(hit.to_tuple()[4].z)
    except Exception:
        pass
    return fallback


def cleanup(world):
    removed = 0
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if TAG in [str(t) for t in actor.tags]:
            if unreal.EditorLevelLibrary.destroy_actor(actor):
                removed += 1
    w("OLD_TASK05_VIRUPAKSHA_ACTORS_REMOVED=%d" % removed)


def tag_actor(actor, label, proxy=False):
    actor.set_actor_label(label)
    actor.set_folder_path(FOLDER + ("/Collision" if proxy else ""))
    actor.tags = [unreal.Name(TAG)]
    return actor


def spawn_visual(world, mesh_name, label, lx, ly, z_offset=0.0, yaw=0.0, scale=1.0):
    mesh = load(MESH_DIR + "/" + mesh_name)
    if not mesh:
        w("VISUAL_MESH_MISSING=%s" % mesh_name)
        return None
    x = CENTER[0] + lx
    y = CENTER[1] + ly
    z = ground_z(world, x, y) + z_offset
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(x, y, z),
        unreal.Rotator(0.0, 0.0, yaw))
    if not actor:
        w("VISUAL_SPAWN_FAILED=%s" % label)
        return None
    tag_actor(actor, label)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(mesh)
        comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        try:
            comp.set_collision_profile_name("NoCollision")
        except Exception:
            pass
        try:
            comp.set_editor_property("cast_shadow", True)
        except Exception:
            pass
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    return actor


def spawn_proxy(world, label, lx, ly, lz, sx, sy, sz, yaw=0.0):
    # Cube is 100 cm. Proxy sits inside visible stonework and is hidden in game.
    mesh = load("/Engine/BasicShapes/Cube")
    if not mesh:
        w("PROXY_CUBE_MISSING")
        return None
    x = CENTER[0] + lx
    y = CENTER[1] + ly
    z = ground_z(world, x, y) + lz
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(x, y, z),
        unreal.Rotator(0.0, 0.0, yaw))
    if not actor:
        return None
    tag_actor(actor, label, True)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(mesh)
        comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        try:
            comp.set_collision_profile_name("BlockAll")
        except Exception:
            pass
    actor.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    try:
        actor.set_actor_hidden_in_game(True)
    except Exception:
        pass
    return actor


def spawn_rock(world, idx, x, y, scale, yaw):
    mesh = load(ROOT + "/Rocks/SM_HampiBoulder_%02d" % (1 + idx % 5))
    if not mesh:
        return None
    z = ground_z(world, x, y) + 5.0
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(x, y, z),
        unreal.Rotator(0.0, 0.0, yaw))
    if not actor:
        return None
    tag_actor(actor, "Task05_TempleGraniteBoulder_%02d" % idx)
    actor.set_folder_path("Hampi/Task05/Virupaksha/Boulders")
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(mesh)
        comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        try:
            comp.set_collision_profile_name("BlockAll")
        except Exception:
            pass
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    return actor


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


def build_road_mesh(world, name, points, width, mat):
    samples = []
    for i in range(len(points) - 1):
        ax, ay = points[i]
        bx, by = points[i + 1]
        length = math.hypot(bx - ax, by - ay)
        count = max(2, int(math.ceil(length / 380.0)))
        for j in range(count):
            if i > 0 and j == 0:
                continue
            t = j / float(count)
            samples.append((ax + (bx - ax) * t, ay + (by - ax) * 0.0 + (by - ay) * t))
    samples.append(points[-1])
    verts, faces = [], []
    for i, (x, y) in enumerate(samples):
        if i == 0:
            dx, dy = samples[1][0] - x, samples[1][1] - y
        elif i == len(samples) - 1:
            dx, dy = x - samples[i - 1][0], y - samples[i - 1][1]
        else:
            dx = samples[i + 1][0] - samples[i - 1][0]
            dy = samples[i + 1][1] - samples[i - 1][1]
        ln = max(0.001, math.hypot(dx, dy))
        px, py = -dy / ln, dx / ln
        z = ground_z(world, x, y) + 6.0
        verts.extend([(x + px * width * 0.5, y + py * width * 0.5, z),
                      (x - px * width * 0.5, y - py * width * 0.5, z)])
    for i in range(len(samples) - 1):
        b = i * 2
        faces.append(("Road", (b, b + 1, b + 3, b + 2)))
    dest = ROOT + "/Task05/Virupaksha/Meshes"
    if not eal.does_directory_exist(dest):
        eal.make_directory(dest)
    path = dest + "/" + name
    mesh = load(path)
    if not mesh:
        mesh = eal.duplicate_asset("/Engine/BasicShapes/Cube", path)
    if not mesh:
        w("ROAD_MESH_CREATE_FAILED=%s" % name)
        return None
    try:
        mesh.set_editor_property("static_materials", [])
    except Exception:
        pass
    slot = mesh.add_material(mat)
    desc = mesh.create_static_mesh_description(mesh)
    desc.empty()
    vids = []
    for p in verts:
        vid = desc.create_vertex()
        desc.set_vertex_position(vid, unreal.Vector(float(p[0]), float(p[1]), float(p[2])))
        vids.append(vid)
    pg = desc.create_polygon_group()
    desc.set_polygon_group_material_slot_name(pg, slot)
    for _mat_name, face in faces:
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
    mesh.build_from_static_mesh_descriptions([desc], True, True)
    try:
        ns = mesh.get_editor_property("nanite_settings")
        ns.enabled = False
        mesh.set_editor_property("nanite_settings", ns)
    except Exception:
        pass
    eal.save_loaded_asset(mesh)
    w("ROAD_MESH_READY %s tris=%d" % (name, desc.get_triangle_count()))
    return mesh


def spawn_road(world, mesh):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if not actor:
        return None
    tag_actor(actor, "Task05_VirupakshaAccessRoad")
    actor.set_folder_path("Hampi/Task05/Virupaksha/Roads")
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(mesh)
        comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        try:
            comp.set_collision_profile_name("NoCollision")
        except Exception:
            pass
    return actor


def create_stone_hism(world):
    mesh = load(ROOT + "/Rocks/SM_SmallGraniteStone")
    if not mesh:
        w("SMALL_STONE_MESH_MISSING")
        return None
    rnd = __import__("random").Random(5104)
    pts = []
    centers = [
        (-46800, 12000), (-46500, 15000), (-45000, 16800), (-42500, 17000),
        (-40500, 16000), (-37500, 15500), (-37800, 11200), (-44500, 10800),
        (-47200, 13800), (-39200, 15000),
    ]
    for cx, cy in centers:
        for _ in range(6):
            a = rnd.uniform(0.0, 2.0 * math.pi)
            r = rnd.uniform(180.0, 1100.0)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if not actor:
        w("STONE_HISM_ACTOR_FAILED")
        return None
    tag_actor(actor, "Task05_VirupakshaSmallStones")
    actor.set_folder_path("Hampi/Task05/Virupaksha/Boulders")
    comp = unreal.HierarchicalInstancedStaticMeshComponent(actor)
    try:
        comp.register_component()
    except Exception:
        pass
    comp.set_static_mesh(mesh)
    actor.set_editor_property("root_component", comp)
    comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    try:
        comp.set_collision_profile_name("NoCollision")
    except Exception:
        pass
    try:
        comp.set_editor_property("instance_start_cull_distance", 1800.0)
        comp.set_editor_property("instance_end_cull_distance", 10000.0)
    except Exception:
        pass
    for i, (x, y) in enumerate(pts):
        z = ground_z(world, x, y) + 5.0
        s = rnd.uniform(0.7, 1.7)
        rot = unreal.Rotator(0.0, 0.0, rnd.uniform(0.0, 360.0))
        comp.add_instance(unreal.Transform(unreal.Vector(x, y, z), rot,
                                           unreal.Vector(s, s, s)))
    w("STONE_HISM_INSTANCES=%d" % len(pts))
    return actor


def main():
    unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    cleanup(world)
    placed = 0

    # Primary landmark geometry.
    visual_specs = [
        ("SM_T05_VirupakshaGopuram", "Task05_Virupaksha_Gopuram", 0, 0, 0.0, 0.0),
        ("SM_T05_VirupakshaMandapa", "Task05_Virupaksha_PillaredMandapa", 200, 0, 0.0, 0.0),
        ("SM_T05_VirupakshaSanctum", "Task05_Virupaksha_Sanctum", -1850, 0, 0.0, 0.0),
        ("SM_T05_VirupakshaTank", "Task05_Virupaksha_TempleTank", 4300, -1800, 0.0, 0.0),
    ]
    for mesh_name, label, lx, ly, zo, yaw in visual_specs:
        if spawn_visual(world, mesh_name, label, lx, ly, zo, yaw):
            placed += 1

    # Smaller shrines around the courtyard.
    shrine_sites = [
        (-1900, 1250), (-1000, 1250), (500, 1250),
        (-1900, -1250), (-1000, -1250), (500, -1250),
    ]
    for i, (lx, ly) in enumerate(shrine_sites, 1):
        if spawn_visual(world, "SM_T05_VirupakshaSubShrine",
                        "Task05_Virupaksha_SubShrine_%02d" % i, lx, ly):
            placed += 1

    # Cloisters inside the courtyard side walls.
    cloister_sites = []
    for lx in [-1600, -600, 400, 1400]:
        cloister_sites.append((lx, 1470, 0.0))
        cloister_sites.append((lx, -1470, 180.0))
    for i, (lx, ly, yaw) in enumerate(cloister_sites, 1):
        if spawn_visual(world, "SM_T05_VirupakshaCloister",
                        "Task05_Virupaksha_Cloister_%02d" % i, lx, ly, 0.0, yaw):
            placed += 1

    # Outer courtyard wall segments.
    wall_sites = []
    for lx in [-2000, -1000, 0, 1000]:
        wall_sites.append((lx, 1750, 0.0))
        wall_sites.append((lx, -1750, 0.0))
    wall_sites.extend([(2050, 1650, 90.0), (2050, -1650, 90.0)])
    for i, (lx, ly, yaw) in enumerate(wall_sites, 1):
        if spawn_visual(world, "SM_T05_VirupakshaCourtyardWall",
                        "Task05_Virupaksha_CourtyardWall_%02d" % i, lx, ly, 0.0, yaw):
            placed += 1

    # Hampi Bazaar-inspired street east of the gopuram.
    shop_sites = []
    for lx in [4200, 5200, 6200, 7200, 8200]:
        shop_sites.append((lx, 720, 0.0))
        shop_sites.append((lx, -720, 180.0))
    for i, (lx, ly, yaw) in enumerate(shop_sites, 1):
        if spawn_visual(world, "SM_T05_HampiBazaarShop",
                        "Task05_HampiBazaarShop_%02d" % i, lx, ly, 0.0, yaw):
            placed += 1

    # Access road and bazaar path, connected to the existing Hampi road node.
    road_mat = load(ROOT + "/Materials/M_HampiDirtRoad_Mobile")
    road_points = [
        (-43000.0, 9000.0), (-41000.0, 10500.0), (-39000.0, 12000.0),
        (-39000.0, 13500.0), (-40500.0, 13500.0), (-38000.0, 13500.0),
    ]
    road_mesh = build_road_mesh(world, "SM_T05_TempleAccessRoad", road_points, 520.0, road_mat)
    if road_mesh and spawn_road(world, road_mesh):
        placed += 1

    # Granite boulders and small stones around the dry temple landscape.
    rock_sites = [
        (-46800, 12000, 1.7, 15), (-46500, 15000, 2.1, 75),
        (-45000, 16800, 1.5, 130), (-42500, 17000, 1.9, 40),
        (-40500, 16000, 1.4, 165), (-37500, 15500, 1.8, 25),
        (-37800, 11200, 1.6, 95), (-44500, 10800, 1.3, 60),
        (-47200, 13800, 2.0, 110), (-39200, 15000, 1.2, 200),
    ]
    for i, (x, y, s, yaw) in enumerate(rock_sites, 1):
        if spawn_rock(world, i, x, y, s, yaw):
            placed += 1
    if create_stone_hism(world):
        placed += 1

    # Hidden collision proxies aligned with visible stonework. These make the
    # temple solid for exploration without making the sacred mesh destructible.
    proxy_count = 0
    spawn_proxy(world, "Task05_Collision_GopuramPylon_S", 2720, -830, 590, 900, 900, 1180)
    spawn_proxy(world, "Task05_Collision_GopuramPylon_N", 2720, 830, 590, 900, 900, 1180)
    proxy_count += 2
    for lx in [-2000, -1000, 0, 1000]:
        spawn_proxy(world, "Task05_Collision_WallN_%d" % (lx + 4000), lx, 1750, 235, 1000, 140, 470)
        spawn_proxy(world, "Task05_Collision_WallS_%d" % (lx + 4000), lx, -1750, 235, 1000, 140, 470)
        proxy_count += 2
    for ix in range(7):
        for iy in range(5):
            lx = 200 + (-1030 + ix * 343)
            ly = -680 + iy * 340
            spawn_proxy(world, "Task05_Collision_MandapaColumn_%02d_%02d" % (ix + 1, iy + 1),
                        lx, ly, 350, 88, 88, 560)
            proxy_count += 1
    spawn_proxy(world, "Task05_Collision_SanctumBack", -1850 - 650, 0, 490, 130, 1300, 900)
    spawn_proxy(world, "Task05_Collision_SanctumN", -1850, 650, 490, 1300, 130, 900)
    spawn_proxy(world, "Task05_Collision_SanctumS", -1850, -650, 490, 1300, 130, 900)
    proxy_count += 3
    for i, (lx, ly) in enumerate(shrine_sites, 1):
        spawn_proxy(world, "Task05_Collision_SubShrine_%02d" % i, lx, ly, 320, 580, 580, 560)
        proxy_count += 1
    for i, (lx, ly, _yaw) in enumerate(shop_sites, 1):
        spawn_proxy(world, "Task05_Collision_BazaarShop_%02d" % i, lx, ly, 235, 600, 500, 430)
        proxy_count += 1

    w("VISUAL_AND_SUPPORT_ACTORS=%d" % placed)
    w("COLLISION_PROXIES=%d" % proxy_count)
    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    w("LEVEL_SAVED=%s" % saved)
    w("VIRUPAKSHA_PLACEMENT_DONE")


try:
    main()
except Exception as e:
    w("VIRUPAKSHA_PLACEMENT_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK05_VIRUPAKSHA_PLACEMENT_WRITTEN")
