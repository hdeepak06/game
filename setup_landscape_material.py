import unreal

world_path = '/Game/Maps/LV_HampiBattleground'
world = unreal.EditorLoadingAndSavingUtils.load_map(world_path)

actors = unreal.EditorLevelLibrary.get_all_level_actors()
landscape = None
has_player_start = False

for a in actors:
    if isinstance(a, unreal.Landscape):
        landscape = a
    elif isinstance(a, unreal.PlayerStart):
        has_player_start = True

print(f"Landscape found: {landscape}")
if landscape:
    # Try loading prototype grid or world grid material
    mat = unreal.EditorAssetLibrary.load_asset('/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray')
    if not mat:
        mat = unreal.EditorAssetLibrary.load_asset('/Engine/EditorMaterials/WorldGridMaterial')
    
    print(f"Loaded material: {mat}")
    if mat:
        landscape.set_editor_property('landscape_material', mat)
        print("Assigned landscape material successfully!")

if not has_player_start:
    # Spawn PlayerStart on the landscape
    start_loc = unreal.Vector(0.0, 0.0, 300.0)
    start_rot = unreal.Rotator(0.0, 0.0, 0.0)
    ps = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, start_loc, start_rot)
    print(f"Spawned PlayerStart: {ps.get_name()} at {start_loc}")

# Save map
saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
print(f"Level saved: {saved}")
