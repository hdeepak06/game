# HAMPI BATTLEGROUND — 20-TASK MASTER PROGRESS CHECKLIST

**Game Title:** HAMPI BATTLEGROUND  
**Target Platform:** Android (ARM64) | Development: Windows (DX11)  
**Engine:** Unreal Engine 5.4.4  
**Game Mode:** Single-Player Battle Royale (1 Player + 5 AI Bots)  

---

## Task Progress Checklist

- [x] **TASK 01: Project Foundation & C++ Infrastructure**
  - Locate existing `.uproject` and verify UE 5.4.4 association.
  - Audit `Content/`, `Config/`, and create `Source/` C++ module.
  - Implement `Battleground.Build.cs`, `Battleground.h`, `Battleground.cpp`, `Battleground.Target.cs`, `BattlegroundEditor.Target.cs`.
  - Fix MSVC 14.44 preprocessor macro compatibility in `ConcurrentLinearAllocator.h`.
  - Compile `Battleground.exe` with Unreal Build Tool (0 Errors).
  - Create `DevelopmentLog.md` and `GameProgress.md`.

- [x] **TASK 02: Landscape & Terrain Foundation**
  - Preserve original $504\text{ m} \times 504\text{ m}$ landscape actor `Landscape_0` (8x8 components, 505x505 resolution).
  - Create safety backup at `Backups/LV_HampiBattleground_Task02_Backup.umap`.
  - Create & compile mobile landscape material `M_HampiLandscape` with 5 layers (`DrySoil`, `RockyGround`, `Sand`, `Grass`, `Riverbank`).
  - Create 5 `LandscapeLayerInfoObject` assets in `/Game/Materials/`.
  - Setup complete dynamic lighting rig (`DirectionalLight`, `SkyLight`, `SkyAtmosphere`, `ExponentialHeightFog`, `PostProcessVolume`) to fix black viewport.
  - Generate 5-region 16-bit 505x505 heightmap (`Hampi_Heightmap_505.png`, `Hampi_Heightmap_505.r16`, and preview).
  - Document exact remaining manual Editor Landscape Import step for Landscapes with Edit Layers.

- [ ] **TASK 03: Playable Character & Locomotion**
  - Integrate full-body military soldier mesh with proper skinning.
  - Implement walking, running, sprinting, crouching, and jumping.
  - Implement third-person camera with smooth follow, obstacle collision, and aim mode.
  - Set up player health, armor, and damage handling components.
  - **2026-11-23 soldier replacement:** Replaced the Manny/Quinn mannequin player with a CC0 Grab3D modern soldier mesh, native `AHampiSoldierCharacter`, and a 1D idle/walk/run BlendSpace; 1K soldier textures and a dedicated mobile material were added. Existing camera, input, movement, jumping, collision, GameMode, and PlayerStart were preserved. Health/armor and mobile crouch are now implemented in later phases; sprint remains the main outstanding Task 03 item, so this task stays open.

- [ ] **TASK 04: Region A — Hampi Rocky Hills**
  - Place large natural granite boulders and rocky elevated terrain.
  - Create narrow rock corridors and natural choke points.
  - Build tactical elevated sniper perches and lookout positions.
  - Place loot spawns and connecting trails toward the village and river.
  - **2026-11-22 Stage 1:** Built and saved a slice in `LV_HampiBattleground`: soil material, 5 low-poly boulder meshes, 10 placed boulders, and 1 small traditional house. Structural validation and numeric live-editor capture verification passed.
  - **2026-11-23 full environment pass:** Added 64 new original Environment assets and populated the existing map with 95 tagged structures, 11 terrain-following roads, a Tungabhadra river strip with sandbanks/reeds/boulders, and 13 persistent HISM groups totaling 904 foliage/river-stone instances. Preserved the Landscape, soil material, Stage 1 actors, PlayerStart, lighting, and collision setup.
  - **Validation:** Fresh reload reports 163 actors, 1 unchanged Landscape, 1 PlayerStart, 11 preserved Stage 1 actors, 95 structures at ground level, 904 persistent HISM instances, 0 missing assets/default-material meshes, and MapCheck `0 Error(s), 0 Warning(s)` in the live editor. Live viewport capture is 98.4% non-black and 92.7% terrain-colored; no material compile errors or HISM usage warnings remain.
  - **Still pending:** Human visual sign-off, play-mode collision walkthrough, enterable interiors, loot spawns, navigation verification after the new obstacles, river bridges, gameplay systems, and Android packaging. This task remains open until those are addressed.

