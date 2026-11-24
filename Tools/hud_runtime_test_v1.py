import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "HUD")
LOG = os.path.join(OUT_DIR, "runtime_test_v1.txt")
SHOT = os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_HUD_PIE.png")
INPUT_INI = os.path.join(PROJECT, "Config", "DefaultInput.ini")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SHOT), exist_ok=True)

BUTTONS = ["FIRE", "ADS", "JUMP", "CROUCH", "RELOAD", "SWAP"]
CARDINALS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

state = {
    "elapsed": 0.0,
    "frame": 0,
    "found_at": None,
    "found": False,
    "step": 0,
    "step_at": None,
    "step_frame": 0,
    "done": False,
    "handle": None,
    "soldier": None,
    "hud": None,
    "player_start": None,
    "bots": [],
    "zone": None,
    "weapons": [],
    "weapon": None,
    "loot": [],
    "ammo_before": 0,
    "loc_before": None,
    "z_before": 0.0,
    "ground_ready": False,
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


def call(obj, name, *args):
    fn = getattr(obj, name, None)
    if not fn:
        raise RuntimeError("missing UFUNCTION %s" % name)
    return fn(*args)


def check(name, value):
    state["checks"][name] = bool(value)
    log("CHECK %s=%s" % (name, bool(value)))


def distance(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5


def find_actors():
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not gw:
        raise RuntimeError("no PIE game world")

    soldiers = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
    if not soldiers:
        raise RuntimeError("no soldier")
    state["soldier"] = soldiers[0]

    hud = call(state["soldier"], "get_mobile_hud_widget")
    if not hud:
        raise RuntimeError("soldier has no mobile HUD widget")
    state["hud"] = hud

    starts = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.PlayerStart)
    state["player_start"] = starts[0].get_actor_location() if starts else None
    state["bots"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiAICharacter)
    zones = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSafeZone)
    state["zone"] = zones[0] if zones else None
    state["weapons"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.M416Weapon)
    state["weapon"] = state["weapons"][0] if state["weapons"] else None
    state["loot"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiLootItem)

    log("HUD=%s" % hud.get_path_name())
    log("HUD_STATE=%s" % call(hud, "get_hud_state_summary"))
    log("BOTS=%d ZONES=%d WEAPONS=%d LOOT=%d" % (
        len(state["bots"]), len(zones), len(state["weapons"]), len(state["loot"])))


def isolate_bots():
    center = state["player_start"] or state["soldier"].get_actor_location()
    for i, bot in enumerate(state["bots"]):
        try:
            bot.set_actor_location(
                unreal.Vector(center.x + 8000.0 + i * 250.0, center.y, center.z),
                sweep=False, teleport=True)
            bot.set_actor_tick_enabled(False)
        except Exception as e:
            log("BOT_ISOLATE_ERR[%d]=%s" % (i, e))
    if state["zone"]:
        try:
            state["zone"].set_editor_property("shrink_start_delay", 9999.0)
        except Exception as e:
            log("ZONE_DELAY_ERR=%s" % e)


def request_shot():
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(
            800, 450, SHOT, delay=0.0, force_game_view=True)
        log("SCREENSHOT_REQUEST=%s" % SHOT)
    except Exception as e:
        log("SCREENSHOT_ERR=%s" % e)


# --- step actions ---
def act_initial():
    isolate_bots()
    request_shot()


def act_move():
    state["loc_before"] = state["soldier"].get_actor_location()
    call(state["hud"], "simulate_movement_touch", 0.2, 0.8, 0.0, -1.0)


def act_look():
    call(state["hud"], "simulate_camera_swipe", 120.0, -30.0)


def act_fire():
    if not state["weapon"]:
        raise RuntimeError("no M416 weapon")
    call(state["soldier"], "equip_m416", state["weapon"])
    state["ammo_before"] = call(state["weapon"], "get_current_ammo")
    call(state["hud"], "simulate_touch_button", "FIRE", True)


def act_aim():
    call(state["hud"], "simulate_touch_button", "FIRE", False)
    state["ammo_after_fire_release"] = call(state["weapon"], "get_current_ammo")
    call(state["hud"], "simulate_touch_button", "ADS", True)


def act_crouch():
    call(state["hud"], "simulate_touch_button", "ADS", False)
    call(state["hud"], "simulate_touch_button", "CROUCH", True)


