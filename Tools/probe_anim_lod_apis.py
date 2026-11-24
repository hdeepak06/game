import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\anim_lod_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


for name in sorted(dir(unreal)):
    if any(k in name.lower() for k in ["skeletalmesh", "ikrig", "ikretarget", "animationblueprint",
                                       "animsequence", "blendspace", "animgraph", "state machine"]):
        w("CLASS %s" % name)

w("--- SKELETAL MESH OBJECT ---")
sm = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
if sm:
    w("SM_METHODS=%s" % ",".join(sorted(m for m in dir(sm) if any(
        k in m.lower() for k in ["lod", "material", "skeleton", "import", "build", "render"]))))
    for prop in ["skeleton", "materials", "lod_info", "min_lod", "lod_group",
                 "import_data", "enable_per_poly_collision", "asset_import_data"]:
        try:
            val = sm.get_editor_property(prop)
            w("SM_PROP %s=%s" % (prop, val))
        except Exception as e:
            w("SM_PROP %s=ERR:%s" % (prop, e))

w("--- IK RETARGET ASSETS ---")
for path in ["/Game/Characters/Mannequins/Rigs/IK_Mannequin",
             "/Game/Characters/Mannequins/Rigs/RTG_Mannequin"]:
    obj = unreal.EditorAssetLibrary.load_asset(path)
    w("ASSET %s=%s" % (path, obj))
    if obj:
        w("  METHODS=%s" % ",".join(sorted(m for m in dir(obj) if not m.startswith("_"))))

for cls_name in ["IKRigDefinition", "IKRetargeter", "IKRigController", "IKRetargetProcessor",
                 "RetargetChainDefinition", "AnimBlueprint", "BlendSpace1D", "AnimSequence"]:
    cls = getattr(unreal, cls_name, None)
    w("CLASS_DETAIL %s exists=%s" % (cls_name, bool(cls)))
    if cls:
        try:
            w("  %s" % ",".join(sorted(m for m in dir(cls) if not m.startswith("_"))[:200]))
        except Exception as e:
            w("  ERR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ANIM_LOD_PROBE_WRITTEN")
