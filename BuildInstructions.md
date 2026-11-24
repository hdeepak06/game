# HAMPI BATTLEGROUND — Build and Test Instructions

_Engine: Unreal Engine 5.4.4 at `G:\Epic Games\UE_5.4\UE_5.4`_

## Editor / game compile

Run from PowerShell in `C:\UnrealProjects\Battleground`:

```powershell
$build = 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Build\BatchFiles\Build.bat'

& $build BattlegroundEditor Win64 Development `
  -Project='C:\UnrealProjects\Battleground\Battleground.uproject' -WaitMutex

& $build Battleground Win64 Development `
  -Project='C:\UnrealProjects\Battleground\Battleground.uproject' -WaitMutex
```

Successful logs are kept in `Saved/WeaponM416/build_editor_recoil.txt` and `Saved/WeaponM416/build_game_recoil.txt` (M416/recoil), `Saved/AI/build_editor_ai_v2.txt` / `build_game_ai_v2.txt` (five AI bots), `Saved/Voice/build_editor_v3.txt` / `build_game_v3.txt` (Kannada dialogue director), and `Saved/HUD/build_editor_v8.txt` / `build_game_v1.txt` (mobile HUD). The latest builds exited 0 with no error lines.

## GPU crash mitigation

UE 5.4 editor autostart enabled the Unreal Insights `gpu` trace channel by default. On this workstation's Intel UHD Graphics (2021 driver, 128 MB dedicated VRAM), that forced D3D11 timestamp queries and ended in `DXGI_ERROR_DEVICE_REMOVED / DXGI_ERROR_DEVICE_HUNG` at `D3D11Query.cpp:361`. All normal PIE commands below therefore include `-traceautostart=0`. This is an editor/test-harness flag only; it does not change gameplay or the Android build.

Evidence: `Saved/GPUCrash/root_cause_report.txt`. Regression command:

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -pie -traceautostart=0 `
  -ExecutePythonScript='C:\UnrealProjects\Battleground\Tools\gpu_crash_regression.py' `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\GPUCrash\regression_editor_v2.log' `
  -windowed -ResX=800 -ResY=450 -nosplash -log
```

The 200-second wall-clock soak passed with `STATUS=PASS`, 572 frames, 316 actors, 1 soldier, 5 bots, and no GPU errors. The HUD harness was also re-run with this flag and still passed 62/62 checks.

## Python structural validation

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -run=pythonscript `
  -script='C:\UnrealProjects\Battleground\Tools\validate_m416_final.py' `
  -unattended -nosplash -nullrhi -log
```

Report: `Saved/WeaponM416/final_validation.txt`.

The mobile HUD adds a dedicated structural check:

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -run=pythonscript `
  -script='C:\UnrealProjects\Battleground\Tools\validate_hud_final.py' `
  -unattended -nosplash -nullrhi -log `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\HUD\final_validation_editor.log'
```

Report: `Saved/HUD/final_validation.txt`. The latest run reports 278 actors, 1 Landscape, 1 PlayerStart, 1 M416 marker, 270 static mesh components, 0 missing meshes, `DefaultTouchInterface=None`, and MapCheck `0 Error(s), 0 Warning(s)`.

## Normal PIE weapon test

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -pie `
  -traceautostart=0 `
  -ExecutePythonScript='C:\UnrealProjects\Battleground\Tools\m416_runtime_test_v4.py' `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\WeaponM416\editor_runtime_v4.log' `
  -windowed -ResX=800 -ResY=450 -nosplash -log
```

The `-pie` flag is required for a real player-controlled PIE session. `editor_play_simulate()` only starts Simulate mode and leaves the player on a spectator pawn.

Report: `Saved/WeaponM416/runtime_test_v4.txt`; screenshot: `Saved/VisualTests/Hampi_M416_PIE.png`.

## Normal PIE five-AI test

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -pie `
  -traceautostart=0 `
  -ExecutePythonScript='C:\UnrealProjects\Battleground\Tools\ai_runtime_test_v1.py' `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\AI\editor_runtime_final.log' `
  -windowed -ResX=800 -ResY=450 -nosplash -log
