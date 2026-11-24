import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "WeaponM416", "place_marker.txt")
MAP = "/Game/Maps/LV_HampiBattleground"
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


try:
    w("PLACE_M416_MARKER_BEGIN")
    unreal.EditorLevelLibrary.load_level(MAP)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTOR_COUNT_BEFORE=%d" % len(actors))

    markers = [a for a in actors if a.actor_has_tag(unreal.Name("M416Pickup"))]
    w("M416_MARKER_COUNT_BEFORE=%d" % len(markers))
    for a in markers:
        w("EXISTING_MARKER=%s loc=%s" % (a.get_path_name(), a.get_actor_location()))

    if not markers:
        starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
        if not starts:
            raise RuntimeError("no PlayerStart found")
        start_loc = starts[0].get_actor_location()
        w("PLAYER_START=%s" % start_loc)

        loc = unreal.Vector(start_loc.x + 200.0, start_loc.y + 100.0, start_loc.z - 20.0)
        rot = unreal.Rotator(0.0, 15.0, 0.0)
        marker = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, loc, rot, transient=False)
        if not marker:
            raise RuntimeError("marker spawn failed")

        mesh = unreal.EditorAssetLibrary.load_asset("/Game/Weapons/M416/SM_M416")
        if not mesh:
            raise RuntimeError("SM_M416 asset missing")

        comp = marker.get_component_by_class(unreal.StaticMeshComponent)
        if not comp:
            raise RuntimeError("marker has no StaticMeshComponent")
        comp.set_static_mesh(mesh)
        comp.set_relative_scale3d(unreal.Vector(0.11, 0.11, 0.11))
        try:
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        except Exception as e:
            w("COLLISION_ERR=%s" % e)
        comp.set_cast_shadow(False)

        marker.set_actor_label("M416_Pickup")
        marker.set_editor_property("tags", [unreal.Name("M416Pickup")])
        w("SPAWNED_MARKER=%s loc=%s rot=%s" % (
            marker.get_path_name(), marker.get_actor_location(), marker.get_actor_rotation()))

    actors_after = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTOR_COUNT_AFTER=%d" % len(actors_after))
    w("M416_MARKER_COUNT_AFTER=%d" % len(
        [a for a in actors_after if a.actor_has_tag(unreal.Name("M416Pickup"))]))

    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    w("SAVE_RESULT=%s" % saved)
    w("PLACE_M416_MARKER_DONE")
except Exception as e:
    w("PLACE_M416_MARKER_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("M416_MARKER_WRITTEN")
