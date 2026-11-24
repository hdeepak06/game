import os
import sys
import random
import unreal

sys.path.insert(0, os.path.dirname(__file__))
import task04_layout as layout

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "Task04FullAudit", "vegetation_placement.txt")
MAP = "/Game/Maps/LV_HampiBattleground"
ROOT = "/Game/Environment/Vegetation"
TAG = "Task04_Vegetation"
lines = []


def w(s=""):
    lines.append(str(s))


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
    w("OLD_VEGETATION_REMOVED=%d" % removed)


def make_transform(x, y, z, yaw, scale):
    return unreal.Transform(
        location=unreal.Vector(float(x), float(y), float(z)),
        rotation=unreal.Rotator(0.0, 0.0, float(yaw)),
        scale=unreal.Vector(float(scale), float(scale), float(scale)))


def create_hism_group(world, label, mesh_path, points, cull_start, cull_end, scale_range):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        w("VEG_MESH_MISSING=%s" % mesh_path)
        return False
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if not actor:
        w("VEG_ACTOR_FAILED=%s" % label)
        return False
    actor.set_actor_label(label)
    actor.set_folder_path("Hampi/Task04/Vegetation")
    actor.tags = [unreal.Name(TAG)]
    comp = unreal.HierarchicalInstancedStaticMeshComponent(actor)
    if not comp:
        w("HISM_FAILED=%s" % label)
        return False
    try:
        comp.register_component()
    except Exception:
        pass
    comp.set_static_mesh(mesh)
    actor.set_editor_property("root_component", comp)
    try:
        comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    except Exception:
        pass
    try:
        comp.set_editor_property("component_tags", [unreal.Name(TAG)])
    except Exception:
        pass
    try:
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:
        pass
    try:
        comp.set_cull_distances(float(cull_start), float(cull_end))
    except Exception:
        pass
    transforms = []
    rnd = random.Random(abs(hash(label)) % 100000)
    for x, y in points:
        z = ground_z(world, x, y) + 2.0
        s = rnd.uniform(scale_range[0], scale_range[1])
        transforms.append(make_transform(x, y, z, rnd.uniform(0, 360), s))
    added = 0
    try:
        comp.add_instances(transforms, False, True, False)
        added = comp.get_instance_count()
    except Exception as e:
        w("HISM_BULK_WARN %s %s" % (label, e))
        for t in transforms:
            try:
                comp.add_instance(t, True)
                added += 1
            except Exception:
                pass
    w("HISM_GROUP %s instances=%d mesh=%s cull=%d..%d" % (
        label, added, mesh.get_name(), cull_start, cull_end))
    return added > 0


def river_bank_points(seed, offset, count):
    rnd = random.Random(seed)
    pts = []
    line = layout.RIVER_CENTERLINE
    for i in range(count):
        seg = rnd.randint(0, len(line) - 2)
        ax, ay = line[seg]
        bx, by = line[seg + 1]
        t = rnd.random()
        x = ax + (bx - ax) * t
        y = ay + (by - ay) * t
        pts.append((x + rnd.uniform(-250, 250), y + offset + rnd.uniform(-260, 260)))
    return pts


def main():
    unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    cleanup(world)

    groups = [
        ("CoconutPalms", "SM_CoconutPalm", 46, [("Kamalapur", 24, 1), ("River", 22, 1)], 7000, 30000, (0.85, 1.20)),
        ("DatePalms", "SM_DatePalm", 26, [("River", 16, 1), ("Hosapete", 10, 1)], 7000, 30000, (0.85, 1.15)),
        ("NeemTrees", "SM_NeemTree", 56, [("Kamalapur", 24, 2), ("Anjanadri", 18, 3), ("Hosapete", 14, 4)], 8000, 34000, (0.80, 1.25)),
        ("BanyanTrees", "SM_BanyanTree", 12, [("Kamalapur", 7, 5), ("Anjanadri", 5, 6)], 9000, 36000, (0.85, 1.18)),
        ("TamarindTrees", "SM_TamarindTree", 34, [("Kamalapur", 14, 7), ("Anjanadri", 10, 8), ("Hosapete", 10, 9)], 7000, 30000, (0.82, 1.18)),
        ("AcaciaTrees", "SM_AcaciaTree", 52, [("Hampi", 24, 10), ("Military", 16, 11), ("Anjanadri", 12, 12)], 8000, 32000, (0.78, 1.16)),
        ("DryRegionTrees", "SM_DryRegionTree", 36, [("Hampi", 22, 13), ("Military", 14, 14)], 8000, 32000, (0.80, 1.15)),
        ("GreenBushes", "SM_GreenBush", 96, [("Kamalapur", 34, 15), ("Anjanadri", 24, 16), ("River", 22, 17), ("Hosapete", 16, 18)], 3000, 16000, (0.75, 1.35)),
        ("DryShrubs", "SM_DryShrub", 78, [("Hampi", 36, 19), ("Military", 24, 20), ("Hosapete", 18, 21)], 3000, 16000, (0.75, 1.30)),
        ("GrassTufts", "SM_GrassTuft", 150, [("Kamalapur", 55, 22), ("Anjanadri", 45, 23), ("Hosapete", 30, 24), ("River", 20, 25)], 1800, 10000, (0.70, 1.35)),
        ("DryGrassTufts", "SM_DryGrassTuft", 170, [("Hampi", 65, 26), ("Military", 50, 27), ("Kamalapur", 30, 28), ("Hosapete", 25, 29)], 1800, 10000, (0.70, 1.35)),
    ]
    total = 0
    for label, mesh_name, _count, region_spec, c0, c1, scale_range in groups:
        pts = []
        for region, count, seed in region_spec:
            pts.extend(layout.scatter_points(region, count, seed, 7600, 7200, True))
        if create_hism_group(world, "Hampi_Full_Veg_" + label, ROOT + "/" + mesh_name,
                             pts, c0, c1, scale_range):
            total += len(pts)
    reeds = river_bank_points(99, 1650, 50) + river_bank_points(199, -1650, 50)
    if create_hism_group(world, "Hampi_Full_Veg_RiversideReeds", ROOT + "/SM_RiversideReeds",
                         reeds, 2200, 12000, (0.80, 1.25)):
        total += len(reeds)
    w("VEGETATION_INSTANCES_TOTAL=%d" % total)
    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    w("LEVEL_SAVED=%s" % saved)
    w("VEGETATION_DONE")


try:
    main()
except Exception as e:
    w("VEGETATION_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK04_VEGETATION_WRITTEN")