- [x] **TASK 05: Region B — Kamalapur Village**
  - Construct village road layout and courtyards.
  - **2026-11-23 documentation correction:** A previously undocumented Virupaksha Temple landmark pass was found on disk and is preserved as completed work. It added 9 temple/bazaar static meshes and 10 material instances under `/Game/Environment/Task05/Virupaksha`, plus 114 `Task05_Virupaksha`-tagged actors at Hampi `(-43800, 13500)`: gopuram, mandapa, sanctum, 6 sub-shrines, cloister/courtyard segments, temple tank, 10 bazaar shops, access road, 10 boulders, and 60 instanced stones with 64 hidden `BlockAll` collision proxies. Validation reported 277 actors, 1 unchanged Landscape, 1 PlayerStart, 0 missing meshes, Nanite disabled, and MapCheck `0 Error(s), 0 Warning(s)`. Human visual sign-off is still recommended.
  - Place rural buildings, houses, and shops with enterable interiors.
  - Add water tanks, perimeter walls, and strategic cover props.
  - Distribute indoor and outdoor loot spawn points.

- [ ] **TASK 06: Region C — Hosapete Outskirts**
  - Build paved highway corridors and industrial lots.
  - Add warehouses, storage depots, and abandoned industrial buildings.
  - Place vehicle-inspired cover props and shipping containers.
  - Establish mid-to-long-range combat sightlines.

- [ ] **TASK 07: Region D — Tungabhadra Riverside**
  - Sculpt and texture riverbanks, sand bars, and water volume.
  - Build small bridge crossings connecting northern and southern banks.
  - Add riverside boulders, natural reeds, and waterfront cover.
  - Establish low-ground stealth paths along the water.

- [ ] **TASK 08: Region E — Military Training Ground**
  - Construct military barracks and command buildings.
  - Add formal shooting range with target markers and sandbags.
  - Erect watchtowers, razor wire barricades, and cargo containers.
  - Place high-tier weapon loot spawners.

- [x] **TASK 09: Road Network & Navigation Mesh**
  - Connect all 5 regions with primary roads and dirt paths.
  - Scale `NavMeshBoundsVolume` ($520\text{ m} \times 520\text{ m}$) across all terrain.
  - Verify continuous, unblocked navigation across borders and bridges.

- [ ] **TASK 10: Weapon System Core Framework**
  - Create reusable C++ / Blueprint base weapon class (`AWeaponBase`).
  - Implement weapon states (Equipped, Holstered, Dropped).
  - Add ammo tracking (Current Magazine + Reserve Pool).
  - Implement weapon fire modes (Single, Burst, Full-Auto) and recoil/spread algorithms.
  - **2026-11-23:** Native `AM416Weapon` implements full-auto fire, spread, recoil, ammo, reserve, reload, pickup, equip, ADS, muzzle flash, traces, and basic audio. Runtime-tested below; a reusable multi-weapon `AWeaponBase` refactor is still pending.

- [ ] **TASK 11: Weapon Arsenal Implementation (5 Classes)**
  - Class 1: Assault Rifle (balanced fire rate, medium-long range).
  - Class 2: Pistol (high mobility, close-range backup).
  - Class 3: Sniper Rifle (high damage, bolt-action, magnified sight).
  - Class 4: Submachine Gun (SMG) (high cyclic rate, close-quarters).
  - Class 5: Shotgun (spread pellets, lethal at point-blank).
  - **2026-11-23:** Class 1 (assault rifle) is complete as the single licensed M416-style rifle `SM_M416` / `AM416Weapon` and is runtime-tested. Classes 2–5 are intentionally not created.

