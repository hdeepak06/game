import os
import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\Loot\material_setup.txt"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []

PATH = "/Game/Environment/Loot/M_LootAmmo"
try:
    eal = unreal.EditorAssetLibrary
    eal.make_directory("/Game/Environment/Loot")
    mat = eal.load_asset(PATH) if eal.does_asset_exist(PATH) else \
        unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_LootAmmo", "/Game/Environment/Loot", unreal.Material,
            unreal.MaterialFactoryNew())
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    color = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -300, -80)
    color.set_editor_property("constant", unreal.LinearColor(1.0, 0.62, 0.08, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        color, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    eal.save_loaded_asset(mat)
    lines.append("LOOT_MATERIAL=" + PATH)
except Exception as e:
    lines.append("LOOT_MATERIAL_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("LOOT_MATERIAL_DONE")
