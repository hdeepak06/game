import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\skeleton_api.txt"
lines = []
skel = unreal.EditorAssetLibrary.load_asset(
    "/Game/Characters/Soldier/SKM_HampiSoldier_Skeleton")
lines.append("DIR")
for n in sorted(x for x in dir(skel) if not x.startswith("_")):
    lines.append(n)
lines.append("PROPS")
for n in ["bone_tree", "sockets"]:
    try:
        lines.append("%s=%s" % (n, skel.get_editor_property(n)))
    except Exception as e:
        lines.append("%s ERR=%s" % (n, e))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SKELETON_API_WRITTEN")