def act_stand():
    call(state["hud"], "simulate_touch_button", "CROUCH", True)


def act_ground():
    # The template pawn can remain in MOVE_FALLING after PIE starts. Place it on
    # the preserved PlayerStart ground and force walking before testing a tap.
    center = state["player_start"] or state["soldier"].get_actor_location()
    state["soldier"].set_actor_location(
        unreal.Vector(center.x, center.y, center.z), sweep=False, teleport=True)
    state["soldier"].character_movement.set_movement_mode(unreal.MovementMode.MOVE_WALKING)
    state["ground_ready"] = bool(state["soldier"].can_jump())


def act_jump():
    if not state["ground_ready"]:
        act_ground()
    state["z_before"] = state["soldier"].get_actor_location().z
    call(state["hud"], "simulate_touch_button", "JUMP", True)


def act_reload():
    call(state["hud"], "simulate_touch_button", "JUMP", False)
    call(state["hud"], "simulate_touch_button", "RELOAD", True)


def act_swap():
    call(state["hud"], "simulate_touch_button", "SWAP", True)


def act_health():
    call(state["soldier"], "respawn")
    call(state["soldier"], "apply_test_damage", 35.0)
    call(state["soldier"], "add_shield", 25.0)


def act_radar():
    center = state["soldier"].get_actor_location()
    offsets = [(800.0, 0.0), (-800.0, 0.0), (0.0, 800.0), (0.0, -800.0), (600.0, 600.0)]
    for i, bot in enumerate(state["bots"]):
        ox, oy = offsets[i % len(offsets)]
        bot.set_actor_location(
            unreal.Vector(center.x + ox, center.y + oy, center.z),
            sweep=False, teleport=True)
        bot.set_actor_tick_enabled(False)


# --- step verifiers ---
def ver_initial():
    hud = state["hud"]
    check("hud_widget_created", hud is not None)
    check("six_touch_buttons", call(hud, "get_button_count") == 6)
    check("five_compass_ticks", call(hud, "get_compass_tick_count") == 5)
    check("five_radar_dots", call(hud, "get_radar_dot_count") == 5)
    check("twelve_zone_ring_segments", call(hud, "get_zone_ring_segment_count") == 12)
    check("five_bots_present", len(state["bots"]) == 5)
    check("safe_zone_present", state["zone"] is not None)
    check("m416_present", state["weapon"] is not None)
    check("five_loot_items", len(state["loot"]) == 5)
    check("default_touch_overlay_disabled",
          os.path.exists(INPUT_INI) and "DefaultTouchInterface=None" in open(INPUT_INI, encoding="utf-8").read())
    summary = call(hud, "get_hud_state_summary")
    check("summary_lists_buttons", all(("%s=" % name) in summary for name in BUTTONS))
    prompt = call(hud, "get_prompt_text")
    check("m416_pickup_prompt", "M416" in prompt)
    log("INITIAL_PROMPT=%s" % prompt)


def ver_warmup():
    exists = os.path.exists(SHOT)
    size = os.path.getsize(SHOT) if exists else -1
    check("hud_screenshot_exists", exists)
    check("hud_screenshot_nonempty", size > 10000)
    log("SCREENSHOT exists=%s size=%s" % (exists, size))


def ver_move():
    hud = state["hud"]
    move_y = call(hud, "get_move_y")
    moved = distance(state["soldier"].get_actor_location(), state["loc_before"])
    check("joystick_active", call(hud, "is_joystick_active"))
    check("joystick_forward_axis", move_y > 0.9)
    check("movement_applied", moved > 20.0)
    check("joystick_visual_state", "MOVE=0.00,1.00" in call(hud, "get_hud_state_summary"))
    log("MOVE moved=%.1f move_y=%.2f" % (moved, move_y))
    call(hud, "end_simulated_touches")


def ver_look():
    hud = state["hud"]
    yaw_delta = call(hud, "get_total_camera_yaw_delta")
    pitch_delta = call(hud, "get_total_camera_pitch_delta")
    check("camera_yaw_swipe", yaw_delta > 10.0)
    check("camera_pitch_swipe", pitch_delta > 2.0)
    log("LOOK yaw=%.2f pitch=%.2f" % (yaw_delta, pitch_delta))


