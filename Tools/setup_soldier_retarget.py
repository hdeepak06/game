import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
DEST = "/Game/Characters/Soldier"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "retarget_setup_report.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def enum_members(name):
    cls = getattr(unreal, name, None)
    w("ENUM %s exists=%s" % (name, bool(cls)))
    if cls:
        for n in dir(cls):
            if not n.startswith("_"):
                try:
                    w("  %s=%s" % (n, getattr(cls, n)))
                except Exception:
                    pass


def main():
    w("RETARGET_SETUP_BEGIN")
    eal = unreal.EditorAssetLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mesh = eal.load_asset(DEST + "/SKM_HampiSoldier")
    source_mesh = eal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple")
    source_ik = eal.load_asset("/Game/Characters/Mannequins/Rigs/IK_Mannequin")
    if not (mesh and source_mesh and source_ik):
        raise RuntimeError("missing source/target assets for retargeting")

    enum_members("RetargetSourceOrTarget")
    enum_members("AutoMapChainType")

    rig_dir = DEST + "/Rigs"
    if not eal.does_directory_exist(rig_dir):
        eal.make_directory(rig_dir)
    ik_path = rig_dir + "/IK_Soldier"
    ik = eal.load_asset(ik_path)
    if not ik:
        ik = tools.create_asset("IK_Soldier", rig_dir, unreal.IKRigDefinition,
                                unreal.IKRigDefinitionFactory())
    if not ik:
        raise RuntimeError("IK rig creation failed")
    ik_ctrl = unreal.IKRigController.get_controller(ik)
    w("IK_SET_MESH=%s" % ik_ctrl.set_skeletal_mesh(mesh))
    auto = ik_ctrl.apply_auto_generated_retarget_definition()
    w("IK_AUTO_DEFINITION=%s chains=%s" % (
        auto, [str(c) for c in (ik_ctrl.get_retarget_chains() or [])]))
    if not auto:
        ik_ctrl.set_retarget_root("Hips")
        chains = [
            ("Spine", "Spine", "Spine02"),
            ("Head", "neck", "Head"),
            ("LeftLeg", "LeftUpLeg", "LeftFoot"),
            ("RightLeg", "RightUpLeg", "RightFoot"),
            ("LeftArm", "LeftShoulder", "LeftHand"),
            ("RightArm", "RightShoulder", "RightHand"),
        ]
        for name, start, end in chains:
            try:
                w("  ADD_CHAIN %s -> %s" % (name, ik_ctrl.add_retarget_chain(
                    name, start, end, "")))
            except Exception as e:
                w("  ADD_CHAIN_ERR %s %s" % (name, e))
    eal.save_loaded_asset(ik)
    w("IK_SAVED=%s chains=%s" % (ik.get_path_name(),
                                 [str(c) for c in (ik_ctrl.get_retarget_chains() or [])]))

    rtg_path = rig_dir + "/RTG_MannyToSoldier"
    rtg = eal.load_asset(rtg_path)
    if not rtg:
        rtg = tools.create_asset("RTG_MannyToSoldier", rig_dir, unreal.IKRetargeter,
                                 unreal.IKRetargetFactory())
    if not rtg:
        raise RuntimeError("retargeter creation failed")
    ctrl = unreal.IKRetargeterController.get_controller(rtg)
    src = unreal.RetargetSourceOrTarget.SOURCE
    tgt = unreal.RetargetSourceOrTarget.TARGET
    ctrl.set_ik_rig(src, source_ik)
    ctrl.set_ik_rig(tgt, ik)
    try:
        ctrl.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    except Exception as e:
        w("AUTO_MAP_ERR=%s" % e)
        try:
            ctrl.auto_map_chains(list(unreal.AutoMapChainType)[1], True)
        except Exception as e2:
            w("AUTO_MAP_FALLBACK_ERR=%s" % e2)
    try:
        ctrl.auto_align_all_bones(src)
        ctrl.auto_align_all_bones(tgt)
    except Exception as e:
        w("AUTO_ALIGN_ERR=%s" % e)
    try:
        ctrl.set_preview_mesh(mesh)
    except Exception as e:
        w("PREVIEW_ERR=%s" % e)
    eal.save_loaded_asset(rtg)
    w("RTG_SAVED=%s" % rtg.get_path_name())

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    src_anim = eal.load_asset("/Game/Characters/Mannequins/Animations/Quinn/MF_Idle")
    if not src_anim:
        w("TEST_SOURCE_ANIM_MISSING")
    else:
        data = ar.get_asset_by_object_path(src_anim.get_path_name())
        w("TEST_ASSET_DATA=%s" % data)
        result = unreal.IKRetargetBatchOperation.duplicate_and_retarget(
            [data], source_mesh, mesh, rtg, prefix="TEST_")
        w("TEST_RETARGET_RESULT=%s" % [str(x) for x in (result or [])])
    w("RETARGET_SETUP_DONE")


try:
    main()
except Exception as e:
    w("RETARGET_SETUP_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("RETARGET_SETUP_WRITTEN")
