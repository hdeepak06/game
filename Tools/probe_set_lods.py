import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\set_lods_doc.txt"
lines = []
for name in ["set_lods", "set_lods_with_notification", "set_lod_reduction_settings", "set_lod_from_static_mesh"]:
    obj = getattr(unreal.EditorStaticMeshLibrary, name, None)
    lines.append("--- %s ---" % name)
    lines.append(str(getattr(obj, "__doc__", None)))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SET_LODS_DOC_WRITTEN")
