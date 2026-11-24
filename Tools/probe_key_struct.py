import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\key_struct.txt"
lines = []
for label, make in [
    ("empty", lambda: unreal.Key()),
    ("kwargs", lambda: unreal.Key(key_name=unreal.Name("LeftMouseButton"))),
]:
    try:
        k = make()
        lines.append("%s=%s" % (label, k))
        for n in sorted(x for x in dir(k) if not x.startswith("_")):
            lines.append("  %s" % n)
        for p in ["key_name", "display_name"]:
            try:
                lines.append("  PROP %s=%s" % (p, k.get_editor_property(p)))
            except Exception as e:
                lines.append("  PROP %s ERR=%s" % (p, e))
    except Exception as e:
        lines.append("%s ERR=%s" % (label, e))
imc = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Input/IMC_Default")
maps = imc.get_editor_property("mappings")
for m in maps[:3]:
    k = m.get_editor_property("key")
    lines.append("EXISTING KEY=%s" % k)
    for p in ["key_name", "display_name"]:
        try:
            lines.append("  %s=%s" % (p, k.get_editor_property(p)))
        except Exception as e:
            lines.append("  %s ERR=%s" % (p, e))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("KEY_STRUCT_WRITTEN")
