import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\controller_methods.txt"
lines = []
pc = unreal.PlayerController
for n in sorted(x for x in dir(pc) if any(k in x.lower() for k in ["possess", "pawn", "camera", "controlrotation", "fov"])):
    lines.append(n)
lines.append("---CAMERA_MANAGER---")
for n in sorted(x for x in dir(unreal.PlayerCameraManager) if "fov" in x.lower()):
    lines.append(n)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("CONTROLLER_METHODS_WRITTEN")
