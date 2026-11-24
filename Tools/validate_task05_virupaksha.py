import os
import unreal

MAP = "/Game/Maps/LV_HampiBattleground"
OUT = r"C:\UnrealProjects\Battleground\Saved\Task05Audit\validate_virupaksha.txt"
ROOT = "/Game/Environment"
TAG = "Task05_Virupaksha"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))


def tagged(actors, tag):
    return [a for a in actors if tag in [str(t) for t in a.tags]]


def main():
    unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTOR_COUNT=%d" % len(actors))
    w("TAG %s=%d" % (TAG, len(tagged(actors, TAG))))
    for old_tag in ["Task04_Stage1", "Task04_Structures", "Task04_Roads",
                    "Task04_River", "Task04_Vegetation"]:
        w("TAG %s=%d" % (old_tag, len(tagged(actors, old_tag))))

    landscapes = [a for a in actors if isinstance(a, unreal.Landscape)]
    players = [a for a in actors if isinstance(a, unreal.PlayerStart)]
    w("LANDSCAPE_COUNT=%d" % len(landscapes))
    w("PLAYERSTART_COUNT=%d" % len(players))
    if landscapes:
        loc = landscapes[0].get_actor_location()
        w("LANDSCAPE_LOCATION=(%.0f,%.0f,%.0f)" % (loc.x, loc.y, loc.z))

    visual = [a for a in actors if "Task05_Virupaksha" in a.get_actor_label()
              and "Collision" not in a.get_actor_label()]
    proxies = [a for a in actors if a.get_actor_label().startswith("Task05_Collision_")]
    w("VISUAL_LABELS=%d" % len(visual))
    w("COLLISION_PROXIES=%d" % len(proxies))

    gopuram = next((a for a in actors if a.get_actor_label() == "Task05_Virupaksha_Gopuram"), None)
    if gopuram:
        try:
            _origin, extent = gopuram.get_actor_bounds(False)
            w("GOPURAM_BOUNDS_EXTENT=(%.0f,%.0f,%.0f)" % (extent.x, extent.y, extent.z))
            w("GOPURAM_HEIGHT_CM=%.0f" % (extent.z * 2.0))
        except Exception as e:
            w("GOPURAM_BOUNDS_ERR=%s" % e)
        gloc = gopuram.get_actor_location()
        w("GOPURAM_LOCATION=(%.0f,%.0f,%.0f)" % (gloc.x, gloc.y, gloc.z))

    hims_actors = [a for a in actors if a.get_class().get_name() == "Actor"
                   and any(str(t) == TAG for t in a.tags)]
    hism_count = 0
    instances = 0
    for a in hims_actors:
        comps = a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)
        for c in comps:
            hism_count += 1
            instances += c.get_instance_count()
    w("TASK05_HISM_COMPONENTS=%d" % hism_count)
    w("TASK05_HISM_INSTANCES=%d" % instances)

    mesh_paths = [
        "SM_T05_VirupakshaGopuram", "SM_T05_VirupakshaMandapa",
        "SM_T05_VirupakshaSanctum", "SM_T05_VirupakshaSubShrine",
        "SM_T05_VirupakshaCloister", "SM_T05_VirupakshaCourtyardWall",
        "SM_T05_VirupakshaTank", "SM_T05_HampiBazaarShop",
        "SM_T05_TempleAccessRoad",
    ]
    missing = []
    for name in mesh_paths:
        mesh = unreal.EditorAssetLibrary.load_asset(ROOT + "/Task05/Virupaksha/Meshes/" + name)
        if not mesh:
            missing.append(name)
            continue
        tris = 0
        for tri_fn in [
            lambda: mesh.get_num_triangles(0),
            lambda: unreal.EditorStaticMeshLibrary.get_number_triangles(mesh, 0),
        ]:
            try:
                tris = int(tri_fn())
                if tris > 0:
                    break
            except Exception:
                continue
        nanite = False
        try:
            nanite = bool(mesh.get_editor_property("nanite_settings").enabled)
        except Exception:
            pass
        w("TASK05_MESH %s tris=%d nanite=%s" % (name, tris, nanite))
    w("TASK05_MISSING_MESHES=%d %s" % (len(missing), missing))

    # Collision setting spot checks.
    for actor in proxies[:3]:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            hidden = False
            for hidden_fn in [
                lambda: actor.get_actor_hidden_in_game(),
                lambda: bool(actor.get_editor_property("hidden")),
            ]:
                try:
                    hidden = bool(hidden_fn())
                    break
                except Exception:
                    continue
            w("PROXY %s profile=%s hidden=%s" % (
                actor.get_actor_label(), comp.get_collision_profile_name(), hidden))
    for actor in visual[:3]:
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            w("VISUAL %s profile=%s" % (actor.get_actor_label(),
                                        comp.get_collision_profile_name()))

    try:
        unreal.SystemLibrary.execute_console_command(world, "MAP CHECKDEP NOCLEARLOG")
        w("MAPCHECK_CMD_SENT=True")
    except Exception as e:
        w("MAPCHECK_CMD_ERR=%s" % e)
    w("TASK05_VALIDATION_DONE")


try:
    main()
except Exception as e:
    w("TASK05_VALIDATION_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK05_VALIDATION_WRITTEN")
