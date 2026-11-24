import os
import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\native_autoload.txt"
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


try:
    w("BEGIN")
    w("PYTHON_CLASS=%s" % getattr(unreal, "HampiSoldierCharacter", None))

    bp = unreal.EditorAssetLibrary.load_asset(
        "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    w("BP=%s" % bp)
    if not bp:
        raise RuntimeError("BP failed to load")

    cls = bp.generated_class()
    w("BP_CLASS=%s" % cls)
    cdo = unreal.get_default_object(cls)
    w("CDO=%s" % cdo)

    try:
        w("IS_NATIVE_SOLDIER=%s" % isinstance(cdo, unreal.HampiSoldierCharacter))
    except Exception as e:
        w("IS_NATIVE_SOLDIER_ERR=%s" % e)

    for prop in ["locomotion_asset", "max_locomotion_speed", "drive_locomotion_animation"]:
        try:
            w("PROP %s=%s" % (prop, cdo.get_editor_property(prop)))
        except Exception as e:
            w("PROP %s ERR=%s" % (prop, e))

    comp = cdo.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    w("MESH=%s" % comp.get_editor_property("skeletal_mesh_asset"))
    w("ANIM_MODE=%s" % comp.get_editor_property("animation_mode"))

    unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
    w("ACTORS=%d" % len(unreal.EditorLevelLibrary.get_all_level_actors()))
    w("DONE")
except Exception as e:
    w("ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("NATIVE_AUTOLOAD_WRITTEN")
