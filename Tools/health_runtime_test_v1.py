import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "Health")
LOG = os.path.join(OUT_DIR, "runtime_test_v1.txt")
SHOT = os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_Health_PIE.png")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SHOT), exist_ok=True)

state = {
    "elapsed": 0.0,
    "found_at": None,
    "found": False,
    "step": 0,
    "step_at": None,
    "done": False,
    "handle": None,
    "soldier": None,
    "player_start": None,
    "bots": [],
    "items": {},
    "health_before_hot": None,
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


def call(obj, name, *args):
    fn = getattr(obj, name, None)
    if not fn:
        raise RuntimeError("missing UFUNCTION %s" % name)
    return fn(*args)


def snap():
    p = state["soldier"]
    return (call(p, "get_current_player_health"), call(p, "get_current_player_shield"),
            call(p, "is_player_alive"), call(p, "is_healing"))


def log_snap(label):
    h, s, alive, healing = snap()
    log("SNAP %s health=%.1f shield=%.1f alive=%s healing=%s" % (label, h, s, alive, healing))


def check(name, value):
    state["checks"][name] = bool(value)
    log("CHECK %s=%s" % (name, bool(value)))


def item_consumed(name):
    item = state["items"].get(name)
    if not item:
        return False
    try:
        return not call(item, "is_available")
    except Exception:
        # Picked-up items are destroyed after a short lifespan.
        return True


def find_actors():
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not gw:
        raise RuntimeError("no PIE game world")
    soldiers = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
    if not soldiers:
        raise RuntimeError("no soldier")
    state["soldier"] = soldiers[0]

    starts = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.PlayerStart)
    state["player_start"] = starts[0].get_actor_location() if starts else None
    log("PLAYER_START=%s" % state["player_start"])

    state["bots"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiAICharacter)
    items = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiHealingItem)
    for item in items:
        state["items"][call(item, "get_item_type_name")] = item
    log("BOT_COUNT=%d ITEM_TYPES=%s" % (len(state["bots"]), sorted(state["items"].keys())))


def isolate_bots():
    center = state["player_start"]
    if not center:
        return
    for i, bot in enumerate(state["bots"]):
        bot.set_actor_location(
            unreal.Vector(center.x + 50000.0 + i * 200.0, center.y, center.z + 300.0),
            sweep=False, teleport=True)
        try:
            bot.character_movement.set_editor_property("max_walk_speed", 0.0)
        except Exception as e:
            log("BOT_FREEZE_ERR=%s" % e)


def request_shot():
    try:
        state["shot_task"] = unreal.AutomationLibrary.take_high_res_screenshot(
            800, 450, SHOT, delay=0.0, force_game_view=True)
        log("SCREENSHOT_REQUEST=%s" % SHOT)
    except Exception as e:
        log("SCREENSHOT_ERR=%s" % e)


def teleport_to_item(item_type):
    item = state["items"].get(item_type)
    if not item:
        raise RuntimeError("missing item %s" % item_type)
    state["soldier"].set_actor_location(item.get_actor_location(), sweep=False, teleport=True)
    log("TELEPORT_TO=%s loc=%s" % (item_type, item.get_actor_location()))


# --- step actions ---
def act_init():
    isolate_bots()
    request_shot()
    log_snap("INITIAL")


def act_damage30():
    call(state["soldier"], "apply_test_damage", 30.0)
    log_snap("AFTER_DAMAGE30")


def act_shield():
    call(state["soldier"], "add_shield", 50.0)
    call(state["soldier"], "apply_test_damage", 20.0)
    log_snap("AFTER_SHIELD_ABSORB")


def act_heal_cap():
    call(state["soldier"], "heal", 25.0)
    call(state["soldier"], "heal", 50.0)
    log_snap("AFTER_INSTANT_HEAL_CAP")


def act_hot_start():
    call(state["soldier"], "apply_test_damage", 40.0)
    state["health_before_hot"] = call(state["soldier"], "get_current_player_health")
    call(state["soldier"], "start_heal_over_time", 40.0, 2.0)
    log_snap("HOT_START")


def act_death():
    call(state["soldier"], "apply_test_damage", 999.0)
    log_snap("AFTER_LETHAL_DAMAGE")


def act_respawn():
    call(state["soldier"], "respawn")
    log_snap("AFTER_RESPAWN")


def act_medkit():
    call(state["soldier"], "apply_test_damage", 40.0)
    teleport_to_item("Medkit")
    log_snap("MEDKit_SETUP")


def act_drink():
    call(state["soldier"], "apply_test_damage", 40.0)
    teleport_to_item("EnergyDrink")
    log_snap("DRINK_SETUP")


def act_armor():
    teleport_to_item("Armor")
    log_snap("ARMOR_SETUP")


def ver_noop():
    log("WARMUP_COMPLETE elapsed=%.1f" % state["elapsed"])


# --- step verifiers ---
def ver_init():
    h, s, a, _ = snap()
    check("initial_full_health", abs(h - 100.0) < 0.01)
    check("initial_no_shield", abs(s) < 0.01)
    check("initial_alive", a)
    check("three_healing_items", len(state["items"]) == 3)
    for name in ("Medkit", "EnergyDrink", "Armor"):
        check("item_%s_exists" % name, name in state["items"])


def ver_damage30():
    h, s, a, _ = snap()
    check("damage_reduces_health", abs(h - 70.0) < 0.01)
    check("damage_keeps_no_shield", abs(s) < 0.01)
    check("alive_after_damage", a)


