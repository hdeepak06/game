import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\AI\class_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


for name in ["HampiAICharacter", "HampiAIBotSpawner", "HampiSoldierCharacter"]:
    cls = getattr(unreal, name, None)
    w("CLASS %s = %s" % (name, cls))
    if cls:
        try:
            w("  PROPS=" + str(sorted([p for p in dir(cls) if not p.startswith("_")]))[:2500])
        except Exception as e:
            w("  ERR=" + str(e))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("AI_CLASS_PROBE_WRITTEN")
