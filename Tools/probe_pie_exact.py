import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\pie_exact.txt"
lines = []
sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
lines.append("SUB=%s" % sub)
for n in ["editor_request_begin_play", "editor_play_simulate", "editor_request_end_play", "is_in_play_in_editor"]:
    lines.append("%s=%s" % (n, hasattr(sub, n)))
    if hasattr(sub, n):
        lines.append("  DOC=%s" % str(getattr(sub, n).__doc__)[:300].replace("\n", " "))
lines.append("KEEP_ALIVE=%s" % unreal.EditorPythonScripting.get_keep_python_script_alive())
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("PIE_EXACT_WRITTEN")
