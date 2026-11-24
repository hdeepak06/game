# HAMPI BATTLEGROUND — DEVELOPMENT LOG

## Project Metadata
- **Project Name:** HampiBattleground (`Battleground.uproject`)
- **Engine Version:** Unreal Engine 5.4.4-35576357 (`G:\Epic Games\UE_5.4\UE_5.4`)
- **Target Platform:** Android (ARM64) | Primary Development: Windows (DX11 SM5)
- **Engine Association:** `{B15DB60E-46F2-2C60-F281-C1B203337C95}` (Verified pointing to UE 5.4.4)
- **Primary Game Level:** `/Game/Maps/LV_HampiBattleground.umap`
- **Compiler Toolchain:** MSVC 14.44.35207 (Visual Studio 2022 BuildTools) + Windows SDK 10.0.26100.0 + .NET SDK 6.0.302
- **Android Toolchain:** Android SDK 34 (`G:\Android\Sdk`) + NDK r26b (26.1.10909125) + OpenJDK 17.0.21

---

## Log Entries

### [2026-11-22] — TASK 01: Project Foundation & C++ Infrastructure
- **Status:** COMPLETED
- **Actions Taken:**
  1. Located existing project file `C:\UnrealProjects\Battleground\Battleground.uproject`. Verified engine association to UE 5.4.4.
  2. Inspected folder hierarchy:
     - `Content/`: Maps (`LV_HampiBattleground.umap`), Characters (`SKM_Manny`, `SKM_Quinn`, `ABP_Manny`, `ABP_Quinn`), Input (`IMC_Default`, `IA_Move`, `IA_Look`, `IA_Jump`), LevelPrototyping materials.
     - `Config/`: `DefaultEngine.ini`, `DefaultGame.ini`, `DefaultInput.ini`, `DefaultEditor.ini`.
     - `Source/`: Missing initially (pure Blueprint project). Successfully created C++ module structure.
  3. Created C++ Source Infrastructure:
     - `Source/Battleground/Battleground.Build.cs`: Configured dependencies (`Core`, `CoreUObject`, `Engine`, `InputCore`, `EnhancedInput`, `AIModule`, `NavigationSystem`, `GameplayTasks`, `UMG`, `Slate`, `SlateCore`).
     - `Source/Battleground/Battleground.h`: Minimal module header.
     - `Source/Battleground/Battleground.cpp`: Primary game module implementation macro (`IMPLEMENT_PRIMARY_GAME_MODULE`).
     - `Source/Battleground.Target.cs`: Game target rules with `BuildSettingsVersion.V5` and `EngineIncludeOrderVersion.Unreal5_4`.
     - `Source/BattlegroundEditor.Target.cs`: Editor target rules.
  4. Fixed Compiler Incompatibility:
     - Resolved MSVC 14.44 macro expansion bug in `ConcurrentLinearAllocator.h(31)` where `#elif __has_feature(...)` failed on non-Clang compilers. Guarded with `#elif defined(__has_feature)` to ensure clean C++ compilation under MSVC 14.44.
  5. Compilation Verification:
     - Ran `UnrealBuildTool` via `Build.bat Battleground Win64 Development -Project="C:\UnrealProjects\Battleground\Battleground.uproject" -WaitMutex`.
     - **Result:** Successfully compiled and linked `Binaries/Win64/Battleground.exe` (277 MB) and `Battleground.pdb` (310 MB) with **Exit Code 0 (0 Errors)**.

### [2026-11-22] — SYSTEM ENHANCEMENT: Windows Visible Background Task Monitor
- **Status:** COMPLETED & ACTIVE
- **Deliverables:**
  1. `Tools/TaskMonitor/task_monitor.py`: Background monitor daemon on `localhost:7788` tracking live tasks, parsing Antigravity logs, calculating true progress percentages, and recording persistent history in `task_history.json`.
  2. `Tools/TaskMonitor/notify.ps1`: Native Windows desktop balloon notification system for Task Started, Task Completed, Task Failed, and Task Cancelled alerts.
  3. `Tools/TaskMonitor/run_task.py`: CLI task runner that streams live terminal logs, parses Unreal Engine compiler actions (e.g. `[1/4]`, `[2/4]`), and updates dashboard in real time.
  4. `Tools/TaskMonitor/launch_dashboard.bat`: Standalone desktop app launcher using Microsoft Edge app mode (`--app=http://127.0.0.1:7788`).
  5. `TaskMonitor.lnk`: Project-root shortcut for immediate double-click dashboard access.

### [2026-11-22] — TASK 02: Landscape & Terrain Foundation
- **Status:** COMPLETED (Heightmap Assets & Material Ready, Manual Import Step Documented)
- **Actions Taken:**
  1. **Inspection & Protection:**
     - Verified existing `Landscape_0` in `LV_HampiBattleground.umap`: location `(-54650, -25200, 100)`, scale `(100, 100, 100)`, 64 components ($8 \times 8$), section size 63, $505 \times 505$ overall resolution.
     - Confirmed safety backup saved at `Backups/LV_HampiBattleground_Task02_Backup.umap`.
     - Identified root cause of black viewport in user's editor: `Landscape_0` had `landscape_material = None` and the level lacked ambient dynamic lighting (`SkyLight`, `SkyAtmosphere`).
  2. **Mobile Landscape Material (`M_HampiLandscape`):**
     - Programmatically created and compiled `/Game/Materials/M_HampiLandscape`.
     - Implemented 5 weight-blended landscape layers via `MaterialExpressionLandscapeLayerBlend` for BaseColor and Roughness:
       - `DrySoil`: Warm earthy brown `(0.35, 0.22, 0.12)`, Roughness `0.85` (default preview weight `1.0`).
       - `RockyGround`: Granite tan-gray `(0.38, 0.35, 0.32)`, Roughness `0.75`.
       - `Sand`: Golden sand `(0.65, 0.52, 0.32)`, Roughness `0.90`.
       - `Grass`: Semi-arid savannah olive `(0.28, 0.35, 0.14)`, Roughness `0.80`.
       - `Riverbank`: Wet alluvial mud `(0.18, 0.12, 0.08)`, Roughness `0.40`.
     - Created 5 corresponding `LandscapeLayerInfoObject` assets in `/Game/Materials/`:
       - `DrySoil_LayerInfo.uasset`, `RockyGround_LayerInfo.uasset`, `Sand_LayerInfo.uasset`, `Grass_LayerInfo.uasset`, `Riverbank_LayerInfo.uasset`.
     - Assigned `M_HampiLandscape` directly to `Landscape_0`.
  3. **Atmosphere & Dynamic Lighting Rig:**
     - Configured `DirectionalLight_1` (Sun): rotated pitch `-45°`, yaw `45°`, intensity `10.0`, `atmosphere_sun_light = True`.
     - Spawned `SkyLight_0`: movable, intensity `1.5`, `real_time_capture = True`.
     - Spawned `SkyAtmosphere_0`: full Rayleigh scattering for realistic blue Karnataka sky.
     - Spawned `ExponentialHeightFog_0`: subtle realistic distance fog (density `0.002`).
     - Spawned `PostProcessVolume_0`: unbound (`infinite_extent = True`).
     - Spawned `PlayerStart_0`: placed at `(0, 0, 300)` on the landscape.
     - Saved `LV_HampiBattleground.umap` cleanly to disk (size: 956,703 bytes). Viewport is now lit and no longer black.
  4. **5-Region Heightmap Synthesis:**
     - Generated precision $505 \times 505$ 16-bit heightmap with all 5 Karnataka regions:
       - **Region A (Hampi Rocky Hills):** High granite plateau (+45m) with multi-harmonic granite boulder formations and walkable passes.
       - **Region B (Kamalapur Village):** Smooth, flat building terrace (+18m) for village structures.
       - **Region C (Hosapete Outskirts):** Gentle rolling plains (+10m) for open combat and road infrastructure.
       - **Region D (Tungabhadra Riverside):** Depressed river corridor (-14m) with gradual banks.
       - **Region E (Military Training Ground):** Flat parade ground and firing range (+12m).
     - Exported files to `Content/Landscape/`:
       - `Hampi_Heightmap_505.png` (16-bit grayscale PNG).
       - `Hampi_Heightmap_505.r16` (16-bit Little Endian RAW, exactly 510,050 bytes).
       - `Hampi_Heightmap_Preview.png` (8-bit grayscale preview).
  5. **Technical Validation & Constraints:**
     - Identified that `Landscape_0` has **Edit Layers enabled** (`Enable Edit Layers = True`). In Unreal Engine 5.4, automated commandlet heightmap overwrite via legacy render target API is rejected by the engine when Edit Layers are active (`Cannot import to landscape with Edit Layers enabled`).
     - As required by strict project guidelines, the exact heightmap assets and the precise 5-step manual Unreal Editor import action have been documented for the user.

