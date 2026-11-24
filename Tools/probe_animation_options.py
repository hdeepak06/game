import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\animation_options.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def members(name):
    cls = getattr(unreal, name, None)
    w("CLASS %s exists=%s" % (name, bool(cls)))
    if cls:
        for n in sorted(dir(cls)):
            if n.startswith("_"):
                continue
            try:
                obj = getattr(cls, n)
                if callable(obj):
                    w("  FN %s" % n)
                else:
                    w("  VAL %s=%s" % (n, str(obj)[:120]))
            except Exception:
                pass


bp = unreal.EditorAssetLibrary.load_asset("/Game/Characters/BP_ThirdPersonCharacter") if unreal.EditorAssetLibrary.does_asset_exist("/Game/Characters/BP_ThirdPersonCharacter") else None
bp_path = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
w("BP=%s" % bp)
if bp:
    try:
        w("BP_PARENT=%s" % bp.get_parent_class())
    except Exception as e:
        w("BP_PARENT_ERR=%s" % e)
    w("BP_GENERATED=%s" % bp.generated_class())
    for n in sorted(dir(bp)):
        if any(k in n.lower() for k in ["component", "reparent", "variable", "graph", "skeleton"]):
            w("  BP_ATTR %s callable=%s" % (n, callable(getattr(bp, n, None))))

for name in ["BlueprintEditorLibrary", "AnimationBlueprintLibrary", "AnimBlueprint",
             "AnimGraphNode_BlendSpacePlayer", "AnimGraphNode_SequencePlayer",
             "AnimGraphNode_StateMachine", "AnimGraphNode_Slot", "BlendSpace1D",
             "AnimationMode", "AnimSingleNodeInstance", "AnimationAsset",
             "SkeletalMeshComponent", "CharacterMovementComponent"]:
    members(name)

w("--- CHAIN SETTINGS ---")
rtg = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Soldier/Rigs/RTG_MannyToSoldier")
if rtg:
    ctrl = unreal.IKRetargeterController.get_controller(rtg)
    for c in ctrl.get_all_chain_settings() or []:
        vals = []
        for p in ["source_chain", "target_chain", "chain_name", "b_enable_chain", "auto_map"]:
            try:
                vals.append("%s=%s" % (p, c.get_editor_property(p)))
            except Exception as e:
                vals.append("%s=ERR" % p)
        w("  " + " ".join(vals))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ANIMATION_OPTIONS_WRITTEN")
