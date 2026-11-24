import os
import sys
import unreal

sys.path.insert(0, os.path.dirname(__file__))
import task04_layout as layout

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "Task04FullAudit", "structures_placement.txt")
MAP = "/Game/Maps/LV_HampiBattleground"
ROOT = "/Game/Environment"
TAG = "Task04_Structures"
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
    w("OLD_STRUCTURES_REMOVED=%d" % removed)


def spawn(world, mesh_path, label, x, y, yaw=0.0, scale=1.0, z_offset=5.0, folder="Hampi/Task04/Structures"):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        w("STRUCTURE_MESH_MISSING=%s" % mesh_path)
        return None
    z = ground_z(world, x, y) + z_offset
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(float(x), float(y), float(z)),
        unreal.Rotator(0.0, 0.0, float(yaw)))
    if not actor:
        w("STRUCTURE_SPAWN_FAILED=%s" % label)
        return None
    actor.set_actor_label(label)
    actor.set_folder_path(folder)
    actor.tags = [unreal.Name(TAG)]
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(mesh)
        comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        try:
            comp.set_collision_profile_name("BlockAll")
        except Exception:
            pass
        try:
            comp.set_editor_property("cast_shadow", True)
        except Exception:
            try:
                comp.set_cast_shadow(True)
            except Exception:
                pass
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    return actor


def main():
    unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    cleanup(world)
    placed = 0

    # Houses, shops, warehouses and barracks.
    for idx, (region, x, y, mesh_name, yaw, scale) in enumerate(layout.absolute_sites(), 1):
        actor = spawn(world, ROOT + "/" + ("Houses/" if "House" in mesh_name or "Shop" in mesh_name or "Warehouse" in mesh_name or "Barracks" in mesh_name else "Houses/") + mesh_name,
                      "Hampi_Full_%s_%02d" % (region, idx), x, y, yaw, scale)
        if actor:
            placed += 1

    # Wells/tanks/ruins/watchtowers.
    for idx, (mesh_name, x, y, yaw, scale) in enumerate(layout.PROP_SITES, 1):
        sub = "Temples" if "Ruin" in mesh_name else "Props"
        actor = spawn(world, ROOT + "/" + sub + "/" + mesh_name,
                      "Hampi_Full_Prop_%02d" % idx, x, y, yaw, scale)
        if actor:
            placed += 1

    # Compound walls and fences.
    for idx, (x, y, yaw, scale) in enumerate(layout.COMPOUND_SITES, 1):
        if spawn(world, ROOT + "/Props/SM_KamalapurCompoundWall",
                 "Hampi_Full_CompoundWall_%02d" % idx, x, y, yaw, scale):
            placed += 1
    for idx, (x, y, yaw, scale) in enumerate(layout.FENCE_SITES, 1):
        if spawn(world, ROOT + "/Props/SM_VillageFence",
                 "Hampi_Full_Fence_%02d" % idx, x, y, yaw, scale):
            placed += 1
    for idx, (x, y, yaw, scale) in enumerate(layout.GATE_SITES, 1):
        if spawn(world, ROOT + "/Props/SM_VillageGate",
                 "Hampi_Full_Gate_%02d" % idx, x, y, yaw, scale):
            placed += 1

    # Hampi stone walls around the ruin cluster.
    for idx, (x, y, yaw, scale) in enumerate([
        (-43600, 10200, 20, 1.0), (-43100, 10400, 20, 1.0),
        (-42600, 10200, 20, 1.0), (-42400, 8200, -70, 1.0),
        (-43800, 7600, 70, 1.0),
    ], 1):
        if spawn(world, ROOT + "/Temples/SM_HampiStoneWall",
                 "Hampi_Full_StoneWall_%02d" % idx, x, y, yaw, scale):
            placed += 1

    # Military training ground cover and targets.
    cover = []
    for i in range(10):
        cover.append((-10000 - 1200 + i * 260, 12000 + 2600, 0.0))
    for idx, (x, y, yaw) in enumerate(cover, 1):
        if spawn(world, ROOT + "/Props/SM_Sandbag",
                 "Hampi_Full_Sandbag_%02d" % idx, x, y, yaw, 1.0):
            placed += 1
    for idx, (x, y, yaw) in enumerate([
        (-10000 - 900, 12000 + 3600, 0.0),
        (-10000 + 200, 12000 + 3600, 0.0),
        (-10000 + 1300, 12000 + 3600, 0.0),
    ], 1):
        if spawn(world, ROOT + "/Props/SM_TargetFrame",
                 "Hampi_Full_Target_%02d" % idx, x, y, yaw, 1.0):
            placed += 1

    w("STRUCTURES_PLACED=%d" % placed)
    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    w("LEVEL_SAVED=%s" % saved)
    w("STRUCTURES_DONE")


try:
    main()
except Exception as e:
    w("STRUCTURES_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK04_STRUCTURES_WRITTEN")
