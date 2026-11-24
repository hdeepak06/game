import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\mesh_bone_api.txt"
lines = []
bp = unreal.EditorAssetLibrary.load_asset(
    "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
cdo = unreal.get_default_object(bp.generated_class())
comp = cdo.get_components_by_class(unreal.SkeletalMeshComponent)[0]
for n in sorted(x for x in dir(comp) if "bone" in x.lower() or "socket" in x.lower()):
    lines.append(n)
try:
    count = comp.get_num_bones()
    lines.append("COUNT=%s" % count)
    for i in range(count):
        lines.append("BONE %d %s" % (i, comp.get_bone_name(i)))
except Exception as e:
    lines.append("ERR=%s" % e)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("MESH_BONE_API_WRITTEN")
