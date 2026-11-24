import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
BP_PATH = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"
SOLDIER_MESH = "/Game/Characters/Soldier/SKM_HampiSoldier"
BLENDSPACE = "/Game/Characters/Soldier/Animations/BS_SoldierLocomotion"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "reparent_full_editor.txt")


def w(msg, lines):
    lines.append(str(msg))
    unreal.log(str(msg))


lines = []
try:
    unreal.load_module("Battleground")
    eal = unreal.EditorAssetLibrary
    bp = eal.load_asset(BP_PATH)
    mesh = eal.load_asset(SOLDIER_MESH)
    bs = eal.load_asset(BLENDSPACE)
    cls = unreal.load_class(None, "/Script/Battleground.HampiSoldierCharacter")
    w("ASSETS bp=%s mesh=%s bs=%s cls=%s" % (bp, mesh, bs, cls), lines)

    unreal.BlueprintEditorLibrary.reparent_blueprint(bp, cls)
    w("REPARENT_OK", lines)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.BlueprintEditorLibrary.refresh_all_open_blueprint_editors()

    cdo = unreal.get_default_object(bp.generated_class())
    comp = cdo.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    comp.set_editor_property("skeletal_mesh_asset", mesh)
    comp.set_editor_property("anim_class", None)
    comp.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    cdo.set_editor_property("locomotion_asset", bs)
    cdo.set_editor_property("max_locomotion_speed", 450.0)
    cdo.set_editor_property("drive_locomotion_animation", True)
    w("PROPS_SET", lines)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ok = eal.save_asset(BP_PATH, only_if_is_dirty=False)
    w("SAVE_OK=%s" % ok, lines)

    cdo2 = unreal.get_default_object(bp.generated_class())
    comp2 = cdo2.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    w("VERIFY mesh=%s anim=%s mode=%s bs=%s" % (
        comp2.get_editor_property("skeletal_mesh_asset"),
        comp2.get_editor_property("anim_class"),
        comp2.get_editor_property("animation_mode"),
        cdo2.get_editor_property("locomotion_asset")), lines)
    w("FULL_EDITOR_REPARENT_DONE", lines)
except Exception:
    w("FULL_EDITOR_REPARENT_ERROR=%s" % traceback.format_exc(), lines)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass
