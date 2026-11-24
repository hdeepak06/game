import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
TEX_DIR = "/Game/Characters/Soldier/Textures"
MAT_DIR = "/Game/Characters/Soldier/Materials"
SRC = os.path.join(PROJECT, "Saved", "SoldierImport", "Textures1024")
MESH_PATH = "/Game/Characters/Soldier/SKM_HampiSoldier"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "material_lod_report.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def import_texture(filename, name, srgb, compression, group):
    eal = unreal.EditorAssetLibrary
    path = TEX_DIR + "/" + name
    if not eal.does_directory_exist(TEX_DIR):
        eal.make_directory(TEX_DIR)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", os.path.join(SRC, filename))
    task.set_editor_property("destination_path", TEX_DIR)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = eal.load_asset(path)
    if not tex:
        raise RuntimeError("texture import failed: " + name)
    tex.set_editor_property("srgb", srgb)
    tex.set_editor_property("compression_settings", compression)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    tex.set_editor_property("lod_group", group)
    for p in ("address_x", "address_y"):
        tex.set_editor_property(p, unreal.TextureAddress.TA_WRAP)
    eal.save_loaded_asset(tex)
    try:
        size = tex.blueprint_get_size_x()
    except Exception:
        size = "?"
    w("TEXTURE %s size=%s srgb=%s compression=%s" % (name, size, srgb, compression))
    return tex


def build_material(tex):
    eal = unreal.EditorAssetLibrary
    if not eal.does_directory_exist(MAT_DIR):
        eal.make_directory(MAT_DIR)
    path = MAT_DIR + "/M_HampiSoldier"
    mat = eal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_HampiSoldier", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        raise RuntimeError("material creation failed")
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("two_sided", False)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)

    def node(cls, x, y, **props):
        n = mel.create_material_expression(mat, cls, x, y)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def connect(src, outs, dst, ins):
        for o in outs:
            for i in ins:
                try:
                    if mel.connect_material_expressions(src, o, dst, i):
                        return True
                except Exception:
                    continue
        w("CONNECT_FAIL %s -> %s" % (src.get_name(), dst.get_name()))
        return False

    base = node(unreal.MaterialExpressionTextureSampleParameter2D, -800, -300,
                parameter_name="BaseColorTexture", texture=tex["base"])
    normal = node(unreal.MaterialExpressionTextureSampleParameter2D, -800, 0,
                  parameter_name="NormalTexture", texture=tex["normal"])
    orm = node(unreal.MaterialExpressionTextureSampleParameter2D, -800, 300,
               parameter_name="ORMTexture", texture=tex["orm"])

    def mask(src, channel, x, y):
        props = {"r": channel == "r", "g": channel == "g",
                 "b": channel == "b", "a": False}
        n = node(unreal.MaterialExpressionComponentMask, x, y, **props)
        connect(src, ["RGB", "RGBA", ""], n, [""])
        return n

    ao = mask(orm, "r", -520, 260)
    rough = mask(orm, "g", -520, 370)
    metal = mask(orm, "b", -520, 480)

    def to_property(src, prop, outputs):
        for o in outputs:
            try:
                if mel.connect_material_property(src, o, prop):
                    return True
            except Exception:
                continue
        return False

    if not to_property(base, unreal.MaterialProperty.MP_BASE_COLOR, ["RGB", "RGBA", ""]):
        raise RuntimeError("base color connect failed")
    if not to_property(normal, unreal.MaterialProperty.MP_NORMAL, ["RGB", "RGBA", ""]):
        raise RuntimeError("normal connect failed")
    if not to_property(ao, unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, ["", "R", "RGB"]):
        w("AO_CONNECT_WARN")
    if not to_property(rough, unreal.MaterialProperty.MP_ROUGHNESS, ["", "R", "RGB"]):
        raise RuntimeError("roughness connect failed")
    if not to_property(metal, unreal.MaterialProperty.MP_METALLIC, ["", "R", "RGB"]):
        raise RuntimeError("metallic connect failed")

    spec = node(unreal.MaterialExpressionScalarParameter, -300, 600,
                parameter_name="Specular", default_value=0.35)
    if not to_property(spec, unreal.MaterialProperty.MP_SPECULAR, ["", "Output"]):
        w("SPECULAR_CONNECT_WARN")

    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    w("MATERIAL=%s base=%s normal=%s rough=%s metal=%s" % (
        mat.get_path_name(),
        mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR),
        mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_NORMAL),
        mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_ROUGHNESS),
        mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_METALLIC)))
    return mat


