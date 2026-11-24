import unreal

world_path = '/Game/Maps/LV_HampiBattleground'
world = unreal.EditorLoadingAndSavingUtils.load_map(world_path)

actors = unreal.EditorLevelLibrary.get_all_level_actors()
has_navmesh = False

for a in actors:
    if isinstance(a, unreal.NavMeshBoundsVolume):
        has_navmesh = True
        break

if not has_navmesh:
    loc = unreal.Vector(0.0, 0.0, 1000.0)
    rot = unreal.Rotator(0.0, 0.0, 0.0)
    nav_vol = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.NavMeshBoundsVolume, loc, rot)
    if nav_vol:
        # Scale to cover 520m x 520m x 60m height
        nav_vol.set_actor_scale3d(unreal.Vector(270.0, 270.0, 40.0))
        print(f"Spawned NavMeshBoundsVolume: {nav_vol.get_name()} at {loc}")

# Set WorldSettings GameMode
ws = world.get_world_settings()
gm_class = unreal.EditorAssetLibrary.load_blueprint_class('/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode')
if gm_class:
    ws.set_editor_property('default_game_mode', gm_class)
    print(f"Set WorldSettings default_game_mode to {gm_class.get_name()}")

saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
print(f"Level saved: {saved}")
