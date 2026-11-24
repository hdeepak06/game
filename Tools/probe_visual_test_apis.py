import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\visual_test_apis.txt"
lines = []

for label, cls in [("EditorLevelLibrary", unreal.EditorLevelLibrary),
                   ("AutomationLibrary", unreal.AutomationLibrary),
                   ("SystemLibrary", unreal.SystemLibrary)]:
    lines.append("--- %s ---" % label)
    for n in sorted(x for x in dir(cls) if not x.startswith("_")):
        if any(k in n.lower() for k in ["play", "screenshot", "viewport", "quit", "console", "tick", "camera"]):
            lines.append("  %s" % n)

for n in sorted(x for x in dir(unreal) if "tick" in x.lower() and "callback" in x.lower()):
    lines.append("GLOBAL %s" % n)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("VISUAL_TEST_APIS_WRITTEN")