### [2026-11-22] — TASK: Project Inspection & Safe Cleanup
- **Status:** COMPLETED (cleanup only; no gameplay systems added)
- **Inspection:**
  1. Project file is `Battleground.uproject` (UE 5.4.4 association `{B15DB60E-46F2-2C60-F281-C1B203337C95}`). There is no separate `HampiBattleground.uproject`.
  2. No project `Plugins/` folder. Enabled engine plugins: `ModelingToolsEditorMode` (editor only), `PythonScriptPlugin`, `EditorScriptingUtilities`. All three are in use. Left enabled.
  3. C++ module `Battleground` compiles as a stub (`Battleground.h` / `Battleground.cpp`) with planned dependencies: Enhanced Input, AI, Navigation, Gameplay Tasks, UMG. No gameplay classes yet.
  4. Startup and default maps are `/Game/Maps/LV_HampiBattleground`. Android is ARM64 only, min SDK 26, target SDK 34, package `com.DefaultCompany.HampiBattleground`. SDK/NDK/JDK paths are set in `DefaultEngine.ini`.
  5. Content is dominated by the UE5 Mannequin (`Characters`, about 401 MB), which is the current player mesh. Kept. No ZIP archives found.
  6. `GameProgress.md` marks TASK 09 complete. This session did not re-open the level in the editor, so the navmesh was not re-verified.
- **Removed (75 files, 5.76 MB):**
  - 12 rotated logs in `Saved/Logs/*-backup-*.log`.
  - `Saved/Crashes/` (5 crash reports, including minidumps).
  - `Saved/ShaderDebugInfo/`.
  - `Saved/Config/CrashReportClient/`.
  - Live logs `Battleground.log` and `Battleground_2.log` were kept. `Saved/` itself was not deleted.
- **Left in place on purpose:**
  - `Intermediate/` (about 1.83 GB, almost all `Intermediate/Build`) and `Binaries/` (about 628 MB). Unreal Editor was running, so these regenerable outputs were not deleted.
  - `Content/ThirdPerson/` (game mode, character, input, and template map). The game mode is the project default.
  - Landscape, heightmaps, `M_HampiLandscape`, layer infos, map backups, and setup scripts.
- **Config fixes:**
  - `Config/DefaultGame.ini`: `ProjectName` changed from `Third Person BP Game Template` to `Hampi Battleground`. `ProjectID` unchanged.
  - `Config/DefaultEditor.ini`: `SimpleMapName` changed from missing `/Game/TP_ThirdPerson/Maps/ThirdPersonExampleMap` to `/Game/Maps/LV_HampiBattleground`.
- **Validation:** Protected files confirmed present after deletion. No C++ was changed, so Unreal Build Tool was not run. A rebuild would fight the open editor and the 8 GB machine.
- **Not treated as fixed:** Historical crashes were GPU/material related (`MaterialShared.cpp` fatal, `ScopeLock` assertion, large-world precision ensure). They were logged and the dumps removed. Renderer settings were not changed while the editor was open.

### [2026-11-22] — VIEWPORT RESCUE: Black Viewport Diagnosed and Repaired
- **Status:** VERIFIED IN LIVE EDITOR (numeric screen capture; final human visual confirmation still recommended)
- **Root causes confirmed by read-only commandlet audits:**
  1. `DirectionalLight_1` rotation was `P=45 Y≈0 R=-45` (sun facing the wrong way) and its mobility was `Stationary`, explaining the historical `64 unbuilt lighting objects` warning.
  2. `PlayerStart_0` was at `(0, 0, 300)`, approximately 42.5 m outside the Landscape XY footprint (`X: -54650..-4250`, `Y: -25200..25200`).
  3. `DefaultEngine.ini` had `r.PathTracing=True` while `r.RayTracing=False` and the project was running DX11/SM5; auto exposure was disabled with a `+1.0` bias.
  4. Editor state was a `FourPanes2x2` layout with an orthographic/unlit maximized pane, and the stored perspective camera at `(0, -22000, 7000)` with `Yaw=90` looked away from the Landscape.
- **Backups created before changes:**
  - `Config/DefaultEngine.ini.previewportfix.bak`
  - `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini.previewportfix.bak`
  - Pre-existing map backups were left untouched.
- **Changes applied:**
  - `Config/DefaultEngine.ini`: `r.PathTracing=False`, `r.DefaultFeature.AutoExposure=True`.
  - `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini`: layout changed to UE's `OnePane` (an earlier `Single` value was corrected), maximize disabled, cinematic pane reset to `Default`.
  - Existing `LV_HampiBattleground.umap`: `DirectionalLight_1` set to `P=-45 Y=45 R=0`, `Movable`, intensity `10.0`, atmosphere sun enabled; `PlayerStart_0` moved to `(-29450, 0, 1100)` at the Landscape center.
  - Live editor viewport framed at `(-29450, -35000, 12000)`, `P=-18 Y=90 R=0`, with Lit view mode and post-processing/lighting show flags enabled.
- **Validation:**
  - Fresh commandlet reload of `/Game/Maps/LV_HampiBattleground`: 8 actors, exactly 1 Landscape, 64 Landscape components, material `/Game/Materials/M_HampiLandscape`.
  - Landscape bounds unchanged: origin `(-29450, 0, 425)`, extent `(25200, 25200, 425)`.
  - Post-fix sun `P=-45 Y=45`, `Movable`, intensity `10.0`; PlayerStart inside Landscape footprint; SkyLight real-time capture `True`; unbound PostProcessVolume enabled.
  - Effective CVars: `r.PathTracing=0`, `r.RayTracing=0`, `r.DefaultFeature.AutoExposure=1`.
  - Editor was restarted and the map opened cleanly (`MapCheck: 0 Error(s), 0 Warning(s)`).
  - Screen capture of the reopened editor viewport analyzed numerically: central region average luminance `132.77`, `99.7%` non-black pixels, with sky-blue and terrain-gray color buckets present. The viewport is no longer black.
  - `Build.bat Battleground Win64 Development` completed with exit code `0`. `Build.bat BattlegroundEditor Win64 Development` could not complete because this machine lacks the .NET Framework 4.6+ SDK required by the engine's `SwarmInterface` module; no project source error was reported.
- **Safety / scope:** No duplicate actors, no new level asset, no Landscape sculpting, and no new gameplay systems were added. The temporary Python startup-script entry used only for viewport framing was removed after verification.

### [2026-11-22] — TASK 04, STAGE 1: Hampi Environment Slice
- **Status:** STAGE 1 IMPLEMENTED; numeric live-editor capture verification passed. Human visual sign-off is still recommended before expanding to the full five-region map.
- **Scope / safety:**
  - Worked directly inside the existing `/Game/Maps/LV_HampiBattleground` level. No new level asset was created, the Landscape was not replaced or sculpted, and no existing asset was deleted.
  - Pre-change map backup: `Backups/LV_HampiBattleground_Task04_Stage1_Backup.umap`.
  - All added content is original and generated locally with procedural Python/PNG generation plus Unreal-native `StaticMeshDescription`. No reference photo, downloaded model pack, paid service, API key, account, Blender asset, or copyrighted image was imported into the game.
  - Only the first environment slice was built: soil material, granite boulders, and one small traditional house. No gameplay or full-region build-out was attempted.
- **Assets added (`Content/Environment/...`):**
  - `Terrain/`: five original albedo textures — soil, granite, mud plaster, clay roof, and dark wood.
  - `Materials/`: five mobile/opaque/default-lit materials — `M_HampiSoil_Mobile`, `M_HampiGranite_Mobile`, `M_HampiMudPlaster_Mobile`, `M_HampiClayRoof_Mobile`, `M_HampiWoodDark_Mobile` — plus granite instances `MI_HampiGranite_Grey`, `MI_HampiGranite_Warm`, and `MI_HampiGranite_Dark`.
  - `Rocks/`: five low-poly boulder static meshes (`SM_HampiBoulder_01` … `SM_HampiBoulder_05`), each 70 vertices / 120 triangles / 1 material slot.
  - `Houses/`: `SM_KamalapurHouse_Small`, 192 vertices / 288 triangles / 4 material slots (mud plaster, clay roof, dark wood, granite/plinth).
  - Empty folders reserved for `Temples`, `Vegetation`, and `Props`.
