import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
FBX = os.path.join(PROJECT, "Saved", "ThirdParty", "Grab3D_Soldier", "soldier-rigged.fbx")
DEST = "/Game/Characters/Soldier"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "anim_import_report.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def main():
    w("ANIM_IMPORT_BEGIN")
    eal = unreal.EditorAssetLibrary
    skeleton = eal.load_asset(DEST + "/SKM_HampiSoldier_Skeleton")
    if not skeleton:
        raise RuntimeError("soldier skeleton missing")

    options = unreal.FbxImportUI()
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_ANIMATION)
    try:
        options.set_editor_property("skeleton", skeleton)
        w("SKELETON_SET=True")
    except Exception as e:
        w("SKELETON_SET_ERR=%s" % e)
    ad = options.get_editor_property("anim_sequence_import_data")
    ad.set_editor_property("import_uniform_scale", 1.0)
    ad.set_editor_property("convert_scene", True)
    ad.set_editor_property("convert_scene_unit", True)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX)
    task.set_editor_property("destination_path", DEST + "/Animations")
    task.set_editor_property("destination_name", "SoldierAnims")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    w("IMPORTED=%s" % [str(p) for p in (task.get_editor_property("imported_object_paths") or [])])

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    ar.scan_files_synchronous([os.path.join(PROJECT, "Content", "Characters", "Soldier")])
    for a in ar.get_assets_by_path(DEST, recursive=True):
        if a.asset_class_path.asset_name in ("AnimSequence", "Skeleton"):
            obj = eal.load_asset(str(a.package_name))
            if obj:
                eal.save_loaded_asset(obj)
                extra = ""
                if isinstance(obj, unreal.AnimSequence):
                    extra = " length=%s skeleton=%s" % (obj.get_play_length(), obj.get_skeleton())
                w("SAVED %s%s" % (a.package_name, extra))
    w("ANIM_IMPORT_DONE")


try:
    main()
except Exception as e:
    w("ANIM_IMPORT_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("ANIM_IMPORT_WRITTEN")
