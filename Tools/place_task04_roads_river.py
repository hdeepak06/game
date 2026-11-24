import os
import sys
import math
import random
import unreal

sys.path.insert(0, os.path.dirname(__file__))
import task04_layout as layout

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "Task04FullAudit", "roads_river_placement.txt")
MAP = "/Game/Maps/LV_HampiBattleground"
ROOT = "/Game/Environment"
ROAD_TAG = "Task04_Roads"
RIVER_TAG = "Task04_River"
lines = []


def w(s=""):
    lines.append(str(s))


eal = unreal.EditorAssetLibrary


def ensure_dir(path):
    if not eal.does_directory_exist(path):
        eal.make_directory(path)


def load(path):
    return eal.load_asset(path)


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
    eal.save_loaded_asset(mesh)
    w("MESH_READY %s verts=%d tris=%d" % (name, desc.get_vertex_count(), tris))
    return mesh


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


def sample_polyline(points, step=380.0):
    out = []
    for i in range(len(points) - 1):
        ax, ay = points[i]
        bx, by = points[i + 1]
        length = math.hypot(bx - ax, by - ay)
        count = max(2, int(math.ceil(length / step)))
        for j in range(count):
            if i > 0 and j == 0:
                continue
            t = j / float(count)
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    out.append(points[-1])
    return out


def normals_for(samples):
    out = []
    for i, (x, y) in enumerate(samples):
        ax, ay = samples[max(0, i - 1)]
        bx, by = samples[min(len(samples) - 1, i + 1)]
        dx, dy = bx - ax, by - ay
        length = max(0.001, math.hypot(dx, dy))
        out.append((-dy / length, dx / length))
    return out


def add_strip(verts, faces, slot, samples, normals, width, z_offset, offset_center=0.0):
    base = len(verts)
    for (x, y), (nx, ny) in zip(samples, normals):
        cx, cy = x + nx * offset_center, y + ny * offset_center
        zl = ground_z(world, cx + nx * width / 2, cy + ny * width / 2) + z_offset
        zr = ground_z(world, cx - nx * width / 2, cy - ny * width / 2) + z_offset
        verts.append((cx + nx * width / 2, cy + ny * width / 2, zl))
        verts.append((cx - nx * width / 2, cy - ny * width / 2, zr))
    for i in range(len(samples) - 1):
        a = base + i * 2
        faces.append((slot, (a, a + 1, a + 3, a + 2)))


def cleanup(tag):
    removed = 0
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if tag in [str(t) for t in actor.tags]:
            if unreal.EditorLevelLibrary.destroy_actor(actor):
                removed += 1
    w("OLD_ACTORS_REMOVED %s=%d" % (tag, removed))


def spawn_mesh(mesh, label, tag, folder, no_collision=True):
    if not mesh:
        return None
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if not actor:
        return None
    actor.set_actor_label(label)
    actor.set_folder_path(folder)
    actor.tags = [unreal.Name(tag)]
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(mesh)
        if no_collision:
            try:
                comp.set_collision_profile_name("NoCollision")
            except Exception:
                try:
                    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                except Exception:
                    pass
    return actor


def make_transform(x, y, z, yaw, scale):
    return unreal.Transform(
        location=unreal.Vector(float(x), float(y), float(z)),
        rotation=unreal.Rotator(0.0, 0.0, float(yaw)),
        scale=unreal.Vector(float(scale), float(scale), float(scale)))


def make_stone_group(label, mesh_path, points, cull_start, cull_end, scale_range):
    mesh = load(mesh_path)
    if not mesh:
        w("STONE_GROUP_MISSING=%s" % mesh_path)
        return 0
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    actor.set_folder_path("Hampi/Task04/River")
    actor.tags = [unreal.Name(RIVER_TAG)]
    comp = unreal.HierarchicalInstancedStaticMeshComponent(actor)
    if not comp:
        return 0
    try:
        comp.register_component()
    except Exception:
        pass
    comp.set_static_mesh(mesh)
    actor.set_editor_property("root_component", comp)
    try:
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:
        pass
    try:
        comp.set_cull_distances(float(cull_start), float(cull_end))
    except Exception:
        pass
    rnd = random.Random(abs(hash(label)) % 100000)
    transforms = []
    for x, y in points:
        transforms.append(make_transform(x, y, ground_z(world, x, y) + 2.0,
                                        rnd.uniform(0, 360), rnd.uniform(scale_range[0], scale_range[1])))
    count = 0
    try:
        comp.add_instances(transforms, False, True, False)
        count = comp.get_instance_count()
    except Exception:
        for t in transforms:
            try:
                comp.add_instance(t, True)
                count += 1
            except Exception:
                pass
    w("STONE_GROUP %s instances=%d" % (label, count))
    return count


