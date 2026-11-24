import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "WeaponM416")
LOG = os.path.join(OUT_DIR, "runtime_test.txt")
SHOT = os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_M416_PIE.png")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SHOT), exist_ok=True)

state = {
    "ticks": 0,
    "started": False,
    "possessed": False,
    "picked": False,
    "aimed": False,
    "fired": False,
    "reloaded": False,
    "shot": False,
    "done": False,
    "handle": None,
    "character": None,
    "weapon": None,
    "controller": None,
    "camera": None,
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


def call(obj, name, *args):
    fn = getattr(obj, name, None)
    if not fn:
        raise RuntimeError("missing UFUNCTION %s" % name)
    return fn(*args)


def camera_manager():
    if not state["controller"]:
        return None
    try:
        return state["controller"].get_editor_property("player_camera_manager")
    except Exception:
        return getattr(state["controller"], "player_camera_manager", None)


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


def weapon_state(label):
    w = state["weapon"]
    c = state["character"]
    if not w or not c:
        log("%s WEAPON_OR_CHAR_MISSING" % label)
        return
    log("%s EQUIPPED=%s AMMO=%s RESERVE=%s RELOADING=%s AIMING_FLAG=%s" % (
        label,
        prop(c, "equipped_m416") is not None,
        prop(w, "current_ammo"),
        prop(w, "reserve_ammo"),
        prop(w, "b_reloading"),
        prop(c, "b_is_aiming_m416")))
    try:
        root = w.get_editor_property("root_component")
        log("%s ATTACH_SOCKET=%s PARENT=%s" % (
            label, root.get_attach_socket_name(), root.get_attach_parent_actor()))
    except Exception as e:
        log("%s ATTACH_INFO_ERR=%s" % (label, e))
    log("%s FOV=%s CONTROL_ROT=%s" % (label, fov(), control_rot()))


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

    character = unreal.EditorLevelLibrary.spawn_actor_from_class(
        bp.generated_class(), start_loc, unreal.Rotator(0, 0, 0), transient=False)
    if not character:
        raise RuntimeError("character spawn failed")
    state["character"] = character
    log("EDITOR_CHARACTER_SPAWNED=%s loc=%s" % (
        character.get_path_name(), character.get_actor_location()))

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
        # Blueprint-generated class instances are also native HampiSoldierCharacter.
        bp = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
        log("PIE_BP_ASSET=%s" % bp)
        if bp:
            chars = unreal.GameplayStatics.get_all_actors_of_class(gw, bp.generated_class())
            log("PIE_BP_CHAR_SEARCH=%d" % len(chars))
    if not chars:
        raise RuntimeError("no soldier character in PIE")
    character = chars[0]
    state["character"] = character
    log("PIE_CHARACTER=%s loc=%s class=%s" % (
        character.get_path_name(), character.get_actor_location(), character.get_class().get_name()))

    weapons = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.M416Weapon)
    log("PIE_M416_COUNT=%d" % len(weapons))
    for w in weapons:
        log("  PIE_M416=%s loc=%s" % (w.get_path_name(), w.get_actor_location()))
    state["weapon"] = weapons[0] if weapons else None

    cams = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor)
    if cams:
        state["camera"] = cams[0]
        log("PIE_CAMERA=%s" % cams[0].get_path_name())

    try:
        pc.possess(character)
        log("PIE_POSSESS_OK pawn=%s" % pc.get_controlled_pawn())
    except Exception as e:
        log("PIE_POSSESS_ERR=%s" % e)


def tick(dt):
    try:
        state["ticks"] += 1
        if state["ticks"] in (1, 30, 60, 90, 120, 150, 180, 210, 250, 280, 330, 360, 400, 430):
            log("TICK=%d DT=%.4f" % (state["ticks"], dt))

        if state["ticks"] == 30 and not state["started"]:
            state["started"] = True
            setup_before_pie()
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
            log("PIE_STARTED")

        if state["ticks"] == 90 and state["started"] and not state["possessed"]:
            state["possessed"] = True
            find_pie_actors()

        if state["ticks"] == 120 and state["character"]:
            c = state["character"]
            if not state["weapon"]:
                try:
                    ok = call(c, "try_pickup_m416")
                    log("PICKUP_RESULT=%s" % ok)
                except Exception as e:
                    log("PICKUP_ERR=%s" % e)
                weapons = unreal.GameplayStatics.get_all_actors_of_class(
                    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(),
                    unreal.M416Weapon)
                state["weapon"] = weapons[0] if weapons else None
            state["picked"] = True
            weapon_state("AFTER_PICKUP")

        if state["ticks"] == 150 and state["character"] and not state["aimed"]:
            state["aimed"] = True
            log("AIM_START_FOV_BEFORE=%s" % fov())
            call(state["character"], "start_m416_aim")
            log("AIM_STARTED")
            weapon_state("AFTER_AIM_START")

        if state["ticks"] == 180 and state["character"]:
            call(state["character"], "stop_m416_aim")
            log("AIM_STOPPED")
            weapon_state("AFTER_AIM_STOP")

        if state["ticks"] == 210 and state["character"] and not state["fired"]:
            state["fired"] = True
            log("FIRE_START")
            call(state["character"], "start_m416_fire")
            weapon_state("FIRE_BEGIN")

        if state["ticks"] == 250 and state["character"]:
            call(state["character"], "stop_m416_fire")
            log("FIRE_STOPPED")
            weapon_state("AFTER_FIRE")
            w = state["weapon"]
            sm = prop(w, "muzzle_flash_mesh") if w else None
            if sm and sm != "ERR:None":
                log("MUZZLE_FLASH_HIDDEN_IN_GAME=%s" % prop(sm, "hidden_in_game"))

        if state["ticks"] == 280 and state["character"] and not state["reloaded"]:
            state["reloaded"] = True
            call(state["character"], "reload_m416")
            log("RELOAD_STARTED")
            weapon_state("RELOAD_BEGIN")

        if state["ticks"] == 330:
            weapon_state("AFTER_RELOAD")

        if state["ticks"] == 360 and not state["shot"]:
            state["shot"] = True
            if not os.path.exists(SHOT):
                task = unreal.AutomationLibrary.take_high_res_screenshot(
                    800, 450, SHOT, camera=state["camera"], delay=0.0, force_game_view=True)
                state["shot_task"] = task
                log("SCREENSHOT_REQUESTED=%s exists=%s" % (SHOT, os.path.exists(SHOT)))
            else:
                log("SCREENSHOT_ALREADY_EXISTS=%s" % SHOT)

        if state["ticks"] == 400:
            task = state.get("shot_task")
            if task:
                try:
                    log("SCREENSHOT_STATUS valid=%s done=%s exists=%s size=%s" % (
                        task.is_valid_task(), task.is_task_done(), os.path.exists(SHOT),
                        os.path.getsize(SHOT) if os.path.exists(SHOT) else -1))
                except Exception as e:
                    log("SCREENSHOT_STATUS_ERR=%s" % e)

        if state["ticks"] == 430:
            finish("M416_RUNTIME_TEST_DONE shot_exists=%s" % os.path.exists(SHOT))
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("M416_RUNTIME_TEST_FAILED")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("M416_RUNTIME_TEST_BEGIN\n")
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
state["handle"] = unreal.register_slate_post_tick_callback(tick)
log("CALLBACK_REGISTERED")
