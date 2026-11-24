import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "CurrentStateAudit", "static_lod_test.txt")
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


try:
    eal = unreal.EditorAssetLibrary
    mesh = eal.load_asset("/Game/Environment/Vegetation/SM_AcaciaTree")
    if not mesh:
        raise RuntimeError("mesh missing")
    w("BEFORE_COUNT=%s" % unreal.EditorStaticMeshLibrary.get_lod_count(mesh))
    opts = unreal.StaticMeshReductionOptions()
    opts.set_editor_property("auto_compute_lod_screen_size", True)
    reductions = []
    for percent, screen in ((0.45, 0.42), (0.18, 0.15)):
        r = unreal.StaticMeshReductionSettings()
        r.set_editor_property("percent_triangles", percent)
        r.set_editor_property("screen_size", screen)
        reductions.append(r)
    opts.set_editor_property("reduction_settings", reductions)
    result = unreal.EditorStaticMeshLibrary.set_lods(mesh, opts)
    w("SET_LODS_RESULT=%s" % result)
    w("AFTER_COUNT=%s" % unreal.EditorStaticMeshLibrary.get_lod_count(mesh))
    eal.save_loaded_asset(mesh)
    w("SAVED")
except Exception as e:
    w("ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("STATIC_LOD_TEST_WRITTEN")
