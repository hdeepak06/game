import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
DEST = "/Game/Characters/Soldier/Animations"
NAME = "BS_SoldierLocomotion"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "blendspace_report.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def main():
    w("BLENDSPACE_BEGIN")
    eal = unreal.EditorAssetLibrary
    skeleton = eal.load_asset("/Game/Characters/Soldier/SKM_HampiSoldier_Skeleton")
    walk = eal.load_asset(DEST + "/SoldierAnims_walk")
    run = eal.load_asset(DEST + "/SoldierAnims_run")
    if not (skeleton and walk and run):
        raise RuntimeError("missing skeleton or soldier animations")

    path = DEST + "/" + NAME
    bs = eal.load_asset(path)
    if not bs:
        factory = unreal.BlendSpaceFactory1D()
        factory.set_editor_property("target_skeleton", skeleton)
        bs = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            NAME, DEST, unreal.BlendSpace1D, factory)
    if not bs:
        raise RuntimeError("blend space creation failed")

    params = list(bs.get_editor_property("blend_parameters") or [])
    while len(params) < 3:
        params.append(unreal.BlendParameter())
    speed = params[0]
    speed.set_editor_property("display_name", "Speed")
    speed.set_editor_property("min", 0.0)
    speed.set_editor_property("max", 450.0)
    speed.set_editor_property("grid_num", 10)
    speed.set_editor_property("wrap_input", False)
    speed.set_editor_property("snap_to_grid", False)
    params[0] = speed
    for i in (1, 2):
        params[i].set_editor_property("display_name", "Unused%d" % i)
        params[i].set_editor_property("min", 0.0)
        params[i].set_editor_property("max", 0.0)
    bs.set_editor_property("blend_parameters", params)

    def sample(anim, value, rate):
        s = unreal.BlendSample()
        s.set_editor_property("animation", anim)
        s.set_editor_property("sample_value", unreal.Vector(value, 0.0, 0.0))
        s.set_editor_property("rate_scale", rate)
        return s

    samples = [
        sample(walk, 0.0, 0.0),
        sample(walk, 160.0, 1.0),
        sample(run, 450.0, 1.0),
    ]
    bs.set_editor_property("sample_data", samples)
    bs.set_editor_property("loop", True)
    axis_enum = getattr(unreal, "BlendSpaceAxis", None)
    if axis_enum:
        for candidate in ("BSA_X", "BSA_AXIS_X", "BSA_BLEND_PARAMETER_1"):
            if hasattr(axis_enum, candidate):
                try:
                    bs.set_editor_property("axis_to_scale_animation", getattr(axis_enum, candidate))
                    w("AXIS_SCALE=%s" % candidate)
                    break
                except Exception as e:
                    w("AXIS_SCALE_ERR %s=%s" % (candidate, e))
    for method in ("validate_sample_data", "on_sample_data_changed"):
        if hasattr(bs, method):
            try:
                getattr(bs, method)()
                w("CALLED %s" % method)
            except Exception as e:
                w("CALL_ERR %s=%s" % (method, e))

    eal.save_loaded_asset(bs)
    w("BLENDSPACE=%s" % bs.get_path_name())
    w("PARAM0=%s" % bs.get_editor_property("blend_parameters")[0])
    w("SAMPLES=%d" % len(bs.get_editor_property("sample_data") or []))
    for s in bs.get_editor_property("sample_data") or []:
        w("  SAMPLE anim=%s value=%s rate=%s" % (
            s.get_editor_property("animation"),
            s.get_editor_property("sample_value"),
            s.get_editor_property("rate_scale")))
    w("BLENDSPACE_DONE")


try:
    main()
except Exception as e:
    w("BLENDSPACE_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("BLENDSPACE_WRITTEN")