def setup_lods(mesh):
    esml = unreal.EditorSkeletalMeshLibrary
    infos = []
    screens = [1.0, 0.42, 0.15]
    tris = [0, 80000, 22000]
    for i in range(3):
        info = unreal.SkeletalMeshLODInfo()
        info.set_editor_property("screen_size", unreal.PerPlatformFloat(default=screens[i]))
        red = unreal.SkeletalMeshOptimizationSettings()
        red.set_editor_property("reduction_method", unreal.SkeletalMeshOptimizationType.SMOT_NUM_OF_TRIANGLES)
        red.set_editor_property("termination_criterion", unreal.SkeletalMeshTerminationCriterion.SMTC_ABS_NUM_OF_TRIANGLES)
        red.set_editor_property("max_num_of_triangles", tris[i])
        red.set_editor_property("max_bones_per_vertex", 4)
        red.set_editor_property("enforce_bone_boundaries", True)
        red.set_editor_property("silhouette_importance", unreal.SkeletalMeshOptimizationImportance.SMOI_HIGH)
        red.set_editor_property("texture_importance", unreal.SkeletalMeshOptimizationImportance.SMOI_NORMAL)
        red.set_editor_property("normal_importance", unreal.SkeletalMeshOptimizationImportance.SMOI_NORMAL) if hasattr(red, "normal_importance") else None
        info.set_editor_property("reduction_settings", red)
        infos.append(info)
    mesh.set_editor_property("lod_info", infos)
    ok = esml.regenerate_lod(mesh, new_lod_count=3, regenerate_even_if_imported=True,
                             generate_base_lod=True)
    w("LOD_REGENERATE=%s count=%s" % (ok, esml.get_lod_count(mesh)))
    for i in range(max(1, int(esml.get_lod_count(mesh)))):
        w("  LOD%d verts=%s" % (i, esml.get_num_verts(mesh, i)))


def main():
    w("SOLDIER_MATERIAL_LOD_BEGIN")
    eal = unreal.EditorAssetLibrary
    tex = {
        "base": import_texture("T_Soldier_BaseColor.png", "T_Soldier_BaseColor", True,
                               unreal.TextureCompressionSettings.TC_DEFAULT,
                               unreal.TextureGroup.TEXTUREGROUP_WORLD),
        "normal": import_texture("T_Soldier_Normal.png", "T_Soldier_Normal", False,
                                 unreal.TextureCompressionSettings.TC_NORMALMAP,
                                 unreal.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP),
        "orm": import_texture("T_Soldier_ORM.png", "T_Soldier_ORM", False,
                              unreal.TextureCompressionSettings.TC_MASKS,
                              unreal.TextureGroup.TEXTUREGROUP_WORLD),
    }
    mat = build_material(tex)

    mesh = eal.load_asset(MESH_PATH)
    if not mesh:
        raise RuntimeError("missing soldier mesh")
    slot = unreal.SkeletalMaterial()
    slot.set_editor_property("material_interface", mat)
    slot.set_editor_property("material_slot_name", "Material_1")
    mesh.set_editor_property("materials", [slot])
    eal.save_loaded_asset(mesh)
    w("MESH_MATERIAL_SET=%s" % [str(m) for m in mesh.get_editor_property("materials")])

    try:
        setup_lods(mesh)
        eal.save_loaded_asset(mesh)
    except Exception as e:
        w("LOD_SETUP_ERROR=%s" % e)
    w("SOLDIER_MATERIAL_LOD_DONE")


try:
    main()
except Exception as e:
    w("SOLDIER_MATERIAL_LOD_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("SOLDIER_MATERIAL_LOD_WRITTEN")