- [ ] **TASK 12: Weapon FX & Audio**
  - Muzzle flash particles and projectile tracer effects.
  - Surface impact effects (dirt, rock, wood, metal, flesh decals).
  - Weapon gunshot sounds with distance attenuation.
  - Reloading foley audio and empty magazine clicks.
  - **2026-11-23:** M416 muzzle flash and procedural fire/reload sounds are implemented and runtime-verified. Surface impact FX, tracers, distance attenuation, and empty-click audio remain pending.

- [x] **TASK 13: AI Bot Core Framework & Behavior Trees**
  - Create `AAIController` with `UAIPerceptionComponent` (Sight & Hearing).
  - Implement Blackboard keys (TargetActor, State, MoveLocation, Health).
  - Build Behavior Tree tasks for Patrol, Investigate, Seek Cover, and Attack.
  - **2026-11-23:** Implemented a mobile-friendly native FSM instead: `AHampiAICharacter` has Patrol / Investigate / Engage / Retreat states, periodic `ECC_Pawn` line-of-sight checks, direct steering with cheap obstacle slide, and `UGameplayStatics::ApplyDamage`. Each bot is auto-possessed by a native `AAIController`. The saved map has no `NavMeshBoundsVolume` and no AI/Behavior Tree assets, so navmesh BT pathing was deliberately avoided. Full UAIPerception/Blackboard/Behavior Tree conversion remains an optional future upgrade.

- [x] **TASK 14: 5 Unique AI Opponents**
  - Bot 1 — Raven: Aggressive flanker using SMG/Shotgun.
  - Bot 2 — Shadow: Stealthy sniper operating from elevated perches.
  - Bot 3 — Hunter: Patrol-heavy combatant seeking player footsteps.
  - Bot 4 — Viper: Mid-range assault rifle specialist, cover-to-cover.
  - Bot 5 — Ghost: Evasive survivalist prioritizing healing and safe zone position.
  - **2026-11-23:** All five exist as `AHampiAICharacter` with distinct names, health, sight range, attack range, preferred range, fire interval, damage, speed, and patrol radius. Because the project deliberately keeps only one weapon model, their weapons are represented by tuned damage/fire-rate parameters plus the shared M416 fire sound rather than separate meshes. Ghost self-heals; Shadow keeps longest range; Raven closes and strafes fastest. Verified in normal PIE: 5 bots, 5 distinct personas, AI controllers, patrol movement, detection, bot damage to player, and M416 kill of a bot.

- [x] **2026-11-23 — Player Health, Damage & Healing (required order: after safe zone, before loot)**
  - `AHampiSoldierCharacter` now has 100 health plus 0/50 shield, shield-first damage absorption, damage-source tracking, 8 s / 3 hp/s out-of-combat regeneration, instant heal, 5 s energy-drink heal-over-time, death, and `Respawn()` at the preserved PlayerStart.
  - Added runtime-spawned one-use pickups `AHampiHealingItem` (Medkit +50 HP, EnergyDrink +40 HP over 5 s, Armor +50 shield) with emissive unlit materials in `/Game/Environment/Health`. No map edits.
  - Normal PIE harness `Tools/health_runtime_test_v1.py` passed all 47 checks; report `Saved/Health/runtime_test_v1.txt`, log `Saved/Health/editor_runtime_final.log`, screenshot `Saved/VisualTests/Hampi_Health_PIE.png` (472,677 bytes). Builds `Saved/Health/build_editor_v2.txt` / `build_game_v2.txt` exit 0, no errors.

