import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = PROJECT + r"\Saved\HUD\jump_probe2.txt"
state = {"t": 0.0, "stage": 0, "handle": None, "soldier": None, "hud": None, "z0": 0.0}


def log(msg):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    unreal.log(str(msg))


def snapshot(tag):
    s = state["soldier"]
    log("%s z=%.1f mode=%s jumping=%s count=%s pressed=%s can=%s" % (
        tag, s.get_actor_location().z,
        s.character_movement.get_editor_property("movement_mode"),
        s.is_jumping(), s.get_editor_property("jump_current_count"),
        s.get_editor_property("pressed_jump"), s.can_jump()))


def tick(dt):
    state["t"] += dt
    if state["stage"] == 0 and state["t"] >= 12.0:
        gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        state["soldier"] = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)[0]
        state["hud"] = state["soldier"].get_mobile_hud_widget()
        state["z0"] = state["soldier"].get_actor_location().z
        snapshot("BEFORE_BUTTON")
        state["hud"].simulate_touch_button("JUMP", True)
        state["stage"] = 1
        state["t"] = 0.0
    elif state["stage"] == 1 and state["t"] >= 0.6:
        snapshot("AFTER_BUTTON")
        state["hud"].simulate_touch_button("JUMP", False)
        state["soldier"].mobile_jump()
        state["stage"] = 2
        state["t"] = 0.0
    elif state["stage"] == 2 and state["t"] >= 0.6:
        snapshot("AFTER_DIRECT")
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
    f.write("JUMP_PROBE2_BEGIN\n")
state["handle"] = unreal.register_slate_post_tick_callback(tick)
