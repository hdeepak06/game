import traceback
import unreal

LOG = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\pie_controllers.txt"
state = {"ticks": 0, "started": False, "done": False, "handle": None}


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    unreal.log(str(msg))


def finish(msg):
    if state["done"]:
        return
    state["done"] = True
    log(msg)
    try:
        if state["handle"] is not None:
            unreal.unregister_slate_post_tick_callback(state["handle"])
    except Exception:
        pass
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception as e:
        log("QUIT_ERR=%s" % e)


def tick(dt):
    try:
        state["ticks"] += 1
        if state["ticks"] == 30 and not state["started"]:
            state["started"] = True
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
            log("PIE_STARTED")

        if state["ticks"] == 100 and state["started"]:
            gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
            log("GAME_WORLD=%s" % gw)
            for cls_name in ["PlayerController", "AIController", "Pawn", "Character", "CameraActor", "M416Weapon"]:
                cls = getattr(unreal, cls_name, None)
                if not cls:
                    log("CLASS_MISSING=%s" % cls_name)
                    continue
                try:
                    actors = unreal.GameplayStatics.get_all_actors_of_class(gw, cls)
                    log("%s_COUNT=%d" % (cls_name, len(actors)))
                    for a in actors[:5]:
                        log("  %s=%s loc=%s" % (cls_name, a.get_path_name(), a.get_actor_location()))
                except Exception as e:
                    log("%s_ERR=%s" % (cls_name, e))
            try:
                pc = unreal.GameplayStatics.get_player_controller(gw, 0)
                log("PLAYER_CONTROLLER_0=%s" % pc)
            except Exception as e:
                log("PLAYER_CONTROLLER_ERR=%s" % e)
            try:
                unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
                log("PIE_END_REQUESTED")
            except Exception as e:
                log("PIE_END_ERR=%s" % e)

        if state["ticks"] == 140:
            finish("PIE_CONTROLLER_PROBE_DONE")
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("PIE_CONTROLLER_PROBE_FAILED")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("PIE_CONTROLLER_PROBE_BEGIN\n")
try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    log("KEEP_ALIVE=True")
except Exception as e:
    log("KEEP_ALIVE_ERR=%s" % e)
state["handle"] = unreal.register_slate_post_tick_callback(tick)
log("CALLBACK_REGISTERED")