- [x] **TASK 15: Ground Loot & Inventory System**
  - Reusable pickup actors (`ALootItemBase`) with glowing indicator markers.
  - Proximity detection and pickup prompts.
  - Multi-slot inventory: Primary Weapon, Secondary Weapon, Pistol, Consumables.
  - Medkits and Energy Drinks to restore Health.
  - **2026-11-23:** Implemented as native `AHampiLootItem` (five runtime-spawned pickups with glowing beam markers and proximity collection) and a stack-based inventory on `AHampiSoldierCharacter` with Primary/Secondary/Pistol slots plus consumable use. Normal PIE harness `Tools/loot_runtime_test_v1.py` passed all 32 checks; report `Saved/Loot/runtime_test_v1.txt`, screenshot `Saved/VisualTests/Hampi_Loot_PIE.png` (471,554 bytes). Builds `Saved/Loot/build_editor_v1.txt` / `build_game_v1.txt` exit 0, no errors. On-screen pickup prompts were subsequently added by the mobile HUD phase.

- [x] **TASK 16: Battle Royale Safe Zone Circle**
  - Cylindrical shrinking boundary actor (`ASafeZoneCircle`).
  - Multi-phase zone contraction with countdown timers.
  - Electric storm boundary visual shader.
  - Periodic damage applied to pawns outside the safe zone.
  - **2026-11-23:** Implemented as native `AHampiSafeZone` plus additive unlit material `/Game/Environment/SafeZone/M_SafeZoneWall`. Runtime-spawned at the PlayerStart by `AHampiSoldierCharacter::BeginPlay`, so the saved map is unchanged. Four-phase linear contraction (24,000 cm to 1,500 cm), 45 s initial delay, 60 s shrink / 25 s hold per phase, countdown via `GetTimeToNextPhase()`, and 6 damage/sec to any player or bot outside. Normal PIE harness `Tools/safezone_runtime_test_v1.py` passed all 12 checks (center, one zone, initial/final radius, phase countdown, wall scaling, bot and player damage, screenshot). Report: `Saved/SafeZone/runtime_test_v1.txt`; screenshot `Saved/VisualTests/Hampi_SafeZone_PIE.png`.

- [x] **2026-11-23 - North Karnataka Kannada Voice Dialogue (required order: after loot, before HUD)**
  - Added eight Kannada battle cues: MatchStart, WeaponEquipped, EnemySpotted, ZoneWarning, LowHealth, Healing, Victory, and Defeat. Audio is imported as `/Game/Audio/Dialogue/VO_*` SoundWaves and generated by `Tools/generate_kannada_dialogue.py`.
  - Added native `AHampiDialogueDirector` with cached cues, per-cue cooldown, played-cue history, and automatic triggers for match start, nearby enemies, zone shrink, low health, healing, defeat, and last-player-standing victory. `WeaponEquipped` is fired by `EquipM416`; `Healing` by `Heal`/`StartHealOverTime`.
  - Normal PIE harness `Tools/voice_runtime_test_v1.py` passed all 56 checks: eight loaded cues, Kannada text/audio source checks, cooldown, and all eight automatic triggers. Report `Saved/Voice/runtime_test_v1.txt`, log `Saved/Voice/editor_runtime_final.log`, screenshot `Saved/VisualTests/Hampi_Voice_PIE.png` (471,840 bytes). Builds `Saved/Voice/build_editor_v3.txt` / `build_game_v3.txt` exit 0, no errors.
  - The script uses North Karnataka colloquial forms; the available Microsoft `kn-IN` neural voices are standard Kannada, so a native-speaker review is recommended before commercial release.

- [ ] **TASK 17: Match Management & Kill Feed**
  - GameMode match state machine: Waiting -> InProgress -> GameOver.
  - Alive counter tracking active combatants (1 human + 5 bots).
  - Real-time Kill Feed displaying elimination notices and weapon icons.
  - End-game Victory screen ("Winner Winner!") and Defeat screen.

