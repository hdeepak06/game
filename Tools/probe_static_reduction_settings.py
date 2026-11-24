import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\static_reduction_settings.txt"
lines = []
cls = getattr(unreal, "StaticMeshReductionSettings", None)
lines.append("CLASS=%s" % cls)
if cls:
    o = cls()
    for n in sorted(dir(o)):
        if n.startswith("_") or callable(getattr(o, n, None)):
            continue
        try:
            lines.append("  %s=%s" % (n, o.get_editor_property(n)))
        except Exception:
            pass
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("STATIC_REDUCTION_SETTINGS_WRITTEN")
