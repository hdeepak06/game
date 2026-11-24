import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\blendspace_instance.txt"
lines = []


def w(s=""):
    lines.append(str(s))


eal = unreal.EditorAssetLibrary
path = "/Game/Characters/Soldier/Animations/BS_TempProbe"
bs = eal.load_asset(path)
if not bs:
    factory = unreal.BlendSpaceFactory1D()
    factory.set_editor_property("target_skeleton", eal.load_asset("/Game/Characters/Soldier/SKM_HampiSoldier_Skeleton"))
    bs = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "BS_TempProbe", "/Game/Characters/Soldier/Animations",
        unreal.BlendSpace1D, factory)
w("BS=%s" % bs)

for n in sorted(dir(bs)):
    if n.startswith("_") or callable(getattr(bs, n, None)):
        continue
    try:
        v = bs.get_editor_property(n)
        w("  ATTR %s=%s" % (n, str(v)[:260]))
    except Exception as e:
        w("  ATTR %s ERR=%s" % (n, str(e)[:80]))

candidates = ["blend_samples", "axis_settings", "axis_setting", "blend_space_axes",
              "interpolation_param", "b_stop_at_max_axis_value", "stop_at_max_axis_value",
              "preview_skeletal_mesh", "skeleton", "rate_scale"]
for n in candidates:
    try:
        w("  CAND %s=%s" % (n, str(bs.get_editor_property(n))[:300]))
    except Exception as e:
        w("  CAND %s ERR=%s" % (n, str(e)[:80]))

w("--- BLEND SAMPLE ---")
try:
    s = unreal.BlendSample()
    w("  SAMPLE=%s" % s)
    for n in ["animation", "value", "rate_scale", "play_rate", "sample_value", "time_scale"]:
        try:
            w("  SCAND %s=%s" % (n, str(s.get_editor_property(n))[:200]))
        except Exception as e:
            w("  SCAND %s ERR=%s" % (n, str(e)[:80]))
except Exception as e:
    w("  SAMPLE_ERR=%s" % e)

w("--- FACTORY ---")
f = unreal.BlendSpaceFactory1D()
for n in sorted(dir(f)):
    if n.startswith("_") or callable(getattr(f, n, None)):
        continue
    try:
        w("  FATTR %s=%s" % (n, str(f.get_editor_property(n))[:200]))
    except Exception:
        pass

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("BLENDSPACE_INSTANCE_WRITTEN")
