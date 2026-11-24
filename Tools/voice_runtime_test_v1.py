import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "Voice")
LOG = os.path.join(OUT_DIR, "runtime_test_v1.txt")
SHOT = os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_Voice_PIE.png")
SRC = os.path.join(PROJECT, "Saved", "ThirdParty", "KannadaDialogue")
IMPORT_REPORT = os.path.join(OUT_DIR, "import_report.txt")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SHOT), exist_ok=True)

CUES = ["MatchStart", "WeaponEquipped", "EnemySpotted", "ZoneWarning",
        "LowHealth", "Healing", "Victory", "Defeat"]

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
    "director": None,
    "player_start": None,
    "bots": [],
    "zone": None,
    "weapons": [],
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


def bot_alive(bot):
    try:
        return bool(call(bot, "is_bot_alive"))
    except Exception:
        return False


def check(name, value):
    state["checks"][name] = bool(value)
    log("CHECK %s=%s" % (name, bool(value)))


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def has_kannada(text):
    return any("\u0c80" <= ch <= "\u0cff" for ch in text)


def find_actors():
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not gw:
        raise RuntimeError("no PIE game world")

    soldiers = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
    if not soldiers:
        raise RuntimeError("no soldier")
    state["soldier"] = soldiers[0]

    directors = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiDialogueDirector)
    if not directors:
        raise RuntimeError("no dialogue director")
    state["director"] = directors[0]

    starts = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.PlayerStart)
    state["player_start"] = starts[0].get_actor_location() if starts else None
    state["bots"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiAICharacter)
    zones = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSafeZone)
    state["zone"] = zones[0] if zones else None
    state["weapons"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.M416Weapon)

    log("DIRECTOR_COUNT=%d BOT_COUNT=%d ZONE_COUNT=%d WEAPON_COUNT=%d" % (
        len(directors), len(state["bots"]), len(zones), len(state["weapons"])))
    log("DIRECTOR=%s" % state["director"].get_path_name())
    log("PLAYER_START=%s" % state["player_start"])
    log("CUE_HISTORY=%s" % call(state["director"], "get_played_cue_history"))


def isolate_bots():
    center = state["player_start"] or state["soldier"].get_actor_location()
    for i, bot in enumerate(state["bots"]):
        try:
            # Keep bots inside the initial zone but outside the 2500 cm
            # EnemySpotted radius so they do not die or fire during setup.
            bot.set_actor_location(
                unreal.Vector(center.x + 8000.0 + i * 250.0, center.y, center.z),
                sweep=False, teleport=True)
        except Exception as e:
            log("BOT_MOVE_ERR[%d]=%s" % (i, e))
        try:
            bot.set_actor_tick_enabled(False)
        except Exception:
            try:
                bot.character_movement.set_editor_property("max_walk_speed", 0.0)
            except Exception as e:
                log("BOT_FREEZE_ERR[%d]=%s" % (i, e))


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


def act_equip():
    if not state["weapons"]:
        raise RuntimeError("no M416 weapon for WeaponEquipped cue")
    call(state["soldier"], "equip_m416", state["weapons"][0])


def act_heal():
    call(state["soldier"], "apply_test_damage", 40.0)
    call(state["soldier"], "heal", 20.0)


def act_enemy():
    if not state["bots"]:
        raise RuntimeError("no bots for EnemySpotted cue")
    player = state["soldier"].get_actor_location()
    state["bots"][0].set_actor_location(
        unreal.Vector(player.x + 600.0, player.y, player.z),
        sweep=False, teleport=True)


def act_zone():
    if not state["zone"]:
        raise RuntimeError("no safe zone")
    center = state["player_start"] or state["soldier"].get_actor_location()
    for i, bot in enumerate(state["bots"]):
        bot.set_actor_location(
            unreal.Vector(center.x + 8000.0 + i * 100.0, center.y, center.z),
            sweep=False, teleport=True)
    state["zone"].set_editor_property("shrink_start_delay", 0.0)


def act_low_health():
    health = call(state["soldier"], "get_current_player_health")
    if health > 30.0:
        call(state["soldier"], "apply_test_damage", health - 30.0)


