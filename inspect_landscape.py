import unreal

world_path = '/Game/Maps/LV_HampiBattleground'
world = unreal.EditorLoadingAndSavingUtils.load_map(world_path)

actors = unreal.EditorLevelLibrary.get_all_level_actors()
landscape = None

for a in actors:
    if isinstance(a, unreal.Landscape):
        landscape = a
        break

lines = []
lines.append("=== LANDSCAPE DETAILED AUDIT ===")
if landscape:
    lines.append(f"Actor Name: {landscape.get_name()}")
    lines.append(f"Location: {landscape.get_actor_location()}")
    lines.append(f"Rotation: {landscape.get_actor_rotation()}")
    lines.append(f"Scale: {landscape.get_actor_scale3d()}")
    try:
        lines.append(f"Material: {landscape.get_editor_property('landscape_material')}")
    except Exception as e:
        lines.append(f"Material error: {e}")
    
    comps = landscape.get_components_by_class(unreal.LandscapeComponent)
    lines.append(f"Total Components: {len(comps)}")
    if len(comps) > 0:
        c0 = comps[0]
        lines.append(f"Component 0 Class: {c0.get_class().get_name()}")
        # Inspect available properties
        c_props = [p for p in dir(c0) if not p.startswith('_')]
        lines.append(f"Component properties sample: {c_props[:20]}")

lines.append("\n=== ENGINE API AVAILABILITY ===")
lines.append(f"Has MaterialEditingLibrary: {hasattr(unreal, 'MaterialEditingLibrary')}")
lines.append(f"Has LandscapeEditorSubsystem: {hasattr(unreal, 'LandscapeEditorSubsystem')}")
lines.append(f"Has LandscapeBlueprintBrushBase: {hasattr(unreal, 'LandscapeBlueprintBrushBase')}")
lines.append(f"Has AssetToolsHelpers: {hasattr(unreal, 'AssetToolsHelpers')}")
lines.append(f"Has EditorActorSubsystem: {hasattr(unreal, 'EditorActorSubsystem')}")

# Check MaterialEditingLibrary methods if available
if hasattr(unreal, 'MaterialEditingLibrary'):
    mel_methods = [m for m in dir(unreal.MaterialEditingLibrary) if not m.startswith('_')]
    lines.append(f"MaterialEditingLibrary methods ({len(mel_methods)}): {', '.join(mel_methods[:15])}")

with open(r'C:\UnrealProjects\Battleground\inspect_landscape_output.txt', 'w') as f:
    f.write('\n'.join(lines))

print("Audit written to inspect_landscape_output.txt")
