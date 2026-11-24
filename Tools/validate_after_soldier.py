import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "structural_validation.txt")
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


try:
    unreal.load_module("Battleground")
    eal = unreal.EditorAssetLibrary
    unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTOR_COUNT=%d" % len(actors))
    landscapes = [a for a in actors if isinstance(a, unreal.Landscape)]
    starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
    w("LANDSCAPE_COUNT=%d PLAYER_START_COUNT=%d" % (len(landscapes), len(starts)))
    for ls in landscapes:
        w("LANDSCAPE %s location=%s scale=%s" % (
            ls.get_path_name(), ls.get_actor_location(), ls.get_actor_scale3d()))

    gm = eal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode")
    w("GAMEMODE=%s" % gm)
    if gm:
        cdo = unreal.get_default_object(gm.generated_class())
        w("DEFAULT_PAWN=%s" % cdo.get_editor_property("default_pawn_class"))

    bp = eal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    cdo = unreal.get_default_object(bp.generated_class())
    w("CHARACTER_CLASS=%s" % cdo.get_class().get_path_name())
    for prop in ["locomotion_asset", "max_locomotion_speed", "drive_locomotion_animation"]:
        try:
            w("CHARACTER_PROP %s=%s" % (prop, cdo.get_editor_property(prop)))
        except Exception as e:
            w("CHARACTER_PROP %s ERR=%s" % (prop, str(e)[:100]))
    mesh_comp = cdo.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    w("PLAYER_MESH=%s" % mesh_comp.get_editor_property("skeletal_mesh_asset"))
    w("PLAYER_ANIM_CLASS=%s" % mesh_comp.get_editor_property("anim_class"))
    w("PLAYER_ANIM_MODE=%s" % mesh_comp.get_editor_property("animation_mode"))
    w("PLAYER_MESH_TRANSFORM=%s" % mesh_comp.get_relative_transform())

    soil = eal.load_asset("/Game/Environment/Materials/M_HampiSoil_Mobile")
    w("SOIL_MATERIAL=%s" % soil)
    if soil:
        mel = unreal.MaterialEditingLibrary
        for prop in [unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialProperty.MP_ROUGHNESS]:
            w("SOIL_INPUT %s=%s" % (prop, mel.get_material_property_input_node(soil, prop)))

    soldier_mat = eal.load_asset("/Game/Characters/Soldier/Materials/M_HampiSoldier")
    w("SOLDIER_MATERIAL=%s" % soldier_mat)
    if soldier_mat:
        mel = unreal.MaterialEditingLibrary
        for prop in [unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialProperty.MP_NORMAL,
                     unreal.MaterialProperty.MP_ROUGHNESS, unreal.MaterialProperty.MP_METALLIC]:
            w("SOLDIER_INPUT %s=%s" % (prop, mel.get_material_property_input_node(soldier_mat, prop)))

    w("VALIDATION_DONE")
except Exception as e:
    w("VALIDATION_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("STRUCTURAL_VALIDATION_WRITTEN")
