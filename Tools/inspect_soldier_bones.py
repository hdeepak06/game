import os
import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\soldier_bones.txt"
lines = []
skel = unreal.EditorAssetLibrary.load_asset(
    "/Game/Characters/Soldier/SKM_HampiSoldier_Skeleton")
w = lambda s: lines.append(str(s))
w("SKELETON=%s" % skel)
if skel:
    bones = skel.get_editor_property("bone_tree")
    w("BONE_TREE=%s" % bones)
    try:
        names = unreal.SkeletalMeshLibrary.get_bone_names(skel)
    except Exception as e:
        w("GET_BONE_NAMES_ERR=%s" % e)
        names = []
    w("BONE_COUNT=%d" % len(names))
    for n in names:
        text = str(n)
        if any(k in text.lower() for k in ("hand", "wrist", "weapon", "root", "spine", "head")):
            w("BONE=%s" % text)
    for idx, n in enumerate(names[:80]):
        w("IDX %d %s" % (idx, n))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SOLDIER_BONES_WRITTEN")