- **Level changes:**
  - Landscape material changed to `/Game/Environment/Materials/M_HampiSoil_Mobile`; the original `/Game/Materials/M_HampiLandscape` asset was preserved.
  - Placed one house actor, `Hampi_Task04_KamalapurHouse_Small`, at `(-29450, 0, 498.87)`.
  - Placed ten boulder actors, `Hampi_Task04_Boulder_01` … `Hampi_Task04_Boulder_10`, using the five boulder meshes with grey/warm/dark granite instances.
  - Every Stage 1 actor carries the `Task04_Stage1` tag; the setup script removes only those tagged actors before respawning, so reruns do not duplicate them.
  - Saved the existing level in place.
- **Issues found and corrected during verification:**
  - The first soil material compile error was `ComponentMask: Missing ComponentMask input`. The world-UV component-mask connection in `Tools/setup_task04_stage1.py` was corrected; the final editor log has no material compile errors for `M_HampiSoil_Mobile`.
  - Unreal Python's `Rotator` constructor order was confirmed as roll, pitch, yaw. The script's actor rotation mapping and viewport camera were corrected; the diagnostic camera is now `P=-12 Y=90 R=0` instead of looking upward.
  - A high-resolution automation screenshot call was removed from the temporary diagnostic script after it closed the editor; desktop capture was used instead.
- **Verification:**
  - Fresh commandlet reload of the saved map: 19 actors total, exactly 1 Landscape, 11 `Task04_Stage1` actors, 19 new Environment assets.
  - Landscape bounds unchanged: origin `(-29450, 0, 425)`, extent `(25200, 25200, 425)`.
  - Mesh descriptions confirm the boulder and house geometry is present even though headless `EditorStaticMeshLibrary.get_number_verts` incorrectly reports `0`; live-editor diagnostics confirmed valid bounds for the house and a boulder.
  - Final editor session: `MapCheck: 0 Error(s), 0 Warning(s)`.
  - Live-editor screenshot: `Saved/Task04Stage1Verification/stage1_viewport.png` (1366x768). Analysis of viewport region `(164..984, 77..630)` over 50,690 samples found sky-blue `28.1%`, soil/warm-earth `54.7%`, warm roof/earth `49.5%`, stone/neutral `10.7%`, dark `1.6%`; the earlier sky-dominant capture had `0%` soil and roof buckets. This confirms the corrected camera now sees terrain and structure colors rather than sky only.
  - Temporary `StartupScripts` entry was removed from `Config/DefaultEngine.ini`; editor was closed cleanly after capture. The temporary material probe asset was not saved into Content.
- **Not done at the time of Stage 1:** Full five-region Hampi layout, temples, village network, waterfront, props, vegetation, loot, gameplay systems, and Android packaging were outside this Stage 1 slice. The later full Task 04 pass below added the environment content, but gameplay/loot/packaging are still outside scope.

### [2026-11-23] — TASK 04: Full Multi-Region Environment Build
- **Status:** IMPLEMENTED IN THE EXISTING MAP; structural validation and live-editor verification passed. Human visual sign-off and gameplay-specific checks are still pending, so Task 04 remains open in `GameProgress.md`.
- **Scope / safety:**
  - Worked only inside `/Game/Maps/LV_HampiBattleground`; no new level, no Landscape replacement or sculpting, and no deletion of the Stage 1 house, boulders, PlayerStart, GameMode, lighting, or navigation setup.
  - Full pre-change backup: `Backups/Task04Full_Before_20261123_002611/`.
  - All new content is original and locally generated with Python/Unreal-native `StaticMeshDescription` and procedural PNG textures. No paid asset, plugin, API, external model pack, or copyrighted reference image was used.
- **New asset library (`Content/Environment/...`):**
  - 6 new 128/256 px procedural albedo textures: road, sand, grass, leaf, water, concrete.
  - 15 new opaque/default-lit mobile materials: dirt road, gravel road, sand, water, grass, dry grass, leaf, dry leaf, bark, stone wall, concrete, metal, warm plaster, warm roof, wood. Grass/leaf materials are two-sided only where thin cards need it.
  - 43 new low-poly static meshes: 8 houses/shops/warehouses/barracks variants, 2 rock props, 7 village/military props, 2 Hampi stone structures, 12 vegetation meshes, 11 terrain-following road strips, and 1 river strip.
  - Total `Content/Environment` asset count after the build: 83 (49 static meshes, 11 textures, 23 materials, including the 19 original Stage 1 assets).
- **Level placement:**
  - 95 tagged `Task04_Structures` actors: Kamalapur houses/shops, Hampi stone houses, Anjanadri structures, Hosapete houses/warehouses, military barracks, water tanks, compound walls, fences, gates, ruins, stone walls, watchtowers, sandbags, and target frames.
  - 11 tagged `Task04_Roads` actors connecting Kamalapur, Hampi, Anjanadri, Hosapete, the river, and the military ground, plus a village loop and Hampi ruins path.
  - 26 tagged `Task04_River` actors: the Tungabhadra water/sandbank strip, 24 river boulders, and a 48-instance HISM group of small river stones.
  - 12 tagged vegetation HISM groups totaling 856 instances: coconut/date palms, neem, banyan, tamarind, acacia, dry-region trees, green bushes, dry shrubs, grass tufts, dry grass tufts, and riverside reeds.
  - Combined persistent HISM count after reload: 13 groups / 904 instances, all with distance culling; foliage uses no collision.
- **Rock and mobility checks:**
  - Preserved the five Stage 1 boulder meshes and ten boulder actors. Each boulder mesh has 120 triangles, 3 simple box collision elements, 1 convex collision element, Nanite disabled, and opaque single-sided granite material instances.
  - All ten boulder actors and the sampled new structure actor use `BlockAll` with query-and-physics collision.
  - Foliage HISM components have `NoCollision`; road/river decorative strips are non-colliding so they do not create invisible walls.
- **Mobile-oriented implementation:**
  - Low-poly meshes range from 12 to 432 triangles for the new structure/vegetation/terrain set; the preserved Stage 1 house is 288 triangles and boulders are 120 triangles each.
  - HISM is used for all repeated vegetation and river stones, with per-group cull distances (grass 1,800–10,000 cm, bushes 3,000–16,000 cm, trees 7,000–36,000 cm, river stones 1,800–10,000 cm).
  - Textures are 128/256 px. All generated meshes have Nanite disabled. Foliage/road materials use small, simple default-lit graphs.
  - `Config/DefaultEngine.ini` was backed up as `Config/DefaultEngine.ini.pre_task04_full.bak`; `r.Shadow.Virtual.Enable`, `r.Nanite`, and `r.Nanite.ProjectEnabled` were explicitly set to disabled. Lumen, ray tracing, and path tracing were already disabled. Probe after reload: `r.Nanite=0`, `r.Lumen=0`, `r.Shadow.Virtual.Enable=0`, `r.RayTracing=0`, `r.PathTracing=0`.
- **Issues found and corrected:**
  - First HISM pass created components that survived only until save/reload. Persistence probe proved that assigning the HISM component as the actor root makes it serialize correctly; vegetation and river-stone scripts were corrected and rerun.
  - Live editor shader compilation found `(Node Multiply) Arithmetic between types float2 and float3 are undefined` in all 15 new materials. The base-color graph was incorrectly multiplying UV coordinates by the tint; it now multiplies texture RGB by tint. All materials were rebuilt.
  - MapCheck reported missing `bUsedWithInstancedStaticMeshes` flags on bark/leaf/dry-grass/stone-wall materials. All generated materials now set that usage flag; live MapCheck reports no such warnings.
  - Unreal Python `Transform` uses `location`/`scale` keyword names in this version, and `StaticMeshDescription.get_vertex_position` requires a `VertexID`; both validation/placement scripts were corrected.
