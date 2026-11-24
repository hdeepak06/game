import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\pie_all.txt"
lines = []
sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for n in sorted(x for x in dir(sub) if not x.startswith("_")):
    lines.append(n)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("PIE_ALL_WRITTEN")
