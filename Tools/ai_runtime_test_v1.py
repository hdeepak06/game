import math
import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "AI")
LOG = os.path.join(OUT_DIR, "runtime_test_v1.txt")
SHOT = os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_AI_PIE.png")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SHOT), exist_ok=True)

state = {
    "elapsed": 0.0,
    "found_at": None,
    "patrol_at": None,
    "pickup_at": None,
    "position_at": None,
    "fire_at": None,
    "kill_at": None,
    "found": False,
    "patrol_marked": False,
    "patrol_checked": False,
    "picked": False,
    "positioned": False,
    "detection_checked": False,
    "aim_count": 0,
    "fire_started": False,
    "fire_stopped": False,
    "killed": False,
    "shot": False,
    "done": False,
    "handle": None,
    "pc": None,
    "soldier": None,
    "spawner": None,
    "bots": [],
    "test_bot": None,
    "patrol_locations": [],
    "checks": {},
    "errors": [],
    "shot_task": None,
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
    log("ERRORS=%s" % state["errors"])
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
    except Exception:
        return None


def call(obj, name, *args):
    fn = getattr(obj, name, None)
    if not fn:
        raise RuntimeError("missing UFUNCTION %s" % name)
    return fn(*args)


def find_actors():
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not gw:
        raise RuntimeError("no PIE game world")
    log("PIE_WORLD=%s" % gw.get_path_name())

    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    if not pc:
        raise RuntimeError("no PIE PlayerController")
    state["pc"] = pc
    controlled = pc.get_controlled_pawn()
    log("PLAYER_CONTROLLER=%s PAWN=%s" % (pc.get_path_name(), controlled))
    state["checks"]["player_controller"] = controlled is not None

    chars = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
    if not chars:
        bp = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
        if bp:
            chars = unreal.GameplayStatics.get_all_actors_of_class(gw, bp.generated_class())
    if not chars:
        raise RuntimeError("no soldier character in PIE")
    state["soldier"] = chars[0]
    log("SOLDIER=%s controller=%s health=%s" % (
        chars[0].get_path_name(), chars[0].get_controller(),
        call(chars[0], "get_current_player_health")))
    state["checks"]["soldier_possessed"] = (chars[0].get_controller() == pc)

    spawners = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiAIBotSpawner)
    log("SPAWNER_COUNT=%d" % len(spawners))
    state["checks"]["spawner_exists"] = len(spawners) == 1
    if spawners:
        state["spawner"] = spawners[0]

    bots = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiAICharacter)
    state["bots"] = bots
    log("BOT_COUNT=%d" % len(bots))
    state["checks"]["five_bots"] = len(bots) == 5
    names = []
    locs = []
    for bot in bots:
        name = str(prop(bot, "display_name"))
        names.append(name)
        locs.append(bot.get_actor_location())
        log("BOT name=%s persona=%s health=%s state=%s alive=%s controller=%s loc=%s" % (
            name, prop(bot, "persona"), call(bot, "get_current_health"),
            call(bot, "get_bot_state_name"), call(bot, "is_bot_alive"),
            bot.get_controller(), bot.get_actor_location()))
    state["checks"]["distinct_personas"] = len(set(names)) == 5 and len(bots) == 5
    state["checks"]["bots_alive"] = all(call(b, "is_bot_alive") for b in bots) and len(bots) == 5
    state["checks"]["bots_have_ai_controller"] = all(b.get_controller() is not None for b in bots) and len(bots) == 5
    state["checks"]["distinct_spawns"] = len(set(
        (round(l.x), round(l.y)) for l in locs)) == 5 and len(locs) == 5

    weapons = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.M416Weapon)
    log("M416_COUNT=%d" % len(weapons))
    if weapons:
        state["weapon"] = weapons[0]


def mark_patrol():
    state["patrol_locations"] = [b.get_actor_location() for b in state["bots"]]


