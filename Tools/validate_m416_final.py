import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "WeaponM416", "final_validation.txt")
MAP = "/Game/Maps/LV_HampiBattleground"
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


try:
    w("FINAL_VALIDATION_BEGIN")
    eal = unreal.EditorAssetLibrary
    unreal.EditorLevelLibrary.load_level(MAP)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTOR_COUNT=%d" % len(actors))
    w("LANDSCAPE_COUNT=%d" % len([a for a in actors if isinstance(a, unreal.Landscape)]))
    w("PLAYER_START_COUNT=%d" % len([a for a in actors if isinstance(a, unreal.PlayerStart)]))

    for ls in [a for a in actors if isinstance(a, unreal.Landscape)]:
        w("LANDSCAPE=%s loc=%s scale=%s" % (
            ls.get_path_name(), ls.get_actor_location(), ls.get_actor_scale3d()))

    markers = [a for a in actors if a.actor_has_tag(unreal.Name("M416Pickup"))]
    w("M416_MARKER_COUNT=%d" % len(markers))
    for m in markers:
        comp = m.get_component_by_class(unreal.StaticMeshComponent)
        mesh = comp.get_editor_property("static_mesh") if comp else None
        w("M416_MARKER=%s loc=%s rot=%s mesh=%s scale=%s" % (
            m.get_path_name(), m.get_actor_location(), m.get_actor_rotation(),
            mesh.get_path_name() if mesh else None,
            comp.get_editor_property("relative_scale3d") if comp else None))

    missing = []
    mesh_components = 0
    for a in actors:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            mesh_components += 1
            if not comp.get_editor_property("static_mesh"):
                missing.append(comp.get_path_name())
    w("STATIC_MESH_COMPONENTS=%d MISSING_MESHES=%d" % (mesh_components, len(missing)))
    for path in missing[:10]:
        w("  MISSING=%s" % path)

    asset_paths = [
        "/Game/Weapons/M416/SM_M416",
        "/Game/Weapons/M416/Materials/M_M416_Primary",
        "/Game/Weapons/M416/Materials/M_M416_Secondary",
        "/Game/Weapons/M416/Materials/M_M416_Highlight",
        "/Game/Weapons/M416/Materials/M_M416_MuzzleFlash",
        "/Game/Weapons/M416/Audio/S_M416_Fire",
        "/Game/Weapons/M416/Audio/S_M416_Reload",
        "/Game/ThirdPerson/Input/Actions/IA_M416_Fire",
        "/Game/ThirdPerson/Input/Actions/IA_M416_Aim",
        "/Game/ThirdPerson/Input/Actions/IA_M416_Reload",
        "/Game/ThirdPerson/Input/Actions/IA_M416_Pickup",
    ]
    for path in asset_paths:
        w("ASSET %s=%s" % (path, bool(eal.load_asset(path))))

    imc = eal.load_asset("/Game/ThirdPerson/Input/IMC_Default")
    mappings = list(imc.get_editor_property("mappings")) if imc else []
    w("IMC_MAPPINGS=%d" % len(mappings))
    added = {}
    for m in mappings:
        try:
            key = str(m.get_editor_property("key").get_editor_property("key_name"))
            path = m.get_editor_property("action").get_path_name()
            if "IA_M416_" in path:
                added[path.rsplit("/", 1)[-1]] = key
        except Exception:
            pass
    w("M416_INPUT_MAPPINGS=%s" % sorted(added.items()))

    gm = eal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode")
    w("GAMEMODE_ASSET=%s" % gm)
    bp = eal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    w("CHARACTER_BP_ASSET=%s" % bp)
    w("FINAL_VALIDATION_DONE")
except Exception as e:
    w("FINAL_VALIDATION_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("M416_FINAL_VALIDATION_WRITTEN")
