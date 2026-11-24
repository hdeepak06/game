import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\pie_api.txt"
lines = []
for label, obj in [
    ("LevelEditorSubsystem", getattr(unreal, "LevelEditorSubsystem", None)),
    ("EditorPythonScripting", getattr(unreal, "EditorPythonScripting", None)),
]:
    lines.append("--- %s ---" % label)
    if obj:
        for n in sorted(x for x in dir(obj) if not x.startswith("_")):
            if any(k in n.lower() for k in ["play", "begin", "end", "keep", "python", "simulate"]):
                fn = getattr(obj, n, None)
                doc = str(getattr(fn, "__doc__", "") or "")[:400].replace("\n", " ")
                lines.append("  %s :: %s" % (n, doc))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("PIE_API_WRITTEN")
