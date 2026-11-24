import unreal

world = unreal.EditorLoadingAndSavingUtils.load_map('/Game/Maps/LV_HampiBattleground')
actors = unreal.EditorLevelLibrary.get_all_level_actors()

lines = []
lines.append('=== ACTORS IN LV_HAMPIBATTLEGROUND ===')
for a in actors:
    lines.append(f"Actor: {a.get_name()} ({a.get_class().get_name()}) | Loc: {a.get_actor_location()} | Rot: {a.get_actor_rotation()}")
    if isinstance(a, unreal.Landscape):
        mat = a.get_editor_property('landscape_material')
        lines.append(f"  Landscape Material: {mat}")
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        if comp:
            lines.append(f"  DirLight Intensity: {comp.get_editor_property('intensity')}, AtmSunLight: {comp.get_editor_property('atmosphere_sun_light')}")
    if isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        if comp:
            lines.append(f"  SkyLight Intensity: {comp.get_editor_property('intensity')}, RealTime: {comp.get_editor_property('real_time_capture')}")
lines.append('=== END ACTORS ===')

with open(r'C:/UnrealProjects/Battleground/inspect_output.txt', 'w') as f:
    f.write('\n'.join(lines))