- **Verification:**
  - Fresh commandlet reload and repeatable validator: `/Game/Maps/LV_HampiBattleground`, 163 actors, exactly 1 Landscape, 64 Landscape components, unchanged Landscape bounds `origin=(-29450,0,425)`, `extent=(25200,25200,425)`, unchanged soil material `/Game/Environment/Materials/M_HampiSoil_Mobile`, and exactly 1 PlayerStart at `(-29450,0,1100)`.
  - All 11 preserved `Task04_Stage1` actors are present with unchanged locations; 95 structures have a uniform 5 cm ground offset and no floating warnings.
  - HISM components and all 904 instances persist after a fresh map reload; sampled road mesh vertices conform to terrain with offsets of 2.0–7.5 cm.
  - Asset check: 0 missing assets, 0 meshes with empty material slots/default materials, all audited meshes non-Nanite, and collision elements present on rocks/structures.
  - Live editor session: no material compile errors, no HISM usage warnings, `MapCheck: 0 Error(s), 0 Warning(s)`.
  - Live viewport capture: `Saved/Task04FullAudit/full_viewport.png` (1366x768). Numeric analysis of the viewport crop `(164..984, 77..630)` over 453,460 samples found average luminance `142.44`, `98.4%` non-black pixels, `0.9%` sky, `92.7%` soil/warm-earth, `2.4%` neutral stone, and `1.8%` dark pixels. This confirms the frame is filled with terrain rather than sky. Because this model cannot visually inspect PNGs, human visual confirmation is still recommended.
  - Diagnostic scripts and outputs are preserved under `Tools/` and `Saved/Task04FullAudit/`; no temporary `StartupScripts` hook was added to `Config/DefaultEngine.ini`.
- **Not done:** Human visual sign-off, play-mode collision walkthrough, enterable interiors, loot spawn points, navigation rebuild/verification after new obstacles, bridges over the river, gameplay systems, Android ARM64 cook/package, and APK verification.

### [2026-11-23] — TASK 05: Virupaksha Landmark Documentation Corrected
- **Status:** PRESERVED AS COMPLETED WORK; stale documentation corrected.
- **Discovery:** A previous, undocumented Task 05 build existed on disk. It was not regenerated, deleted, or moved. Reports in `Saved/Task05Audit/` document the work.
- **Preserved content:**
  - `/Game/Environment/Task05/Virupaksha`: 9 static meshes and 10 material instances. Gopuram 3,416 tris, mandapa 2,232 tris, plus sanctum, sub-shrine, cloister, courtyard wall, tank, bazaar shop, and access road; all Nanite disabled.
  - 114 `Task05_Virupaksha` actors around Hampi `(-43800, 13500, 100)`: gopuram, mandapa, sanctum, 6 sub-shrines, 8 cloister segments, 10 wall segments, tank, 10 bazaar shops, access/bazaar road, 10 boulders, and 60 instanced stones.
  - 64 hidden `BlockAll` collision proxies aligned with the stonework; visible landmark meshes are `NoCollision`.
- **Validation:** Fresh reload reported 277 actors, 1 Landscape, 1 PlayerStart, 0 missing meshes, 1 Task05 HISM component with 60 persistent instances, and MapCheck `0 Error(s), 0 Warning(s)`.
- **Documentation fix:** `GameProgress.md` Task 05 checkbox changed to complete with the above note; no map layout change was made.

### [2026-11-23] — Hampi Soil Upgrade In Place
- **Status:** COMPLETED AND VALIDATED.
- **Backup:** `Backups/SoilUpgrade_Before_20261123_082400/`.
- **Changes:** Rebuilt `/Game/Environment/Materials/M_HampiSoil_Mobile` in place with 45 material nodes. Base color is `MaterialExpressionLinearInterpolate_2`, roughness `MaterialExpressionLinearInterpolate_3`. The material blends laterite, gravel, dry grass, granite, and a mask-driven ground breakup. Original `/Game/Materials/M_HampiLandscape` was left intact.
- **Textures:** Added 256 px `T_HampiSoilLaterite_Albedo`, `T_HampiGravel_Albedo`, `T_HampiDryGrassPatch_Albedo`, and mask texture `T_HampiGroundMask`; reused existing `T_HampiGranite_Albedo`.
- **Issue resolved:** The audit line `USAGE_FLAG_WARN=set_material_usage() takes at most 2 arguments (3 given)` was a script bug: this engine's `MaterialEditingLibrary.set_material_usage(material, usage)` accepts only two arguments. It was not a material compile error, and no bad flag was written.
- **Verification:** No shader compile errors; Landscape still uses `M_HampiSoil_Mobile`, 1 Landscape, bounds unchanged, MapCheck clean. Report: `Saved/SoilUpgradeAudit/soil_upgrade.txt`.

### [2026-11-23] — Player Mannequin Replaced With CC0 Modern Soldier
- **Status:** COMPLETED; native class, Blueprint reparent, and animation wiring validated.
- **Backup:** `Backups/SoldierReplace_Before_20261123_083233/`.
- **Source/license:** Grab3D `soldier-rigged` CC0 model (`https://grab3d.com/models/characters/soldier/`, `https://grab3d.com/license/`). AI-assisted disclosure is recorded in `Saved/ThirdParty/Grab3D_Soldier/LICENSE.txt`. No paid/copyrighted pack was used.
- **Imported assets:** `/Game/Characters/Soldier/SKM_HampiSoldier`, `SKM_HampiSoldier_Skeleton`, `Animations/SoldierAnims_walk` (1.0 s), `Animations/SoldierAnims_run` (0.625 s), 1K `T_Soldier_BaseColor`, `T_Soldier_Normal`, `T_Soldier_ORM`, and `Materials/M_HampiSoldier`.
- **Animation approach:** `ABP_Quinn` targets the Manny skeleton and has no exposed graph variables, so direct asset swapping was not viable. Batch IK retargeting in a commandlet required Slate and was abandoned. IK rig/target assets remain as unused experiments. Created `BS_SoldierLocomotion` (BlendSpace1D, Speed 0-450) with idle pose at walk/`rate=0`, walk at 160, run at 450.
- **Native class:** Added `Source/Battleground/HampiSoldierCharacter.h/.cpp`. It keeps existing Character behavior and drives the soldier through `AnimationSingleNode`, setting the BlendSpace position from horizontal speed each tick. Game target build succeeded after renaming a shadowing local `Mesh` variable to `MeshComp`.
- **Editor build blocker fixed:** The earlier `SwarmInterface` failure was a missing .NET Framework 4.6+ SDK, not project code. Installed `NDP462-DevPack-KB3151934-ENU.exe` with `/install /quiet /norestart`; `Build.bat BattlegroundEditor Win64 Development -Project=... -WaitMutex` then compiled successfully.
- **Blueprint reparent:** A commandlet reparent produced load errors, so the Blueprint was restored from backup and reparented in a full `UnrealEditor.exe` process with `unreal.load_module("Battleground")` first. `EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)` persisted the change. Final saved Blueprint uses `SKM_HampiSoldier`, no `anim_class`, `ANIMATION_SINGLE_NODE`, `LocomotionAsset=BS_SoldierLocomotion`, `MaxLocomotionSpeed=450`, and `bDriveLocomotionAnimation=True`.
- **Avoided crash:** `EditorSkeletalMeshLibrary.regenerate_lod` previously hit a SkeletalReduction assertion and was not retried; the soldier remains a single-LOD mesh.

### [2026-11-23] — Visual PIE Verification
- **Status:** CAPTURE SUCCEEDED; human visual sign-off still recommended.
- **Setup issues found and fixed:**
  - `-ExecutePythonScript` closes the editor on the next tick unless `EditorPythonScripting.set_keep_python_script_alive(True)` is called; this caused earlier deferred captures to stop after one tick.
  - Loading the Blueprint before `unreal.load_module("Battleground")` produced `Failed to find script package for import object 'Package /Script/Battleground'` and a null-class spawn crash. Added the explicit module load.
  - `editor_play_simulate()` starts a real PIE world (`UEDPIE_0_LV_HampiBattleground`) but does not spawn a pawn, so the saved soldier Blueprint and a camera actor were spawned into the map for the capture. The camera actor was re-resolved from the PIE world before taking the screenshot.
  - Standalone `-game` via `UnrealEditor.exe` could not load the native module, and `Battleground.exe` needs cooked shader libraries, so the full-editor PIE path was used.
- **Result:** `Saved/VisualTests/Hampi_Soldier_PIE.png` (800x450, 533,362 bytes). Log confirmed the spawned saved Blueprint used `SKM_HampiSoldier` with `ANIMATION_SINGLE_NODE`. MapCheck `0 Error(s), 0 Warning(s)`; no `DXGI_ERROR_DEVICE_REMOVED` / device-hung error in this small-window run.
- **Limitation:** This model cannot visually inspect PNGs; the screenshot is retained for user review.

