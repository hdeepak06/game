import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "Loot")
LOG = os.path.join(OUT_DIR, "runtime_test_v1.txt")
SHOT = os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_Loot_PIE.png")
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
    "items": [],
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


def call(obj, name, *args):
    fn = getattr(obj, name, None)
    if not fn:
        raise RuntimeError("missing UFUNCTION %s" % name)
    return fn(*args)


def check(name, value):
    state["checks"][name] = bool(value)
    log("CHECK %s=%s" % (name, bool(value)))


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
    state["bots"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiAICharacter)
    state["items"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiLootItem)
    log("LOOT_ITEM_COUNT=%d BOT_COUNT=%d" % (len(state["items"]), len(state["bots"])))
    for item in state["items"]:
        try:
            log("LOOT_ITEM %s amount=%s loc=%s" % (
                call(item, "get_loot_display_name"), call(item, "get_loot_amount"),
                item.get_actor_location()))
        except Exception as e:
            log("LOOT_ITEM_INFO_ERR=%s" % e)


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
        except Exception:
            pass


def request_shot():
    try:
        unreal.AutomationLibrary.take_high_res_screenshot(
            800, 450, SHOT, delay=0.0, force_game_view=True)
        log("SCREENSHOT_REQUEST=%s" % SHOT)
    except Exception as e:
        log("SCREENSHOT_ERR=%s" % e)


def item_consumed(item):
    try:
        return not call(item, "is_available")
    except Exception:
        return True


def inv_count(item_id):
    return call(state["soldier"], "get_inventory_count", item_id)


# --- step actions ---
def act_init():
    isolate_bots()
    request_shot()


def make_pickup_action(index):
    def act():
        item = state["items"][index]
        item_id = call(item, "get_loot_type_id")
        state["soldier"].set_actor_location(
            item.get_actor_location(), sweep=False, teleport=True)
        log("PICKUP_TARGET[%d]=%s" % (index, item_id))
    return act


def act_slots():
    call(state["soldier"], "set_weapon_slot", "Primary", "M416")
    call(state["soldier"], "set_weapon_slot", "Secondary", "None")
    call(state["soldier"], "set_weapon_slot", "Pistol", "None")


def act_medkit_use():
    call(state["soldier"], "apply_test_damage", 40.0)
    log("USE_MEDKIT_RESULT=%s" % call(state["soldier"], "use_consumable", "Medkit"))


def act_drink_use():
    call(state["soldier"], "apply_test_damage", 40.0)
    log("USE_DRINK_RESULT=%s" % call(state["soldier"], "use_consumable", "EnergyDrink"))


def act_armor_use():
    log("USE_ARMOR_RESULT=%s" % call(state["soldier"], "use_consumable", "Armor"))


# --- step verifiers ---
def ver_init():
    check("five_loot_items", len(state["items"]) == 5)
    check("inventory_starts_empty", call(state["soldier"], "get_inventory_summary") == "Empty")
    for slot in ("Primary", "Secondary", "Pistol"):
        check("slot_%s_starts_none" % slot, call(state["soldier"], "get_weapon_slot", slot) == "None")


def ver_noop():
    log("WARMUP_COMPLETE elapsed=%.1f" % state["elapsed"])


def make_pickup_verify(index):
    def verify():
        item = state["items"][index]
        item_id = call(item, "get_loot_type_id")
        amount = call(item, "get_loot_amount")
        before = inv_count(item_id)
        check("loot_%d_consumed" % index, item_consumed(item))
        check("loot_%d_added_to_inventory" % index, inv_count(item_id) >= before + amount)
        log("INVENTORY_AFTER_%d=%s" % (index, call(state["soldier"], "get_inventory_summary")))
    return verify


def ver_all_loot():
    check("ammo_total_90", inv_count("Ammo556") == 90)
    check("medkit_count_1", inv_count("Medkit") == 1)
    check("drink_count_2", inv_count("EnergyDrink") == 2)
    check("armor_count_1", inv_count("Armor") == 1)


def ver_slots():
    check("primary_slot_m416", call(state["soldier"], "get_weapon_slot", "Primary") == "M416")
    check("secondary_slot_none", call(state["soldier"], "get_weapon_slot", "Secondary") == "None")
    check("pistol_slot_none", call(state["soldier"], "get_weapon_slot", "Pistol") == "None")


def ver_medkit_use():
    h = call(state["soldier"], "get_current_player_health")
    check("medkit_use_heals", h >= 95.0)
    check("medkit_use_decrements_stock", inv_count("Medkit") == 0)
    check("ammo_unaffected_by_consumable", inv_count("Ammo556") == 90)


def ver_drink_use():
    check("drink_use_starts_heal", call(state["soldier"], "is_healing"))
    check("drink_use_decrements_stock", inv_count("EnergyDrink") == 1)


def ver_drink_done():
    h = call(state["soldier"], "get_current_player_health")
    check("drink_heal_completes", h >= 99.9)
    check("drink_heal_flag_cleared", not call(state["soldier"], "is_healing"))


def ver_armor_use():
    s = call(state["soldier"], "get_current_player_shield")
    check("armor_use_grants_shield", s >= 45.0)
    check("armor_use_decrements_stock", inv_count("Armor") == 0)


def ver_done():
    exists = os.path.exists(SHOT)
    log("SCREENSHOT exists=%s size=%s" % (
        exists, os.path.getsize(SHOT) if exists else -1))
    check("screenshot", exists)


STEPS = [("INITIAL", act_init, ver_init, 0.3), ("WARMUP", None, ver_noop, 10.0)]
for i in range(5):
    STEPS.append(("PICKUP_%d" % i, make_pickup_action(i), make_pickup_verify(i), 0.6))
STEPS.extend([
    ("ALL_LOOT", None, ver_all_loot, 0.2),
    ("SLOTS", act_slots, ver_slots, 0.2),
    ("MEDKIT_USE", act_medkit_use, ver_medkit_use, 0.3),
    ("DRINK_USE", act_drink_use, ver_drink_use, 0.3),
    ("DRINK_DONE", None, ver_drink_done, 6.0),
    ("ARMOR_USE", act_armor_use, ver_armor_use, 0.3),
    ("DONE", None, ver_done, 0.3),
])


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
                    finish("LOOT_RUNTIME_TEST_V1_DONE")
                else:
                    next_label, act, _, _ = STEPS[state["step"]]
                    if act:
                        act()
                    state["step_at"] = state["elapsed"]

        if state["found"] and state["elapsed"] - state["found_at"] >= 90.0:
            finish("LOOT_RUNTIME_TEST_V1_TIMEOUT")
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("LOOT_RUNTIME_TEST_V1_FAILED")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("LOOT_RUNTIME_TEST_V1_BEGIN\n")
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
