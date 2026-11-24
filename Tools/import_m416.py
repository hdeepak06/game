import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
FBX = os.path.join(PROJECT, "Saved", "ThirdParty", "PolyPizza_M4Carbine",
                   "extracted", "source", "M4.fbx")
DEST = "/Game/Weapons/M416"
OUT = os.path.join(PROJECT, "Saved", "WeaponM416", "import_report.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


try:
    w("IMPORT_BEGIN")
    w("FBX=%s EXISTS=%s" % (FBX, os.path.exists(FBX)))
    eal = unreal.EditorAssetLibrary
    eal.make_directory(DEST)

    task = unreal.AssetImportTask()
    task.filename = FBX
    task.destination_path = DEST
    task.destination_name = "SM_M416"
    task.replace_existing = True
    task.automated = True
    task.save = True

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = True
    options.import_textures = True
    options.import_animations = False

    sm = options.static_mesh_import_data
    for prop, value in [
        ("auto_generate_collision", True),
        ("combine_meshes", True),
        ("generate_lightmap_u_vs", False),
        ("one_convex_hull_per_ucx", False),
    ]:
        try:
            sm.set_editor_property(prop, value)
        except Exception as e:
            w("OPTION_SKIP %s=%s (%s)" % (prop, value, e))

    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    w("IMPORT_TASKS_DONE")

    assets = eal.list_assets(DEST, recursive=True, include_folder=False)
    for path in assets:
        obj = eal.load_asset(path)
        w("ASSET %s class=%s" % (path, obj.get_class().get_name() if obj else None))

    mesh = eal.load_asset(DEST + "/SM_M416")
    w("MESH=%s" % mesh)
    if mesh:
        try:
            bounds = mesh.get_bounds()
            w("BOUNDS=%s" % bounds)
        except Exception as e:
            w("BOUNDS_ERR=%s" % e)
        for fn_name in ["get_num_lods", "get_number_verts", "get_number_triangles"]:
            fn = getattr(unreal.EditorStaticMeshLibrary, fn_name, None)
            if fn:
                try:
                    if fn_name == "get_num_lods":
                        w("LODS=%s" % fn(mesh))
                    else:
                        w("%s=%s" % (fn_name.upper(), fn(mesh, 0)))
                except Exception as e:
                    w("%s_ERR=%s" % (fn_name.upper(), e))
        w("MATERIAL_SLOTS=%d" % len(mesh.get_editor_property("static_materials")))
        for idx, smat in enumerate(mesh.get_editor_property("static_materials")):
            w("  SLOT %d name=%s material=%s" % (
                idx, smat.material_slot_name, smat.material_interface))
        w("NANITE_SETTINGS=%s" % mesh.get_editor_property("nanite_settings"))
    w("IMPORT_DONE")
except Exception as e:
    w("IMPORT_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("M416_IMPORT_WRITTEN")