- [x] **TASK 18: Mobile Touch HUD & On-Screen Controls**
  - Virtual floating touch joystick for movement: native `UHampiMobileHUDWidget` is created at runtime by `AHampiSoldierCharacter` and added to the viewport, leaving the saved map and existing GameMode/camera/input setup untouched.
  - Right-screen dynamic swipe area rotates the camera through `APlayerController::AddYawInput`/`AddPitchInput`; mouse input mirrors touch so desktop PIE can test the same handlers.
  - Six touch action buttons are implemented and wired to real soldier/weapon actions: FIRE, ADS, JUMP, CROUCH, RELOAD, and SWAP (Primary -> Secondary -> Pistol).
  - Health/armor bars, ammo text, 5-tick compass tape, 5-enemy radar dots with zone-ring segments, and contextual pickup prompts are updated every HUD tick.
  - `Config/DefaultInput.ini` now uses `DefaultTouchInterface=None` so Android does not show the engine's duplicate virtual joysticks.
  - Builds `Saved/HUD/build_editor_v8.txt` and `build_game_v1.txt` exited 0 with no error lines. Normal PIE harness `Tools/hud_runtime_test_v1.py` passed all 62 checks; report `Saved/HUD/runtime_test_v1.txt`, final log `Saved/HUD/editor_runtime_final.log`, structural report `Saved/HUD/final_validation.txt`, screenshot `Saved/VisualTests/Hampi_HUD_PIE.png` (471,840 bytes). MapCheck stayed at `0 Error(s), 0 Warning(s)`; actor count remained 278 with 1 Landscape, 1 PlayerStart, 1 M416 marker, and 0 missing meshes. Human visual sign-off and real-device touch testing are still recommended because the automation screenshot does not include the UMG overlay.

- [ ] **TASK 19: Performance Optimization & Scalable Profiles**
  - Implement LOW / MEDIUM / HIGH graphics profiles (this supersedes the earlier Smooth/Balanced/HD/Ultra plan).
  - Profiles are in `Config/DefaultDeviceProfiles.ini` and `Config/Android/AndroidScalability.ini`; validation passed 108/108.
  - Calibrate dynamic resolution scaling and LOD distances for Intel UHD / mobile Mali & Adreno GPUs; on-device FPS/memory numbers are still pending.
  - Target stable 30 FPS on supported entry-level devices and optional 60 FPS on capable devices; no frame-rate cap is applied.

- [ ] **TASK 20: Android ARM64 Packaging & APK Verification**
  - Validated Android SDK 34, NDK 26.1, JDK 17, and installed UE-expected API 33/build-tools 33.0.1.
  - Configured package name `com.DefaultCompany.HampiBattleground`, ARM64 only, landscape, and display name.
  - Cook/package is blocked: UE 5.4.4 engine install lacks the Android platform component (`Engine\Binaries\Android\UnrealGame.target`). Enable it in Epic Games Launcher, then retry.
  - Expected outputs: `Builds/Android/HampiBattleground-Development.apk` and `Builds/Android/HampiBattleground-Shipping.apk`; neither exists yet.

---

## Maintenance Notes

- [x] **2026-11-22 — Inspection & safe cleanup**
  - Removed 75 regenerable log, crash, and shader-debug files (5.76 MB).
  - Corrected the project display name and the missing editor simple-map path.
  - Did not delete `Intermediate/` or `Binaries/` because Unreal Editor was open.
  - Did not mark any gameplay task complete. TASK 09 stays checked from earlier work and was not re-verified in the editor this session.

- [x] **2026-11-22 — Black viewport diagnosed and repaired**
  - Confirmed the real root causes: wrong-facing Stationary sun, PlayerStart outside the Landscape, path tracing enabled on DX11/no-RT, auto exposure disabled, and a misconfigured four-pane/orthographic editor camera.
  - Preserved `LV_HampiBattleground` and `Landscape_0`; no duplicate actors or new level assets were created.
  - Fixed the sun direction/mobility, moved PlayerStart to the Landscape center, disabled path tracing, restored auto exposure, and reset the editor to a single Lit perspective view framed on the terrain.
  - Reopened the editor and verified the viewport is non-black by numeric screen-capture analysis; user should still confirm visually.
  - Game target build passed (exit 0). Editor target build is blocked by a machine-level .NET Framework SDK dependency for `SwarmInterface`, not by project code.
  - No gameplay task status was changed.

