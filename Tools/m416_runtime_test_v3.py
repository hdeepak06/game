import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "WeaponM416")
LOG = os.path.join(OUT_DIR, "runtime_test_v3.txt")
SHOT = os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_M416_PIE.png")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SHOT), exist_ok=True)

state = {
    "elapsed": 0.0,
    "found_at": None,
    "picked_at": None,
    "fire_start_at": None,
    "reload_at": None,
    "found": False,
    "picked": False,
    "aim_started": False,
    "aim_stopped": False,
    "fire_started": False,
    "fire_stopped": False,
    "reloaded": False,
    "shot": False,
    "done": False,
    "handle": None,
    "character": None,
    "weapon": None,
    "controller": None,
    "fov_before_aim": None,
    "fov_during_aim": None,
    "rot_before_fire": None,
    "rot_after_fire": None,
    "flash_seen": False,
    "shot_task": None,
    "checks": {},
}


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    unreal.log(str(msg))


def finish(msg):
    if state["done"]:
        return
    state["done"] = True
    log(msg)
    log("CHECKS=%s" % sorted(state["checks"].items()))
    try:
        if state["handle"] is not None:
            unreal.unregister_slate_post_tick_callback(state["handle"])
    except Exception:
        pass
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    except Exception:
        pass
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception as e:
        log("QUIT_ERR=%s" % e)


def prop(obj, name):
    try:
        return obj.get_editor_property(name)
    except Exception as e:
        return "ERR:%s" % e


def prop_any(obj, names):
    for name in names:
        value = prop(obj, name)
        if not (isinstance(value, str) and value.startswith("ERR:")):
            return name, value
    return None, "MISSING"


def call(obj, name, *args):
    fn = getattr(obj, name, None)
    if not fn:
        raise RuntimeError("missing UFUNCTION %s" % name)
    return fn(*args)


def camera_manager():
    pc = state["controller"]
    if not pc:
        return None
    cm = prop(pc, "player_camera_manager")
    if isinstance(cm, str) and cm.startswith("ERR:"):
        return None
    return cm


def fov():
    cm = camera_manager()
    if not cm:
        return None
    try:
        return cm.get_fov_angle()
    except Exception:
        return None


def control_rot():
    pc = state["controller"]
    if not pc:
        return None
    try:
        return pc.get_control_rotation()
    except Exception:
        return prop(pc, "control_rotation")


def snapshot(label):
    c = state["character"]
    w = state["weapon"]
    if not c or not w:
        log("%s NO_CHAR_OR_WEAPON" % label)
        return None
    _, equipped = prop_any(c, ["equipped_m416", "EquippedM416"])
    _, aiming = prop_any(c, ["is_aiming_m416", "b_is_aiming_m416"])
    _, reloading = prop_any(w, ["reloading", "b_reloading"])
    root = prop(w, "root")
    socket = root.get_attach_socket_name() if root and hasattr(root, "get_attach_socket_name") else "NO_ROOT"
    log("%s EQUIPPED=%s AIMING=%s AMMO=%s RESERVE=%s RELOADING=%s" % (
        label, bool(equipped), aiming, prop(w, "current_ammo"),
        prop(w, "reserve_ammo"), reloading))
    log("%s ATTACH socket=%s root_rel=%s" % (
        label, socket, prop(root, "relative_location") if root else None))
    log("%s FOV=%s CONTROL_ROT=%s" % (label, fov(), control_rot()))
    return {
        "equipped": bool(equipped),
        "aiming": aiming,
        "ammo": prop(w, "current_ammo"),
        "reserve": prop(w, "reserve_ammo"),
        "reloading": reloading,
        "socket": socket,
        "fov": fov(),
        "rot": control_rot(),
    }