def check_patrol():
    moved = 0
    for bot, before in zip(state["bots"], state["patrol_locations"]):
        after = bot.get_actor_location()
        dist = math.sqrt((after.x - before.x) ** 2 + (after.y - before.y) ** 2)
        log("PATROL_MOVE %s dist=%.1f cm state=%s" % (
            prop(bot, "display_name"), dist, call(bot, "get_bot_state_name")))
        if dist > 10.0:
            moved += 1
    state["checks"]["bots_patrol"] = moved >= 3
    log("PATROL_MOVED_COUNT=%d" % moved)


def pickup_weapon():
    w = state.get("weapon")
    if not w:
        state["errors"].append("no M416 available for damage test")
        return
    loc = w.get_actor_location()
    state["soldier"].set_actor_location(
        unreal.Vector(loc.x - 110.0, loc.y, loc.z + 90.0), sweep=False, teleport=True)
    result = call(state["soldier"], "try_pickup_m416")
    log("PICKUP_RESULT=%s equipped=%s" % (
        result, prop(state["soldier"], "equipped_m416") is not None))
    state["checks"]["weapon_equipped_for_damage"] = bool(result)


def position_test_bot():
    bots = state["bots"]
    if not bots:
        return
    bot = bots[0]
    state["test_bot"] = bot
    player = state["soldier"]
    forward = player.get_actor_forward_vector()
    player_loc = player.get_actor_location()
    target = unreal.Vector(
        player_loc.x + forward.x * 260.0,
        player_loc.y + forward.y * 260.0,
        player_loc.z)
    bot.set_actor_location(target, sweep=False, teleport=True)
    movement = bot.character_movement
    try:
        movement.set_editor_property("max_walk_speed", 0.0)
    except Exception as e:
        log("FREEZE_ERR=%s" % e)
    state["test_bot_health_before"] = call(bot, "get_current_health")
    log("TEST_BOT=%s loc=%s health_before=%s player_loc=%s" % (
        prop(bot, "display_name"), bot.get_actor_location(),
        state["test_bot_health_before"], player_loc))


def sample_states():
    states = [(str(prop(b, "display_name")), call(b, "get_bot_state_name")) for b in state["bots"]]
    if any(s == "Engage" for _, s in states):
        state["checks"]["bot_detects_player"] = True


def aim_at_bot():
    bot = state["test_bot"]
    if not bot:
        return
    cm = prop(state["pc"], "player_camera_manager")
    cam_loc = cm.get_camera_location()
    bot_loc = bot.get_actor_location()
    dx = bot_loc.x - cam_loc.x
    dy = bot_loc.y - cam_loc.y
    dz = (bot_loc.z + 65.0) - cam_loc.z
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy)))
    rot = unreal.Rotator(roll=0.0, pitch=pitch, yaw=yaw)
    state["pc"].set_control_rotation(rot)
    log("AIM_AT_BOT pitch=%.2f yaw=%.2f cam=%s bot=%s control_after=%s" % (
        pitch, yaw, cam_loc, bot_loc, state["pc"].get_control_rotation()))


def fire_at_bot():
    cm = prop(state["pc"], "player_camera_manager")
    w = state.get("weapon")
    log("FIRE_DIAG control=%s camera_rot=%s camera_loc=%s ammo_before=%s bot_loc=%s" % (
        state["pc"].get_control_rotation(), cm.get_camera_rotation(), cm.get_camera_location(),
        prop(w, "current_ammo") if w else None,
        state["test_bot"].get_actor_location() if state["test_bot"] else None))
    call(state["soldier"], "start_m416_fire")


def stop_fire():
    call(state["soldier"], "stop_m416_fire")
    bot = state["test_bot"]
    if bot:
        health = call(bot, "get_current_health")
        log("BOT_HEALTH_AFTER_M416 before=%s after=%s ammo_after=%s bot_loc=%s" % (
            state.get("test_bot_health_before"), health,
            prop(state.get("weapon"), "current_ammo") if state.get("weapon") else None,
            bot.get_actor_location() if bot else None))
        state["checks"]["m416_damages_bot"] = health < state.get("test_bot_health_before", health)
        if health is not None and health <= 0.0:
            state["checks"]["bot_dies"] = True
            state["checks"]["bot_killed_by_m416"] = True


