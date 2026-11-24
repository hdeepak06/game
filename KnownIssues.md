# HAMPI BATTLEGROUND — Known Issues

_Last updated: 2026-11-23_

## Environment constraint (resolved for the current build)

- **Windows Application Control blocks newly rebuilt project binaries until approved.**
  - After each successful C++ rebuild, `Binaries/Win64/UnrealEditor-Battleground.dll` and `Binaries/Win64/Battleground.exe` can be denied with `GetLastError=4551` ("An Application Control policy has blocked this file"), CodeIntegrity events 3033/3077, policy `{0283AC0F-FFF1-49AE-ADA1-8A933130CAD6}`.
  - This is a machine security policy, not a project compile error. Do not disable or bypass Windows security.
  - The current rebuilt hashes load successfully and all current PIE test suites ran:
    - `UnrealEditor-Battleground.dll`: `706366A9F1DB2A0450B922ED4A2478EE50EF45DE7FC4673B4BCDBD8BC8570D5A`
    - `Battleground.exe`: `FB08362C44C3DCA5EA3F9EE72F01EF6FB2DBA9FB229E319493264C662AA5CCF5`
  - Any later C++ rebuild will produce new hashes and may need the same administrator allow/sign action.

## GPU crash status (resolved in editor harness)

- **Root cause:** UE 5.4 editor autostart enabled the Unreal Insights `gpu` trace channel, forcing D3D11 timestamp queries on an old Intel UHD driver and ending in `DXGI_ERROR_DEVICE_REMOVED / DXGI_ERROR_DEVICE_HUNG` at `D3D11Query.cpp:361`. It was not a gameplay crash or proven VRAM exhaustion. Full evidence: `Saved/GPUCrash/root_cause_report.txt`.
- **Fix:** all normal PIE commands now pass `-traceautostart=0`. A 200-second wall-clock PIE soak passed with no GPU errors (`Saved/GPUCrash/regression_v1.txt`, `regression_editor_v2.log`), and the HUD suite still passed 62/62 with the flag.
- No Windows security, driver, Defender, Smart App Control, Application Control, or administrator policy was changed.

## Verification status

- **M416:** Normal PIE verified pickup, equip, right-hand attachment, ADS FOV, automatic fire, muzzle flash, recoil, ammo, and reload. All 14 harness checks pass. Report: `Saved/WeaponM416/runtime_test_v4.txt`.
- **Five AI bots:** Normal PIE verified spawner, five distinct personas, AI controllers, patrol, detection, bot damage to player, M416 damage killing a bot, and death state. All 17 harness checks pass. Report: `Saved/AI/runtime_test_v1.txt`.
- **Shrinking safe zone:** Normal PIE verified one zone centered on PlayerStart, initial/final radius, phase shrink, countdown, wall scaling, and damage to bots and players outside. All 12 harness checks pass. Report: `Saved/SafeZone/runtime_test_v1.txt`.
- **Health/damage/healing:** Normal PIE verified shield absorption, damage, instant cap, heal-over-time, death, respawn at PlayerStart, and three consumable pickups. All 47 harness checks pass. Report: `Saved/Health/runtime_test_v1.txt`.
- **Loot/inventory:** Normal PIE verified five proximity pickups, stacking, Primary/Secondary/Pistol slots, consumable use and stock decrements. All 32 harness checks pass. Report: `Saved/Loot/runtime_test_v1.txt`.
- **Kannada dialogue:** Normal PIE verified eight imported cues, Kannada source/attribution files, per-cue cooldown, and automatic MatchStart, WeaponEquipped, Healing, EnemySpotted, ZoneWarning, LowHealth, Defeat, and Victory triggers. All 56 harness checks pass. Report: `Saved/Voice/runtime_test_v1.txt`.
- **Mobile HUD:** Normal PIE verified the native widget, floating joystick movement, right-side camera swipe, all six touch buttons and their soldier/weapon side effects, jump launch, health/shield bars, ammo text, compass, five enemy radar dots, zone ring, and pickup prompt. All 62 harness checks pass. Report: `Saved/HUD/runtime_test_v1.txt`; structural report `Saved/HUD/final_validation.txt`.
- **GPU-safe regression:** all seven gameplay harnesses were rerun with `-traceautostart=0` after the graphics profiles were added; all checks pass and no GPU error lines appeared. Summary: `Saved/GPUCrash/gameplay_regression_summary.txt`.
- Recoil was tuned after the first PIE run because the original recovery was too fast at a 0.125 s editor tick; the final run measured 4.55° pitch / 0.34° yaw kick and clean recovery.
- Character hit traces use `ECC_Pawn` because the engine default `Pawn` collision profile ignores the `Visibility` channel. Visibility traces are still used for ground snapping and obstacle nudging.

