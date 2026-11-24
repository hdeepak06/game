import unreal

unreal.log("=== STEP 1: CREATING HAMPI LANDSCAPE MATERIAL ===")
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

mat_path = '/Game/Materials'
mat_name = 'M_HampiLandscape'
mat = unreal.EditorAssetLibrary.load_asset(f'{mat_path}/{mat_name}')
if not mat:
    factory = unreal.MaterialFactoryNew()
    mat = asset_tools.create_asset(mat_name, mat_path, unreal.Material, factory)

mel.delete_all_material_expressions(mat)

blend_color = mel.create_material_expression(mat, unreal.MaterialExpressionLandscapeLayerBlend, -200, -100)
blend_roughness = mel.create_material_expression(mat, unreal.MaterialExpressionLandscapeLayerBlend, -200, 200)

layers_data = [
    ('DrySoil', '(X=0.35,Y=0.22,Z=0.12)', '(X=0.85,Y=0.85,Z=0.85)', 1.0),
    ('RockyGround', '(X=0.38,Y=0.35,Z=0.32)', '(X=0.75,Y=0.75,Z=0.75)', 0.0),
    ('Sand', '(X=0.65,Y=0.52,Z=0.32)', '(X=0.90,Y=0.90,Z=0.90)', 0.0),
    ('Grass', '(X=0.28,Y=0.35,Z=0.14)', '(X=0.80,Y=0.80,Z=0.80)', 0.0),
    ('Riverbank', '(X=0.18,Y=0.12,Z=0.08)', '(X=0.40,Y=0.40,Z=0.40)', 0.0),
]

color_layers = []
rough_layers = []
for name, col_str, rough_str, prev_wt in layers_data:
    lc = unreal.LayerBlendInput()
    lc.import_text(f'(LayerName="{name}",BlendType=LB_WeightBlend,PreviewWeight={prev_wt},ConstLayerInput={col_str})')
    color_layers.append(lc)
    
    lr = unreal.LayerBlendInput()
    lr.import_text(f'(LayerName="{name}",BlendType=LB_WeightBlend,PreviewWeight={prev_wt},ConstLayerInput={rough_str})')
    rough_layers.append(lr)

blend_color.set_editor_property('layers', color_layers)
blend_roughness.set_editor_property('layers', rough_layers)

mel.connect_material_property(blend_color, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(blend_roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("Material M_HampiLandscape created and compiled!")

unreal.log("=== STEP 2: CREATING LAYER INFO OBJECTS ===")
layer_factory = unreal.LandscapeLayerInfoObjectFactory()
for name, _, _, _ in layers_data:
    info_name = f'{name}_LayerInfo'
    asset_path = f'{mat_path}/{info_name}'
    if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        obj = asset_tools.create_asset(info_name, mat_path, unreal.LandscapeLayerInfoObject, layer_factory)
        if obj:
            unreal.EditorAssetLibrary.save_loaded_asset(obj)
            unreal.log(f"Created LayerInfo: {info_name}")
    else:
        unreal.log(f"LayerInfo exists: {info_name}")

unreal.log("=== STEP 3: CONFIGURING LEVEL LV_HAMPIBATTLEGROUND ===")
world_path = '/Game/Maps/LV_HampiBattleground'
world = unreal.EditorLoadingAndSavingUtils.load_map(world_path)
actors = unreal.EditorLevelLibrary.get_all_level_actors()

landscape = None
dir_light = None
has_skylight = False
has_sky_atm = False
has_fog = False
has_pp = False
has_player_start = False

for a in actors:
    if isinstance(a, unreal.Landscape):
        landscape = a
    elif isinstance(a, unreal.DirectionalLight):
        dir_light = a
    elif isinstance(a, unreal.SkyLight):
        has_skylight = True
    elif isinstance(a, unreal.SkyAtmosphere):
        has_sky_atm = True
    elif isinstance(a, unreal.ExponentialHeightFog):
        has_fog = True
    elif isinstance(a, unreal.PostProcessVolume):
        has_pp = True
    elif isinstance(a, unreal.PlayerStart):
        has_player_start = True

# Assign landscape material
if landscape:
    landscape.set_editor_property('landscape_material', mat)
    unreal.log(f"Assigned M_HampiLandscape to {landscape.get_name()}")

# Configure Directional Light
if dir_light:
    dir_light.set_actor_rotation(unreal.Rotator(-45.0, 45.0, 0.0), False)
    comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
    if comp:
        comp.set_editor_property('intensity', 10.0)
        comp.set_editor_property('atmosphere_sun_light', True)
        unreal.log("Configured DirectionalLight")

# Spawn SkyLight if missing
if not has_skylight:
    sl = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 5000), unreal.Rotator(0, 0, 0))
    if sl:
        sl_comp = sl.get_component_by_class(unreal.SkyLightComponent)
        if sl_comp:
            sl_comp.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
            sl_comp.set_editor_property('intensity', 1.5)
            sl_comp.set_editor_property('real_time_capture', True)
        unreal.log(f"Spawned SkyLight: {sl.get_name()}")

# Spawn SkyAtmosphere if missing
if not has_sky_atm:
    sa = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    unreal.log(f"Spawned SkyAtmosphere: {sa.get_name()}")

# Spawn ExponentialHeightFog if missing
if not has_fog:
    fog = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 100), unreal.Rotator(0, 0, 0))
    if fog:
        fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if fog_comp:
            fog_comp.set_editor_property('fog_density', 0.002)
        unreal.log(f"Spawned ExponentialHeightFog: {fog.get_name()}")

# Spawn PostProcessVolume for stable mobile exposure
if not has_pp:
    pp = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if pp:
        pp.set_editor_property('unbound', True)
        unreal.log(f"Spawned PostProcessVolume: {pp.get_name()}")

# Spawn PlayerStart if missing
if not has_player_start:
    ps = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 300), unreal.Rotator(0, 0, 0))
    unreal.log(f"Spawned PlayerStart: {ps.get_name()}")

# Save Level
saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
unreal.log(f"Level saved: {saved}")
