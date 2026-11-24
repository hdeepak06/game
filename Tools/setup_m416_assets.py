import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "WeaponM416", "asset_setup.txt")
MAT_DIR = "/Game/Weapons/M416/Materials"
AUDIO_DIR = "/Game/Weapons/M416/Audio"
INPUT_DIR = "/Game/ThirdPerson/Input/Actions"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def ensure_asset(asset_path, asset_class, factory):
    eal = unreal.EditorAssetLibrary
    if eal.does_asset_exist(asset_path):
        return eal.load_asset(asset_path)
    name = asset_path.rsplit("/", 1)[-1]
    folder = asset_path.rsplit("/", 1)[0]
    eal.make_directory(folder)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, folder, asset_class, factory())


def rebuild_material(path, color, roughness=0.7, metallic=0.0,
                     emissive=None, additive=False):
    mat = ensure_asset(path, unreal.Material, unreal.MaterialFactoryNew)
    if not mat:
        w("MATERIAL_FAIL=%s" % path)
        return None
    try:
        unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    except Exception as e:
        w("MATERIAL_CLEAR_ERR %s=%s" % (path, e))

    base = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -320, -120)
    base.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -320, 40)
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    metal = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -320, 140)
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(
        metal, "", unreal.MaterialProperty.MP_METALLIC)

    if emissive:
        em = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant3Vector, -320, 240)
        em.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        unreal.MaterialEditingLibrary.connect_material_property(
            em, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    if additive:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property("two_sided", True)

    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    w("MATERIAL=%s" % path)
    return mat


def ensure_input_action(name, key_name):
    path = "%s/%s" % (INPUT_DIR, name)
    action = ensure_asset(path, unreal.InputAction, unreal.InputAction_Factory)
    if not action:
        w("INPUT_ACTION_FAIL=%s" % path)
        return None
    try:
        action.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
        unreal.EditorAssetLibrary.save_loaded_asset(action)
    except Exception as e:
        w("INPUT_ACTION_PROP_ERR %s=%s" % (name, e))
    w("INPUT_ACTION=%s key=%s" % (path, key_name))
    return action


def import_audio(src_name, dst_name):
    src = os.path.join(PROJECT, "Saved", "ThirdParty", "ProceduralAudio", src_name)
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = AUDIO_DIR
    task.destination_name = dst_name
    task.replace_existing = True
    task.automated = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    path = "%s/%s" % (AUDIO_DIR, dst_name)
    obj = unreal.EditorAssetLibrary.load_asset(path)
    w("AUDIO=%s loaded=%s" % (path, bool(obj)))
    return obj


try:
    w("ASSET_SETUP_BEGIN")
    eal = unreal.EditorAssetLibrary
    for folder in [MAT_DIR, AUDIO_DIR, INPUT_DIR]:
        eal.make_directory(folder)

    mat_map = {
        "Primary": (0.12, 0.14, 0.16),
        "Secondary": (0.045, 0.05, 0.055),
        "Highlight": (0.31, 0.27, 0.21),
    }
    mats = {}
    for label, color in mat_map.items():
        mats[label] = rebuild_material(
            "%s/M_M416_%s" % (MAT_DIR, label), color, roughness=0.72,
            metallic=0.35 if label == "Primary" else 0.1)

    rebuild_material(
        "%s/M_M416_MuzzleFlash" % MAT_DIR,
        (1.0, 0.52, 0.08), roughness=1.0, metallic=0.0,
        emissive=(8.0, 2.4, 0.15), additive=True)

    mesh = eal.load_asset("/Game/Weapons/M416/SM_M416")
    if mesh:
        slots = list(mesh.get_editor_property("static_materials"))
        replacements = [mats["Primary"], mats["Secondary"], mats["Highlight"]]
        for idx, slot in enumerate(slots):
            if idx < len(replacements) and replacements[idx]:
                slot.set_editor_property("material_interface", replacements[idx])
        mesh.set_editor_property("static_materials", slots)
        try:
            mesh.set_editor_property("nanite_settings", mesh.get_editor_property("nanite_settings"))
        except Exception:
            pass
        eal.save_loaded_asset(mesh)
        w("MESH_MATERIALS_ASSIGNED slots=%d" % len(slots))
    else:
        w("MESH_MISSING")

    import_audio("S_M416_Fire.wav", "S_M416_Fire")
    import_audio("S_M416_Reload.wav", "S_M416_Reload")

    actions = [
        ("IA_M416_Fire", "LeftMouseButton"),
        ("IA_M416_Aim", "RightMouseButton"),
        ("IA_M416_Reload", "R"),
        ("IA_M416_Pickup", "E"),
    ]
    created = {}
    for name, key in actions:
        created[name] = ensure_input_action(name, key)

    imc = eal.load_asset("/Game/ThirdPerson/Input/IMC_Default")
    if imc:
        mappings = list(imc.get_editor_property("mappings"))
        existing = set()
        for m in mappings:
            try:
                existing.add((m.get_editor_property("action").get_path_name(),
                              str(m.get_editor_property("key").get_editor_property("key_name"))))
            except Exception:
                pass
        for name, key in actions:
            action = created.get(name)
            if not action:
                continue
            marker = (action.get_path_name(), key)
            if marker in existing:
                w("MAPPING_EXISTS=%s" % name)
                continue
            mapping = unreal.EnhancedActionKeyMapping()
            mapping.set_editor_property("action", action)
            k = unreal.Key()
            k.set_editor_property("key_name", unreal.Name(key))
            mapping.set_editor_property("key", k)
            mappings.append(mapping)
            existing.add(marker)
            w("MAPPING_ADDED %s -> %s" % (name, key))
        imc.set_editor_property("mappings", mappings)
        eal.save_loaded_asset(imc)
        w("IMC_SAVED mappings=%d" % len(mappings))
    else:
        w("IMC_MISSING")
    w("ASSET_SETUP_DONE")
except Exception as e:
    w("ASSET_SETUP_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("M416_ASSET_SETUP_WRITTEN")