def kill_test_bot():
    bot = state["test_bot"]
    if not bot or not call(bot, "is_bot_alive"):
        return
    call(bot, "apply_test_damage", 999.0)
    log("TEST_BOT_AFTER_KILL health=%s alive=%s state=%s" % (
        call(bot, "get_current_health"), call(bot, "is_bot_alive"),
        call(bot, "get_bot_state_name")))
    state["checks"]["bot_dies"] = not call(bot, "is_bot_alive")


def request_shot():
    if state["shot"]:
        return
    state["shot"] = True
    try:
        state["shot_task"] = unreal.AutomationLibrary.take_high_res_screenshot(
            800, 450, SHOT, delay=0.0, force_game_view=True)
        log("SCREENSHOT_REQUEST=%s" % SHOT)
    except Exception as e:
        log("SCREENSHOT_ERR=%s" % e)


def tick(dt):
    try:
        state["elapsed"] += dt

        if not state["found"] and state["elapsed"] >= 5.0:
            state["found"] = True
            state["found_at"] = state["elapsed"]
            find_actors()

        if state["found"] and not state["patrol_marked"] and state["elapsed"] - state["found_at"] >= 1.0:
            state["patrol_marked"] = True
            mark_patrol()

        if state["patrol_marked"] and not state["patrol_checked"] and state["elapsed"] - state["found_at"] >= 4.0:
            state["patrol_checked"] = True
            check_patrol()
            request_shot()

        if state["patrol_checked"] and not state["picked"] and state["elapsed"] - state["found_at"] >= 5.0:
            state["picked"] = True
            pickup_weapon()

        if state["picked"] and not state["positioned"] and state["elapsed"] - state["found_at"] >= 5.75:
            state["positioned"] = True
            position_test_bot()

        if state["positioned"]:
            sample_states()

        if state["positioned"] and state["aim_count"] < 3 and \
                state["elapsed"] - state["found_at"] >= 7.3 + state["aim_count"] * 0.5:
            aim_at_bot()
            state["aim_count"] += 1

        if state["aim_count"] >= 3 and not state["fire_started"] and state["elapsed"] - state["found_at"] >= 9.0:
            state["fire_started"] = True
            state["fire_at"] = state["elapsed"]
            fire_at_bot()

        if state["fire_started"] and not state["fire_stopped"] and state["elapsed"] - state["fire_at"] >= 0.85:
            state["fire_stopped"] = True
            stop_fire()

        if state["fire_stopped"] and not state["killed"] and state["elapsed"] - state["fire_at"] >= 1.6:
            state["killed"] = True
            state["kill_at"] = state["elapsed"]
            kill_test_bot()

        if state["kill_at"] is not None and "player_takes_bot_damage" not in state["checks"] and \
                state["elapsed"] - state["kill_at"] >= 3.0:
            hp = call(state["soldier"], "get_current_player_health")
            log("PLAYER_HEALTH_AFTER_BOT_FIRE=%s" % hp)
            state["checks"]["player_takes_bot_damage"] = hp < 100.0

        if state["kill_at"] is not None and state["shot_task"] is not None and \
                "screenshot" not in state["checks"] and state["elapsed"] - state["kill_at"] >= 1.0:
            try:
                exists = os.path.exists(SHOT)
                log("SCREENSHOT valid=%s done=%s exists=%s size=%s" % (
                    state["shot_task"].is_valid_task(), state["shot_task"].is_task_done(),
                    exists, os.path.getsize(SHOT) if exists else -1))
                state["checks"]["screenshot"] = exists
            except Exception as e:
                log("SCREENSHOT_STATUS_ERR=%s" % e)

        if state["kill_at"] is not None and state["elapsed"] - state["kill_at"] >= 4.0:
            finish("AI_RUNTIME_TEST_V1_DONE")
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("AI_RUNTIME_TEST_V1_FAILED")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("AI_RUNTIME_TEST_V1_BEGIN\n")
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
