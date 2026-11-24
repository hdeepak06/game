import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
BP_PATH = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"
SOLDIER_MESH = "/Game/Characters/Soldier/SKM_HampiSoldier"
BLENDSPACE = "/Game/Characters/Soldier/Animations/BS_SoldierLocomotion"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "character_swap_report.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def set_prop(obj, names, value, label):
    for name in names:
        try:
            obj.set_editor_property(name, value)
            w("%s SET %s=%s" % (label, name, value))
            return True
        except Exception as e:
            w("%s TRY %s ERR=%s" % (label, name, str(e)[:120]))
    return False


def main():
    w("CHARACTER_SWAP_BEGIN")
    eal = unreal.EditorAssetLibrary
    bp = eal.load_asset(BP_PATH)
    mesh = eal.load_asset(SOLDIER_MESH)
    bs = eal.load_asset(BLENDSPACE)
    if not (bp and mesh and bs):
        raise RuntimeError("missing blueprint, soldier mesh, or blend space")

    try:
        unreal.load_module("Battleground")
        w("MODULE_LOADED")
    except Exception as e:
        w("MODULE_LOAD_ERR=%s" % e)

    new_class = None
    for cls_path in ["/Script/Battleground.HampiSoldierCharacter",
                     "/Script/Battleground.Default__HampiSoldierCharacter"]:
        try:
            new_class = unreal.load_class(None, cls_path)
            if new_class:
                break
        except Exception:
            pass
    if not new_class:
        new_class = getattr(unreal, "HampiSoldierCharacter", None)
    w("NEW_CLASS=%s" % new_class)
    if not new_class:
        raise RuntimeError("native HampiSoldierCharacter class unavailable")

    try:
        unreal.BlueprintEditorLibrary.reparent_blueprint(bp, new_class)
        w("REPARENT_OK")
    except Exception as e:
        w("REPARENT_ERR=%s" % e)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    w("CDO=%s" % cdo)

    mesh_comps = cdo.get_components_by_class(unreal.SkeletalMeshComponent)
    w("MESH_COMPONENTS=%d" % len(mesh_comps))
    if not mesh_comps:
        raise RuntimeError("no skeletal mesh component on character")
    mesh_comp = mesh_comps[0]
    w("BEFORE_MESH=%s ANIM_CLASS=%s TRANSFORM=%s" % (
        mesh_comp.get_editor_property("skeletal_mesh_asset"),
        mesh_comp.get_editor_property("anim_class"),
        mesh_comp.get_relative_transform()))

    mesh_comp.set_editor_property("skeletal_mesh_asset", mesh)
    mesh_comp.set_editor_property("anim_class", None)
    mesh_comp.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)

    set_prop(cdo, ["locomotion_asset"], bs, "CDO")
    set_prop(cdo, ["max_locomotion_speed"], 450.0, "CDO")
    for name in ["b_drive_locomotion_animation", "drive_locomotion_animation"]:
        if set_prop(cdo, [name], True, "CDO"):
            break

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    eal.save_loaded_asset(bp)

    cdo2 = unreal.get_default_object(bp.generated_class())
    comp2 = cdo2.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    w("AFTER_MESH=%s" % comp2.get_editor_property("skeletal_mesh_asset"))
    w("AFTER_ANIM_CLASS=%s" % comp2.get_editor_property("anim_class"))
    w("AFTER_ANIM_MODE=%s" % comp2.get_editor_property("animation_mode"))
    for name in ["locomotion_asset", "max_locomotion_speed", "b_drive_locomotion_animation",
                 "drive_locomotion_animation"]:
        try:
            w("AFTER_CDO %s=%s" % (name, cdo2.get_editor_property(name)))
        except Exception as e:
            w("AFTER_CDO %s ERR=%s" % (name, str(e)[:100]))
    w("CHARACTER_SWAP_DONE")


try:
    main()
except Exception as e:
    w("CHARACTER_SWAP_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("CHARACTER_SWAP_WRITTEN")
