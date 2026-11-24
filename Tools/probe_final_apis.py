import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\final_api_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def doc(obj, label):
    w("--- %s ---" % label)
    try:
        w(str(getattr(obj, "__doc__", None))[:1600])
    except Exception as e:
        w("ERR=%s" % e)


for name in ["SkeletalMeshOptimizationType", "SkeletalMeshTerminationCriterion",
             "SkeletalMeshOptimizationImportance", "FBXImportType", "FBXNormalImportMethod"]:
    cls = getattr(unreal, name, None)
    w("ENUM %s=%s" % (name, cls))
    if cls:
        for n in dir(cls):
            if n.startswith("_"):
                continue
            try:
                w("  %s=%s" % (n, getattr(cls, n)))
            except Exception:
                pass

for obj, label in [
    (unreal.IKRigController.set_skeletal_mesh, "IKRigController.set_skeletal_mesh"),
    (unreal.IKRigController.apply_auto_generated_retarget_definition, "IKRigController.apply_auto_generated_retarget_definition"),
    (unreal.IKRigController.add_retarget_chain, "IKRigController.add_retarget_chain"),
    (unreal.IKRetargeterController.set_ik_rig, "IKRetargeterController.set_ik_rig"),
    (unreal.IKRetargeterController.auto_map_chains, "IKRetargeterController.auto_map_chains"),
    (unreal.IKRetargeterController.auto_align_all_bones, "IKRetargeterController.auto_align_all_bones"),
    (unreal.IKRetargeterController.create_retarget_pose, "IKRetargeterController.create_retarget_pose"),
    (unreal.IKRigDefinitionFactory, "IKRigDefinitionFactory"),
    (unreal.IKRetargetFactory, "IKRetargetFactory"),
    (unreal.SkeletalMaterial, "SkeletalMaterial"),
    (unreal.EditorAssetLibrary.delete_asset, "delete_asset"),
    (unreal.EditorAssetLibrary.rename_asset, "rename_asset"),
    (unreal.EditorAssetLibrary.duplicate_asset, "duplicate_asset"),
    (unreal.AnimBlueprint, "AnimBlueprint"),
]:
    doc(obj, label)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("FINAL_API_PROBE_WRITTEN")