def act_defeat():
    call(state["soldier"], "apply_test_damage", 999.0)


def act_respawn():
    call(state["soldier"], "respawn")


def act_victory():
    for i, bot in enumerate(state["bots"]):
        try:
            call(bot, "apply_test_damage", 999.0)
        except Exception as e:
            log("VICTORY_KILL_SKIPPED[%d]=%s" % (i, e))


# --- step verifiers ---
def ver_initial():
    check("one_dialogue_director", state["director"] is not None)
    check("eight_dialogue_sounds", call(state["director"], "get_dialogue_count") == 8)
    for cue in CUES:
        check("cue_available_%s" % cue, call(state["director"], "is_dialogue_available", cue))
    check("five_bots_present", len(state["bots"]) == 5)
    check("safe_zone_present", state["zone"] is not None)
    check("m416_present", len(state["weapons"]) >= 1)

    lines_path = os.path.join(SRC, "dialogue_lines.txt")
    license_path = os.path.join(SRC, "LICENSE.txt")
    wavs = [name for name in os.listdir(SRC) if name.lower().endswith(".wav")]
    check("dialogue_lines_file", os.path.exists(lines_path))
    check("dialogue_license_file", os.path.exists(license_path))
    check("eight_wav_files", len(wavs) == 8)
    check("wav_files_nonempty", all(
        os.path.getsize(os.path.join(SRC, name)) > 100000 for name in wavs))
    check("import_report_exists", os.path.exists(IMPORT_REPORT))

    if os.path.exists(lines_path):
        lines = [line for line in read_text(lines_path).splitlines() if line.strip()]
        check("eight_dialogue_lines", len(lines) == 8)
        check("dialogue_lines_are_kannada", all(has_kannada(line.split("|")[1]) for line in lines))
        log("DIALOGUE_LINES=%s" % " || ".join(lines))
    if os.path.exists(license_path):
        license_text = read_text(license_path)
        check("license_names_edge_tts", "edge-tts" in license_text)
        check("license_names_lgplv3", "LGPLv3" in license_text)
        check("license_names_kannada_voices",
              "kn-IN-GaganNeural" in license_text and "kn-IN-SapnaNeural" in license_text)
    if os.path.exists(IMPORT_REPORT):
        report = read_text(IMPORT_REPORT)
        check("import_report_eight_sounds", report.count("SOUND=") == 8)
        check("import_report_all_loaded", "loaded=False" not in report)


def ver_noop():
    check("match_start_autoplay", call(state["director"], "has_played_cue", "MatchStart"))
    check("bots_alive_after_warmup", all(bot_alive(bot) for bot in state["bots"]))
    log("WARMUP_COMPLETE elapsed=%.1f history=%s" % (
        state["elapsed"], call(state["director"], "get_played_cue_history")))


def ver_equip():
    last = call(state["director"], "get_last_cue")
    check("weapon_equipped_autoplay", last == "WeaponEquipped")
    check("weapon_equipped_history", call(state["director"], "has_played_cue", "WeaponEquipped"))
    check("weapon_equipped_audio_playing", call(state["director"], "is_playing_dialogue"))
    check("weapon_primary_slot", call(state["soldier"], "get_weapon_slot", "Primary") == "M416")
    repeat = call(state["director"], "play_dialogue", "WeaponEquipped")
    check("weapon_cue_cooldown", repeat is False)
    log("WEAPON_CUE last=%s repeat=%s history=%s" % (
        last, repeat, call(state["director"], "get_played_cue_history")))


def ver_heal():
    health = call(state["soldier"], "get_current_player_health")
    check("healing_autoplay", call(state["director"], "has_played_cue", "Healing"))
    check("healing_cue_last", call(state["director"], "get_last_cue") == "Healing")
    check("healing_audio_playing", call(state["director"], "is_playing_dialogue"))
    check("heal_test_health", abs(health - 80.0) < 0.01)
    log("HEAL health=%.1f history=%s" % (
        health, call(state["director"], "get_played_cue_history")))


