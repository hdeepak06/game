import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\optimization_apis.txt"
lines = []

for label, fn in [
    ("set_material_usage", getattr(unreal.MaterialEditingLibrary, "set_material_usage", None)),
    ("set_material_usage_flag", getattr(unreal.MaterialEditingLibrary, "set_material_usage_flag", None)),
    ("set_lod_count", getattr(unreal.EditorSkeletalMeshLibrary, "set_lod_count", None)),
    ("set_lod_screen_sizes", getattr(unreal.EditorSkeletalMeshLibrary, "set_lod_screen_sizes", None)),
    ("get_lod_screen_sizes", getattr(unreal.EditorSkeletalMeshLibrary, "get_lod_screen_sizes", None)),
    ("set_min_lod", getattr(unreal.EditorSkeletalMeshLibrary, "set_min_lod", None)),
]:
    lines.append("--- %s ---" % label)
    lines.append(str(getattr(fn, "__doc__", None)))

for enum_name in ["MaterialUsage", "MaterialUsageFlags"]:
    e = getattr(unreal, enum_name, None)
    lines.append("ENUM %s=%s" % (enum_name, e))
    if e:
        for n in sorted(x for x in dir(e) if not x.startswith("_")):
            lines.append("  %s" % n)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("OPTIMIZATION_APIS_WRITTEN")