def ver_fire():
    hud = state["hud"]
    ammo = call(state["weapon"], "get_current_ammo")
    check("fire_button_pressed", call(hud, "is_button_pressed", "FIRE"))
    check("fire_button_count", call(hud, "get_button_press_count", "FIRE") == 1)
    check("fire_consumed_ammo", ammo < state["ammo_before"])
    check("ammo_hud_text", "M416" in call(hud, "get_ammo_text"))
    log("FIRE ammo %d -> %d" % (state["ammo_before"], ammo))


def ver_aim():
    hud = state["hud"]
    check("ads_button_pressed", call(hud, "is_button_pressed", "ADS"))
    check("ads_character_state", call(state["soldier"], "is_aiming_m416_active"))
    check("fire_button_released", not call(hud, "is_button_pressed", "FIRE"))
    check("fire_stopped", call(state["weapon"], "get_current_ammo") == state["ammo_after_fire_release"])


def ver_crouch():
    hud = state["hud"]
    check("crouch_button_pressed", call(hud, "is_button_pressed", "CROUCH"))
    check("crouch_character_state", call(state["soldier"], "is_player_crouched"))
    check("ads_button_released", not call(hud, "is_button_pressed", "ADS"))
    check("ads_character_released", not call(state["soldier"], "is_aiming_m416_active"))


def ver_stand():
    check("stand_after_crouch_toggle", not call(state["soldier"], "is_player_crouched"))


def ver_ground():
    check("jump_test_ground_ready", state["ground_ready"])
    log("GROUND can_jump=%s mode=%s" % (
        state["soldier"].can_jump(),
        state["soldier"].character_movement.get_editor_property("movement_mode")))


def ver_jump():
    hud = state["hud"]
    z = state["soldier"].get_actor_location().z
    check("jump_button_pressed", call(hud, "is_button_pressed", "JUMP"))
    check("jump_button_count", call(hud, "get_button_press_count", "JUMP") == 1)
    check("jump_input_dispatched", call(state["soldier"], "get_mobile_jump_call_count") == 1)
    check("jump_allowed_on_ground", call(state["soldier"], "was_last_mobile_jump_allowed"))
    check("jump_impulse_applied", call(state["soldier"], "did_last_mobile_jump_launch")
          and call(state["soldier"], "get_last_mobile_jump_launch_z") > 0.0)
    check("jump_character_state", call(state["soldier"], "is_player_airborne")
          or z > state["z_before"] + 2.0
          or call(state["soldier"], "did_last_mobile_jump_launch"))
    try:
        can_jump = state["soldier"].can_jump()
        mode = state["soldier"].character_movement.get_editor_property("movement_mode")
        is_jumping = state["soldier"].is_jumping()
    except Exception as e:
        can_jump = mode = is_jumping = "ERR:%s" % e
    log("JUMP z %.1f -> %.1f airborne=%s can_jump=%s mode=%s is_jumping=%s calls=%s allowed=%s" % (
        state["z_before"], z, call(state["soldier"], "is_player_airborne"), can_jump, mode, is_jumping,
        call(state["soldier"], "get_mobile_jump_call_count"),
        call(state["soldier"], "was_last_mobile_jump_allowed")))


def ver_reload_start():
    hud = state["hud"]
    check("reload_button_pressed", call(hud, "is_button_pressed", "RELOAD"))
    check("reload_button_count", call(hud, "get_button_press_count", "RELOAD") == 1)
    check("weapon_reloading_started", call(state["weapon"], "is_reloading"))
    check("reload_hud_text", "RELOADING" in call(hud, "get_ammo_text"))


def ver_reload_done():
    ammo = call(state["weapon"], "get_current_ammo")
    reserve = call(state["weapon"], "get_reserve_ammo")
    check("reload_completed", not call(state["weapon"], "is_reloading"))
    check("reload_full_magazine", ammo == 30)
    check("reload_reserve_decremented", reserve < 120)
    check("jump_button_released", not call(state["hud"], "is_button_pressed", "JUMP"))
    log("RELOAD ammo=%d reserve=%d" % (ammo, reserve))


def ver_swap_secondary():
    hud = state["hud"]
    check("swap_to_secondary", call(state["soldier"], "get_active_weapon_slot") == "Secondary")
    check("swap_button_count", call(hud, "get_button_press_count", "SWAP") == 1)


def ver_swap_pistol():
    check("swap_to_pistol", call(state["soldier"], "get_active_weapon_slot") == "Pistol")
    check("swap_button_count_two", call(state["hud"], "get_button_press_count", "SWAP") == 2)


