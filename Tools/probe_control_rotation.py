import unreal
LOG = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\control_rotation.txt"
state = {"ticks": 0, "done": False, "handle": None}


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    unreal.log(str(msg))


def tick(dt):
    if state["done"]:
        return
    state["ticks"] += 1
    if state["ticks"] == 80:
        gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pc = unreal.GameplayStatics.get_player_controller(gw, 0)
        log("BEFORE=%s DT=%.4f" % (pc.get_control_rotation(), dt))
        pc.set_control_rotation(unreal.Rotator(10.0, 5.0, 0.0))
        log("AFTER_SET=%s" % pc.get_control_rotation())
        state["done"] = True
        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
        except Exception:
            pass
        unreal.SystemLibrary.quit_editor()


with open(LOG, "w", encoding="utf-8") as f:
    f.write("CONTROL_ROTATION_PROBE_BEGIN\n")
try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
except Exception:
    pass
state["handle"] = unreal.register_slate_post_tick_callback(tick)
