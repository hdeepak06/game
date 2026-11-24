import unreal
LOG = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\cmdline_pie.txt"
state = {"ticks": 0, "done": False, "handle": None}


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
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    except Exception:
        pass
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception as e:
        log("QUIT_ERR=%s" % e)


def tick(dt):
    if state["done"]:
        return
    state["ticks"] += 1
    if state["ticks"] == 80:
        log("TICKS=%d" % state["ticks"])
        sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        gw = sub.get_game_world()
        log("GAME_WORLD=%s" % gw)
        log("IS_PIE=%s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).is_in_play_in_editor())
        if gw:
            pc = unreal.GameplayStatics.get_player_controller(gw, 0)
            log("PC=%s" % pc)
            if pc:
                log("CONTROLLED_PAWN=%s" % pc.get_controlled_pawn())
            chars = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.HampiSoldierCharacter)
            log("CHARS=%d" % len(chars))
            for c in chars:
                log("  CHAR=%s controller=%s" % (c.get_path_name(), c.get_controller()))
        finish("CMDLINE_PIE_PROBE_DONE")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("CMDLINE_PIE_PROBE_BEGIN\n")
try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
except Exception:
    pass
state["handle"] = unreal.register_slate_post_tick_callback(tick)
