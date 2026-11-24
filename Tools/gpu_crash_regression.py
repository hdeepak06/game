import os
import time
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "GPUCrash")
REPORT = os.path.join(OUT_DIR, "regression_v1.txt")
SURVIVE_SECONDS = 200.0

os.makedirs(OUT_DIR, exist_ok=True)

state = {
    "elapsed": 0.0,
    "frame": 0,
    "handle": None,
    "done": False,
    "next_marker": 10.0,
    "markers": [],
    "errors": [],
    "start": time.monotonic(),
}


def log(msg):
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    unreal.log(str(msg))


def finish(status):
    if state["done"]:
        return
    state["done"] = True
    log("STATUS=%s" % status)
    log("SURVIVED_SECONDS=%.2f" % state["elapsed"])
    log("FRAMES=%s" % state["frame"])
    log("MARKERS=%s" % state["markers"])
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


def world_snapshot():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        return "NO_GAME_WORLD"
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    soldiers = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.HampiSoldierCharacter)
    bots = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.HampiAICharacter)
    return "actors=%d soldiers=%d bots=%d" % (len(actors), len(soldiers), len(bots))


def tick(dt):
    if state["done"]:
        return
    try:
        state["elapsed"] = time.monotonic() - state["start"]
        state["frame"] += 1
        if state["elapsed"] >= state["next_marker"]:
            snapshot = world_snapshot()
            state["markers"].append("%.1f:%s" % (state["elapsed"], snapshot))
            log("MARKER %s" % state["markers"][-1])
            state["next_marker"] += 10.0
        if state["elapsed"] >= SURVIVE_SECONDS:
            finish("PASS")
    except Exception:
        state["errors"].append(traceback.format_exc())
        finish("FAIL")


with open(REPORT, "w", encoding="utf-8") as f:
    f.write("GPU_CRASH_REGRESSION_V1_BEGIN\n")
try:
    unreal.load_module("Battleground")
    log("MODULE_LOADED")
except Exception as e:
    state["errors"].append("MODULE_LOAD_ERR=%s" % e)
    log(state["errors"][-1])
try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
except Exception:
    pass
state["handle"] = unreal.register_slate_post_tick_callback(tick)
log("CALLBACK_REGISTERED")
