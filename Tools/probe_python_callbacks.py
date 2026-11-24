import unreal
out = r"C:\UnrealProjects\Battleground\Saved\Task05Audit\python_callbacks.txt"
lines = []
for name in dir(unreal):
    low = name.lower()
    if "slate" in low or "tick" in low or "delegate" in low:
        lines.append(name)
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("TASK05_CALLBACK_PROBE_WRITTEN")
