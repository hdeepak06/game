import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\automation_task.txt"
lines = []
cls = getattr(unreal, "AutomationEditorTask", None)
lines.append("CLASS=%s" % cls)
if cls:
    for n in sorted(x for x in dir(cls) if not x.startswith("_")):
        fn = getattr(cls, n, None)
        lines.append("  %s :: %s" % (n, str(getattr(fn, "__doc__", ""))[:300].replace("\n", " ")))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("AUTOMATION_TASK_WRITTEN")
