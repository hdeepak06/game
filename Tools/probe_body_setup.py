import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\Task04FullAudit\body_setup_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def safe(fn, default=None):
    try:
        return fn()
    except Exception as e:
        return default if default is not None else "ERR:%s" % e


mesh = unreal.EditorAssetLibrary.load_asset("/Game/Environment/Rocks/SM_HampiBoulder_01")
w("MESH=%s" % mesh)
w("MESH_PROPS_COLLISION=%s" % [m for m in dir(mesh) if "body" in m.lower() or "collision" in m.lower()])
bs = safe(lambda: mesh.get_editor_property("body_setup"))
w("BODY_SETUP=%s" % bs)
if bs and not str(bs).startswith("ERR"):
    w("BS_PROPS=%s" % [m for m in dir(bs) if not m.startswith("_")])
    agg = safe(lambda: bs.get_editor_property("agg_geom"))
    w("AGG_GEOM=%s" % agg)
    if agg and not str(agg).startswith("ERR"):
        w("AGG_PROPS=%s" % [m for m in dir(agg) if not m.startswith("_")])
for cname in ["BodySetup", "KAggregateGeom", "KSphereElem", "KBoxElem", "KCapsuleElem", "CollisionEnabled", "BoxComponent", "CapsuleComponent"]:
    cls = getattr(unreal, cname, None)
    w("CLASS %s=%s" % (cname, bool(cls)))
    if cls:
        names = [m for m in dir(cls) if any(tok in m.lower() for tok in ["shape", "elem", "extent", "radius", "collision", "hidden"])]
        w("  METHODS=%s" % ",".join(names[:120]))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("BODY_SETUP_PROBE_WRITTEN")
