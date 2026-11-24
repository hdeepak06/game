import os
import traceback
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "VisualTests")
LOG = os.path.join(OUT_DIR, "visual_pie_capture.txt")
SHOT = os.path.join(OUT_DIR, "Hampi_Soldier_PIE.png")
os.makedirs(OUT_DIR, exist_ok=True)
state = {"ticks": 0, "started": False, "shot": False, "handle": None, "finished": False, "camera": None, "soldier": None, "task": None}


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    unreal.log(str(msg))


def finish(msg):
    if state["finished"]:
        return
    state["finished"] = True
    log(msg)
    try:
        if state["handle"] is not None:
            unreal.unregister_slate_post_tick_callback(state["handle"])
    except Exception:
        pass
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception as e:
        log("QUIT_ERR=%s" % e)


def setup_scene():
    eal = unreal.EditorAssetLibrary
    bp = eal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    if not bp:
        raise RuntimeError("character blueprint missing")
    starts = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if isinstance(a, unreal.PlayerStart)]
    if not starts:
        raise RuntimeError("no PlayerStart")
    start_loc = starts[0].get_actor_location()
    log("PLAYER_START=%s" % start_loc)

    soldier = unreal.EditorLevelLibrary.spawn_actor_from_class(
        bp.generated_class(), start_loc, unreal.Rotator(0, 0, 0), transient=False)
    if not soldier:
        raise RuntimeError("soldier spawn failed")
    state["soldier"] = soldier
    log("SOLDIER_SPAWNED=%s" % soldier.get_path_name())
    for comp in soldier.get_components_by_class(unreal.SkeletalMeshComponent):
        log("  MESH=%s ANIM_MODE=%s" % (
            comp.get_editor_property("skeletal_mesh_asset"),
            comp.get_editor_property("animation_mode")))

    focus = unreal.Vector(start_loc.x, start_loc.y, start_loc.z + 100.0)
    cam_loc = unreal.Vector(start_loc.x + 320.0, start_loc.y - 260.0, start_loc.z + 175.0)
    cam_rot = unreal.MathLibrary.find_look_at_rotation(cam_loc, focus)
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, cam_loc, cam_rot, transient=False)
    if not camera:
        raise RuntimeError("camera spawn failed")
    state["camera"] = camera
    try:
        camera.get_camera_component().set_editor_property("field_of_view", 55.0)
    except Exception as e:
        log("CAM_FOV_ERR=%s" % e)
    log("CAMERA=%s LOC=%s ROT=%s" % (camera.get_path_name(), cam_loc, cam_rot))


def tick(delta_time):
    try:
        state["ticks"] += 1
        if state["ticks"] in (1, 10, 30, 60, 90, 120, 150, 180, 210, 240, 260, 270, 300):
            log("TICK=%d DT=%.3f" % (state["ticks"], delta_time))

        if state["ticks"] == 30 and not state["started"]:
            state["started"] = True
            setup_scene()
            sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
            sub.editor_play_simulate()
            log("PIE_STARTED")

        if state["ticks"] == 90 and state["started"]:
            try:
                gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
                cams = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if gw else []
                log("PIE_CAMERAS=%d" % len(cams))
                if cams:
                    state["camera"] = cams[0]
                    log("PIE_CAMERA=%s" % cams[0].get_path_name())
            except Exception as e:
                log("PIE_CAMERA_ERR=%s" % e)

        if state["ticks"] == 150 and state["started"] and not state["shot"]:
            state["shot"] = True
            log("CAPTURE_BEGIN camera=%s" % state["camera"])
            task = unreal.AutomationLibrary.take_high_res_screenshot(
                800, 450, SHOT, camera=state["camera"], delay=0.0, force_game_view=True)
            state["task"] = task
            try:
                log("CAPTURE_TASK valid=%s done=%s" % (task.is_valid_task(), task.is_task_done()))
            except Exception as e:
                log("CAPTURE_TASK_STATUS_ERR=%s" % e)

        if state["task"] is not None and state["ticks"] in (180, 210, 240, 260):
            try:
                log("CAPTURE_STATUS valid=%s done=%s exists=%s" % (
                    state["task"].is_valid_task(), state["task"].is_task_done(), os.path.exists(SHOT)))
            except Exception as e:
                log("CAPTURE_STATUS_ERR=%s" % e)

        if state["ticks"] == 270:
            try:
                unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
                log("PIE_ENDED")
            except Exception as e:
                log("PIE_END_ERR=%s" % e)

        if state["ticks"] == 300:
            finish("VISUAL_CAPTURE_DONE exists=%s size=%s" % (
                os.path.exists(SHOT), os.path.getsize(SHOT) if os.path.exists(SHOT) else -1))
    except Exception:
        log("TICK_ERROR=%s" % traceback.format_exc())
        finish("VISUAL_CAPTURE_FAILED")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("VISUAL_CAPTURE_BEGIN\n")
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
