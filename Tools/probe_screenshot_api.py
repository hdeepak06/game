import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\screenshot_api.txt"
lines = []
for cls, names in [(unreal.AutomationLibrary, ["take_high_res_screenshot"]),
                   (unreal.AutomationEditorTask, ["is_task_done", "is_valid_task"])]:
    lines.append("=== %s ===" % cls.__name__)
    for n in names:
        lines.append("%s :: %s" % (n, getattr(getattr(cls, n, None), "__doc__", "MISSING")))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SCREENSHOT_API_WRITTEN")
