import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "SoldierImport", "mobile_finishing.txt")
lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def enum_value(enum, names):
    for n in names:
        v = getattr(enum, n, None)
        if v is not None:
            return v
    return None


try:
    eal = unreal.EditorAssetLibrary
    mat = eal.load_asset("/Game/Characters/Soldier/Materials/M_HampiSoldier")
    if mat:
        usage = unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
        w("MATERIAL_BEFORE=%s" % mat.get_path_name())
        try:
            result = unreal.MaterialEditingLibrary.set_material_usage(mat, usage)
            w("SET_MATERIAL_USAGE_RESULT=%s" % result)
            eal.save_loaded_asset(mat)
            w("MATERIAL_SAVED")
        except Exception as e:
            w("SET_MATERIAL_USAGE_ERR=%s" % e)

    tex_specs = [
        ("/Game/Characters/Soldier/Textures/T_Soldier_BaseColor",
         ["TEXTUREGROUP_CHARACTER", "TEXTUREGROUP_WORLD"]),
        ("/Game/Characters/Soldier/Textures/T_Soldier_Normal",
         ["TEXTUREGROUP_CHARACTER_NORMAL", "TEXTUREGROUP_WORLD_NORMAL_MAP"]),
        ("/Game/Characters/Soldier/Textures/T_Soldier_ORM",
         ["TEXTUREGROUP_CHARACTER", "TEXTUREGROUP_WORLD"]),
    ]
    for path, candidates in tex_specs:
        tex = eal.load_asset(path)
        if not tex:
            w("TEXTURE_MISSING=%s" % path)
            continue
        before = tex.get_editor_property("lod_group")
        group = enum_value(unreal.TextureGroup, candidates)
        if group is not None:
            try:
                tex.set_editor_property("lod_group", group)
                eal.save_loaded_asset(tex)
                w("TEXTURE_GROUP %s before=%s after=%s" % (path, before, tex.get_editor_property("lod_group")))
            except Exception as e:
                w("TEXTURE_GROUP_ERR %s=%s" % (path, e))
        else:
            w("TEXTURE_GROUP_SKIP %s no enum" % path)

    w("MOBILE_FINISHING_DONE")
except Exception as e:
    w("MOBILE_FINISHING_ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("MOBILE_FINISHING_WRITTEN")
