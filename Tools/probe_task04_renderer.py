import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\Task04FullAudit\renderer_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def cvar(name):
    for fn_name in ["get_console_variable_int_value", "get_console_variable_float_value"]:
        fn = getattr(unreal.SystemLibrary, fn_name, None)
        if not fn:
            continue
        try:
            return fn(name)
        except Exception:
            continue
    return "unavailable"


def main():
    unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
    world = unreal.EditorLevelLibrary.get_editor_world()
    for name in [
        "r.Nanite",
        "r.Lumen",
        "r.Shadow.Virtual.Enable",
        "r.RayTracing",
        "r.PathTracing",
        "r.MobileContentUsed",
    ]:
        w("%s=%s" % (name, cvar(name)))
    try:
        unreal.SystemLibrary.execute_console_command(world, "MAP CHECKDEP NOCLEARLOG")
        w("MAPCHECK_CMD_SENT=True")
    except Exception as e:
        w("MAPCHECK_CMD_ERR=%s" % e)


try:
    main()
except Exception as e:
    w("RENDERER_PROBE_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK04_RENDERER_PROBE_WRITTEN")
