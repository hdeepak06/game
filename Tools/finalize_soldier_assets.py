import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
DEST = "/Game/Characters/Soldier"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "finalize_report.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def main():
    w("FINALIZE_BEGIN")
    eal = unreal.EditorAssetLibrary
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = list(ar.get_assets_by_path(DEST, recursive=True))

    def find(name):
        for a in assets:
            if str(a.asset_name) == name:
                return eal.load_asset(str(a.package_name))
        return None

    for a in assets:
        w("REGISTRY %s.%s class=%s" % (a.package_name, a.asset_name, a.asset_class_path.asset_name))
        obj = eal.load_asset(str(a.package_name))
        if obj:
            eal.save_loaded_asset(obj)

    mesh = find("SKM_HampiSoldier")
    mat = find("M_HampiSoldier")
    if not mesh:
        raise RuntimeError("soldier mesh missing")
    if not mat:
        raise RuntimeError("soldier material missing")

    mel = unreal.MaterialEditingLibrary
    if True:
        tex_base = eal.load_asset(DEST + "/Textures/T_Soldier_BaseColor")
        tex_normal = eal.load_asset(DEST + "/Textures/T_Soldier_Normal")
        tex_orm = eal.load_asset(DEST + "/Textures/T_Soldier_ORM")
        if not (tex_base and tex_normal and tex_orm):
            raise RuntimeError("soldier textures missing")
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
            return False

        def prop(src, target, outs):
            for o in outs:
                try:
                    if mel.connect_material_property(src, o, target):
                        return True
                except Exception:
                    continue
            return False

        base = node(unreal.MaterialExpressionTextureSampleParameter2D, -800, -300,
                    parameter_name="BaseColorTexture", texture=tex_base)
        normal = node(unreal.MaterialExpressionTextureSampleParameter2D, -800, 0,
                      parameter_name="NormalTexture", texture=tex_normal)
        orm = node(unreal.MaterialExpressionTextureSampleParameter2D, -800, 300,
                   parameter_name="ORMTexture", texture=tex_orm)

        def mask(src, channel, x, y):
            n = node(unreal.MaterialExpressionComponentMask, x, y,
                     r=channel == "r", g=channel == "g", b=channel == "b", a=False)
            connect(src, ["RGB", "RGBA", ""], n, [""])
            return n

        ao = mask(orm, "r", -520, 260)
        rough = mask(orm, "g", -520, 370)
        metal = mask(orm, "b", -520, 480)
        if not prop(base, unreal.MaterialProperty.MP_BASE_COLOR, ["RGB", "RGBA", ""]):
            raise RuntimeError("base connect failed")
        if not prop(normal, unreal.MaterialProperty.MP_NORMAL, ["RGB", "RGBA", ""]):
            raise RuntimeError("normal connect failed")
        prop(ao, unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, ["", "R", "RGB"])
        if not prop(rough, unreal.MaterialProperty.MP_ROUGHNESS, ["", "R", "RGB"]):
            raise RuntimeError("rough connect failed")
        if not prop(metal, unreal.MaterialProperty.MP_METALLIC, ["", "R", "RGB"]):
            raise RuntimeError("metal connect failed")
        spec = node(unreal.MaterialExpressionScalarParameter, -300, 600,
                    parameter_name="Specular", default_value=0.35)
        prop(spec, unreal.MaterialProperty.MP_SPECULAR, ["", "Output"])
        mel.recompile_material(mat)
        eal.save_loaded_asset(mat)
        w("MATERIAL_REBUILT")
    else:
        w("MATERIAL_ALREADY_BUILT")

    slot = unreal.SkeletalMaterial()
    slot.set_editor_property("material_interface", mat)
    slot.set_editor_property("material_slot_name", "Material_1")
    mesh.set_editor_property("materials", [slot])
    eal.save_loaded_asset(mesh)
    w("MESH_MATERIALS=%s" % [str(m) for m in mesh.get_editor_property("materials")])
    w("MESH_BOUNDS=%s" % mesh.get_imported_bounds())
    w("FINALIZE_DONE")


try:
    main()
except Exception as e:
    w("FINALIZE_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("FINALIZE_WRITTEN")
