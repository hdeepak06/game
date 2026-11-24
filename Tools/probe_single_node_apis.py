import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\single_node_apis.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def doc(obj, label):
    w("--- %s ---" % label)
    try:
        w(str(getattr(obj, "__doc__", None))[:2200])
    except Exception as e:
        w("ERR=%s" % e)


for obj, label in [
    (unreal.BlueprintEditorLibrary.reparent_blueprint, "reparent_blueprint"),
    (unreal.SkeletalMeshComponent.set_animation_mode, "SkeletalMeshComponent.set_animation_mode"),
    (unreal.SkeletalMeshComponent.set_animation, "SkeletalMeshComponent.set_animation"),
    (unreal.SkeletalMeshComponent.play_animation, "SkeletalMeshComponent.play_animation"),
    (unreal.SkeletalMeshComponent.set_play_rate, "SkeletalMeshComponent.set_play_rate"),
    (unreal.AnimSingleNodeInstance.set_blend_space_position, "AnimSingleNodeInstance.set_blend_space_position"),
    (unreal.AnimSingleNodeInstance.set_animation_asset, "AnimSingleNodeInstance.set_animation_asset"),
]:
    doc(obj, label)

w("--- BLENDSPACE METHODS ---")
for n in sorted(dir(unreal.BlendSpace)):
    if any(k in n.lower() for k in ["sample", "axis", "blend"]):
        w("  BS %s callable=%s" % (n, callable(getattr(unreal.BlendSpace, n, None))))
for n in sorted(dir(unreal.BlendSpace1D)):
    if any(k in n.lower() for k in ["sample", "axis", "blend"]):
        w("  BS1D %s callable=%s" % (n, callable(getattr(unreal.BlendSpace1D, n, None))))
for n in sorted(dir(unreal.BlendSpaceBase)):
    if any(k in n.lower() for k in ["sample", "axis", "blend"]):
        w("  BSBASE %s callable=%s" % (n, callable(getattr(unreal.BlendSpaceBase, n, None))))
for clsname in ["BlendSpaceLibrary", "BlendSpace1D", "BlendSampleData", "BlendSpaceAxis", "AnimationBlendInputType"]:
    cls = getattr(unreal, clsname, None)
    w("CLASS %s=%s" % (clsname, cls))
    if cls:
        for n in sorted(dir(cls)):
            if not n.startswith("_") and any(k in n.lower() for k in ["sample", "axis", "add", "edit", "remove", "rate"]):
                w("  %s callable=%s" % (n, callable(getattr(cls, n, None))))

w("--- BP GENERATED SUPER ---")
bp = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
if bp:
    gc = bp.generated_class()
    try:
        super_cls = gc.get_editor_property("super_class") if gc else None
    except Exception as e:
        super_cls = "ERR:%s" % e
    w("  GC=%s SUPER=%s" % (gc, super_cls))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SINGLE_NODE_APIS_WRITTEN")