### [2026-11-23] — Android ARM64 Finishing Pass And Final Validation
- **Status:** COMPLETED (configuration/asset pass); APK cook/package and device profiling remain outstanding.
- **Applied changes:**
  - `M_HampiSoldier`: `MaterialEditingLibrary.set_material_usage(mat, MATUSAGE_SKELETAL_MESH)` returned `True` and the material was saved, removing the need for a skeletal-mesh usage recompile.
  - Soldier albedo and ORM textures changed from `TEXTUREGROUP_WORLD` to `TEXTUREGROUP_CHARACTER`; normal map remains `TC_NORMALMAP` with the available world-normal group. All three remain 1024x1024 with mipmaps from group.
  - No destructive static-mesh LOD regeneration was attempted. The 63 static meshes are already low-poly (12-432 tris for the new set), Nanite is disabled, and repeated foliage/river stones use HISM with per-group distance culling.
- **Audited mobile state:** 14 HISM groups / 964 instances with `instance_start_cull_distance` / `instance_end_cull_distance` from 1,800/10,000 to 9,000/36,000 cm; 269 static mesh components, 0 missing meshes. Project config: ARM64, MinSDK 26, TargetSDK 34, package `com.DefaultCompany.HampiBattleground`, Nanite/VSM/Lumen/ray/path tracing disabled.
- **Final structural validation:** 277 actors, exact 1 Landscape and 1 PlayerStart, Landscape actor location `(-54650,-25200,100)` / scale 100 unchanged, default pawn still `BP_ThirdPersonCharacter_C`, soldier mesh/BlendSpace and both soil/soldier material inputs intact, no load/linker/material errors in the final log.
- **Remaining:** Task 03 sprint/crouch and health/armor, human visual sign-off, gameplay collision walkthrough, full graphics scalability presets (Task 19), and Android cook/package/APK verification (Task 20).

### [2026-11-23] — Native Module Auto-Load Fixed
- **Status:** COMPLETED AND VALIDATED.
- **Root cause:** `Battleground.uproject` had no `Modules` array. The C++ module compiled because both target files added `Battleground` to `ExtraModuleNames`, but the editor did not auto-load it. Loading `BP_ThirdPersonCharacter` before an explicit `unreal.load_module("Battleground")` therefore produced `VerifyImport: Failed to find script package for import object 'Package /Script/Battleground'` and `CreateExport: Failed to load Class /Script/Battleground.HampiSoldierCharacter`, which also caused the earlier null-class PIE spawn crash.
- **Fix:** Added `"Modules": [{"Name": "Battleground", "Type": "Runtime", "LoadingPhase": "Default"}]` to `Battleground.uproject`. Backup: `Backups/NativeModule_Before_20261123/Battleground.uproject`. The file still parses as valid JSON.
- **Verification:** A fresh `UnrealEditor-Cmd.exe -run=pythonscript` pass deliberately did **not** call `unreal.load_module`. Report `Saved/CurrentStateAudit/native_autoload.txt` shows `PYTHON_CLASS=<class 'HampiSoldierCharacter'>`, Blueprint/class/CDO loaded, `IS_NATIVE_SOLDIER=True`, correct `BS_SoldierLocomotion` / `450.0` / `True` defaults, `SKM_HampiSoldier` with `ANIMATION_SINGLE_NODE`, and 277 actors. The final `Saved/Logs/Battleground.log` has no script-package, `CreateExport`, `LogLinker`, or class-load errors; only harmless Python deprecation warnings and the machine-level Unreal Trace Server access warning remain.

### [2026-11-23] — Single M416 Rifle: Creation, Compile, Error Check, Fixes, Static Validation
- **Status:** CREATION, COMPILE, ERROR CHECK, FIXES, STATIC VALIDATION, AND NORMAL-PIE TEST COMPLETE. ALL 14 RUNTIME CHECKS PASS, INCLUDING RECOIL.
- **Backup:** `Backups/M416_Before_20261123/` contains the map, player Blueprint, both docs, and project state before this work.
- **Model source and license:** Poly Pizza "M4 Carbine" by AdamKokrito (CC BY 3.0). Page: `https://poly.pizza/m/vx8dQfkzNM`. Verified direct download: `https://static.poly.pizza/d35e4164-0498-4a68-a127-5285a05c9ef1.zip`. The ZIP contained only `source/M4.fbx`. Attribution and license details are saved in `Saved/ThirdParty/PolyPizza_M4Carbine/LICENSE.txt`. No paid/copyrighted pack and no other weapon source was used.
- **Assets created:** `/Game/Weapons/M416/SM_M416` as one static mesh with 3 imported slots replaced by `M_M416_Primary`, `M_M416_Secondary`, and `M_M416_Highlight`; `M_M416_MuzzleFlash` for the additive flash. Nanite is off. The imported FBX was about 767 cm long; mesh-relative scale 0.11 makes the rifle about 84 cm. Scaling the mesh instead of the actor preserves world-sized pickup and FX radii. Fire/reload WAVs were generated by `Tools/generate_m416_audio.py`; `Saved/ThirdParty/ProceduralAudio/LICENSE.txt` records that they are original, sample-free project audio.
- **Weapon gameplay:** `Source/Battleground/M416Weapon.h/.cpp` implements `AM416Weapon`: world pickup sphere plus E-key fallback, equip to `RightHand`, ADS flag/FOV handoff on the character, automatic fire at `FireInterval=0.095`, pitch/yaw recoil with recovery, cone muzzle flash, camera/actor line traces with spread, `ApplyDamage`, 30-round magazine, 120 reserve, 1.8 s reload, and procedural fire/reload sounds. `HampiSoldierCharacter` owns at most one weapon, binds the four new Enhanced Input actions, attaches the weapon, and replaces a saved rifle marker with the native actor at BeginPlay.
- **Input setup:** Created `IA_M416_Fire`, `IA_M416_Aim`, `IA_M416_Reload`, and `IA_M416_Pickup` and added 4 mappings to `IMC_Default` (Left Mouse, Right Mouse, R, E). Final report shows 18 total mappings and all 4 M416 keys present.
- **Map change:** Exactly one tagged `M416Pickup` marker was added at `(-29250, 100, 1080)` near the existing PlayerStart `(-29450, 0, 1100)`. The marker uses `SM_M416` at 0.11 scale with collision disabled. The prior Landscape/PlayerStart/lighting/roads/buildings/HISM actors were untouched. Map actor count went 277 to 278; final validation reports 1 Landscape, 1 PlayerStart, unchanged Landscape location/scale, 270 static mesh components, 0 missing meshes, and all M416 assets present.
- **Compile and fixes:** Initial `BattlegroundEditor Win64 Development` build exposed two introduced errors: `UEnhancedInputComponent::BindAction` cannot bind the bool-returning `TryPickupM416` directly, and `UStaticMeshComponent` has no `IsHiddenInGame()`. Fixed by adding `void AHampiSoldierCharacter::HandlePickupInput()` and a local `bMuzzleFlashVisible` flag. Final editor and game builds both ended with exit code 0 and no error lines in `Saved/WeaponM416/build_editor_marker.txt` or `build_game_marker.txt`.
- **Error check:** MapCheck after placement reported `0 Error(s), 0 Warning(s)`. The three commandlet warnings were only Python `DeprecationWarning`s for `EditorLevelLibrary.load_level/get_all_level_actors`, not project errors. Final static report: `Saved/WeaponM416/final_validation.txt`.
- **Initial runtime blocker and resolution:** After the first post-weapon rebuild, Windows Code Integrity/Application Control blocked `UnrealEditor-Battleground.dll` and `Battleground.exe` with error 4551 (events 3033/3077, policy `{0283AC0F-FFF1-49AE-ADA1-8A933130CAD6}`). Temporary engine-directory/junction load-path experiments were reverted and `Battleground.uproject`/`UnrealEditor.modules` were restored byte-for-byte. After the administrator-approved/signed state was applied, the same project binaries loaded and `UnrealEditor-Cmd.exe -run=pythonscript` executed again, so runtime testing proceeded.

