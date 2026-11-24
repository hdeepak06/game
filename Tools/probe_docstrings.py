import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\docstring_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def doc(obj, label):
    w("--- %s ---" % label)
    try:
        w(str(getattr(obj, "__doc__", None)))
    except Exception as e:
        w("DOC_ERR=%s" % e)


def props_of(obj, label):
    w("--- PROPS %s ---" % label)
    for name in sorted(n for n in dir(obj) if not n.startswith("_")):
        try:
            if callable(getattr(obj, name)):
                continue
        except Exception:
            continue
        try:
            v = obj.get_editor_property(name)
            w("  %s=%s" % (name, str(v)[:300]))
        except Exception:
            pass


for cls, label in [
    (unreal.IKRetargetBatchOperation.duplicate_and_retarget, "duplicate_and_retarget"),
    (unreal.EditorSkeletalMeshLibrary.regenerate_lod, "regenerate_lod"),
    (unreal.EditorSkeletalMeshLibrary.import_lod, "import_lod"),
    (unreal.EditorSkeletalMeshLibrary.get_lod_build_settings, "get_lod_build_settings"),
    (unreal.EditorSkeletalMeshLibrary.set_lod_build_settings, "set_lod_build_settings"),
    (unreal.IKRigController.add_retarget_chain, "add_retarget_chain"),
    (unreal.IKRetargeterController.auto_map_chains, "auto_map_chains"),
    (unreal.IKRetargeterController.set_ik_rig, "set_ik_rig"),
    (unreal.AnimBlueprint.get_animation_graphs, "get_animation_graphs"),
    (unreal.AnimBlueprint.get_nodes_of_class, "get_nodes_of_class"),
]:
    doc(cls, label)

fi = unreal.FbxImportUI()
sm = fi.get_editor_property("skeletal_mesh_import_data")
am = fi.get_editor_property("anim_sequence_import_data")
ti = fi.get_editor_property("texture_import_data")
props_of(sm, "FbxSkeletalMeshImportData")
props_of(am, "FbxAnimSequenceImportData")
props_of(ti, "FbxTextureImportData")

for cls_name in ["SkeletalMeshLODInfo", "SkeletalMeshOptimizationSettings",
                 "SkeletalMeshBuildSettings", "USkeletalMeshReductionSettings",
                 "BlendSpace1D", "AnimSequence", "FbxSkeletalMeshImportData"]:
    cls = getattr(unreal, cls_name, None)
    if cls:
        doc(cls, cls_name)

abp = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Animations/ABP_Quinn")
if abp:
    try:
        graphs = abp.get_animation_graphs()
        w("ABP_GRAPHS=%s" % graphs)
        for g in graphs or []:
            w("  GRAPH %s class=%s" % (g.get_name(), g.get_class().get_name()))
            w("  GRAPH_METHODS=%s" % ",".join(
                m for m in sorted(dir(g)) if not m.startswith("_")))
    except Exception as e:
        w("ABP_GRAPHS_ERR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("DOCSTRING_PROBE_WRITTEN")
