import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\static_lod_apis.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def doc(obj, label):
    w("--- %s ---" % label)
    try:
        w(str(getattr(obj, "__doc__", None))[:1800])
    except Exception as e:
        w("ERR=%s" % e)


w("--- EDITOR STATIC MESH LIBRARY METHODS ---")
for n in sorted(x for x in dir(unreal.EditorStaticMeshLibrary) if not x.startswith("_")):
    w("  %s" % n)

for name in ["generate_lods", "get_lod_count", "set_lod_build_settings", "get_lod_build_settings",
             "remove_lods", "get_number_verts", "set_min_lod", "set_reduction_settings"]:
    obj = getattr(unreal.EditorStaticMeshLibrary, name, None)
    if obj:
        doc(obj, name)

for clsname in ["StaticMeshOptimizationSettings", "MeshReductionSettings", "StaticMeshSourceModel", "StaticMeshBuildSettings"]:
    cls = getattr(unreal, clsname, None)
    w("CLASS %s=%s" % (clsname, cls))
    if cls:
        try:
            o = cls()
            for n in sorted(dir(o)):
                if n.startswith("_") or callable(getattr(o, n, None)):
                    continue
                try:
                    w("  %s=%s" % (n, o.get_editor_property(n)))
                except Exception:
                    pass
        except Exception as e:
            w("  ERR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("STATIC_LOD_APIS_WRITTEN")