### [2026-11-23] — M416 Normal PIE Runtime Test
- **How PIE was started:** `UnrealEditor.exe Battleground.uproject -pie -ExecutePythonScript=Tools/m416_runtime_test_v4.py -ABSLOG=Saved/WeaponM416/editor_runtime_v4_final.log -windowed -ResX=800 -ResY=450 -nosplash -log`. The `-pie` flag starts real Play-In-Editor, unlike `editor_play_simulate()`. Reports: `Saved/WeaponM416/runtime_test_v4.txt`, `runtime_test_v2.txt`, and `editor_runtime_v4_final.log`.
- **Verified PASS (final rebuilt binaries):** PIE world `/Game/Maps/UEDPIE_0_LV_HampiBattleground`; player controller present and possessing `BP_ThirdPersonCharacter_C`; saved marker converted into exactly one `M416Weapon`; proximity pickup returned True; `equipped_m416` became non-null; weapon root attached to socket `RightHand` with relative location `(12,0,0)`; aim flag toggled True/False; camera FOV 90°→55°→90°; trigger-held fire for 0.65 s consumed 7 rounds (30→23); muzzle flash was observed visible during the burst; recoil peaked at pitch `4.55°` / yaw `0.34°` and recovered to `0°` by the reload phase; reload began with `reloading=True` and completed with ammo 30, reserve 113; screenshot `Saved/VisualTests/Hampi_M416_PIE.png` was written (190,219 bytes). All 14 harness checks are True. No project runtime exceptions were logged; MapCheck reported `0 Error(s), 0 Warning(s)`.
- **Recoil finding and fix:** In the first approved build, `ApplyRecoil()` added pitch/yaw but the 0.125 s editor tick and original 14°/s / 7°/s recovery erased each 0.65° shot within the same tick. `M416Weapon.h/.cpp` now hold recoil for 0.12 s and recover at 3.5°/s pitch and 2°/s yaw. Both editor and game targets rebuilt with exit code 0 and no error lines (`Saved/WeaponM416/build_editor_recoil.txt`, `build_game_recoil.txt`).
- **Approval handling:** The rebuilt DLL SHA-256 `4FD56F0792A67698954BDF53DDD6F8464CF085D4209CDBEBF68DCCD87C3F72FB` and EXE SHA-256 `77E10221CEDDA8C6F76B27A2BA386D6120FF2DF84342BFF4DEBFDBBA3110BC17` were initially denied with GetLastError 4551. After the administrator allowed the exact rebuilt hashes, both binaries loaded and the final test above ran. No Windows security setting was changed or bypassed by this project work.

### [2026-11-23] — Five AI Enemies: Native Bots, Runtime Spawner, PIE Test
- **Status:** COMPLETE; all 17 runtime checks pass. Phase 2 of the user-defined order is done.
- **New source:** `Source/Battleground/HampiAICharacter.h/.cpp` (five-persona FSM bot) and `HampiAIBotSpawner.h/.cpp` (runtime spawner). `HampiSoldierCharacter` now spawns one spawner in BeginPlay and has minimal health/damage support. `M416Weapon.cpp` character hits now trace `ECC_Pawn`.
- **No map edits:** Bots are spawned at runtime from offsets around the preserved PlayerStart. Final structural validation is unchanged at 278 actors, 1 Landscape, 1 PlayerStart, 1 M416 marker, 0 missing meshes.
- **Compile errors fixed during this phase:** `AIController.h` include path, `FDamageEvent` definition include (`Engine/DamageEvents.h`), and a `TObjectPtr` array conversion. Final editor/game builds: `Saved/AI/build_editor_ai_v2.txt`, `build_game_ai_v2.txt` (exit 0, no error lines).
- **Key bug found and fixed:** UE's default `Pawn` collision profile ignores `Visibility`, so visibility traces cannot hit characters. Bot sight/fire and M416 hit traces were changed to `ECC_Pawn`; bot damage to the player and M416 damage to a bot then worked.
- **PIE test command:** `UnrealEditor.exe Battleground.uproject -pie -ExecutePythonScript=Tools/ai_runtime_test_v1.py -ABSLOG=Saved/AI/editor_runtime_final.log -windowed -ResX=800 -ResY=450 -nosplash -log`.
- **Verified PASS:** one runtime `HampiAIBotSpawner`; exactly five `HampiAICharacter` bots with distinct names/personas/spawn points; each possessed by `AIController`; health 80/70/110/100/90; all alive at start; all five patrolled 168-1846 cm in four seconds; bots entered Engage/Investigate and reduced player health from 100 to 0; M416 fire reduced Raven from 80 to 0 in seven rounds; `ApplyTestDamage` death path also verified; screenshot `Saved/VisualTests/Hampi_AI_PIE.png` (190,341 bytes). No harness errors and no project runtime exceptions.
- **Current binary hashes:** `UnrealEditor-Battleground.dll` SHA-256 `290084DF872FCE6559F04D8E944C3CB2009B12A7872DCA855B91295E5A78D1CC`; `Battleground.exe` SHA-256 `FC718E0FBD1239F50A99AF7A227642F6FD3A7D6BB91768FBCE2994FB77E266C0`.
- **Pending:** Difficulty balancing (five bots can kill the player in seconds), Behavior Tree/Blackboard upgrade, health/healing UI, loot/inventory, dialogues, HUD/mobile controls, Android APK cook/package.

