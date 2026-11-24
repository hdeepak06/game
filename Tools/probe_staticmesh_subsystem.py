import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\staticmesh_subsystem.txt"
lines = []


def w(s=""):
    lines.append(str(s))


cls = getattr(unreal, "StaticMeshEditorSubsystem", None)
w("CLASS=%s" % cls)
if cls:
    for n in sorted(x for x in dir(cls) if not x.startswith("_")):
        obj = getattr(cls, n, None)
        try:
            doc = str(getattr(obj, "__doc__", ""))[:500].replace("\n", " ")
        except Exception:
            doc = ""
        w("  %s :: %s" % (n, doc))

sm = unreal.EditorAssetLibrary.load_asset("/Game/Environment/Vegetation/SM_AcaciaTree")
if sm and cls:
    try:
        subsystem = unreal.get_editor_subsystem(cls)
        w("SUBSYSTEM=%s" % subsystem)
        w("GET_LOD_COUNT=%s" % subsystem.get_lod_count(sm))
        w("GET_NUM_VERTS=%s" % subsystem.get_number_verts(sm, 0))
        w("GET_SCREEN_SIZES=%s" % subsystem.get_lod_screen_sizes(sm))
    except Exception as e:
        w("SUBSYSTEM_ERR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("STATICMESH_SUBSYSTEM_WRITTEN")
