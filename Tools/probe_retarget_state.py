import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\retarget_state.txt"
lines = []


def w(s=""):
    lines.append(str(s))


for name in ["AutoMapChainType", "RetargetSourceOrTarget"]:
    cls = getattr(unreal, name, None)
    w("ENUM %s=%s" % (name, cls))
    if cls:
        try:
            w("  MEMBERS=%s" % [(k, str(v)) for k, v in cls.__members__.items()])
        except Exception as e:
            w("  MEMBERS_ERR=%s" % e)

rtg = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Soldier/Rigs/RTG_MannyToSoldier")
w("RTG=%s" % rtg)
if rtg:
    ctrl = unreal.IKRetargeterController.get_controller(rtg)
    w("SOURCE_RIG=%s" % ctrl.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE))
    w("TARGET_RIG=%s" % ctrl.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET))
    chains = ctrl.get_all_chain_settings() or []
    w("CHAIN_COUNT=%d" % len(chains))
    for c in chains:
        w("  CHAIN=%s" % c)
    w("ROOT=%s" % ctrl.get_root_settings())

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("RETARGET_STATE_WRITTEN")
