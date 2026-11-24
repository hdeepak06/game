import os
import unreal

MARKER = r"C:\UnrealProjects\Battleground\Saved\Task04FullAudit\viewport_camera_ready.txt"


def main():
    unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
    camera_location = unreal.Vector(-30000.0, -23000.0, 17000.0)
    camera_rotation = unreal.Rotator(0.0, -55.0, 90.0)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_location, camera_rotation)
    world = unreal.EditorLevelLibrary.get_editor_world()
    for command in [
        "viewmode lit",
        "showflag.staticmeshes 1",
        "showflag.landscape 1",
        "showflag.lighting 1",
        "showflag.postprocessing 1",
    ]:
        try:
            unreal.SystemLibrary.execute_console_command(world, command)
        except Exception:
            pass
    with open(MARKER, "w", encoding="utf-8") as f:
        f.write("CAMERA_READY\n")
    unreal.log("TASK04_VIEWPORT_CAMERA_READY")


try:
    main()
except Exception as e:
    with open(MARKER, "w", encoding="utf-8") as f:
        f.write("ERROR:%s\n" % e)
    unreal.log("TASK04_VIEWPORT_CAMERA_ERROR=%s" % e)
