import unreal

MARKER = r"C:\UnrealProjects\Battleground\Saved\Task05Audit\temple_camera_ready.txt"


def main():
    unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
    # East-south-east elevated view looking at the nine-tier eastern gopuram.
    camera_location = unreal.Vector(-35500.0, 10500.0, 7000.0)
    camera_rotation = unreal.Rotator(0.0, -34.0, 151.0)
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
        f.write("TEMPLE_CAMERA_READY\n")
    unreal.log("TASK05_TEMPLE_CAMERA_READY")


try:
    main()
except Exception as e:
    with open(MARKER, "w", encoding="utf-8") as f:
        f.write("ERROR:%s\n" % e)
    unreal.log("TASK05_TEMPLE_CAMERA_ERROR=%s" % e)
