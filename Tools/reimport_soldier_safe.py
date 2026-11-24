import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
FBX = os.path.join(PROJECT, "Saved", "ThirdParty", "Grab3D_Soldier", "soldier-rigged.fbx")
DEST = "/Game/Characters/Soldier"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "reimport_report.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def main():
    w("REIMPORT_BEGIN")
    eal = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    options = unreal.FbxImportUI()
    options.set_editor_property("automated_import_should_detect_type", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("create_physics_asset", False)
    options.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    sm = options.get_editor_property("skeletal_mesh_import_data")
    sm.set_editor_property("import_uniform_scale", 1.0)
    sm.set_editor_property("convert_scene", True)
    sm.set_editor_property("convert_scene_unit", True)
    sm.set_editor_property("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    sm.set_editor_property("import_mesh_lo_ds", False)
    anim = options.get_editor_property("anim_sequence_import_data")
    anim.set_editor_property("import_uniform_scale", 1.0)
    anim.set_editor_property("convert_scene", True)
    anim.set_editor_property("convert_scene_unit", True)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX)
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", "SKM_HampiSoldier")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    tools.import_asset_tasks([task])
    w("IMPORTED=%s" % [str(p) for p in (task.get_editor_property("imported_object_paths") or [])])

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    ar.scan_files_synchronous([os.path.join(PROJECT, "Content", "Characters", "Soldier")])
    assets = list(ar.get_assets_by_path(DEST, recursive=True))
    for a in assets:
        obj = eal.load_asset(str(a.package_name))
        if obj:
            ok = eal.save_loaded_asset(obj)
            w("SAVED %s class=%s ok=%s" % (
                a.package_name, a.asset_class_path.asset_name, ok))
    mesh = eal.load_asset(DEST + "/SKM_HampiSoldier")
    if mesh:
        w("MESH_SKELETON=%s" % mesh.get_editor_property("skeleton"))
        w("MESH_MATERIALS=%s" % [str(m) for m in mesh.get_editor_property("materials")])
    w("REIMPORT_DONE")


try:
    main()
except Exception as e:
    w("REIMPORT_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("REIMPORT_WRITTEN")
