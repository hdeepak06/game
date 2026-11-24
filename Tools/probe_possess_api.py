import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\possess_api.txt"
lines = []
for cls, names in [
    (unreal.PlayerController, ["possess", "un_possess", "get_controlled_pawn", "set_control_rotation", "get_control_rotation"]),
    (unreal.Pawn, ["auto_possess", "get_controller", "set_controller"]),
    (unreal.PlayerCameraManager, ["set_fov", "get_fov_angle"]),
]:
    lines.append("=== %s ===" % cls.__name__)
    for n in names:
        fn = getattr(cls, n, None)
        lines.append("%s :: %s" % (n, getattr(fn, "__doc__", "MISSING")))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("POSSESS_API_WRITTEN")