def find_pie_actors():
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not gw:
        raise RuntimeError("no PIE game world")
    log("PIE_WORLD=%s" % gw.get_path_name())
    log("IS_PIE=%s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor())

    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    if not pc:
        raise RuntimeError("no PIE PlayerController")
    state["controller"] = pc
    controlled = pc.get_controlled_pawn()
    log("PIE_PLAYER_CONTROLLER=%s CONTROLLED_PAWN=%s" % (pc.get_path_name(), controlled))
    state["checks"]["player_controller"] = controlled is not None

    chars = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
    if not chars:
        bp = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
        if bp:
            chars = unreal.GameplayStatics.get_all_actors_of_class(gw, bp.generated_class())
    if not chars:
        raise RuntimeError("no soldier character in PIE")
    character = chars[0]
    state["character"] = character
    log("PIE_CHARACTER=%s controller=%s" % (character.get_path_name(), character.get_controller()))
    state["checks"]["soldier_possessed"] = (character.get_controller() == pc)

    weapons = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.M416Weapon)
    log("PIE_M416_COUNT=%d" % len(weapons))
    for w in weapons:
        log("  PIE_M416=%s loc=%s" % (w.get_path_name(), w.get_actor_location()))
    if not weapons:
        raise RuntimeError("marker did not become an M416Weapon in PIE")
    state["weapon"] = weapons[0]


def pickup():
    c = state["character"]
    w = state["weapon"]
    weapon_loc = w.get_actor_location()
    near = unreal.Vector(weapon_loc.x - 110.0, weapon_loc.y, weapon_loc.z + 90.0)
    c.set_actor_location(near, sweep=False, teleport=True)
    log("MOVED_TO_PICKUP=%s" % c.get_actor_location())
    result = call(c, "try_pickup_m416")
    log("PICKUP_RESULT=%s" % result)
    state["checks"]["pickup"] = bool(result)


def request_shot():
    if state["shot"]:
        return
    state["shot"] = True
    log("SCREENSHOT_REQUEST=%s" % SHOT)
    try:
        state["shot_task"] = unreal.AutomationLibrary.take_high_res_screenshot(
            800, 450, SHOT, delay=0.0, force_game_view=True)
        log("SCREENSHOT_TASK=%s" % state["shot_task"])
    except Exception as e:
        log("SCREENSHOT_ERR=%s" % e)


