import os
import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\AI\baseline.txt"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


try:
    unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTOR_COUNT=%d" % len(actors))
    nav_volumes = [a for a in actors if isinstance(a, unreal.NavMeshBoundsVolume)]
    w("NAV_VOLUME_COUNT=%d" % len(nav_volumes))
    for a in nav_volumes:
        w("  NAV=%s loc=%s scale=%s" % (
            a.get_path_name(), a.get_actor_location(), a.get_actor_scale3d()))
    w("AI_CONTROLLER_COUNT=%d" % len([a for a in actors if isinstance(a, unreal.AIController)]))
    w("CHARACTER_COUNT=%d" % len([a for a in actors if isinstance(a, unreal.Character)]))

    mat = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Soldier/Materials/M_HampiSoldier")
    w("SOLDIER_MATERIAL=%s" % mat)
    if mat:
        try:
            names = [str(n) for n in unreal.MaterialEditingLibrary.get_vector_parameter_names(mat)]
            w("VECTOR_PARAMS=%s" % names)
        except Exception as e:
            w("VECTOR_PARAMS_ERR=%s" % e)
        try:
            names = [str(n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat)]
            w("SCALAR_PARAMS=%s" % names)
        except Exception as e:
            w("SCALAR_PARAMS_ERR=%s" % e)

    bs = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Soldier/Animations/BS_SoldierLocomotion")
    w("BLEND_SPACE=%s" % bs)
except Exception as e:
    w("AUDIT_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("AI_BASELINE_WRITTEN")
