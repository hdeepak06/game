import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\soldier_import_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def dirs(obj):
    return sorted(m for m in dir(obj) if not m.startswith("__"))


bp = unreal.EditorAssetLibrary.load_asset(
    "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
cdo = unreal.get_default_object(bp.generated_class())
mesh_comp = cdo.get_component_by_class(unreal.SkeletalMeshComponent)
w("--- CHARACTER MESH COMPONENT ---")
for prop in ["animation_mode", "animation_data", "anim_class", "animation_blueprint",
             "skeletal_mesh", "anim_to_play", "enable_per_frame_contact_offset",
             "use_bone_followers_for_lower_body", "visibility_based_update",
             "update_animation_in_editor"]:
    try:
        val = mesh_comp.get_editor_property(prop)
        w("%s=%s" % (prop, val.get_path_name() if hasattr(val, "get_path_name") else val))
    except Exception as e:
        w("%s=ERR:%s" % (prop, e))
w("MESH_COMP_METHODS=%s" % ",".join(
    m for m in dirs(mesh_comp) if any(k in m.lower() for k in
    ["anim", "mesh", "lod", "material"])))

w("--- ANIMATION ASSETS IN PROJECT ---")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/Game", recursive=True)
for a in assets:
    cls = str(a.asset_class_path.asset_name)
    if any(k in cls for k in ["AnimBlueprint", "AnimSequence", "BlendSpace", "Skeleton", "IK"]):
        w("ASSET %s.%s class=%s" % (a.package_name, a.asset_name, cls))

w("--- IMPORT / LOD / TEXTURE API ---")
for name in ["FbxImportUI", "FbxMeshImportData", "FbxAnimSequenceImportData",
             "FbxTextureImportData", "SkeletalMeshImportData", "SkeletalMeshEditorSubsystem",
             "TextureEditorSubsystem", "EditorAssetSubsystem", "AssetImportTask",
             "SkeletalMeshLODSettings", "SkeletalMeshLODGroupSettings",
             "AnimationBlueprintLibrary", "AnimBlueprintFactory"]:
    obj = getattr(unreal, name, None)
    w("CLASS %s exists=%s" % (name, bool(obj)))
    if obj:
        try:
            props = [p for p in dirs(obj) if not p.startswith("_")]
            w("  %s" % ",".join(props[:160]))
        except Exception as e:
            w("  ERR %s" % e)

try:
    fi = unreal.FbxImportUI()
    for p in ["mesh_type_to_import", "import_mesh", "import_animations",
              "import_as_skeletal", "import_rotation", "import_translation",
              "import_mesh_lo_ds", "automated_import_should_detect_type",
              "skeletal_mesh_import_data", "anim_sequence_import_data",
              "texture_import_data", "original_import_type", "create_physics_asset"]:
        try:
            val = fi.get_editor_property(p)
            w("FBX_OPTION %s=%s" % (p, val.get_path_name() if hasattr(val, "get_path_name") else val))
        except Exception as e:
            w("FBX_OPTION %s=ERR:%s" % (p, e))
    sm = fi.get_editor_property("skeletal_mesh_import_data")
    if sm:
        w("SKELETAL_IMPORT_DATA_METHODS=%s" % ",".join(
            m for m in dirs(sm) if any(k in m.lower() for k in ["lod", "normal", "scale", "material", "import"])))
    ti = fi.get_editor_property("texture_import_data")
    if ti:
        w("TEXTURE_IMPORT_DATA_METHODS=%s" % ",".join(
            m for m in dirs(ti) if any(k in m.lower() for k in ["import", "material", "texture"])))
except Exception as e:
    w("FBX_OPTIONS_ERR=%s" % e)

w("--- ENUMS ---")
for name in ["FbxImportType", "FBXIT_StaticMesh", "FBXIT_SkeletalMesh", "FBXIT_Animation",
             "AnimationMode", "TextureMipGenSettings", "TextureCompressionSettings"]:
    obj = getattr(unreal, name, None)
    w("ENUM %s=%s" % (name, obj))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SOLDIER_IMPORT_PROBE_WRITTEN")