```

This verifies the runtime spawner, five distinct bots with AI controllers, patrol/detection, bot damage to the player, and M416 damage killing a bot.

Report: `Saved/AI/runtime_test_v1.txt`; screenshot: `Saved/VisualTests/Hampi_AI_PIE.png`.

## Normal PIE safe-zone test

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -pie `
  -traceautostart=0 `
  -ExecutePythonScript='C:\UnrealProjects\Battleground\Tools\safezone_runtime_test_v1.py' `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\SafeZone\editor_runtime_final.log' `
  -windowed -ResX=800 -ResY=450 -nosplash -log
```

This verifies zone centering, default/accelerated radius, phase shrink, countdown, wall scaling, and damage to out-of-zone bots and player.

Report: `Saved/SafeZone/runtime_test_v1.txt`; screenshot: `Saved/VisualTests/Hampi_SafeZone_PIE.png`.

## Normal PIE health test

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -pie `
  -traceautostart=0 `
  -ExecutePythonScript='C:\UnrealProjects\Battleground\Tools\health_runtime_test_v1.py' `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\Health\editor_runtime_final.log' `
  -windowed -ResX=800 -ResY=450 -nosplash -log
```

This verifies shield absorption, damage, instant/heal-over-time effects, death/respawn, and the three consumable pickups.

Report: `Saved/Health/runtime_test_v1.txt`; screenshot: `Saved/VisualTests/Hampi_Health_PIE.png`.

## Normal PIE loot test

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -pie `
  -traceautostart=0 `
  -ExecutePythonScript='C:\UnrealProjects\Battleground\Tools\loot_runtime_test_v1.py' `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\Loot\editor_runtime_v1.log' `
  -windowed -ResX=800 -ResY=450 -nosplash -log
```

This verifies all five proximity pickups, inventory stacking, three weapon slots, and consumable use.

Report: `Saved/Loot/runtime_test_v1.txt`; screenshot: `Saved/VisualTests/Hampi_Loot_PIE.png`.

## Normal PIE Kannada dialogue test

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -pie `
  -traceautostart=0 `
  -ExecutePythonScript='C:\UnrealProjects\Battleground\Tools\voice_runtime_test_v1.py' `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\Voice\editor_runtime_final.log' `
  -windowed -ResX=800 -ResY=450 -nosplash -log
```

This verifies the eight imported Kannada cues, source/license files, per-cue cooldown, and all automatic triggers: MatchStart, WeaponEquipped, Healing, EnemySpotted, ZoneWarning, LowHealth, Defeat, and Victory.

Report: `Saved/Voice/runtime_test_v1.txt`; screenshot: `Saved/VisualTests/Hampi_Voice_PIE.png`.

## Regenerating Kannada dialogue

```powershell
python 'C:\UnrealProjects\Battleground\Tools\generate_kannada_dialogue.py'
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -run=pythonscript `
  -script='C:\UnrealProjects\Battleground\Tools\import_kannada_dialogue.py' `
  -unattended -nosplash -nullrhi -log
```

The generator uses `edge-tts` (LGPLv3) and the Microsoft `kn-IN-GaganNeural` / `kn-IN-SapnaNeural` voices. Attribution and the standard-voice dialect caveat are written to `Saved/ThirdParty/KannadaDialogue/LICENSE.txt`.

## Normal PIE mobile HUD test

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -pie `
  -traceautostart=0 `
  -ExecutePythonScript='C:\UnrealProjects\Battleground\Tools\hud_runtime_test_v1.py' `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\HUD\editor_runtime_final.log' `
  -windowed -ResX=800 -ResY=450 -nosplash -log