def tick(dt):
    try:
        state["elapsed"] += dt
        if dt > 0.0 and state["elapsed"] < 0.01:
            pass

        if not state["found"] and state["elapsed"] >= 5.0:
            state["found"] = True
            state["found_at"] = state["elapsed"]
            find_pie_actors()
            snapshot("AFTER_PIE_FOUND")

        if state["found"] and not state["picked"] and state["elapsed"] - state["found_at"] >= 0.75:
            state["picked"] = True
            state["picked_at"] = state["elapsed"]
            pickup()
            snap = snapshot("AFTER_PICKUP")
            if snap:
                state["checks"]["equipped"] = snap["equipped"]
                state["checks"]["right_hand"] = (str(snap["socket"]) == "RightHand")

        if state["picked"] and not state["aim_started"] and state["elapsed"] - state["picked_at"] >= 0.5:
            state["aim_started"] = True
            state["fov_before_aim"] = fov()
            call(state["character"], "start_m416_aim")
            state["fov_during_aim"] = fov()
            snap = snapshot("AFTER_AIM_START")
            log("AIM FOV before=%s during=%s" % (
                state["fov_before_aim"], state["fov_during_aim"]))
            if snap:
                state["checks"]["aim_flag"] = bool(snap["aiming"])
            if state["fov_before_aim"] is not None and state["fov_during_aim"] is not None:
                state["checks"]["aim_fov"] = state["fov_during_aim"] < state["fov_before_aim"]

        if state["aim_started"] and not state["aim_stopped"] and state["elapsed"] - state["picked_at"] >= 1.25:
            state["aim_stopped"] = True
            call(state["character"], "stop_m416_aim")
            log("AIM_STOPPED FOV=%s" % fov())
            snap = snapshot("AFTER_AIM_STOP")
            if snap and state["fov_before_aim"] is not None:
                state["checks"]["aim_restore"] = abs(snap["fov"] - state["fov_before_aim"]) < 0.1

        if state["aim_stopped"] and not state["fire_started"] and state["elapsed"] - state["picked_at"] >= 1.75:
            state["fire_started"] = True
            state["rot_before_fire"] = control_rot()
            call(state["character"], "start_m416_fire")
            log("FIRE_STARTED ammo=%s rot=%s" % (
                prop(state["weapon"], "current_ammo"), state["rot_before_fire"]))
            state["fire_start_at"] = state["elapsed"]

        if state["fire_start_at"] is not None and not state["fire_stopped"] and state["elapsed"] - state["fire_start_at"] >= 0.65:
            state["fire_stopped"] = True
            call(state["character"], "stop_m416_fire")
            state["rot_after_fire"] = control_rot()
            ammo = prop(state["weapon"], "current_ammo")
            log("FIRE_STOPPED ammo=%s rot_after=%s flash_seen=%s" % (
                ammo, state["rot_after_fire"], state["flash_seen"]))
            state["checks"]["automatic_fire"] = isinstance(ammo, int) and ammo < 30
            state["checks"]["muzzle_flash"] = state["flash_seen"]
            if state["rot_before_fire"] and state["rot_after_fire"]:
                state["checks"]["recoil"] = (
                    abs(state["rot_after_fire"].pitch - state["rot_before_fire"].pitch) > 0.01
                    or abs(state["rot_after_fire"].yaw - state["rot_before_fire"].yaw) > 0.01)
            snapshot("AFTER_FIRE")

        if state["fire_stopped"] and not state["reloaded"] and state["elapsed"] - state["fire_start_at"] >= 1.1:
            state["reloaded"] = True
            state["reload_at"] = state["elapsed"]
            call(state["character"], "reload_m416")
            log("RELOAD_STARTED")
            snap = snapshot("RELOAD_BEGIN")
            if snap:
                state["checks"]["reload_started"] = bool(snap["reloading"])

        if state["reload_at"] is not None and "reload_finished" not in state["checks"] and state["elapsed"] - state["reload_at"] >= 2.2:
            snap = snapshot("AFTER_RELOAD")
            if snap:
                state["checks"]["reload_finished"] = (
                    snap["ammo"] == 30 and not bool(snap["reloading"]) and snap["reserve"] < 120)

        if state["reload_at"] is not None and not state["shot"] and state["elapsed"] - state["reload_at"] >= 2.5:
            request_shot()

        if state["shot_task"] is not None and state["elapsed"] - state["reload_at"] >= 3.5:
            task = state["shot_task"]
            try:
                log("SCREENSHOT_STATUS valid=%s done=%s exists=%s size=%s" % (
                    task.is_valid_task(), task.is_task_done(), os.path.exists(SHOT),
                    os.path.getsize(SHOT) if os.path.exists(SHOT) else -1))
                state["checks"]["screenshot"] = os.path.exists(SHOT)
            except Exception as e:
                log("SCREENSHOT_STATUS_ERR=%s" % e)

        if state["reload_at"] is not None and state["elapsed"] - state["reload_at"] >= 4.0:
            finish("M416_RUNTIME_TEST_V3_DONE shot_exists=%s" % os.path.exists(SHOT))
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("M416_RUNTIME_TEST_V3_FAILED")


def watch_flash(tick_fn):
    def wrapped(dt):
        w = state["weapon"]
        if w and state["fire_start_at"] is not None and not state["fire_stopped"]:
            flash = prop(w, "muzzle_flash_mesh")
            if flash and not isinstance(flash, str) and prop(flash, "hidden_in_game") is False:
                state["flash_seen"] = True
        return tick_fn(dt)
    return wrapped


with open(LOG, "w", encoding="utf-8") as f:
    f.write("M416_RUNTIME_TEST_V3_BEGIN\n")
try:
    unreal.load_module("Battleground")
    log("MODULE_LOADED")
except Exception as e:
    log("MODULE_LOAD_ERR=%s" % e)
try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    log("KEEP_ALIVE=True")
except Exception as e:
    log("KEEP_ALIVE_ERR=%s" % e)
state["handle"] = unreal.register_slate_post_tick_callback(watch_flash(tick))
log("CALLBACK_REGISTERED")
