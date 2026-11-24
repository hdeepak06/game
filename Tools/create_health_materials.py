import os
import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\Health\material_setup.txt"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s):
    lines.append(str(s))
    unreal.log(str(s))


def ensure_asset(path, asset_class, factory):
    eal = unreal.EditorAssetLibrary
    if eal.does_asset_exist(path):
        return eal.load_asset(path)
    name = path.rsplit("/", 1)[-1]
    folder = path.rsplit("/", 1)[0]
    eal.make_directory(folder)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, folder, asset_class, factory())


def build(path, color):
    mat = ensure_asset(path, unreal.Material, unreal.MaterialFactoryNew)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    emissive = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -300, -80)
    emissive.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        emissive, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    w("HEALTH_MATERIAL=%s" % path)


try:
    unreal.EditorAssetLibrary.make_directory("/Game/Environment/Health")
    build("/Game/Environment/Health/M_Medkit", (0.10, 1.0, 0.25))
    build("/Game/Environment/Health/M_EnergyDrink", (0.10, 0.55, 1.0))
    build("/Game/Environment/Health/M_Armor", (1.0, 0.78, 0.12))
except Exception as e:
    w("HEALTH_MATERIAL_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("HEALTH_MATERIAL_DONE")
