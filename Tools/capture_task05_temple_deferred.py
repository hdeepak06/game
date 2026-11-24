import unreal

MARKER = r"C:\UnrealProjects\Battleground\Saved\Task05Audit\temple_camera_ready.txt"
with open(MARKER, "w", encoding="utf-8") as _f:
    _f.write("SCRIPT_STARTED\n")
_tick_count = 0
_handle = None
_done = False


def apply_camera():
    camera_location = unreal.Vector(-35500.0, 10500.0, 7000.0)
    camera_rotation = unreal.Rotator(0.0, -34.0, 151.0)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_location, camera_rotation)
    with open(MARKER, "w", encoding="utf-8") as f:
        f.write("TEMPLE_CAMERA_READY_DEFERRED\n")
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        return True
    for command in [
        "viewmode lit",
        "showflag.staticmeshes 1",
        "showflag.landscape 1",
        "showflag.lighting 1",
        "showflag.postprocessing 1",
    ]:
        try:
            unreal.SystemLibrary.execute_console_command(world, command)
        except Exception:
            pass
    with open(MARKER, "w", encoding="utf-8") as f:
        f.write("TEMPLE_CAMERA_READY_DEFERRED\n")
    unreal.log("TASK05_TEMPLE_CAMERA_READY_DEFERRED")
    return True


def on_tick(delta_time):
    global _tick_count, _handle, _done
    if _done:
        return
    _tick_count += 1
    if _tick_count < 180:
        return
    _done = True
    try:
        apply_camera()
    except Exception as e:
        with open(MARKER, "w", encoding="utf-8") as f:
            f.write("ERROR:%s\n" % e)
    try:
        if _handle is not None:
            unreal.unregister_slate_post_tick_callback(_handle)
    except Exception:
        pass


try:
    _handle = unreal.register_slate_post_tick_callback(on_tick)
    unreal.log("TASK05_DEFERRED_CAMERA_REGISTERED")
except Exception as e:
    with open(MARKER, "w", encoding="utf-8") as f:
        f.write("REGISTER_ERROR:%s\n" % e)
