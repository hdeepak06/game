import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "HUD", "final_validation.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


try:
    w("HUD_FINAL_VALIDATION_BEGIN")

    unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTOR_COUNT=%d" % len(actors))
    w("LANDSCAPE_COUNT=%d" % len([a for a in actors if isinstance(a, unreal.Landscape)]))
    w("PLAYER_START_COUNT=%d" % len([a for a in actors if isinstance(a, unreal.PlayerStart)]))
    w("M416_MARKER_COUNT=%d" % len([a for a in actors if a.actor_has_tag(unreal.Name("M416Pickup"))]))

    mesh_components = 0
    missing = 0
    for actor in actors:
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh_components += 1
            if not comp.get_editor_property("static_mesh"):
                missing += 1
    w("STATIC_MESH_COMPONENTS=%d MISSING_MESHES=%d" % (mesh_components, missing))

    eal = unreal.EditorAssetLibrary
    w("GAMEMODE_ASSET=%s" % bool(eal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode")))
    w("CHARACTER_BP_ASSET=%s" % bool(eal.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")))

    white = eal.load_asset("/Engine/EngineResources/WhiteSquareTexture")
    w("WHITE_TEXTURE=%s CLASS=%s" % (
        bool(white), white.get_class().get_name() if white else "None"))

    ini = read(os.path.join(PROJECT, "Config", "DefaultInput.ini"))
    w("DEFAULT_TOUCH_INTERFACE_NONE=%s" % ("DefaultTouchInterface=None" in ini))

    hud_h = read(os.path.join(PROJECT, "Source", "Battleground", "HampiMobileHUDWidget.h"))
    hud_cpp = read(os.path.join(PROJECT, "Source", "Battleground", "HampiMobileHUDWidget.cpp"))
    soldier_h = read(os.path.join(PROJECT, "Source", "Battleground", "HampiSoldierCharacter.h"))
    soldier_cpp = read(os.path.join(PROJECT, "Source", "Battleground", "HampiSoldierCharacter.cpp"))
    build_cs = read(os.path.join(PROJECT, "Source", "Battleground", "Battleground.Build.cs"))

    required_hud_symbols = [
        "NativeOnTouchStarted", "NativeOnTouchMoved", "NativeOnTouchEnded",
        "SimulateMovementTouch", "SimulateCameraSwipe", "GetButtonPressCount",
        "GetHealthBarPercent", "GetShieldBarPercent",
    ]
    required_soldier_symbols = [
        "SpawnMobileHUD", "GetMobileHUDWidget", "CycleWeaponSlot",
        "TogglePlayerCrouch", "MobileJump", "IsAimingM416",
    ]
    for symbol in required_hud_symbols:
        w("HUD_SYMBOL %s=%s" % (symbol, symbol in hud_h and symbol in hud_cpp))
    for symbol in required_soldier_symbols:
        w("SOLDIER_SYMBOL %s=%s" % (
            symbol, symbol in soldier_h or symbol in soldier_cpp))
    w("SPAWN_HUD_WIRED=%s" % ("SpawnMobileHUD();" in soldier_cpp))
    w("UMG_DEPENDENCIES=%s" % all(dep in build_cs for dep in ["UMG", "Slate", "SlateCore"]))

    runtime = read(os.path.join(PROJECT, "Saved", "HUD", "runtime_test_v1.txt"))
    w("HUD_RUNTIME_ALL_CHECKS_PASSED=%s" % ("CHECK all_checks_passed=True" in runtime))
    w("HUD_RUNTIME_ERRORS_EMPTY=%s" % ("ERRORS=[]" in runtime))
    w("HUD_FINAL_VALIDATION_DONE")
except Exception as e:
    w("HUD_FINAL_VALIDATION_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("HUD_FINAL_VALIDATION_WRITTEN")
