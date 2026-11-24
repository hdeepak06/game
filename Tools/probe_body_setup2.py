import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\Task04FullAudit\body_setup_probe2.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def safe(fn, default=None):
    try:
        return fn()
    except Exception as e:
        return default if default is not None else "ERR:%s" % e


mesh = unreal.EditorAssetLibrary.load_asset("/Game/Environment/Rocks/SM_HampiBoulder_01")
bs = mesh.get_editor_property("body_setup")
agg = bs.get_editor_property("agg_geom")
for field in ["sph_elems", "box_elems", "sphyl_elems", "convex_elems", "tri_mesh"]:
    val = safe(lambda: agg.get_editor_property(field))
    w("AGG.%s=%s" % (field, val))

sph = unreal.KSphereElem()
for field in ["center", "radius"]:
    w("KSPHERE.%s=%s" % (field, safe(lambda: sph.get_editor_property(field))))
box = unreal.KBoxElem()
for field in ["center", "extent", "rotation"]:
    w("KBOX.%s=%s" % (field, safe(lambda: box.get_editor_property(field))))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("BODY_SETUP_PROBE2_WRITTEN")
