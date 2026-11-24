import unreal
import os

OUT = r"C:\UnrealProjects\Battleground\Saved\Task04FullAudit\collision_lod_probe.txt"
TEMP_DIR = "/Game/Environment/TempProbe"
TEMP_PATH = TEMP_DIR + "/SM_CollisionLodProbe"
lines = []


def w(s=""):
    lines.append(str(s))


def safe(fn, default=None):
    try:
        return fn()
    except Exception as e:
        return default if default is not None else "ERR:%s" % e


w("COLLISION_LOD_PROBE_BEGIN")
eal = unreal.EditorAssetLibrary
esml = unreal.EditorStaticMeshLibrary
if not eal.does_directory_exist(TEMP_DIR):
    eal.make_directory(TEMP_DIR)
if eal.does_asset_exist(TEMP_PATH):
    eal.delete_asset(TEMP_PATH)
mesh = eal.duplicate_asset("/Game/Environment/Rocks/SM_HampiBoulder_01", TEMP_PATH)
w("DUPLICATE=%s" % bool(mesh))
if mesh:
    sro_cls = getattr(unreal, "StaticMeshReductionOptions", None)
    mrs_cls = getattr(unreal, "MeshReductionSettings", None)
    w("SRO=%s MRS=%s" % (bool(sro_cls), bool(mrs_cls)))
    if sro_cls:
        w("SRO_PROPS=%s" % [m for m in dir(sro_cls()) if not m.startswith("_")])
    if mrs_cls:
        w("MRS_PROPS=%s" % [m for m in dir(mrs_cls()) if not m.startswith("_")])

    for shape in [unreal.ScriptingCollisionShapeType.SPHERE,
                  unreal.ScriptingCollisionShapeType.BOX,
                  unreal.ScriptingCollisionShapeType.NDOP26]:
        w("ADD_COLLISION shape=%s result=%s simple=%s convex=%s" % (
            shape, safe(lambda: esml.add_simple_collisions(mesh, shape)),
            safe(lambda: esml.get_simple_collision_count(mesh)),
            safe(lambda: esml.get_convex_collision_count(mesh))))

    try:
        opts = unreal.StaticMeshReductionOptions()
        settings = []
        for i in range(1):
            s = unreal.MeshReductionSettings()
            for prop, val in [("percent_triangles", 0.5),
                              ("silhouette_importance", 0.5),
                              ("shading_importance", 0.5),
                              ("texel_importance", 0.5),
                              ("loop_importance", 0.5),
                              ("wireframe_importance", 0.5),
                              ("locking_type", unreal.ReductionOptionType.OPTION_NONE)]:
                try:
                    s.set_editor_property(prop, val)
                except Exception:
                    pass
            settings.append(s)
        opts.set_editor_property("reduction_settings", settings)
        try:
            opts.set_editor_property("auto_compute_reduction", False)
        except Exception:
            pass
        w("SET_LODS_RESULT=%s count=%s sizes=%s" % (
            safe(lambda: esml.set_lods(mesh, opts)),
            safe(lambda: esml.get_lod_count(mesh)),
            str(safe(lambda: esml.get_lod_screen_sizes(mesh)))))
    except Exception as e:
        w("SET_LODS_ERR=%s" % e)

    eal.save_loaded_asset(mesh)
    w("SAVED_PROBE=%s" % TEMP_PATH)
    eal.delete_asset(TEMP_PATH)
    w("DELETED_PROBE=%s" % (not eal.does_asset_exist(TEMP_PATH)))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("COLLISION_LOD_PROBE_WRITTEN")