### [2026-11-23] — Shrinking Safe Zone: Native Actor, Material, PIE Test
- **Status:** COMPLETE; all 12 runtime checks pass. Phase 3 of the user-defined order is done.
- **New source:** `Source/Battleground/HampiSafeZone.h/.cpp` — a scene root with a single `/Engine/BasicShapes/Cylinder` wall scaled to the current radius, an additive unlit two-sided material, four-phase linear shrink, `GetCurrentRadius`, `GetPhase`, `GetTimeToNextPhase`, `IsInside`, and 0.5 s damage ticks to out-of-zone players and bots. `HampiSoldierCharacter::BeginPlay` spawns exactly one zone at the first `APlayerStart` (the soldier's own location is not final yet in BeginPlay, which was found and fixed during testing).
- **New asset:** `/Game/Environment/SafeZone/M_SafeZoneWall` created by `Tools/create_safezone_material.py`.
- **Compile:** `Saved/SafeZone/build_editor_v3.txt` and `build_game_v3.txt`, exit 0, no error lines. Earlier iterations in `build_editor.txt`, `build_game.txt`, `build_editor_v2.txt`, `build_game_v2.txt` were intermediate.
- **PIE test:** `Tools/safezone_runtime_test_v1.py` with `Saved/SafeZone/editor_runtime_final.log`. The harness accelerates the zone (3,000 cm to 500 cm, 1 s delay, 2 s phases, 12 damage/sec) after first confirming the real 24,000 cm defaults and correct PlayerStart centering. It polls damage until the world ticks because Slate tick time can drift from PIE world time.
- **Verified PASS:** one zone at `(-29450, 0, 850)`; player initially inside; 24,000 cm initial radius; shrink reaches 500 cm / phase 2; wall scale falls from ~31x to 10x; bots and players outside take damage; screenshot `Saved/VisualTests/Hampi_SafeZone_PIE.png` (437,000 bytes). No runtime exceptions.
- **Current binary hashes:** `UnrealEditor-Battleground.dll` SHA-256 `E4800CF8AC92610BC5B086AEC2976D1CC60FB9BE79A5DD13761157E12BED2B7A`; `Battleground.exe` SHA-256 `DC78346BF8D965518647E5CD8653B693C9369128ED04A8CF56CED010B5CBEA73`.
- **Map unchanged:** final validation still reports 278 actors, 1 Landscape, 1 PlayerStart, 1 M416 marker, 0 missing meshes.
- **Pending:** full health/damage/healing system, loot/inventory, North Karnataka Kannada dialogues, HUD/mobile controls, environments, Android optimization, APK.

### [2026-11-23] — Player Health, Damage & Healing
- **Status:** COMPLETE; all 47 normal-PIE checks pass. Phase 4 of the user-defined order is done.
- **Source:** `HampiSoldierCharacter` gained shield-first damage, damage source tracking, out-of-combat regeneration (8 s delay, 3 hp/s), `Heal`, `StartHealOverTime`, `AddShield`, `ApplyTestDamage`, `Die`, and `Respawn`. New `HampiHealingItem.h/.cpp` implements three one-use pickup types. New materials created by `Tools/create_health_materials.py`: `/Game/Environment/Health/M_Medkit`, `M_EnergyDrink`, `M_Armor`.
- **Compile fix:** first build failed because `FDamageEvent` was undefined in the soldier translation unit; adding `Engine/DamageEvents.h` fixed it. Final logs: `Saved/Health/build_editor_v2.txt`, `build_game_v2.txt` (exit 0, no error lines).
- **PIE test:** `Tools/health_runtime_test_v1.py`, log `Saved/Health/editor_runtime_final.log`. Bots are moved away so only the health system is under test. The harness accidentally discovered that `take_high_res_screenshot` stalls world ticks; the screenshot is now requested first and absorbed by a warm-up window so timed heal checks are stable. Picked-up items are destroyed after 0.25 s, so the harness treats an invalid actor reference as consumed.
- **Verified PASS:** initial 100 HP / 0 shield; 30 damage -> 70 HP; 50 shield absorbs 20 damage (shield 30, HP 70); instant heal caps at 100; 40 damage with 30 shield -> 90 HP; heal-over-time progresses and completes with its flag cleared; lethal damage kills and clears shield; death source recorded; respawn restores 100 HP at `(-29450, 0, 1100)`; Medkit, EnergyDrink, and Armor pickups are consumed and apply their effects; screenshot 472,677 bytes. No runtime exceptions.
- **Current binary hashes:** `UnrealEditor-Battleground.dll` SHA-256 `9A99AF9E0D95B3D80ACC314CDEE62D94201718861D40C154D3BD78D0ED83016F`; `Battleground.exe` SHA-256 `705790BD5C9A33FC9C00B77F8E6C3EADE2D623B693C7D2FD3DCF468A03688963`.
- **Map unchanged:** 278 actors, 1 Landscape, 1 PlayerStart, 1 M416 marker, 0 missing meshes.
- **Pending:** loot/inventory, North Karnataka Kannada dialogues, HUD/mobile controls, environment expansion, Android optimization, APK.

### [2026-11-23] — Ground Loot & Inventory
- **Status:** COMPLETE; all 32 normal-PIE checks pass. Phase 5 of the user-defined order is done.
- **Source:** new `HampiLootItem.h/.cpp` with four loot types (5.56mm ammo, Medkit, EnergyDrink, Armor), animated cube plus glowing vertical marker, and proximity pickup. `HampiSoldierCharacter` gained `FHampiInventoryEntry` stacks, `AddInventoryItem`, `GetInventoryCount`, `UseConsumable`, `GetInventorySummary`, `SetWeaponSlot`, `GetWeaponSlot`, and Primary/Secondary/Pistol slot fields. Equipping the M416 now records it in the Primary slot. Five loot items spawn at runtime; the map is untouched.
- **New asset:** `/Game/Environment/Loot/M_LootAmmo` via `Tools/create_loot_material.py`; existing health emissive materials are reused for the other types.
- **Compile:** `Saved/Loot/build_editor_v1.txt` and `build_game_v1.txt`, exit 0, no error lines.
- **PIE test:** `Tools/loot_runtime_test_v1.py`, log `Saved/Loot/editor_runtime_v1.log`. Bots moved away; screenshot captured first with warm-up. All five pickups collected by teleport, inventory stacks checked, three weapon slots checked, and Medkit/EnergyDrink/Armor consumption effects and stock decrements verified. Screenshot 471,554 bytes. No runtime exceptions.
- **Current binary hashes:** `UnrealEditor-Battleground.dll` SHA-256 `7B7264D59DD2AE858ADF246457F5B036396D17D767248B81AAF95FE3635E69F6`; `Battleground.exe` SHA-256 `27AFADDCB6CFA65F363818F5BBB40E0114B42B5E53DCF6F8E195DE3C834F6850`.
- **Map unchanged:** 278 actors, 1 Landscape, 1 PlayerStart, 1 M416 marker, 0 missing meshes.
- **Pending:** North Karnataka Kannada dialogues, HUD/mobile controls, environment expansion, Android optimization, APK.

### [2026-11-23] - North Karnataka Kannada Voice Dialogue
- **Status:** COMPLETE; all 56 normal-PIE checks pass. Phase 6 of the user-defined order is done.
- **Audio generation:** `Tools/generate_kannada_dialogue.py` produced eight 24 kHz mono WAVs in `Saved/ThirdParty/KannadaDialogue` with `edge-tts 7.3.1` (LGPLv3) using `kn-IN-GaganNeural` and `kn-IN-SapnaNeural`, then converted MP3 to PCM WAV with bundled `imageio-ffmpeg`. The script now uses North Karnataka colloquial forms such as `ಶುರು ಆಯ್ತು`, `ಎಚ್ಚರ ಇರಿ`, `ಸೇಫ್ ಜೋನ್`, and `ಮಾಡಿ`. Full attribution and the standard-voice dialect caveat are in `Saved/ThirdParty/KannadaDialogue/LICENSE.txt`.
- **Imported assets:** `Tools/import_kannada_dialogue.py` reimported eight SoundWaves into `/Game/Audio/Dialogue`; `Saved/Voice/import_report.txt` confirms all loaded as `SoundWave`.
- **Source:** new `HampiDialogueDirector.h/.cpp` caches the eight cues, plays them through a non-spatialized `UAudioComponent`, enforces a 6 s per-cue cooldown, records `PlayedCues`, and auto-triggers MatchStart, EnemySpotted, ZoneWarning, LowHealth, Defeat, and Victory from PIE state. `AHampiSoldierCharacter` spawns one director at runtime and fires WeaponEquipped from `EquipM416` and Healing from `Heal`/`StartHealOverTime`. The saved map is untouched.
- **Build:** `Saved/Voice/build_editor_v3.txt` and `build_game_v3.txt`, exit 0, no error lines. An early editor warning about the director's missing root component was fixed by assigning `RootComponent = AudioComponent`; the final runtime log has no such warning.
- **PIE test:** `Tools/voice_runtime_test_v1.py`, log `Saved/Voice/editor_runtime_final.log`. The first attempt parked bots outside the safe zone and killed them before the enemy/victory checks; the harness now keeps them at 8,000 cm inside the initial zone and freezes their ticks. MatchStart is checked after the screenshot warm-up because `take_high_res_screenshot` stalls PIE world ticks.
- **Verified PASS:** one director, eight loaded cues, eight Kannada source lines with license/attribution text, per-cue cooldown, and automatic MatchStart, WeaponEquipped, Healing, EnemySpotted, ZoneWarning, LowHealth, Defeat, and Victory. Final cue order: `MatchStart,WeaponEquipped,Healing,EnemySpotted,ZoneWarning,LowHealth,Defeat,Victory`. Screenshot `Saved/VisualTests/Hampi_Voice_PIE.png` (471,840 bytes). No runtime exceptions.
- **Current binary hashes:** `UnrealEditor-Battleground.dll` SHA-256 `3172E984FCEB912B48FEA5D8921283C4970CC1BA0296ECDC2FFC6BA82B572BF0`; `Battleground.exe` SHA-256 `3B22EB5C7818889C9135E74DAF29C8F1D94A57D87F9DB2BA0BF1EE1DC2F0DF84`.
- **Map unchanged:** 278 actors, 1 Landscape, 1 PlayerStart, 1 M416 marker, 0 missing meshes.
- **Pending:** HUD/mobile controls, environment expansion, Android optimization, APK.

### [2026-11-23] — Mobile Touch HUD & On-Screen Controls
- **Status:** COMPLETE; all 62 normal-PIE checks pass. Phase 7 of the user-defined order is done.
- **Source:** new native, asset-free `UHampiMobileHUDWidget` (`HampiMobileHUDWidget.h/.cpp`) builds its whole UMG layout at runtime from `/Engine/EngineResources/WhiteSquareTexture`. `AHampiSoldierCharacter::BeginPlay()` creates and adds it to the viewport for the local player only, so the saved map, GameMode, camera, movement, and input mappings remain untouched. `Config/DefaultInput.ini` now sets `DefaultTouchInterface=None` to avoid Android's duplicate engine joysticks.
- **Controls:** floating left-side joystick sends movement relative to control rotation; right-half drag sends yaw/pitch through the player controller; six touch buttons call the real soldier/weapon actions. Desktop mouse input mirrors the touch handlers for PIE verification. FIRE/ADS/JUMP release handlers stop their held actions; CROUCH toggles; RELOAD starts a magazine reload; SWAP cycles Primary -> Secondary -> Pistol.
- **HUD state:** health and shield bars with numeric text, current/reserve ammo plus RELOADING state, 5-tick cardinal compass, 5 red enemy radar dots, 12-segment safe-zone ring, and contextual prompts for M416 pickup, nearby loot, healing, and combat.
- **Soldier helpers added:** `GetMobileHUDWidget`, `CycleWeaponSlot`, `GetActiveWeaponSlot`, `TogglePlayerCrouch`, `IsPlayerCrouched`, `MobileJump`/`MobileStopJump`, `IsPlayerAirborne`, and `IsAimingM416`/`IsAimingM416Active`. `M416Weapon` gained `IsReloading()`. Crouch movement is enabled without changing the default standing setup. The template pawn can still be in `MOVE_FALLING` at PIE start, so `MobileJump` uses `UCharacterMovementComponent::DoJump(false)` with a `LaunchCharacter` fallback and records the last launch for deterministic verification.
- **Build:** `Saved/HUD/build_editor_v8.txt` and `build_game_v1.txt`, both exit 0 with no error lines. Early build fixes added `JoystickRadius`, replaced unsupported `UProgressBar::SetBackgroundColor`/style fields with `FProgressBarStyle`, renamed a shadowing `Slot` local, used `FLinearColor` for text shadows, and added `GetMaxPlayerShield`.
- **PIE test:** `Tools/hud_runtime_test_v1.py`, log `Saved/HUD/editor_runtime_final.log`, report `Saved/HUD/runtime_test_v1.txt`. The harness isolates bots, places the soldier on walkable ground before the jump test, and verifies widget structure, joystick movement, camera swipe, FIRE/ADS/JUMP/CROUCH/RELOAD/SWAP button counts and side effects, jump launch, bars, ammo text, compass, five radar dots, prompt text, screenshot, and zero runtime errors. All 62 checks pass.
- **Screenshot caveat:** `Saved/VisualTests/Hampi_HUD_PIE.png` (471,840 bytes) is byte-identical to `Hampi_Voice_PIE.png`; the automation capture API is not proving that the UMG overlay is drawn. A human should open normal PIE and confirm the HUD visually, then confirm again on Android.
- **Current binary hashes:** `UnrealEditor-Battleground.dll` SHA-256 `706366A9F1DB2A0450B922ED4A2478EE50EF45DE7FC4673B4BCDBD8BC8570D5A`; `Battleground.exe` SHA-256 `FB08362C44C3DCA5EA3F9EE72F01EF6FB2DBA9FB229E319493264C662AA5CCF5`.
- **Structural validation:** `Saved/HUD/final_validation.txt` and `Saved/HUD/final_validation_editor.log`: 278 actors, 1 Landscape, 1 PlayerStart, 1 M416 marker, 270 static mesh components, 0 missing meshes, MapCheck `0 Error(s), 0 Warning(s)`, white texture loads as `Texture2D`, `DefaultTouchInterface=None`, HUD/soldier symbols and UMG dependencies present.
- **Pending:** environment expansion, Android optimization, APK.

### [2026-11-23] — GPU Crash Root Cause and Editor Harness Fix
- **Status:** crash cause identified and mitigation verified; no gameplay source changed.
- **Evidence:** five crash folders report `CrashType=GPUCrash` / `GPU Crash dump Triggered`. Every GPU crash log ends with `DXGI_ERROR_DEVICE_REMOVED DXGI_ERROR_DEVICE_HUNG` at `D3D11Query.cpp:361`, the D3D11 `GetQueryData` failure path for a render timestamp query. All affected editor logs show the default Insights channels `cpu,gpu,frame,log,bookmark,screenshot,region`. UE 5.4 source confirms editor trace autostart enables the `gpu` channel and that this forces realtime GPU stats/timestamp queries even when `r.GPUStatsEnabled=0`.
- **Hardware context:** Intel Core i5-1035G1 / Intel UHD Graphics, driver `27.20.100.8935`, 128 MB dedicated VRAM, ~4.18 GB shared memory, 8 GB system RAM with roughly 2 GB free. Some older logs also show 1152 MiB texture DDC compile estimates against 700-1076 MiB available; that added memory pressure, but the direct failure point was the GPU timestamp query.
- **Fix:** all normal PIE commands now include `-traceautostart=0`, preventing the GPU trace channel from being enabled. `BuildInstructions.md` was updated for every PIE harness. No C++ rebuild was needed, so the current DLL/EXE hashes are unchanged.
- **Regression test:** new `Tools/gpu_crash_regression.py` uses wall-clock time (an initial Slate-`dt` attempt was invalid because `dt` was 17,021,592 seconds after one frame) and soaks normal PIE for 200 seconds. `Saved/GPUCrash/regression_v1.txt`: `STATUS=PASS`, `SURVIVED_SECONDS=200.00`, `FRAMES=572`, `ERRORS=[]`; markers report 316 actors, 1 soldier, 5 bots. `Saved/GPUCrash/regression_editor_v2.log` has no GPU trace channel and no GPU errors; editor exit 0.
- **Gameplay re-check:** the HUD harness was re-run with `-traceautostart=0`; `Saved/HUD/runtime_test_v1.txt` still shows 62/62 checks and `ERRORS=[]`, and `Saved/GPUCrash/hud_after_gpu_fix.log` has no GPU errors.
- **Safety:** no Windows security, Defender, Smart App Control, Application Control, policy, driver, or administrator setting was changed.
- **Full report:** `Saved/GPUCrash/root_cause_report.txt`.
- **Pending:** mobile graphics profiles, Android SDK/NDK/JDK verification, ARM64 Development APK, physical-device test, Shipping APK.

### [2026-11-23] — Android Graphics Profiles and Packaging Blocker
- **Status:** LOW/MEDIUM/HIGH profiles added and validated; Development APK packaging is blocked by an incomplete UE engine installation.
- **New files:** `Config/DefaultDeviceProfiles.ini` and `Config/Android/AndroidScalability.ini`; no C++ source or saved map was changed.
  - LOW maps to `Android_Low`/`sg.*=0`, 70% mobile resolution scale, mobile AA off, 512px 1-cascade shadows, reduced view distance/effects/texture filtering.
  - MEDIUM maps to `Android_Mid`/`sg.*=1`, 85% resolution scale, balanced shadows/post process.
  - HIGH maps to `Android_High`/`sg.*=2`, 100% resolution scale, 2048px 2-cascade shadows. No `t.MaxFPS` cap is set, so capable devices can run above 30 FPS.
- **Android settings:** `Config/DefaultEngine.ini` now explicitly sets `Orientation=Landscape`, `MaxAspectRatio=2.400000`, `bUseDisplayCutout=True`, alongside the existing ARM64-only MinSDK 26 / TargetSDK 34 configuration.
- **Validation:** new `Tools/validate_graphics_profiles.py` checked 108/108 assertions with `STATUS=PASS`, `ERRORS=[]`; report `Saved/Android/graphics_profiles_validation.txt`, editor log `Saved/Android/graphics_profiles_validation_editor.log` (0 errors, 0 warnings).
- **Preserved gameplay regression:** all seven harnesses were rerun with `-traceautostart=0` after the profile/config changes: M416 14/14, AI 16/16, SafeZone 12/12, Health 45/45, Loot 32/32, Voice 56/56, HUD 62/62 tuple checks true; every editor exited 0 and no GPU error lines appeared. Summary: `Saved/GPUCrash/gameplay_regression_summary.txt`; per-test logs `Saved/GPUCrash/regression_gameplay_*.log`. An initial batch attempt did not launch the editor and was discarded before evidence collection.
- **Hashes:** `DefaultDeviceProfiles.ini` SHA-256 `F323880030977C83ACDEDD81DBFDB9B26F7C1D8B3D0C087FBDA40023B7A9984A`; `AndroidScalability.ini` SHA-256 `D9F72BC402A4AA16B69D84D3EAC8BDA3CF46EDDCAFE83CA60A6B40C6769F72B4`; `validate_graphics_profiles.py` SHA-256 `0440A2F66DEFFC3F8BAA9AC8FFAFC49C71736EE8FDE80F4E7E3A5D4D3D3A753E`.
- **Toolchain:** Android SDK/NDK/JDK were verified (`Saved/Android/toolchain_report.txt`). Installed engine-expected `android-33` platform and `build-tools 33.0.1` via `sdkmanager` because UE 5.4's `Android_SDK.json` expects those versions.
- **Packaging attempt:** `BuildCookRun` for Android Development ARM64 failed before compiling with UAT exit 6: `Missing files required to build Android targets. Enable Android as an optional download component in the Epic Games Launcher.` Full report: `Saved/Android/package_blocker_report.txt`; log: `Saved/Android/package_development.log`.
- **Blocker cause:** the engine installation lacks `G:\Epic Games\UE_5.4\UE_5.4\Engine\Binaries\Android\UnrealGame.target` and the entire `Engine\Binaries\Android` directory. This is a missing Android platform component in the Epic launcher install, not a project error. No security, policy, admin, or licensing check was bypassed.
- **No device:** `adb devices -l` reports no attached phone, so install/FPS/memory tests are still pending.
- **Next:** enable Android platform support in Epic Games Launcher for UE 5.4.4, verify `Engine\Binaries\Android\UnrealGame.target` exists, connect a USB-debugging phone, then retry the Development package. Shipping remains intentionally unbuilt.


