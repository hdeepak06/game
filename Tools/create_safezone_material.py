import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\SafeZone\material_setup.txt"
import os
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


PATH = "/Game/Environment/SafeZone/M_SafeZoneWall"
try:
    mat = ensure_asset(PATH, unreal.Material, unreal.MaterialFactoryNew)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    color = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -320, -120)
    color.set_editor_property("constant", unreal.LinearColor(0.12, 0.55, 1.0, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        color, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    w("SAFEZONE_MATERIAL=%s" % PATH)
except Exception as e:
    w("SAFEZONE_MATERIAL_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SAFEZONE_MATERIAL_DONE")
