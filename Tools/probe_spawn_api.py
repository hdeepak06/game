import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\spawn_api.txt"
lines = []
for label, cls in [("GameplayStatics", unreal.GameplayStatics), ("EditorLevelLibrary", unreal.EditorLevelLibrary)]:
    lines.append("--- %s ---" % label)
    for n in sorted(x for x in dir(cls) if "spawn" in x.lower()):
        fn = getattr(cls, n, None)
        lines.append("  %s :: %s" % (n, str(getattr(fn, "__doc__", ""))[:500].replace("\n", " ")))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SPAWN_API_WRITTEN")
