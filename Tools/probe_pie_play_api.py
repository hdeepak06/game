import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\pie_play_api.txt"
lines = []
sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for n in sorted(x for x in dir(sub) if "play" in x.lower() or "pie" in x.lower()):
    fn = getattr(sub, n, None)
    lines.append("%s :: %s" % (n, str(getattr(fn, "__doc__", ""))[:400].replace("\n", " ")))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("PIE_PLAY_API_WRITTEN")