- [x] **2026-11-22 — Task 04 Stage 1 environment slice built and capture-verified**
  - Created 19 original Environment assets: 5 textures, 5 mobile materials, 3 granite instances, 5 boulder meshes, and 1 small house mesh.
  - Modified `LV_HampiBattleground` in place with one soil-materials swap, one house actor, and ten tagged boulder actors; backup exists and Landscape bounds are unchanged.
  - Corrected a soil material ComponentMask compile error and Unreal Python Rotator/camera-direction mistakes found during verification.
  - Final commandlet validation: 19 actors, 1 Landscape, 11 Task 04 actors, 19 new assets, mesh geometry/slots confirmed.
  - Final live-editor capture is non-black and includes terrain and structure color buckets; MapCheck reported 0 errors and 0 warnings.
  - Full five-region Task 04 remains unchecked; no gameplay systems or packaging were added.

- [x] **2026-11-23 — Task 04 full environment build completed and verified in the existing map**
  - Created 64 additional original assets: 6 textures, 15 mobile materials, 43 low-poly static meshes. `Content/Environment` now contains 83 assets total.
  - Populated Kamalapur, Hampi, Anjanadri, Hosapete, the military ground, and the riverside with 95 structures, 11 roads, a river strip, 24 river boulders, 48 instanced river stones, and 856 instanced vegetation pieces.
  - Confirmed Stage 1 boulders have simple/convex collision, opaque single-sided materials, Nanite disabled, and `BlockAll` profiles; structures are `BlockAll` and ground-conforming.
  - Fixed HISM save persistence by assigning HISM components as actor roots; fixed all new material shader compile errors and instanced-mesh usage flags found in the live editor.
  - Disabled Nanite and Virtual Shadow Maps in project config in addition to the existing Lumen/ray/path-tracing off settings; no external or paid content was used.
  - Final checks: 163 actors, 1 Landscape with unchanged bounds, 1 PlayerStart, 904 persisted HISM instances, 0 missing assets, 0 default-material slots, live editor MapCheck `0 Error(s), 0 Warning(s)`, and a terrain-filled numeric viewport capture.
  - Human visual confirmation and gameplay-specific checks are still outstanding; no gameplay task checkbox was changed.

- [x] **2026-11-23 — Virupaksha landmark documentation corrected**
  - The on-disk Task 05 build was preserved, not regenerated: 9 meshes, 10 material instances, 114 tagged actors, 64 hidden collision proxies, and 60 persistent HISM stones.
  - `GameProgress.md` now records the work as completed; `DevelopmentLog.md` gains the corresponding detailed entry. No map actor was deleted or moved.

- [x] **2026-11-23 — Hampi soil upgraded in place**
  - Rebuilt `/Game/Environment/Materials/M_HampiSoil_Mobile` with 45 nodes and layered laterite, gravel, dry-grass, granite, and mask-driven breakup; original `/Game/Materials/M_HampiLandscape` preserved.
  - Added 4 new 256 px textures: `T_HampiSoilLaterite_Albedo`, `T_HampiGravel_Albedo`, `T_HampiDryGrassPatch_Albedo`, `T_HampiGroundMask`; reused `T_HampiGranite_Albedo`.
  - No shader compile errors; Landscape material and bounds unchanged. The earlier `set_material_usage()` warning came from a script passing 3 arguments to a 2-argument API, not from the material asset.

- [x] **2026-11-23 — Player mannequin replaced with a CC0 modern soldier**
  - Source: Grab3D `soldier-rigged` (CC0, AI-assisted disclosure recorded in `Saved/ThirdParty/Grab3D_Soldier/LICENSE.txt`); no paid or copyrighted pack used.
  - Imported `SKM_HampiSoldier`, its skeleton, 1.0 s walk and 0.625 s run clips; created 1K `T_Soldier_BaseColor`, `T_Soldier_Normal`, `T_Soldier_ORM` and `M_HampiSoldier`.
  - Added native `AHampiSoldierCharacter` in `Source/Battleground`, reparented `BP_ThirdPersonCharacter` in a full editor process, cleared `ABP_Quinn`, and set `BS_SoldierLocomotion` with `MaxLocomotionSpeed=450`.
  - Installed the .NET Framework 4.6.2 Developer Pack to resolve the machine-level `SwarmInterface` editor-build blocker; `BattlegroundEditor Win64 Development` now compiles.
  - IK rig/target assets were created experimentally but are unused; commandlet batch retargeting required Slate and was abandoned. SkeletalReduction LOD regeneration crashed the engine and was not retried.

