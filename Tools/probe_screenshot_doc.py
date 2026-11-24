import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\screenshot_doc.txt"
lines = []
for obj, label in [
    (unreal.AutomationLibrary.take_high_res_screenshot, "take_high_res_screenshot"),
    (unreal.EditorLevelLibrary.editor_play_simulate, "editor_play_simulate"),
    (unreal.EditorLevelLibrary.editor_end_play, "editor_end_play"),
    (unreal.register_slate_post_tick_callback, "register_slate_post_tick_callback"),
]:
    lines.append("--- %s ---" % label)
    lines.append(str(getattr(obj, "__doc__", None)))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SCREENSHOT_DOC_WRITTEN")
