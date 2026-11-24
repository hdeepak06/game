import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\bp_mesh_defaults.txt"
lines = []


def w(s=""):
    lines.append(str(s))


bp = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
cdo = unreal.get_default_object(bp.generated_class())
w("CDO=%s" % cdo)
for comp in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
    w("MESH_COMP=%s" % comp.get_path_name())
    for p in ["skeletal_mesh_asset", "anim_class", "animation_mode", "animation_asset",
              "override_animation_data", "play_rate", "min_lod", "visibility_based_update",
              "update_animation_in_editor"]:
        try:
            w("  %s=%s" % (p, comp.get_editor_property(p)))
        except Exception as e:
            w("  %s ERR=%s" % (p, str(e)[:100]))
    w("  COMPONENT_TAGS=%s" % comp.get_editor_property("component_tags"))

for p in ["locomotion_asset", "max_locomotion_speed", "b_drive_locomotion_animation"]:
    try:
        w("CDO_PROP %s=%s" % (p, cdo.get_editor_property(p)))
    except Exception as e:
        w("CDO_PROP %s ERR=%s" % (p, str(e)[:100]))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("BP_MESH_DEFAULTS_WRITTEN")