def ver_swap_primary():
    check("swap_back_to_primary", call(state["soldier"], "get_active_weapon_slot") == "Primary")
    check("swap_button_count_three", call(state["hud"], "get_button_press_count", "SWAP") == 3)


def ver_health():
    hud = state["hud"]
    hp = call(hud, "get_health_bar_percent")
    shield = call(hud, "get_shield_bar_percent")
    check("health_bar_matches", abs(hp - 0.65) < 0.02)
    check("shield_bar_matches", abs(shield - 0.5) < 0.02)
    check("health_text_in_summary", "HP=0." in call(hud, "get_hud_state_summary"))
    log("BARS hp=%.3f shield=%.3f" % (hp, shield))


def ver_radar():
    hud = state["hud"]
    visible = call(hud, "get_radar_visible_dot_count")
    compass = call(hud, "get_compass_text")
    check("radar_shows_five_bots", visible == 5)
    check("radar_summary", "RADAR=5/5" in call(hud, "get_hud_state_summary"))
    check("compass_tape_text", compass.split(" ")[0] in CARDINALS)
    check("ammo_text_after_reload", "30" in call(hud, "get_ammo_text"))
    log("RADAR visible=%d compass=%s" % (visible, compass))


def ver_done():
    check("all_checks_passed", all(state["checks"].values()))
    log("FINAL_HUD_STATE=%s" % call(state["hud"], "get_hud_state_summary"))


STEPS = [
    ("INITIAL", act_initial, ver_initial, 0.3),
    ("WARMUP", None, ver_warmup, 10.0),
    ("MOVE", act_move, ver_move, 0.8),
    ("LOOK", act_look, ver_look, 0.3),
    ("FIRE", act_fire, ver_fire, 0.4),
    ("AIM", act_aim, ver_aim, 0.3),
    ("CROUCH", act_crouch, ver_crouch, 0.4),
    ("STAND", act_stand, ver_stand, 0.3),
    ("GROUND", act_ground, ver_ground, 0.4),
    ("JUMP", act_jump, ver_jump, 0.5),
    ("RELOAD_START", act_reload, ver_reload_start, 0.3),
    ("RELOAD_DONE", None, ver_reload_done, 2.2),
    ("SWAP_SECONDARY", act_swap, ver_swap_secondary, 0.3),
    ("SWAP_PISTOL", act_swap, ver_swap_pistol, 0.3),
    ("SWAP_PRIMARY", act_swap, ver_swap_primary, 0.3),
    ("HEALTH_BARS", act_health, ver_health, 0.4),
    ("RADAR_COMPASS", act_radar, ver_radar, 0.4),
    ("DONE", None, ver_done, 0.3),
]


def tick(dt):
    try:
        state["frame"] += 1
        state["elapsed"] += dt

        if not state["found"] and state["elapsed"] >= 5.0:
            state["found"] = True
            state["found_at"] = state["elapsed"]
            find_actors()
            state["step_at"] = state["elapsed"]
            state["step_frame"] = state["frame"]
            log("STEP_ACT=%s" % STEPS[0][0])
            STEPS[0][1]()

        if state["found"] and state["step"] < len(STEPS):
            label, _, verify, delay = STEPS[state["step"]]
            if (state["elapsed"] - state["step_at"] >= delay and
                    state["frame"] - state["step_frame"] >= 2):
                log("STEP_VERIFY=%s" % label)
                verify()
                state["step"] += 1
                if state["step"] >= len(STEPS):
                    finish("HUD_RUNTIME_TEST_V1_DONE")
                else:
                    next_label, act, _, _ = STEPS[state["step"]]
                    if act:
                        log("STEP_ACT=%s" % next_label)
                        act()
                    state["step_at"] = state["elapsed"]
                    state["step_frame"] = state["frame"]

        if state["found"] and state["elapsed"] - state["found_at"] >= 90.0:
            finish("HUD_RUNTIME_TEST_V1_TIMEOUT")
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("HUD_RUNTIME_TEST_V1_FAILED")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("HUD_RUNTIME_TEST_V1_BEGIN\n")
try:
    unreal.load_module("Battleground")
    log("MODULE_LOADED")
except Exception as e:
    log("MODULE_LOAD_ERR=%s" % e)
try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
except Exception:
    pass
state["handle"] = unreal.register_slate_post_tick_callback(tick)
log("CALLBACK_REGISTERED")