## Active gameplay issues

- **Combat difficulty is too high:** with all five bots engaging together, the player can go from 100 to 0 health in a few seconds. Bot damage/fire-rate and engagement ranges need balancing before release.
- **Bot AI is intentionally lightweight:** a native Patrol/Investigate/Engage/Retreat FSM with direct steering is used instead of `UAIPerception`, Blackboard, and Behavior Trees. The saved map has no `NavMeshBoundsVolume`, so bots do not use navmesh pathing. Obstacle handling is a short forward trace plus sideways slide and may snag on complex geometry.
- **Death still needs a match-level screen:** health, shield, bars, regen, healing items, death and respawn now have HUD support, but death still disables movement and waits for an explicit `Respawn()` call. A match-level defeat screen remains part of the later match/UI work.
- **Bot weapons are parameterised, not modelled:** to respect the single-weapon rule, bots use tuned damage/fire intervals and the shared M416 fire sound instead of distinct weapon meshes.
- **Dialogue accent is not native North Karnataka:** the script uses North Karnataka colloquial Kannada, but the available Microsoft `kn-IN` neural voices are standard Kannada. A native-speaker review and re-record are recommended before commercial release. The generated audio also depends on Microsoft's online TTS terms.
- Surface impact FX, tracers, distance attenuation, and empty-magazine audio remain pending.

## Android packaging status (blocked)

- **Development APK failed before compile:** UAT exit 6, `Missing files required to build Android targets. Enable Android as an optional download component in the Epic Games Launcher.` (`Saved/Android/package_development.log`).
- **Cause:** the UE 5.4.4 install lacks `Engine\Binaries\Android\UnrealGame.target` and the `Engine\Binaries\Android` directory. The Android SDK, NDK 26.1, JDK 17, API 33/34, build-tools, and project ARM64/landscape config are all present; this is an engine install component issue only.
- **Action required:** enable Android platform support in Epic Games Launcher for UE 5.4.4, then retry Development packaging. No Windows security, policy, admin, or licensing check was bypassed.
- **Profiles are ready:** LOW/MEDIUM/HIGH are configured in `Config/DefaultDeviceProfiles.ini` and `Config/Android/AndroidScalability.ini`; validation passed 108/108 (`Saved/Android/graphics_profiles_validation.txt`).
- **No phone:** `adb devices -l` shows no attached device, so install/FPS/memory/thermal testing is still outstanding.

## Gameplay still pending

- Environment expansion, Android APK cook/package, and on-device performance validation.

## Non-blocking notes

- Unreal Build Tool warns that Visual Studio 2022 compiler `14.44.35230` is not the preferred version `14.38.33130`. Builds succeed.
- Python commandlets emit `DeprecationWarning`s for `EditorLevelLibrary.load_level/get_all_level_actors`; these are editor-scripting API warnings, not project errors.
- Human visual sign-off is recommended for `Saved/VisualTests/Hampi_Soldier_PIE.png`, `Hampi_M416_PIE.png`, `Hampi_AI_PIE.png`, `Hampi_Voice_PIE.png`, and `Hampi_HUD_PIE.png`. Native Kannada speaker review is recommended for the dialogue audio.
- `Hampi_HUD_PIE.png` is byte-identical to `Hampi_Voice_PIE.png`, so the automation screenshot API is not capturing the UMG overlay. Open normal PIE manually to confirm HUD placement and readability; the functional HUD harness passes regardless.
- The earlier M416, recoil, and Voice rebuild hashes recorded in `DevelopmentLog.md` are historical; the hashes above are the current ones.