```

This verifies the native widget, six touch buttons, floating joystick movement, right-side swipe camera, fire/ADS/reload/jump/crouch/swap actions, health/armor bars, ammo text, compass, radar dots, zone ring, and pickup prompt. All 62 checks pass in `Saved/HUD/runtime_test_v1.txt`; no runtime errors were logged.

The automation screenshot at `Saved/VisualTests/Hampi_HUD_PIE.png` is byte-identical to the earlier dialogue screenshot, so the capture API is not proving that the UMG overlay is drawn. Human visual sign-off in a real PIE window (and later on Android) is still required.

## Application Control

If PowerShell reports `An Application Control policy has blocked this file` / error 4551, an administrator must allow or sign the newly rebuilt binaries. See `KnownIssues.md` for current hashes. Do not disable Windows Defender, Smart App Control, or Application Control.

## Android configuration and graphics profiles

Project settings target ARM64, MinSDK 26, TargetSDK 34, package `com.DefaultCompany.HampiBattleground`, landscape, max aspect ratio 2.4, with Nanite, Virtual Shadow Maps, Lumen, and ray/path tracing disabled. Android SDK/NDK/JDK are configured in `Config/DefaultEngine.ini`; API 33 and build-tools 33.0.1 were also installed for UE 5.4 compatibility.

LOW / MEDIUM / HIGH are defined in `Config/DefaultDeviceProfiles.ini` and `Config/Android/AndroidScalability.ini`. Validate them after any edit:

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Win64\UnrealEditor-Cmd.exe' `
  'C:\UnrealProjects\Battleground\Battleground.uproject' `
  -run=pythonscript -script='C:\UnrealProjects\Battleground\Tools\validate_graphics_profiles.py' `
  -unattended -nosplash -nullrhi -log `
  -ABSLOG='C:\UnrealProjects\Battleground\Saved\Android\graphics_profiles_validation_editor.log'
```

Expected: `CHECKS=108/108`, `STATUS=PASS`, report `Saved/Android/graphics_profiles_validation.txt`.

Development package command (run after Android platform support is installed in the launcher):

```powershell
& 'G:\Epic Games\UE_5.4\UE_5.4\Engine\Build\BatchFiles\RunUAT.bat' BuildCookRun `
  -project='C:\UnrealProjects\Battleground\Battleground.uproject' -noP4 -unattended -utf8output `
  -platform=Android -targetplatform=Android -clientconfig=Development -serverconfig=Development `
  -build -cook -allmaps -stage -pak -apk -archive `
  -archivedirectory='C:\UnrealProjects\Battleground\Builds\Android' `
  -nocompileeditor -skipbuildeditor
```

Status: this command currently fails before compilation with UAT exit 6 because the UE 5.4.4 install is missing the Android platform component (`Engine\Binaries\Android\UnrealGame.target`). Enable Android platform support in Epic Games Launcher for UE 5.4.4, then retry. See `Saved/Android/package_blocker_report.txt`. No phone is currently attached (`adb devices -l`), so on-device install/FPS/memory tests and the Shipping APK remain pending.

## Third-party attribution

- Soldier: Grab3D `soldier-rigged`, CC0. Record in `Saved/ThirdParty/Grab3D_Soldier/LICENSE.txt`.
- Rifle: “M4 Carbine” by AdamKokrito via Poly Pizza, CC BY 3.0. `https://poly.pizza/m/vx8dQfkzNM`. Record in `Saved/ThirdParty/PolyPizza_M4Carbine/LICENSE.txt`.
- Fire/reload sounds are original procedural project audio. Record in `Saved/ThirdParty/ProceduralAudio/LICENSE.txt`.
- Kannada battle dialogue: generated with `edge-tts 7.3.1` (LGPLv3, `https://github.com/rany2/edge-tts`) using Microsoft Edge `kn-IN-GaganNeural` and `kn-IN-SapnaNeural` voices, converted with `imageio-ffmpeg`. Script and attribution: `Tools/generate_kannada_dialogue.py`, `Saved/ThirdParty/KannadaDialogue/dialogue_lines.txt`, and `LICENSE.txt`. The script is North Karnataka colloquial Kannada; the neural voices are standard Kannada and need native-speaker review before commercial release.
