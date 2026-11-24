import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "SafeZone")
LOG = os.path.join(OUT_DIR, "runtime_test_v1.txt")
SHOT = os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_SafeZone_PIE.png")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SHOT), exist_ok=True)

state = {
    "elapsed": 0.0,
    "found_at": None,
    "config_at": None,
    "radius_sample_1": None,
    "bot_test_at": None,
    "player_test_at": None,
    "shot_at": None,
    "found": False,
    "isolated": False,
    "configured": False,
    "sampled_mid": False,
    "sampled_final": False,
    "bot_placed": False,
    "bot_checked": False,
    "player_placed": False,
    "player_checked": False,
    "shot": False,
    "done": False,
    "handle": None,
    "zone": None,
    "player": None,
    "bots": [],
    "test_bot": None,
    "initial_radius": None,
    "bot_health_before": None,
    "player_health_before": None,
    "bot_last_health": None,
    "player_last_health": None,
    "shot_task": None,
    "checks": {},
    "errors": [],
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
    zones = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSafeZone)
    log("SAFEZONE_COUNT=%d" % len(zones))
    state["checks"]["zone_exists"] = len(zones) == 1
    if not zones:
        raise RuntimeError("no safe zone actor")
    state["zone"] = zones[0]
    state["initial_radius"] = call(zones[0], "get_current_radius")
    log("ZONE_INITIAL radius=%s phase=%s loc=%s" % (
        state["initial_radius"], call(zones[0], "get_phase"), zones[0].get_actor_location()))
    state["checks"]["initial_radius_large"] = state["initial_radius"] >= 20000.0

    players = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
    state["player"] = players[0] if players else None
    if state["player"]:
        inside = call(zones[0], "is_inside", state["player"].get_actor_location())
        log("PLAYER_INITIAL inside=%s health=%s" % (
            inside, call(state["player"], "get_current_player_health")))
        state["checks"]["player_inside_initial"] = bool(inside)

    state["bots"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiAICharacter)
    log("BOT_COUNT=%d" % len(state["bots"]))
    if state["bots"]:
        state["test_bot"] = state["bots"][0]


def isolate_player():
    z = state["zone"]
    player = state["player"]
    if not z or not player:
        return
    center = z.get_actor_location()
    player.set_actor_location(
        unreal.Vector(center.x + 20000.0, center.y, center.z + 300.0),
        sweep=False, teleport=True)
    log("PLAYER_ISOLATED loc=%s inside=%s health=%s" % (
        player.get_actor_location(), call(z, "is_inside", player.get_actor_location()),
        call(player, "get_current_player_health")))
    state["checks"]["player_isolated_inside_initial"] = bool(
        call(z, "is_inside", player.get_actor_location()))


def configure_shrink():
    z = state["zone"]
    z.set_editor_property("initial_radius", 3000.0)
    z.set_editor_property("final_radius", 500.0)
    z.set_editor_property("shrink_start_delay", 1.0)
    z.set_editor_property("phase_duration", 2.0)
    z.set_editor_property("time_between_phases", 0.5)
    z.set_editor_property("phase_count", 2)
    z.set_editor_property("zone_damage_per_second", 12.0)
    log("ZONE_CONFIGURED radius=%s phase=%s" % (
        call(z, "get_current_radius"), call(z, "get_phase")))


def wall_scale():
    z = state["zone"]
    mesh = prop(z, "wall_mesh")
    if not mesh:
        return None
    return prop(mesh, "relative_scale3d")


def sample(label):
    z = state["zone"]
    radius = call(z, "get_current_radius")
    phase = call(z, "get_phase")
    log("ZONE_%s radius=%.1f phase=%s time_to_next=%.2f wall_scale=%s" % (
        label, radius, phase, call(z, "get_time_to_next_phase"), wall_scale()))
    return radius, phase


def place_outside_bot():
    z = state["zone"]
    center = z.get_actor_location()
    log("BOT_HEALTH_POOL=%s" % [
        (str(prop(b, "display_name")), call(b, "get_current_health"),
         call(b, "is_bot_alive")) for b in state["bots"]])
    alive = [b for b in state["bots"] if call(b, "is_bot_alive")]
    if not alive:
        log("BOT_PLACEMENT_ERR=no living bot available")
        state["checks"]["bot_outside_zone"] = False
        return
    bot = alive[0]
    state["test_bot"] = bot
    bot.set_actor_location(
        unreal.Vector(center.x + 6000.0, center.y, center.z + 300.0),
        sweep=False, teleport=True)
    try:
        prop(bot, "character_movement").set_editor_property("max_walk_speed", 0.0)
    except Exception as e:
        log("BOT_FREEZE_ERR=%s" % e)
    state["bot_health_before"] = call(bot, "get_current_health")
    log("BOT_PLACED_OUTSIDE name=%s inside=%s health_before=%s loc=%s" % (
        prop(bot, "display_name"), call(z, "is_inside", bot.get_actor_location()),
        state["bot_health_before"], bot.get_actor_location()))
    state["checks"]["bot_outside_zone"] = not call(z, "is_inside", bot.get_actor_location())


