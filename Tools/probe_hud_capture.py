import hashlib
import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "HUD", "capture_probe.txt")
SHOT_A = os.path.join(PROJECT, "Saved", "HUD", "capture_gameview.png")
SHOT_B = os.path.join(PROJECT, "Saved", "HUD", "capture_editorview.png")
state = {"t": 0.0, "stage": 0, "handle": None, "hud": None}


def log(msg):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    unreal.log(str(msg))


def sha(path):
    if not os.path.exists(path):
        return "MISSING"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def tick(dt):
    state["t"] += dt
    if state["stage"] == 0 and state["t"] >= 8.0:
        gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        soldiers = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
        state["hud"] = soldiers[0].get_mobile_hud_widget()
        hud = state["hud"]
        log("HUD=%s" % hud.get_path_name())
        log("VISIBILITY=%s" % hud.get_visibility())
        log("CACHED_GEOMETRY=%s" % hud.get_cached_geometry())
        log("IS_FOCUSABLE=%s" % hud.is_focusable)
        try:
            log("LOCAL_SIZE=%s" % hud.get_cached_geometry().get_local_size())
        except Exception as e:
            log("LOCAL_SIZE_ERR=%s" % e)
        unreal.AutomationLibrary.take_high_res_screenshot(
            800, 450, SHOT_A, delay=0.0, force_game_view=True)
        log("SHOT_A_REQUEST=%s" % SHOT_A)
        state["stage"] = 1
        state["t"] = 0.0
    elif state["stage"] == 1 and state["t"] >= 12.0:
        unreal.AutomationLibrary.take_high_res_screenshot(
            800, 450, SHOT_B, delay=0.0, force_game_view=False)
        log("SHOT_B_REQUEST=%s" % SHOT_B)
        state["stage"] = 2
        state["t"] = 0.0
    elif state["stage"] == 2 and state["t"] >= 12.0:
        for tag, path in [("A", SHOT_A), ("B", SHOT_B),
                          ("V", os.path.join(PROJECT, "Saved", "VisualTests", "Hampi_Voice_PIE.png"))]:
            log("HASH_%s=%s size=%s" % (
                tag, sha(path), os.path.getsize(path) if os.path.exists(path) else -1))
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
    f.write("HUD_CAPTURE_PROBE_BEGIN\n")
state["handle"] = unreal.register_slate_post_tick_callback(tick)
