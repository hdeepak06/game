import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = PROJECT + r"\Saved\HUD\jump_probe.txt"
state = {"t": 0.0, "done": False, "handle": None}


def log(msg):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    unreal.log(str(msg))


def try_call(obj, name):
    fn = getattr(obj, name, None)
    if not fn:
        return "MISSING"
    try:
        return str(fn())
    except Exception as e:
        return "ERR:%s" % e


def tick(dt):
    if state["done"]:
        return
    state["t"] += dt
    if state["t"] < 6.0:
        return
    state["done"] = True
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    soldiers = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
    s = soldiers[0]
    log("SOLDIER=%s" % s.get_path_name())
    log("METHODS=%s" % ",".join(sorted(m for m in dir(s) if any(k in m.lower() for k in ["jump", "fall", "movement", "crouch"]))))
    for name in ["can_jump", "is_falling", "is_crouched", "is_player_airborne", "is_player_crouched", "is_aiming_m416_active"]:
        log("%s=%s" % (name, try_call(s, name)))
    try:
        cm = s.character_movement
        log("MOVEMENT_MODE=%s" % cm.get_editor_property("movement_mode"))
        log("JUMP_Z=%s" % cm.get_editor_property("jump_z"))
        log("JUMP_MAX_COUNT=%s" % s.get_editor_property("jump_max_count"))
        log("CM_METHODS=%s" % ",".join(sorted(m for m in dir(cm) if any(k in m.lower() for k in ["jump", "fall", "walk", "mode"]))))
    except Exception as e:
        log("MOVEMENT_ERR=%s" % e)
    try:
        s.jump()
        log("DIRECT_JUMP_CALLED")
    except Exception as e:
        log("DIRECT_JUMP_ERR=%s" % e)
    try:
        unreal.unregister_slate_post_tick_callback(state["handle"])
    except Exception:
        pass
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass


with open(OUT, "w", encoding="utf-8") as f:
    f.write("JUMP_PROBE_BEGIN\n")
state["handle"] = unreal.register_slate_post_tick_callback(tick)
