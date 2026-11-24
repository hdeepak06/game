import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "WeaponM416")
LOG = os.path.join(OUT_DIR, "runtime_test_v2.txt")
SHOT = os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_M416_PIE.png")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SHOT), exist_ok=True)

state = {
    "elapsed": 0.0,
    "pie_start": None,
    "found_at": None,
    "picked_at": None,
    "fire_start_at": None,
    "reload_at": None,
    "started": False,
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
    "camera": None,
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
        return
    equipped_name, equipped = prop_any(c, ["equipped_m416", "EquippedM416"])
    aiming_name, aiming = prop_any(c, ["is_aiming_m416", "b_is_aiming_m416"])
    reloading_name, reloading = prop_any(w, ["reloading", "b_reloading"])
    root = prop(w, "root")
    socket = root.get_attach_socket_name() if root and hasattr(root, "get_attach_socket_name") else "NO_ROOT"
    parent = root.get_attach_parent_actor() if root and hasattr(root, "get_attach_parent_actor") else "NO_ROOT"
    log("%s EQUIPPED[%s]=%s AIMING[%s]=%s AMMO=%s RESERVE=%s RELOADING[%s]=%s" % (
        label, equipped_name, bool(equipped), aiming_name, aiming,
        prop(w, "current_ammo"), prop(w, "reserve_ammo"), reloading_name, reloading))
    log("%s ATTACH socket=%s parent=%s root_rel=%s" % (
        label, socket, parent, prop(root, "relative_location") if root else None))
    log("%s FOV=%s CONTROL_ROT=%s" % (label, fov(), control_rot()))
    return {
        "equipped": bool(equipped),
        "aiming": aiming,
        "ammo": prop(w, "current_ammo"),
        "reserve": prop(w, "reserve_ammo"),
        "reloading": reloading,
        "socket": socket,
        "parent": parent,
        "fov": fov(),
        "rot": control_rot(),
    }


def setup_before_pie():
    eal = unreal.EditorAssetLibrary
    bp = eal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    if not bp:
        raise RuntimeError("character blueprint missing")

    starts = [a for a in unreal.EditorLevelLibrary.get_all_level_actors()
              if isinstance(a, unreal.PlayerStart)]
    if not starts:
        raise RuntimeError("no PlayerStart")
    start_loc = starts[0].get_actor_location()
    log("PLAYER_START=%s" % start_loc)

    character = unreal.EditorLevelLibrary.spawn_actor_from_class(
        bp.generated_class(), start_loc, unreal.Rotator(0, 0, 0), transient=False)
    if not character:
        raise RuntimeError("character spawn failed")
    state["character"] = character
    log("EDITOR_CHARACTER_SPAWNED=%s" % character.get_path_name())

    focus = unreal.Vector(start_loc.x, start_loc.y, start_loc.z + 100.0)
    cam_loc = unreal.Vector(start_loc.x + 320.0, start_loc.y - 260.0, start_loc.z + 175.0)
    cam_rot = unreal.MathLibrary.find_look_at_rotation(cam_loc, focus)
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, cam_loc, cam_rot, transient=False)
    if not camera:
        raise RuntimeError("camera spawn failed")
    state["camera"] = camera
    log("EDITOR_CAMERA_SPAWNED=%s loc=%s rot=%s" % (
        camera.get_path_name(), cam_loc, cam_rot))


def find_pie_actors():
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not gw:
        raise RuntimeError("no PIE game world")
    log("PIE_WORLD=%s" % gw.get_path_name())

    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    if not pc:
        raise RuntimeError("no PIE PlayerController")
    state["controller"] = pc
    log("PIE_PLAYER_CONTROLLER=%s" % pc.get_path_name())

    chars = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
    log("PIE_NATIVE_CHAR_SEARCH=%d" % len(chars))
    if not chars:
        bp = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
        if bp:
            chars = unreal.GameplayStatics.get_all_actors_of_class(gw, bp.generated_class())
    if not chars:
        raise RuntimeError("no soldier character in PIE")
    character = chars[0]
    state["character"] = character
    log("PIE_CHARACTER=%s class=%s" % (character.get_path_name(), character.get_class().get_name()))

    weapons = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.M416Weapon)
    log("PIE_M416_COUNT=%d" % len(weapons))
    for w in weapons:
        log("  PIE_M416=%s loc=%s" % (w.get_path_name(), w.get_actor_location()))
    if not weapons:
        raise RuntimeError("marker did not become an M416Weapon in PIE")
    state["weapon"] = weapons[0]

    cams = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor)
    if cams:
        state["camera"] = cams[0]
        log("PIE_CAMERA=%s" % cams[0].get_path_name())

    # Simulate-mode PIE keeps the spectator pawn. Try to hand control to the soldier
    # so aim FOV and recoil can be observed when the engine permits possession.
    try:
        controlled_before = pc.get_controlled_pawn()
        log("CONTROLLED_BEFORE=%s" % controlled_before)
        pc.un_possess()
        pc.possess(character)
        controlled_after = pc.get_controlled_pawn()
        character_controller = character.get_controller()
        log("CONTROLLED_AFTER=%s CHARACTER_CONTROLLER=%s" % (
            controlled_after, character_controller))
        state["checks"]["possessed"] = (controlled_after == character)
    except Exception as e:
        log("POSSESSION_ERR=%s" % e)
        state["checks"]["possessed"] = False