- [x] **2026-11-23 — Visual PIE verification in `LV_HampiBattleground`**
  - Captured `Saved/VisualTests/Hampi_Soldier_PIE.png` (800x450, 533 KB) from a camera in the simulated PIE world; the spawned saved Blueprint reported `SKM_HampiSoldier` with `ANIMATION_SINGLE_NODE`.
  - MapCheck stayed at `0 Error(s), 0 Warning(s)`; no `DXGI_ERROR_DEVICE_REMOVED` / device-hung error occurred in this small-window run.
  - This model cannot visually inspect PNGs, so human visual sign-off of soldier/soil appearance is still recommended.

- [x] **2026-11-23 — Android ARM64 finishing pass**
  - Set `MATUSAGE_SKELETAL_MESH` on `M_HampiSoldier`; set soldier albedo/ORM textures to `TEXTUREGROUP_CHARACTER` (normal map remains `TC_NORMALMAP` / world-normal group).
  - Confirmed 14 HISM groups / 964 instances with start/end cull distances from 1,800/10,000 up to 9,000/36,000 cm; 269 static mesh components, 0 missing meshes.
  - Final commandlet validation: 277 actors, 1 Landscape, 1 PlayerStart, unchanged GameMode/default pawn, correct soldier mesh/BlendSpace, soil and soldier material inputs intact, no load/linker errors.
  - Project config still has ARM64, MinSDK 26, TargetSDK 34, Nanite/VSM/Lumen/ray/path tracing disabled. Actual APK cook/package and on-device FPS remain Tasks 19/20.

- [x] **2026-11-23 — Native module auto-load fixed in `Battleground.uproject`**
  - Added the missing `Modules` entry (`Battleground`, `Runtime`, `LoadingPhase=Default`) so `/Script/Battleground.HampiSoldierCharacter` resolves during a normal editor/game load without an explicit `unreal.load_module("Battleground")` call.
  - Backup saved at `Backups/NativeModule_Before_20261123/Battleground.uproject`; JSON validity confirmed.
  - Fresh commandlet check with no module-load call: `HampiSoldierCharacter` is present in Python, `BP_ThirdPersonCharacter` loads, CDO is an instance of the native class, soldier mesh/BlendSpace defaults are intact, and 277 actors are present. No script-package, `CreateExport`, `LogLinker`, or class-load errors remain.

