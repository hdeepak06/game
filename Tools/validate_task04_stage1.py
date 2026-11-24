import unreal, traceback

OUT = r"C:\Users\HP\AppData\Local\Temp\opencode\task04_stage1_validation.txt"
lines = []
def w(s=""):
    lines.append(str(s))

def p(obj, prop):
    try: return str(obj.get_editor_property(prop))
    except Exception as e: return "<%s>" % e

try:
    world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/LV_HampiBattleground")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("WORLD=%s" % (world.get_path_name() if world else None))
    w("ACTOR_COUNT=%d" % len(actors))
    lands = [a for a in actors if isinstance(a, unreal.Landscape)]
    w("LANDSCAPE_COUNT=%d" % len(lands))
    if lands:
        w("LANDSCAPE_MATERIAL=%s" % p(lands[0], "landscape_material"))
        origin, extent = lands[0].get_actor_bounds(False)
        w("LANDSCAPE_BOUNDS origin=%s extent=%s" % (origin, extent))

    task_actors = []
    for a in actors:
        try:
            if unreal.Name("Task04_Stage1") in list(a.get_editor_property("tags")):
                task_actors.append(a)
        except Exception:
            pass
    w("TASK04_ACTORS=%d" % len(task_actors))
    for a in task_actors:
        mesh = None
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            mesh = comp.get_editor_property("static_mesh")
        w("  %s class=%s loc=%s mesh=%s" % (
            a.get_actor_label(), a.get_class().get_name(), a.get_actor_location(),
            mesh.get_path_name() if mesh else None))

    asset_paths = []
    for folder in ["Terrain", "Materials", "Rocks", "Houses"]:
        folder_path = "/Game/Environment/" + folder
        for name in unreal.EditorAssetLibrary.list_assets(folder_path, recursive=False, include_folder=False):
            asset_paths.append(name)
    w("ASSET_COUNT=%d" % len(asset_paths))
    for name in sorted(asset_paths):
        w("  ASSET %s" % name)

    w("--- MESH SLOTS ---")
    mesh_names = ["SM_HampiBoulder_01", "SM_HampiBoulder_02", "SM_HampiBoulder_03",
                  "SM_HampiBoulder_04", "SM_HampiBoulder_05", "SM_KamalapurHouse_Small"]
    for name in mesh_names:
        path = None
        if "House" in name:
            path = "/Game/Environment/Houses/" + name
        else:
            path = "/Game/Environment/Rocks/" + name
        mesh = unreal.EditorAssetLibrary.load_asset(path)
        if not mesh:
            w("  %s MISSING" % name)
            continue
        count = len(mesh.get_editor_property("static_materials"))
        mats = []
        for i in range(count):
            m = mesh.get_material(i)
            mats.append(m.get_path_name() if m else None)
        try:
            desc = mesh.get_static_mesh_description(0)
            verts = desc.get_vertex_count()
            tris = desc.get_triangle_count()
        except Exception as e:
            verts = "ERR:%s" % e
            tris = "ERR:%s" % e
        w("  %s slots=%d materials=%s verts=%s tris=%s" % (
            name, count, mats, verts, tris))

    w("--- MATERIAL INPUT CHECK ---")
    mat_names = ["M_HampiSoil_Mobile", "M_HampiGranite_Mobile", "M_HampiMudPlaster_Mobile",
                 "M_HampiClayRoof_Mobile", "M_HampiWoodDark_Mobile"]
    for name in mat_names:
        mat = unreal.EditorAssetLibrary.load_asset("/Game/Environment/Materials/" + name)
        if not mat:
            w("  %s MISSING" % name)
            continue
        info = []
        for attr in ["get_material_property_input_node", "get_material_default_scalar_parameter_value",
                     "get_material_default_vector_parameter_value"]:
            info.append("%s=%s" % (attr, hasattr(unreal.MaterialEditingLibrary, attr)))
        w("  %s shading=%s blend=%s two_sided=%s helpers=%s" % (
            name, p(mat, "shading_model"), p(mat, "blend_mode"), p(mat, "two_sided"), ",".join(info)))
        if hasattr(unreal.MaterialEditingLibrary, "get_material_property_input_node"):
            for prop in ["MP_BASE_COLOR", "MP_ROUGHNESS", "MP_SPECULAR"]:
                try:
                    node = unreal.MaterialEditingLibrary.get_material_property_input_node(
                        mat, getattr(unreal.MaterialProperty, prop))
                    w("    %s=%s" % (prop, node.get_name() if node else None))
                except Exception as e:
                    w("    %s_ERR=%s" % (prop, e))

except Exception:
    w("FATAL:\n" + traceback.format_exc())

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("TASK04_STAGE1_VALIDATION_WRITTEN", OUT)
