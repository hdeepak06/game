import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\play_modes.txt"
lines = []
for cls_name in ["LevelEditorSubsystem", "EditorLevelLibrary", "UnrealEditorSubsystem", "LevelEditorPlaySettings"]:
    cls = getattr(unreal, cls_name, None)
    lines.append("=== %s ===" % cls_name)
    if cls is None:
        lines.append("MISSING")
        continue
    names = [n for n in dir(cls) if any(k in n.lower() for k in ["play", "pie", "session", "world"])]
    lines.extend(sorted(names))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("PLAY_MODES_WRITTEN")