def ver_enemy():
    check("enemy_spotted_autoplay", call(state["director"], "has_played_cue", "EnemySpotted"))
    check("enemy_spotted_cue_last", call(state["director"], "get_last_cue") == "EnemySpotted")
    log("ENEMY_CUE last=%s history=%s" % (
        call(state["director"], "get_last_cue"),
        call(state["director"], "get_played_cue_history")))


def ver_zone():
    phase = call(state["zone"], "get_phase") if state["zone"] else -1
    check("zone_phase_started", phase > 0)
    check("zone_warning_autoplay", call(state["director"], "has_played_cue", "ZoneWarning"))
    check("zone_warning_cue_last", call(state["director"], "get_last_cue") == "ZoneWarning")
    log("ZONE phase=%s history=%s" % (
        phase, call(state["director"], "get_played_cue_history")))


def ver_low_health():
    health = call(state["soldier"], "get_current_player_health")
    check("low_health_autoplay", call(state["director"], "has_played_cue", "LowHealth"))
    check("low_health_cue_last", call(state["director"], "get_last_cue") == "LowHealth")
    check("low_health_value", 0.0 < health <= 30.01)
    log("LOW_HEALTH health=%.1f history=%s" % (
        health, call(state["director"], "get_played_cue_history")))


def ver_defeat():
    check("defeat_autoplay", call(state["director"], "has_played_cue", "Defeat"))
    check("defeat_cue_last", call(state["director"], "get_last_cue") == "Defeat")
    check("defeat_player_dead", not call(state["soldier"], "is_player_alive"))
    log("DEFEAT history=%s" % call(state["director"], "get_played_cue_history"))


def ver_respawn():
    check("respawn_after_defeat", call(state["soldier"], "is_player_alive"))
    check("respawn_full_health", abs(call(state["soldier"], "get_current_player_health") - 100.0) < 0.01)
    check("defeat_still_recorded", call(state["director"], "has_played_cue", "Defeat"))
    check("bots_alive_before_victory", all(bot_alive(bot) for bot in state["bots"]))


def ver_victory():
    alive = [bot for bot in state["bots"] if bot_alive(bot)]
    check("all_bots_dead_for_victory", len(alive) == 0)
    check("victory_autoplay", call(state["director"], "has_played_cue", "Victory"))
    check("victory_cue_last", call(state["director"], "get_last_cue") == "Victory")
    log("VICTORY alive_bots=%d history=%s" % (
        len(alive), call(state["director"], "get_played_cue_history")))


def ver_done():
    exists = os.path.exists(SHOT)
    log("SCREENSHOT exists=%s size=%s" % (
        exists, os.path.getsize(SHOT) if exists else -1))
    check("screenshot", exists)
    check("all_eight_cues_played", call(state["director"], "get_played_cue_count") >= 8)
    log("FINAL_CUE_HISTORY=%s" % call(state["director"], "get_played_cue_history"))


STEPS = [
    ("INITIAL", act_initial, ver_initial, 0.3),
    ("WARMUP", None, ver_noop, 10.0),
    ("EQUIP", act_equip, ver_equip, 0.5),
    ("HEAL", act_heal, ver_heal, 0.5),
    ("ENEMY", act_enemy, ver_enemy, 0.5),
    ("ZONE", act_zone, ver_zone, 0.5),
    ("LOW_HEALTH", act_low_health, ver_low_health, 0.5),
    ("DEFEAT", act_defeat, ver_defeat, 0.5),
    ("RESPAWN", act_respawn, ver_respawn, 0.5),
    ("VICTORY", act_victory, ver_victory, 0.5),
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
                    finish("VOICE_RUNTIME_TEST_V1_DONE")
                else:
                    next_label, act, _, _ = STEPS[state["step"]]
                    if act:
                        log("STEP_ACT=%s" % next_label)
                        act()
                    state["step_at"] = state["elapsed"]
                    state["step_frame"] = state["frame"]

        if state["found"] and state["elapsed"] - state["found_at"] >= 90.0:
            finish("VOICE_RUNTIME_TEST_V1_TIMEOUT")
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("VOICE_RUNTIME_TEST_V1_FAILED")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("VOICE_RUNTIME_TEST_V1_BEGIN\n")
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
