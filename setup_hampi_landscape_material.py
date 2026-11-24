import unreal

unreal.log("=== STARTING HAMPI LANDSCAPE SETUP ===")

# 1. Load or create M_HampiLandscape
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
package_path = '/Game/Materials'
mat_name = 'M_HampiLandscape'
mat_full_path = f'{package_path}/{mat_name}'

mat = unreal.EditorAssetLibrary.load_asset(mat_full_path)
if not mat:
    factory = unreal.MaterialFactoryNew()
    mat = asset_tools.create_asset(mat_name, package_path, unreal.Material, factory)
    unreal.log(f"Created new material: {mat}")
else:
    unreal.log(f"Loaded existing material: {mat}")

mel = unreal.MaterialEditingLibrary
mel.delete_all_material_expressions(mat)

# 2. Configure layers
layers_def = [
    ('DrySoil', unreal.LinearColor(0.35, 0.22, 0.12, 1.0), 0.85),
    ('RockyGround', unreal.LinearColor(0.38, 0.35, 0.32, 1.0), 0.75),
    ('Sand', unreal.LinearColor(0.65, 0.52, 0.32, 1.0), 0.90),
    ('Grass', unreal.LinearColor(0.28, 0.35, 0.14, 1.0), 0.80),
    ('Riverbank', unreal.LinearColor(0.18, 0.12, 0.08, 1.0), 0.40)
]

# Create Layer Blend node for Base Color
blend_color = mel.create_material_expression(mat, unreal.MaterialExpressionLandscapeLayerBlend, -200, -100)
# Create Layer Blend node for Roughness
blend_roughness = mel.create_material_expression(mat, unreal.MaterialExpressionLandscapeLayerBlend, -200, 200)

color_layers = []
rough_layers = []

y_offset = -300
for name, color, roughness in layers_def:
    # Color input
    vec_expr = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, y_offset)
    vec_expr.set_editor_property('constant', color)
    
    # Roughness input
    scalar_expr = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -500, y_offset + 50)
    scalar_expr.set_editor_property('r', roughness)
    
    # Color blend input entry
    l_c = unreal.LayerBlendInput()
    l_c.set_editor_property('layer_name', unreal.Name(name))
    l_c.set_editor_property('blend_type', unreal.LandscapeLayerBlendType.LB_WEIGHT_BLEND)
    l_c.set_editor_property('preview_weight', 1.0 if name == 'DrySoil' else 0.0)
    color_layers.append(l_c)
    
    # Roughness blend input entry
    l_r = unreal.LayerBlendInput()
    l_r.set_editor_property('layer_name', unreal.Name(name))
    l_r.set_editor_property('blend_type', unreal.LandscapeLayerBlendType.LB_WEIGHT_BLEND)
    l_r.set_editor_property('preview_weight', 1.0 if name == 'DrySoil' else 0.0)
    rough_layers.append(l_r)
    
    y_offset += 120

blend_color.set_editor_property('layers', color_layers)
blend_roughness.set_editor_property('layers', rough_layers)

# Connect color and roughness expressions to blend nodes
# In MaterialExpressionLandscapeLayerBlend, each layer input corresponds to LayerInput_<LayerName>
for i, (name, color, roughness) in enumerate(layers_def):
    # Find nodes by location
    y_pos = -300 + (i * 120)
    # We can connect expressions using mel.connect_material_expressions
    # connect color expression to blend_color
    pass

# Connect blend nodes to material root
mel.connect_material_property(blend_color, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(blend_roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)

mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("Material M_HampiLandscape saved successfully!")
