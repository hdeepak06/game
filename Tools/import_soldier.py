import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
FBX = os.path.join(PROJECT, "Saved", "ThirdParty", "Grab3D_Soldier", "soldier-rigged.fbx")
DEST = "/Game/Characters/Soldier"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "import_report.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def main():
    w("SOLDIER_IMPORT_BEGIN")
    if not os.path.exists(FBX):
        raise RuntimeError("missing FBX: " + FBX)
    eal = unreal.EditorAssetLibrary
    if not eal.does_directory_exist(DEST):
        eal.make_directory(DEST)
        w("CREATED_DIR %s" % DEST)

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

    sm_data = options.get_editor_property("skeletal_mesh_import_data")
    sm_data.set_editor_property("import_uniform_scale", 1.0)
    sm_data.set_editor_property("convert_scene", True)
    sm_data.set_editor_property("convert_scene_unit", True)
    sm_data.set_editor_property("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    sm_data.set_editor_property("compute_weighted_normals", True)
    sm_data.set_editor_property("import_mesh_lo_ds", False)
    anim_data = options.get_editor_property("anim_sequence_import_data")
    anim_data.set_editor_property("import_uniform_scale", 1.0)
    anim_data.set_editor_property("convert_scene", True)
    anim_data.set_editor_property("convert_scene_unit", True)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX)
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", "SKM_HampiSoldier")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    task.set_editor_property("factory", None)
    tools.import_asset_tasks([task])
    w("IMPORT_PATHS=%s" % [str(p) for p in (task.get_editor_property("imported_object_paths") or [])])

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in ar.get_assets_by_path(DEST, recursive=True):
        w("ASSET %s.%s class=%s" % (a.package_name, a.asset_name, a.asset_class_path.asset_name))

    mesh = eal.load_asset(DEST + "/SKM_HampiSoldier")
    if not mesh:
        raise RuntimeError("mesh import failed")
    w("MESH=%s" % mesh.get_path_name())
    w("MESH_SKELETON=%s" % mesh.get_editor_property("skeleton"))
    w("MESH_BOUNDS=%s" % mesh.get_imported_bounds())
    w("MESH_LOD_COUNT=%s" % unreal.EditorSkeletalMeshLibrary.get_lod_count(mesh))
    w("MESH_NUM_VERTS_LOD0=%s" % unreal.EditorSkeletalMeshLibrary.get_num_verts(mesh, 0))
    w("MESH_MATERIALS=%s" % [str(m) for m in mesh.get_editor_property("materials")])
    for anim_path in [DEST + "/walk", DEST + "/run", DEST + "/SKM_HampiSoldier_walk",
                      DEST + "/SKM_HampiSoldier_run"]:
        seq = eal.load_asset(anim_path)
        if seq:
            w("ANIM %s length=%s skeleton=%s" % (
                anim_path, seq.get_play_length(), seq.get_skeleton()))
    w("SOLDIER_IMPORT_DONE")


try:
    main()
except Exception as e:
    w("SOLDIER_IMPORT_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("SOLDIER_IMPORT_WRITTEN")