- [x] **2026-11-23 — Single M416-style rifle created, compiled, and statically validated**
  - Source/license: Poly Pizza "M4 Carbine" by AdamKokrito, CC BY 3.0, model page `https://poly.pizza/m/vx8dQfkzNM`, direct ZIP `https://static.poly.pizza/d35e4164-0498-4a68-a127-5285a05c9ef1.zip`. Full attribution is in `Saved/ThirdParty/PolyPizza_M4Carbine/LICENSE.txt`. No other weapon model was added.
  - Imported one static mesh `/Game/Weapons/M416/SM_M416` with 3 mobile materials, Nanite off, mesh-only 0.11 scale (about 84 cm rifle length), and culling; cull distances remain Android-friendly. Added original procedural fire/reload WAVs in `/Game/Weapons/M416/Audio` with their own license note.
  - Added native `AM416Weapon` with proximity/E-key pickup, equip to `RightHand`, ADS/FOV narrowing, automatic fire, recoil, muzzle flash, visibility/noise-correct traces with damage, ammo, reserve, reload, and fire/reload sounds. `AHampiSoldierCharacter` owns one equipped M416 and converts the saved map marker into the native weapon at BeginPlay.
  - Added input actions and IMC mappings: Fire = Left Mouse, Aim = Right Mouse, Reload = R, Pickup = E (`IMC_Default` now has 18 mappings).
  - Added exactly one rifle pickup marker at `(-29250, 100, 1080)`, about 2.2 m from PlayerStart `(-29450, 0, 1100)`. No existing actor was moved or deleted. Actor count is 278 (was 277), with 1 Landscape, 1 PlayerStart, unchanged Landscape transform, and unchanged GameMode/default pawn asset.
  - Compile: `BattlegroundEditor Win64 Development` and `Battleground Win64 Development` both completed with exit code 0. Fixed two introduced C++ errors: Enhanced Input `BindAction` signature mismatch for the bool-returning pickup function and `IsHiddenInGame()` used on `UStaticMeshComponent`.
  - Error check: no C++ errors in either final build log; MapCheck reported `0 Error(s), 0 Warning(s)` after placement; final structural report `Saved/WeaponM416/final_validation.txt` shows 270 static mesh components, 0 missing meshes, all weapon/material/audio/input assets present, and all 4 M416 mappings assigned. Only non-blocking Python deprecation warnings occurred.
  - **Runtime test after administrator approval:** Normal PIE was started with `UnrealEditor.exe -pie`; `Saved/WeaponM416/runtime_test_v4.txt` confirms the saved marker became one native `M416Weapon`, the player controller possessed the soldier, proximity pickup succeeded, the rifle attached to `RightHand` with a 12 cm forward offset, aim changed FOV 90→55 and restored to 90, trigger-hold fire consumed 30→24 rounds in 0.65 s, the muzzle flash was visible, reload began immediately and finished with ammo 30 / reserve 114, and `Saved/VisualTests/Hampi_M416_PIE.png` was captured (190,968 bytes). Simulate-mode results are in `runtime_test_v2.txt`.
  - **Recoil fix and final re-test:** The first PIE sample showed recoil applied in code but fully recovered within the 0.125 s editor tick. A 0.12 s hold and slower recovery were added in `M416Weapon.cpp`; editor and game builds both pass again (`build_editor_recoil.txt`, `build_game_recoil.txt`, exit 0, no errors). After the rebuilt hashes were approved, the final normal-PIE run measured pitch `4.55°` and yaw `0.34°` during the burst, with recovery back to `0°` by the reload phase. All 14 harness checks now pass, including recoil; MapCheck remains `0 Error(s), 0 Warning(s)` and structural validation still reports 278 actors, 1 Landscape, 1 PlayerStart, and 0 missing meshes.

- [x] **2026-11-23 — Five AI enemies implemented and runtime-tested**
  - Added native `AHampiAICharacter` (five personas) and `AHampiAIBotSpawner`. The spawner is created at runtime by `AHampiSoldierCharacter::BeginPlay`, so the saved map was not modified (still 278 actors, 1 Landscape, 1 PlayerStart).
  - Added minimal player health to the soldier so bot attacks are observable; full health UI/healing remains a later phase. Bot sight/fire and M416 character hits use `ECC_Pawn` because the engine default `Pawn` profile ignores `Visibility`.
  - Builds: `Saved/AI/build_editor_ai_v2.txt` and `build_game_ai_v2.txt`, exit 0, no error lines.
  - Normal PIE harness `Tools/ai_runtime_test_v1.py` passed all 17 checks; report `Saved/AI/runtime_test_v1.txt`, final log `editor_runtime_final.log`, screenshot `Saved/VisualTests/Hampi_AI_PIE.png` (190,341 bytes). Verified: one runtime spawner, exactly five bots with distinct personas/spawn points, AI controllers, patrol movement, player detection, bot damage to player, M416 damage killing a bot, bot death state, and screenshot capture.
  - Known tuning note: with all five bots engaging at once the player can die within a few seconds, so combat difficulty needs balancing before release.
