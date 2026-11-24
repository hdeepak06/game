import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\screenshot_at_camera_doc.txt"
lines = []
for name in ["take_automation_screenshot_at_camera", "take_high_res_screenshot", "take_automation_screenshot"]:
    fn = getattr(unreal.AutomationLibrary, name, None)
    lines.append("--- %s ---" % name)
    lines.append(str(getattr(fn, "__doc__", None)))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SCREENSHOT_AT_CAMERA_DOC_WRITTEN")