def check_bot_damage():
    bot = state["test_bot"]
    if not bot:
        return
    after = call(bot, "get_current_health")
    if after != state["bot_last_health"]:
        state["bot_last_health"] = after
        z = state["zone"]
        log("BOT_HEALTH_AFTER_ZONE before=%s after=%s alive=%s inside=%s radius=%s loc=%s" % (
            state["bot_health_before"], after, call(bot, "is_bot_alive"),
            call(z, "is_inside", bot.get_actor_location()),
            call(z, "get_current_radius"), bot.get_actor_location()))
    if after is not None and after < state["bot_health_before"]:
        state["checks"]["zone_damages_bot"] = True


def place_outside_player():
    z = state["zone"]
    player = state["player"]
    if not player:
        return
    center = z.get_actor_location()
    player.set_actor_location(
        unreal.Vector(center.x - 6000.0, center.y, center.z + 300.0),
        sweep=False, teleport=True)
    state["player_health_before"] = call(player, "get_current_player_health")
    log("PLAYER_PLACED_OUTSIDE inside=%s health_before=%s loc=%s" % (
        call(z, "is_inside", player.get_actor_location()),
        state["player_health_before"], player.get_actor_location()))
    state["checks"]["player_outside_zone"] = not call(z, "is_inside", player.get_actor_location())


def check_player_damage():
    player = state["player"]
    if not player:
        return
    after = call(player, "get_current_player_health")
    if after != state["player_last_health"]:
        state["player_last_health"] = after
        log("PLAYER_HEALTH_AFTER_ZONE before=%s after=%s" % (
            state["player_health_before"], after))
    if after is not None and after < state["player_health_before"]:
        state["checks"]["zone_damages_player"] = True


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

        if state["found"] and not state["isolated"] and state["elapsed"] - state["found_at"] >= 0.25:
            state["isolated"] = True
            isolate_player()

        if state["isolated"] and not state["configured"] and state["elapsed"] - state["found_at"] >= 0.5:
            state["configured"] = True
            state["config_at"] = state["elapsed"]
            configure_shrink()

        if state["configured"] and not state["sampled_mid"] and state["elapsed"] - state["config_at"] >= 1.0:
            state["sampled_mid"] = True
            radius, phase = sample("MID")
            state["checks"]["shrink_started"] = radius < 3000.0 or phase > 0
            request_shot()

        if state["sampled_mid"] and not state["sampled_final"] and state["elapsed"] - state["config_at"] >= 4.0:
            state["sampled_final"] = True
            radius, phase = sample("FINAL")
            state["checks"]["shrink_reached_final"] = radius <= 550.0 and phase >= 2
            state["checks"]["wall_scales"] = wall_scale() is not None and wall_scale().x < 30.0

        if state["sampled_mid"] and not state["bot_placed"] and state["elapsed"] - state["config_at"] >= 1.2:
            state["bot_placed"] = True
            state["bot_test_at"] = state["elapsed"]
            place_outside_bot()

        if state["bot_placed"] and not state["bot_checked"] and \
                state["elapsed"] - state["bot_test_at"] >= 0.4:
            check_bot_damage()
            if state["checks"].get("zone_damages_bot") or \
                    state["elapsed"] - state["bot_test_at"] >= 5.0:
                state["bot_checked"] = True
                check_bot_damage()

        if state["bot_checked"] and not state["player_placed"] and state["elapsed"] - state["bot_test_at"] >= 1.4:
            state["player_placed"] = True
            state["player_test_at"] = state["elapsed"]
            place_outside_player()

        if state["player_placed"] and not state["player_checked"] and \
                state["elapsed"] - state["player_test_at"] >= 0.4:
            check_player_damage()
            if state["checks"].get("zone_damages_player") or \
                    state["elapsed"] - state["player_test_at"] >= 5.0:
                state["player_checked"] = True
                check_player_damage()

        if state["player_checked"] and state["shot_task"] is not None and \
                "screenshot" not in state["checks"] and state["elapsed"] - state["player_test_at"] >= 1.0:
            try:
                exists = os.path.exists(SHOT)
                log("SCREENSHOT exists=%s size=%s" % (
                    exists, os.path.getsize(SHOT) if exists else -1))
                state["checks"]["screenshot"] = exists
            except Exception as e:
                log("SCREENSHOT_STATUS_ERR=%s" % e)

        if state["player_checked"] and state["sampled_final"] and \
                state["elapsed"] - state["player_test_at"] >= 1.0:
            if "screenshot" not in state["checks"] and state["shot_task"] is not None:
                exists = os.path.exists(SHOT)
                log("SCREENSHOT_FINAL exists=%s size=%s" % (
                    exists, os.path.getsize(SHOT) if exists else -1))
                state["checks"]["screenshot"] = exists
            if "screenshot" in state["checks"]:
                finish("SAFEZONE_RUNTIME_TEST_V1_DONE")

        if state["found"] and state["elapsed"] - state["found_at"] >= 35.0:
            finish("SAFEZONE_RUNTIME_TEST_V1_TIMEOUT")
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("SAFEZONE_RUNTIME_TEST_V1_FAILED")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("SAFEZONE_RUNTIME_TEST_V1_BEGIN\n")
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