def build_road_meshes():
    dirt = load(ROOT + "/Materials/M_HampiDirtRoad_Mobile")
    gravel = load(ROOT + "/Materials/M_HampiGravelRoad_Mobile")
    for name, points, width, kind in layout.ROADS:
        safe_name = "".join(c if c.isalnum() else "_" for c in name)
        verts, faces = [], []
        samples = sample_polyline(points, 420.0 if width > 300 else 300.0)
        normals = normals_for(samples)
        add_strip(verts, faces, "Shoulder", samples, normals, width + 320.0, 2.0)
        add_strip(verts, faces, "Road", samples, normals, width, 5.0)
        if width > 300:
            add_strip(verts, faces, "Track", samples, normals, width * 0.10, 7.5, width * 0.22)
            add_strip(verts, faces, "Track", samples, normals, width * 0.10, 7.5, -width * 0.22)
        mesh = build_static_mesh("SM_Road_" + safe_name, "Terrain", verts, faces,
                                 [("Shoulder", gravel), ("Road", dirt if kind == "dirt" else gravel), ("Track", gravel)])
        if spawn_mesh(mesh, "Hampi_Full_Road_" + name, ROAD_TAG, "Hampi/Task04/Roads"):
            w("ROAD_PLACED %s width=%d samples=%d" % (name, width, len(samples)))


def build_river():
    sand = load(ROOT + "/Materials/M_HampiSand_Mobile")
    water = load(ROOT + "/Materials/M_HampiWater_Mobile")
    gravel = load(ROOT + "/Materials/M_HampiGravelRoad_Mobile")
    samples = sample_polyline(layout.RIVER_CENTERLINE, 420.0)
    normals = normals_for(samples)
    verts, faces = [], []

    # Sandbanks and water share the same sampled centerline.
    add_strip(verts, faces, "Sand", samples, normals, 780.0, 3.0, layout.RIVER_WIDTH * 0.5 + 390.0)
    add_strip(verts, faces, "Sand", samples, normals, 780.0, 3.0, -layout.RIVER_WIDTH * 0.5 - 390.0)
    add_strip(verts, faces, "Bank", samples, normals, 420.0, 2.0, layout.RIVER_WIDTH * 0.5 + 120.0)
    add_strip(verts, faces, "Bank", samples, normals, 420.0, 2.0, -layout.RIVER_WIDTH * 0.5 - 120.0)

    z_samples = [ground_z(world, x, y) for x, y in samples]
    water_z = max(z_samples) + 11.0
    base = len(verts)
    for (x, y), (nx, ny) in zip(samples, normals):
        verts.append((x + nx * layout.RIVER_WIDTH / 2, y + ny * layout.RIVER_WIDTH / 2, water_z))
        verts.append((x - nx * layout.RIVER_WIDTH / 2, y - ny * layout.RIVER_WIDTH / 2, water_z))
    for i in range(len(samples) - 1):
        a = base + i * 2
        faces.append(("Water", (a, a + 1, a + 3, a + 2)))
    mesh = build_static_mesh("SM_TungabhadraRiverStrip", "Terrain", verts, faces,
                             [("Sand", sand), ("Bank", gravel), ("Water", water)])
    if spawn_mesh(mesh, "Hampi_Full_River_Tungabhadra", RIVER_TAG, "Hampi/Task04/River"):
        w("RIVER_PLACED surface_z=%.2f" % water_z)

    # Rocks and gravel along both banks.
    rnd = random.Random(841)
    large, small = [], []
    for i in range(72):
        seg = rnd.randint(0, len(layout.RIVER_CENTERLINE) - 2)
        ax, ay = layout.RIVER_CENTERLINE[seg]
        bx, by = layout.RIVER_CENTERLINE[seg + 1]
        t = rnd.random()
        x = ax + (bx - ax) * t
        y = ay + (by - ay) * t
        side = 1 if i % 2 == 0 else -1
        offset = side * (layout.RIVER_WIDTH * 0.5 + rnd.uniform(120, 900))
        nx, ny = normals_for([(x, y), (bx, by)])[0]
        px, py = x + nx * offset, y + ny * offset
        (large if i % 3 == 0 else small).append((px, py))
    for idx, (x, y) in enumerate(large):
        mesh_path = ROOT + "/Rocks/SM_HampiBoulder_%02d" % (1 + idx % 5)
        rock = load(mesh_path)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(x, y, ground_z(world, x, y) + 4),
            unreal.Rotator(0, 0, rnd.uniform(0, 360)))
        actor.set_actor_label("Hampi_Full_RiverBoulder_%02d" % idx)
        actor.set_folder_path("Hampi/Task04/River")
        actor.tags = [unreal.Name(RIVER_TAG)]
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            comp.set_static_mesh(rock)
            try:
                comp.set_collision_profile_name("BlockAll")
            except Exception:
                pass
            s = rnd.uniform(0.45, 0.85)
            actor.set_actor_scale3d(unreal.Vector(s, s, s * 0.75))
    w("RIVER_BOULDERS_PLACED=%d" % len(large))
    make_stone_group("Hampi_Full_RiverSmallStones", ROOT + "/Rocks/SM_SmallGraniteStone",
                     small, 1800, 10000, (0.55, 1.25))


def main():
    global world
    unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    cleanup(ROAD_TAG)
    cleanup(RIVER_TAG)
    build_road_meshes()
    build_river()
    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    w("LEVEL_SAVED=%s" % saved)
    w("ROADS_RIVER_DONE")


try:
    main()
except Exception as e:
    w("ROADS_RIVER_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK04_ROADS_RIVER_WRITTEN")
