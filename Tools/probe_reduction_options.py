import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\reduction_options.txt"
lines = []
for clsname in ["StaticMeshReductionOptions", "MeshReductionSettings"]:
    cls = getattr(unreal, clsname, None)
    lines.append("CLASS %s=%s" % (clsname, cls))
    if cls:
        try:
            o = cls()
            for n in sorted(dir(o)):
                if n.startswith("_") or callable(getattr(o, n, None)):
                    continue
                try:
                    lines.append("  %s=%s" % (n, o.get_editor_property(n)))
                except Exception:
                    pass
        except Exception as e:
            lines.append("  ERR=%s" % e)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("REDUCTION_OPTIONS_WRITTEN")
