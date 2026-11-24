import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\retarget_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def dump(name):
    cls = getattr(unreal, name, None)
    w("CLASS %s exists=%s" % (name, bool(cls)))
    if cls:
        w("  %s" % ",".join(sorted(m for m in dir(cls) if not m.startswith("_"))))


for n in ["IKRigController", "IKRetargeterController", "IKRetargetBatchOperation",
          "EditorSkeletalMeshLibrary", "SkeletalMeshUtilitiesLibrary", "AnimGraphLibrary",
          "BlendSpaceLibrary", "BlendSpacePlayerLibrary", "AnimBlueprint",
          "AnimGraphNode_SequencePlayer", "AnimGraphNode_BlendSpacePlayer",
          "AnimGraphNode_StateMachine", "AnimGraphNode_StateResult",
          "AnimGraphNode_BlendListByBool", "AnimGraphNode_TwoWayBlend",
          "AnimGraphNode_Slot", "AnimGraphNode_Root", "AnimGraphNode_LinkedInputPose",
          "AnimationStateMachine", "AnimationState", "AnimationStateTransition",
          "AnimBlueprintGeneratedClass", "AnimInstance"]:
    dump(n)

w("--- IK CONTROLLERS ON ASSETS ---")
ik = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Rigs/IK_Mannequin")
rtg = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Rigs/RTG_Mannequin")
for label, obj in [("IKRIG", ik), ("RTG", rtg)]:
    if not obj:
        continue
    w("%s PROPS" % label)
    for p in ["skeletal_mesh", "preview_skeletal_mesh", "source_ik_rig_asset",
              "target_ik_rig_asset", "source_ik_rig", "target_ik_rig",
              "retarget_chains", "root_settings", "global_settings"]:
        try:
            v = obj.get_editor_property(p)
            w("  %s=%s" % (p, v))
        except Exception as e:
            w("  %s=ERR:%s" % (p, e))
    try:
        ctrl = unreal.IKRigController.get_controller(obj) if label == "IKRIG" else unreal.IKRetargeterController.get_controller(obj)
        w("%s CONTROLLER=%s" % (label, ctrl))
        if ctrl:
            w("  METHODS=%s" % ",".join(sorted(m for m in dir(ctrl) if not m.startswith("_"))))
    except Exception as e:
        w("%s CONTROLLER_ERR=%s" % (label, e))

w("--- ABP QUINN GRAPH NODES ---")
abp = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Animations/ABP_Quinn")
w("ABP=%s" % abp)
if abp:
    for p in ["skeleton", "preview_skeletal_mesh", "target_skeleton"]:
        try:
            w("  %s=%s" % (p, abp.get_editor_property(p)))
        except Exception as e:
            w("  %s=ERR:%s" % (p, e))
    for cls_name in ["AnimGraphNode_SequencePlayer", "AnimGraphNode_BlendSpacePlayer",
                     "AnimGraphNode_StateMachine", "AnimGraphNode_StateResult",
                     "AnimGraphNode_BlendListByBool", "AnimGraphNode_TwoWayBlend"]:
        cls = getattr(unreal, cls_name, None)
        if not cls:
            continue
        try:
            nodes = abp.get_nodes_of_class(cls)
            w("  NODES %s count=%s" % (cls_name, len(nodes) if nodes else 0))
            for n in (nodes or []):
                w("    NODE %s props=%s" % (n.get_name(), ",".join(sorted(
                    m for m in dir(n) if not m.startswith("_")))))
                for prop in ["sequence", "blend_space", "state_machine", "bound_graph",
                             "node", "result", "asset"]:
                    try:
                        v = n.get_editor_property(prop)
                        w("      %s=%s" % (prop, v.get_path_name() if hasattr(v, "get_path_name") else v))
                    except Exception:
                        pass
        except Exception as e:
            w("  NODES %s ERR=%s" % (cls_name, e))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("RETARGET_PROBE_WRITTEN")
