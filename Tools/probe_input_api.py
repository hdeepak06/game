import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\input_api.txt"
lines = []
for name in ["InputActionValueType", "EnhancedActionKeyMapping", "Key", "InputAction"]:
    obj = getattr(unreal, name, None)
    lines.append("CLASS %s=%s" % (name, obj))
    if obj and name == "InputActionValueType":
        for n in sorted(x for x in dir(obj) if not x.startswith("_")):
            lines.append("  VAL %s" % n)
    if obj and name == "EnhancedActionKeyMapping":
        for n in sorted(x for x in dir(obj) if not x.startswith("_")):
            lines.append("  MAP %s" % n)
lines.append("KEY_TEST")
try:
    k = unreal.Key("LeftMouseButton")
    lines.append("KEY=%s" % k)
except Exception as e:
    lines.append("KEY_ERR=%s" % e)
imc = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Input/IMC_Default")
lines.append("IMC=%s" % imc)
if imc:
    try:
        maps = imc.get_editor_property("mappings")
        lines.append("MAPPINGS=%d" % len(maps))
        for m in maps[:5]:
            lines.append("  %s %s" % (m.get_editor_property("action"), m.get_editor_property("key")))
    except Exception as e:
        lines.append("MAPPINGS_ERR=%s" % e)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("INPUT_API_WRITTEN")
