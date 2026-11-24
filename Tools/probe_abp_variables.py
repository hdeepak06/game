import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\abp_variables.txt"
lines = []


def w(s=""):
    lines.append(str(s))


for path in ["/Game/Characters/Mannequins/Animations/ABP_Quinn",
             "/Game/Characters/Mannequins/Animations/ABP_Manny"]:
    abp = unreal.EditorAssetLibrary.load_asset(path)
    w("ABP %s loaded=%s" % (path, bool(abp)))
    if not abp:
        continue
    cls = abp.generated_class()
    cdo = unreal.get_default_object(cls) if cls else None
    w("  CLASS=%s CDO=%s" % (cls, cdo))
    if not cdo:
        continue
    for name in sorted(n for n in dir(cdo) if not n.startswith("_")):
        if any(k in name.lower() for k in ["idle", "walk", "run", "speed", "anim", "state", "jump", "fall", "land", "blend", " accel", "direction", "pose", "ground"]):
            try:
                val = cdo.get_editor_property(name)
                w("  VAR %s=%s" % (name, val.get_path_name() if hasattr(val, "get_path_name") else val))
            except Exception as e:
                w("  VAR %s=ERR:%s" % (name, e))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ABP_VARIABLES_WRITTEN")
