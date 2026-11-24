import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "WeaponM416", "place_pickup.txt")
MAP = "/Game/Maps/LV_HampiBattleground"
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


try:
    w("PLACE_M416_BEGIN")
    unreal.load_module("Battleground")
    cls = getattr(unreal, "M416Weapon", None)
    if not cls:
        cls = unreal.load_class(None, "/Script/Battleground.M416Weapon")
    w("M416_CLASS=%s" % cls)
    if not cls:
        raise RuntimeError("M416Weapon class unavailable")

    unreal.EditorLevelLibrary.load_level(MAP)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTOR_COUNT_BEFORE=%d" % len(actors))

    existing = [a for a in actors if isinstance(a, cls)]
    w("M416_ACTOR_COUNT_BEFORE=%d" % len(existing))
    if existing:
        for a in existing:
            w("EXISTING=%s loc=%s" % (a.get_path_name(), a.get_actor_location()))
    else:
        starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
        if not starts:
            raise RuntimeError("no PlayerStart found")
        start = starts[0]
        start_loc = start.get_actor_location()
        w("PLAYER_START=%s rot=%s" % (start_loc, start.get_actor_rotation()))

        # About 2.2 m from the spawn, close enough for the E-key fallback and
        # one short walk for the proximity pickup. No existing actor is moved.
        loc = unreal.Vector(start_loc.x + 200.0, start_loc.y + 100.0, start_loc.z - 20.0)
        rot = unreal.Rotator(0.0, 15.0, 0.0)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            cls, loc, rot, transient=False)
        if not actor:
            raise RuntimeError("M416 pickup spawn failed")
        actor.set_actor_label("M416_Pickup")
        try:
            actor.set_editor_property(
                "tags", [unreal.Name("M416"), unreal.Name("WeaponPickup")])
        except Exception as e:
            w("TAG_ERR=%s" % e)
        w("SPAWNED=%s loc=%s rot=%s" % (
            actor.get_path_name(), actor.get_actor_location(), actor.get_actor_rotation()))

    actors_after = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTOR_COUNT_AFTER=%d" % len(actors_after))
    w("M416_ACTOR_COUNT_AFTER=%d" % len([a for a in actors_after if isinstance(a, cls)]))

    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    w("SAVE_RESULT=%s" % saved)
    w("PLACE_M416_DONE")
except Exception as e:
    w("PLACE_M416_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("M416_PICKUP_WRITTEN")