def ver_shield():
    h, s, a, _ = snap()
    check("shield_absorbs_damage", abs(s - 30.0) < 0.01)
    check("health_unchanged_behind_shield", abs(h - 70.0) < 0.01)
    check("alive_behind_shield", a)


def ver_heal_cap():
    h, _, a, _ = snap()
    check("instant_heal", abs(h - 100.0) < 0.01)
    check("alive_after_heal", a)


def ver_hot_start():
    h, s, a, healing = snap()
    check("hot_damage_applied", abs(state["health_before_hot"] - 90.0) < 0.01)
    check("hot_shield_depleted", abs(s) < 0.01)
    check("hot_flag_set", healing)
    check("alive_during_hot", a)


def ver_hot_mid():
    h, _, a, healing = snap()
    log("HOT_MID health=%.1f before=%.1f" % (h, state["health_before_hot"]))
    check("hot_heals_over_time", h > state["health_before_hot"] + 1.0)
    check("hot_still_active", healing or h >= 99.9)
    check("alive_during_hot_mid", a)


def ver_hot_done():
    h, _, a, healing = snap()
    check("hot_completes", abs(h - 100.0) < 0.01)
    check("hot_flag_cleared", not healing)
    check("alive_after_hot", a)


def ver_death():
    h, s, a, _ = snap()
    check("lethal_damage_kills", abs(h) < 0.01 and not a)
    check("death_clears_shield", abs(s) < 0.01)
    check("death_source_recorded", call(state["soldier"], "get_last_damage_source") != "None")


def ver_respawn():
    h, s, a, healing = snap()
    loc = state["soldier"].get_actor_location()
    start = state["player_start"]
    dist = ((loc.x - start.x) ** 2 + (loc.y - start.y) ** 2) ** 0.5 if start else -1.0
    log("RESPAWN_LOCATION loc=%s distance_to_start=%.1f" % (loc, dist))
    check("respawn_restores_health", abs(h - 100.0) < 0.01)
    check("respawn_restores_alive", a)
    check("respawn_at_player_start", 0.0 <= dist < 250.0)
    check("respawn_clears_healing", not healing)


def ver_medkit():
    h, _, a, _ = snap()
    item = state["items"].get("Medkit")
    check("medkit_consumed", item_consumed("Medkit"))
    check("medkit_restores_health", h >= 95.0)
    check("alive_after_medkit", a)


def ver_drink():
    h, _, a, healing = snap()
    item = state["items"].get("EnergyDrink")
    check("energy_drink_consumed", item_consumed("EnergyDrink"))
    check("energy_drink_starts_heal", healing)
    check("alive_after_drink", a)


def ver_drink_done():
    h, _, a, healing = snap()
    check("energy_drink_completes", abs(h - 100.0) < 0.01)
    check("energy_drink_flag_cleared", not healing)
    check("alive_after_drink_done", a)


def ver_armor():
    h, s, a, _ = snap()
    item = state["items"].get("Armor")
    check("armor_consumed", item_consumed("Armor"))
    check("armor_grants_shield", s >= 45.0)
    check("alive_after_armor", a)


def ver_done():
    exists = os.path.exists(SHOT)
    log("SCREENSHOT exists=%s size=%s" % (
        exists, os.path.getsize(SHOT) if exists else -1))
    check("screenshot", exists)


STEPS = [
    ("INITIAL", act_init, ver_init, 0.3),
    ("WARMUP", None, ver_noop, 10.0),
    ("DAMAGE30", act_damage30, ver_damage30, 0.3),
    ("SHIELD", act_shield, ver_shield, 0.3),
    ("HEAL_CAP", act_heal_cap, ver_heal_cap, 0.3),
    ("HOT_START", act_hot_start, ver_hot_start, 0.2),
    ("HOT_MID", None, ver_hot_mid, 1.2),
    ("HOT_DONE", None, ver_hot_done, 1.4),
    ("DEATH", act_death, ver_death, 0.3),
    ("RESPAWN", act_respawn, ver_respawn, 0.3),
    ("MEDKIT", act_medkit, ver_medkit, 0.6),
    ("DRINK", act_drink, ver_drink, 0.6),
    ("DRINK_DONE", None, ver_drink_done, 2.4),
    ("ARMOR", act_armor, ver_armor, 0.6),
    ("DONE", None, ver_done, 0.3),
]


def tick(dt):
    try:
        state["elapsed"] += dt

        if not state["found"] and state["elapsed"] >= 5.0:
            state["found"] = True
            state["found_at"] = state["elapsed"]
            find_actors()
            state["step_at"] = state["elapsed"]
            STEPS[0][1]()

        if state["found"] and state["step"] < len(STEPS):
            label, _, verify, delay = STEPS[state["step"]]
            if state["elapsed"] - state["step_at"] >= delay:
                log("STEP_VERIFY=%s" % label)
                verify()
                state["step"] += 1
                if state["step"] >= len(STEPS):
                    finish("HEALTH_RUNTIME_TEST_V1_DONE")
                else:
                    next_label, act, _, _ = STEPS[state["step"]]
                    if act:
                        log("STEP_ACT=%s" % next_label)
                        act()
                    state["step_at"] = state["elapsed"]

        if state["found"] and state["elapsed"] - state["found_at"] >= 60.0:
            finish("HEALTH_RUNTIME_TEST_V1_TIMEOUT")
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("HEALTH_RUNTIME_TEST_V1_FAILED")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("HEALTH_RUNTIME_TEST_V1_BEGIN\n")
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
