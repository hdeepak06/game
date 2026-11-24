import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\game_world_api.txt"
lines = []
cls = getattr(unreal, "UnrealEditorSubsystem", None)
lines.append("CLASS=%s" % cls)
if cls:
    sub = unreal.get_editor_subsystem(cls)
    for n in sorted(x for x in dir(sub) if not x.startswith("_")):
        if "world" in n.lower() or "play" in n.lower():
            lines.append("  %s :: %s" % (n, str(getattr(sub, n).__doc__)[:250].replace("\n", " ")))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("GAME_WORLD_API_WRITTEN")