def pickup():
    c = state["character"]
    w = state["weapon"]
    weapon_loc = w.get_actor_location()
    # PlayerStart pawn settles about 160 cm above the rifle; move within E-pickup radius.
    near = unreal.Vector(weapon_loc.x - 110.0, weapon_loc.y, weapon_loc.z + 90.0)
    c.set_actor_location(near, sweep=False, teleport=True)
    log("MOVED_TO_PICKUP=%s" % c.get_actor_location())
    result = call(c, "try_pickup_m416")
    log("PICKUP_RESULT=%s" % result)
    state["checks"]["pickup"] = bool(result)


def fire_window():
    c = state["character"]
    w = state["weapon"]
    state["rot_before_fire"] = control_rot()
    call(c, "start_m416_fire")
    log("FIRE_STARTED ammo=%s rot=%s" % (prop(w, "current_ammo"), state["rot_before_fire"]))
    state["fire_start_at"] = state["elapsed"]


def stop_fire():
    c = state["character"]
    w = state["weapon"]
    call(c, "stop_m416_fire")
    state["rot_after_fire"] = control_rot()
    ammo = prop(w, "current_ammo")
    log("FIRE_STOPPED ammo=%s rot_after=%s flash_seen=%s" % (
        ammo, state["rot_after_fire"], state["flash_seen"]))
    state["checks"]["automatic_fire"] = isinstance(ammo, int) and ammo < 30
    state["checks"]["muzzle_flash"] = state["flash_seen"]
    if state["rot_before_fire"] is not None and state["rot_after_fire"] is not None:
        state["checks"]["recoil"] = (
            abs(state["rot_after_fire"].pitch - state["rot_before_fire"].pitch) > 0.01
            or abs(state["rot_after_fire"].yaw - state["rot_before_fire"].yaw) > 0.01)


def request_shot():
    if state["shot"] or not state["camera"]:
        return
    state["shot"] = True
    log("SCREENSHOT_REQUEST=%s camera=%s" % (SHOT, state["camera"].get_path_name()))
    try:
        state["shot_task"] = unreal.AutomationLibrary.take_high_res_screenshot(
            800, 450, SHOT, camera=state["camera"], delay=0.0, force_game_view=True)
        log("SCREENSHOT_TASK=%s" % state["shot_task"])
    except Exception as e:
        log("SCREENSHOT_ERR=%s" % e)


def tick(dt):
    try:
        state["elapsed"] += dt

        if not state["started"] and state["elapsed"] >= 2.0:
            state["started"] = True
            setup_before_pie()
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
            state["pie_start"] = state["elapsed"]
            log("PIE_STARTED elapsed=%.2f" % state["elapsed"])

        if state["pie_start"] is not None and not state["found"] and state["elapsed"] - state["pie_start"] >= 4.0:
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
            snapshot("AFTER_AIM_STOP")

        if state["aim_stopped"] and not state["fire_started"] and state["elapsed"] - state["picked_at"] >= 1.75:
            state["fire_started"] = True
            fire_window()

        if state["fire_start_at"] is not None and not state["fire_stopped"] and state["elapsed"] - state["fire_start_at"] >= 0.55:
            state["fire_stopped"] = True
            stop_fire()
            snapshot("AFTER_FIRE")

        if state["fire_stopped"] and not state["reloaded"] and state["elapsed"] - state["fire_start_at"] >= 1.0:
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
            finish("M416_RUNTIME_TEST_V2_DONE shot_exists=%s" % os.path.exists(SHOT))
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("M416_RUNTIME_TEST_V2_FAILED")


# Detect the brief muzzle flash on every tick while the trigger is held.
def watch_flash(tick_fn):
    def wrapped(dt):
        w = state["weapon"]
        if w and state["fire_start_at"] is not None and not state["fire_stopped"]:
            flash = prop(w, "muzzle_flash_mesh")
            if flash and not isinstance(flash, str):
                hidden = prop(flash, "hidden_in_game")
                if hidden is False:
                    state["flash_seen"] = True
        return tick_fn(dt)
    return wrapped


with open(LOG, "w", encoding="utf-8") as f:
    f.write("M416_RUNTIME_TEST_V2_BEGIN\n")
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
