import math
import os
import struct
import zlib

import unreal

# ---------------------------------------------------------------------------
# Hampi Battleground - landscape soil upgrade.
# Original, locally generated tileable textures and a compact mobile material:
# matte reddish-brown laterite soil, weathered granite on slopes, scattered
# gravel and sparse dry grass. No downloaded or copyrighted imagery is used.
# The existing M_HampiSoil_Mobile asset is edited in place after a file backup.
# ---------------------------------------------------------------------------

PROJECT = r"C:\UnrealProjects\Battleground"
INTERMEDIATE = os.path.join(PROJECT, "Saved", "SoilUpgradeIntermediate")
OUT_DIR = os.path.join(PROJECT, "Saved", "SoilUpgradeAudit")
OUT = os.path.join(OUT_DIR, "soil_upgrade.txt")
os.makedirs(INTERMEDIATE, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

MAT_PATH = "/Game/Environment/Materials/M_HampiSoil_Mobile"
TEX_DIR = "/Game/Environment/Terrain"
MAP_PATH = "/Game/Maps/LV_HampiBattleground"

lines = []


def w(s=""):
    lines.append(str(s))
    unreal.log(str(s))


def clamp(v, a, b):
    return max(a, min(b, v))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_rgb(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def smoothstep(e0, e1, x):
    if e1 == e0:
        return 0.0
    t = clamp((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def hash2(ix, iy, seed):
    n = (int(ix) * 374761393 + int(iy) * 668265263 + int(seed) * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 4294967295.0


def tile_noise(u, v, period, seed):
    x = u * period
    y = v * period
    xi = int(math.floor(x))
    yi = int(math.floor(y))
    xf = x - xi
    yf = y - yi
    x0 = xi % period
    y0 = yi % period
    x1 = (x0 + 1) % period
    y1 = (y0 + 1) % period
    a = hash2(x0, y0, seed)
    b = hash2(x1, y0, seed)
    c = hash2(x0, y1, seed)
    d = hash2(x1, y1, seed)
    sx = xf * xf * (3.0 - 2.0 * xf)
    sy = yf * yf * (3.0 - 2.0 * yf)
    return lerp(lerp(a, b, sx), lerp(c, d, sx), sy)


def fbm(u, v, seed, periods=(4, 8, 16, 32), weights=(0.42, 0.28, 0.18, 0.12)):
    total = 0.0
    wsum = 0.0
    for p, wt in zip(periods, weights):
        total += tile_noise(u, v, p, seed + p) * wt
        wsum += wt
    return total / wsum


def png_chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def write_png(path, size, pixels):
    raw = bytearray()
    for y in range(size):
        raw.append(0)
        start = y * size * 4
        raw.extend(pixels[start:start + size * 4])
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def rgb_bytes(r, g, b, a=255):
    return (int(clamp(r, 0.0, 1.0) * 255.0 + 0.5),
            int(clamp(g, 0.0, 1.0) * 255.0 + 0.5),
            int(clamp(b, 0.0, 1.0) * 255.0 + 0.5),
            int(clamp(a, 0.0, 1.0) * 255.0 + 0.5))


def generate_soil(size=256):
    px = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            u = x / float(size)
            v = y / float(size)
            broad = fbm(u, v, 211, (3, 7, 15), (0.52, 0.31, 0.17))
            patch = fbm(u, v, 227, (5, 11, 23, 41), (0.43, 0.27, 0.19, 0.11))
            grit = fbm(u, v, 241, (32, 64), (0.65, 0.35))
            grain = hash2(x, y, 251)

            # Weathered laterite: iron-rich red-brown base with paler sandy lenses.
            col = lerp_rgb((0.31, 0.145, 0.082), (0.49, 0.265, 0.145), broad)
            iron = smoothstep(0.58, 0.80, patch)
            col = lerp_rgb(col, (0.53, 0.20, 0.095), iron * 0.55)
            sand = smoothstep(0.60, 0.82, 1.0 - patch)
            col = lerp_rgb(col, (0.58, 0.44, 0.29), sand * 0.38)

            # Granite grit and small pale quartz/laterite fragments.
            pebble = smoothstep(0.70, 0.83, grit) * 0.5
            col = lerp_rgb(col, (0.42, 0.38, 0.33), pebble)
            fleck = 1.0 if grain > 0.961 else (0.45 if grain > 0.925 else 0.0)
            if fleck:
                col = lerp_rgb(col, (0.66, 0.61, 0.53) if grain > 0.961 else (0.24, 0.19, 0.15), fleck)

            shade = 0.94 + 0.12 * broad
            px[(y * size + x) * 4:(y * size + x) * 4 + 4] = rgb_bytes(
                col[0] * shade, col[1] * shade, col[2] * shade)
    path = os.path.join(INTERMEDIATE, "T_HampiSoilLaterite_Albedo.png")
    write_png(path, size, px)
    return path


def generate_gravel(size=256):
    px = bytearray(size * size * 4)
    cells = 28
    for y in range(size):
        for x in range(size):
            u = x / float(size)
            v = y / float(size)
            n = fbm(u, v, 313, (4, 10, 22), (0.50, 0.32, 0.18))
            soil = lerp_rgb((0.33, 0.17, 0.10), (0.47, 0.27, 0.16), n)

            # Tileable scattered rounded gravel using a 3x3 cell neighbourhood.
            cx = u * cells
            cy = v * cells
            ix = int(math.floor(cx))
            iy = int(math.floor(cy))
            best = None
            for oy in (-1, 0, 1):
                for ox in (-1, 0, 1):
                    gx = ix + ox
                    gy = iy + oy
                    h = hash2(gx, gy, 331)
                    if h < 0.42:
                        continue
                    jx = hash2(gx, gy, 337)
                    jy = hash2(gx, gy, 347)
                    wx = (gx + 0.15 + 0.7 * jx) - cx
                    wy = (gy + 0.15 + 0.7 * jy) - cy
                    r = 0.22 + 0.24 * hash2(gx, gy, 353)
                    d = math.sqrt(wx * wx + wy * wy * 1.28)
                    if d < r and (best is None or d < best[0]):
                        best = (d, r, h, wx, wy)
            if best:
                d, r, h, wx, wy = best
                edge = 1.0 - smoothstep(r * 0.62, r, d)
                light = clamp(0.5 - (wx + wy) * 1.1, 0.0, 1.0)
                stone = lerp_rgb((0.30, 0.27, 0.24), (0.62, 0.58, 0.52), h * 0.6 + light * 0.4)
                soil = lerp_rgb(soil, stone, edge * 0.88)
            px[(y * size + x) * 4:(y * size + x) * 4 + 4] = rgb_bytes(*soil)
    path = os.path.join(INTERMEDIATE, "T_HampiGravel_Albedo.png")
    write_png(path, size, px)
    return path


def generate_dry_grass(size=256):
    px = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            u = x / float(size)
            v = y / float(size)
            patch = fbm(u, v, 401, (4, 9, 19), (0.50, 0.31, 0.19))
            strands = tile_noise(u * 0.35 + v * 0.08, v * 2.4, 48, 419)
            fine = hash2(x, y, 421)
            base = lerp_rgb((0.29, 0.17, 0.10), (0.40, 0.25, 0.14), patch)
            straw = lerp_rgb((0.43, 0.37, 0.18), (0.61, 0.52, 0.27), strands)
            cover = smoothstep(0.52, 0.76, patch) * smoothstep(0.42, 0.70, strands)
            col = lerp_rgb(base, straw, cover * 0.82)
            if fine > 0.972:
                col = lerp_rgb(col, (0.72, 0.64, 0.36), 0.55)
            px[(y * size + x) * 4:(y * size + x) * 4 + 4] = rgb_bytes(*col)
    path = os.path.join(INTERMEDIATE, "T_HampiDryGrassPatch_Albedo.png")
    write_png(path, size, px)
    return path


def generate_mask(size=256):
    px = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            u = x / float(size)
            v = y / float(size)
            gravel = fbm(u, v, 503, (3, 8, 18), (0.48, 0.32, 0.20))
            grass = fbm(u, v, 521, (4, 10, 21), (0.46, 0.31, 0.23))
            rock = fbm(u, v, 541, (3, 7, 16, 31), (0.44, 0.27, 0.18, 0.11))
            grain = hash2(x, y, 557)

            r = smoothstep(0.55, 0.72, gravel)
            g = smoothstep(0.63, 0.80, grass) * 0.72
            b = smoothstep(0.62, 0.81, rock)
            a = clamp(0.35 + 0.65 * grain, 0.0, 1.0)
            px[(y * size + x) * 4:(y * size + x) * 4 + 4] = rgb_bytes(r, g, b, a)
    path = os.path.join(INTERMEDIATE, "T_HampiGroundMask.png")
    write_png(path, size, px)
    return path


def import_texture(png_path, name, linear=False):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", png_path)
    task.set_editor_property("destination_path", TEX_DIR)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    tools.import_asset_tasks([task])
    tex = unreal.EditorAssetLibrary.load_asset(TEX_DIR + "/" + name)
    if not tex:
        w("TEXTURE_IMPORT_FAILED %s" % name)
        return None
    try:
        tex.set_editor_property("srgb", not linear)
    except Exception as e:
        w("TEXTURE_SRGB_WARN %s %s" % (name, e))
    try:
        tex.set_editor_property("compression_settings",
                                unreal.TextureCompressionSettings.TC_MASKS if linear
                                else unreal.TextureCompressionSettings.TC_DEFAULT)
    except Exception as e:
        w("TEXTURE_COMPRESSION_WARN %s %s" % (name, e))
    try:
        tex.set_editor_property("mip_gen_settings",
                                unreal.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE if linear
                                else unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    except Exception as e:
        w("TEXTURE_MIP_WARN %s %s" % (name, e))
    try:
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
    except Exception:
        pass
    for prop in ("address_x", "address_y"):
        try:
            tex.set_editor_property(prop, unreal.TextureAddress.TA_WRAP)
        except Exception:
            pass
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    w("TEXTURE_READY %s srgb=%s compression=%s" % (
        name, tex.get_editor_property("srgb"), tex.get_editor_property("compression_settings")))
    return tex


mel = unreal.MaterialEditingLibrary
node_count = [0]


def make_node(mat, cls, x, y, **props):
    node = mel.create_material_expression(mat, cls, x, y)
    if not node:
        raise RuntimeError("could not create %s" % cls)
    node_count[0] += 1
    for key, value in props.items():
        node.set_editor_property(key, value)
    return node


def connect(src, outs, dst, ins):
    for out in outs:
        for inp in ins:
            try:
                if mel.connect_material_expressions(src, out, dst, inp):
                    return True
            except Exception:
                continue
    w("CONNECT_FAIL %s -> %s outs=%s ins=%s" % (
        src.get_name(), dst.get_name(), outs, ins))
    return False


def scalar(mat, name, value, x, y):
    return make_node(mat, unreal.MaterialExpressionScalarParameter, x, y,
                     parameter_name=name, default_value=float(value))


def vector(mat, name, rgb, x, y):
    return make_node(mat, unreal.MaterialExpressionVectorParameter, x, y,
                     parameter_name=name,
                     default_value=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))


def texture_sample(mat, name, tex, u, v):
    node = make_node(mat, unreal.MaterialExpressionTextureSampleParameter2D, u, v,
                     parameter_name=name)
    if tex:
        node.set_editor_property("texture", tex)
    return node


def mask_node(mat, channels, x, y):
    props = {"r": "r" in channels, "g": "g" in channels,
             "b": "b" in channels, "a": "a" in channels}
    return make_node(mat, unreal.MaterialExpressionComponentMask, x, y, **props)


def saturate(mat, value, x, y):
    if hasattr(unreal, "MaterialExpressionSaturate"):
        node = make_node(mat, unreal.MaterialExpressionSaturate, x, y)
        connect(value, ["", "Output"], node, ["", "Input"])
        return node
    node = make_node(mat, unreal.MaterialExpressionClamp, x, y,
                     min_default=0.0, max_default=1.0)
    connect(value, ["", "Output"], node, ["", "Input", "Value"])
    return node


def multiply(mat, a, a_out, b, b_out, x, y):
    node = make_node(mat, unreal.MaterialExpressionMultiply, x, y)
    connect(a, a_out, node, ["A"])
    connect(b, b_out, node, ["B"])
    return node


def lerp_node(mat, a, a_out, b, b_out, alpha, alpha_out, x, y):
    node = make_node(mat, unreal.MaterialExpressionLinearInterpolate, x, y)
    connect(a, a_out, node, ["A"])
    connect(b, b_out, node, ["B"])
    connect(alpha, alpha_out, node, ["Alpha"])
    return node


def rebuild_material(textures):
    mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
    if not mat:
        raise RuntimeError("missing material " + MAT_PATH)
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("two_sided", False)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)

    # World-space UVs: fine detail at ~6 m per tile, macro masks at ~90 m.
    world = make_node(mat, unreal.MaterialExpressionWorldPosition, -2000, -900)
    detail_uv = mask_node(mat, "rg", -1800, -900)
    connect(world, ["", "XYZ", "RGB"], detail_uv, [""])
    detail_tiling = scalar(mat, "DetailTiling", 0.0017, -1800, -740)
    detail_uv_scaled = multiply(mat, detail_uv, ["", "RGB", "RG"],
                                detail_tiling, ["", "Output"], -1580, -840)

    macro_uv = mask_node(mat, "rg", -1800, -560)
    connect(world, ["", "XYZ", "RGB"], macro_uv, [""])
    macro_tiling = scalar(mat, "MacroTiling", 0.00011, -1800, -400)
    macro_uv_scaled = multiply(mat, macro_uv, ["", "RGB", "RG"],
                               macro_tiling, ["", "Output"], -1580, -500)

    soil = texture_sample(mat, "SoilTexture", textures["soil"], -1300, -1050)
    gravel = texture_sample(mat, "GravelTexture", textures["gravel"], -1300, -780)
    grass = texture_sample(mat, "DryGrassTexture", textures["grass"], -1300, -510)
    granite = texture_sample(mat, "GraniteTexture", textures["granite"], -1300, -240)
    mask = texture_sample(mat, "GroundMask", textures["mask"], -1300, 30)
    for sample, uv in ((soil, detail_uv_scaled), (gravel, detail_uv_scaled),
                       (grass, detail_uv_scaled), (granite, detail_uv_scaled),
                       (mask, macro_uv_scaled)):
        connect(uv, ["", "Output"], sample, ["UVs", "Coordinates"])

    soil_tint = vector(mat, "SoilTint", (1.0, 0.98, 0.95), -1050, -1050)
    gravel_tint = vector(mat, "GravelTint", (1.0, 1.0, 1.0), -1050, -780)
    grass_tint = vector(mat, "DryGrassTint", (0.95, 0.96, 0.88), -1050, -510)
    granite_tint = vector(mat, "GraniteTint", (1.0, 0.99, 0.97), -1050, -240)

    soil_col = multiply(mat, soil, ["RGB", "RGBA", ""],
                        soil_tint, ["RGB", ""], -820, -1000)
    gravel_col = multiply(mat, gravel, ["RGB", "RGBA", ""],
                          gravel_tint, ["RGB", ""], -820, -730)
    grass_col = multiply(mat, grass, ["RGB", "RGBA", ""],
                         grass_tint, ["RGB", ""], -820, -460)
    granite_col = multiply(mat, granite, ["RGB", "RGBA", ""],
                           granite_tint, ["RGB", ""], -820, -190)

    # Gravel patches, then sparse dry grass.
    mask_r = mask_node(mat, "r", -1050, 30)
    mask_g = mask_node(mat, "g", -1050, 140)
    mask_b = mask_node(mat, "b", -1050, 250)
    connect(mask, ["RGB", "RGBA", ""], mask_r, [""])
    connect(mask, ["RGB", "RGBA", ""], mask_g, [""])
    connect(mask, ["RGB", "RGBA", ""], mask_b, [""])

    gravel_strength = scalar(mat, "GravelStrength", 0.72, -820, 30)
    grass_strength = scalar(mat, "DryGrassStrength", 0.34, -820, 140)
    rock_strength = scalar(mat, "MaskRockStrength", 0.62, -820, 250)
    gravel_alpha = multiply(mat, mask_r, ["", "R", "RGB"],
                            gravel_strength, ["", "Output"], -620, 30)
    grass_alpha = multiply(mat, mask_g, ["", "G", "RGB"],
                           grass_strength, ["", "Output"], -620, 140)
    mask_rock_alpha = multiply(mat, mask_b, ["", "B", "RGB"],
                               rock_strength, ["", "Output"], -620, 250)

    base = lerp_node(mat, soil_col, ["", "RGB"],
                     gravel_col, ["", "RGB"], gravel_alpha, ["", "Output"], -390, -830)
    with_grass = lerp_node(mat, base, ["", "RGB"],
                           grass_col, ["", "RGB"], grass_alpha, ["", "Output"], -160, -650)

    # Expose granite on steep slopes as well as in macro-mask rock patches.
    normal = make_node(mat, unreal.MaterialExpressionPixelNormalWS, -1300, 430)
    normal_z = mask_node(mat, "b", -1050, 430)
    connect(normal, ["", "RGB", "XYZ"], normal_z, [""])
    slope_threshold = scalar(mat, "SlopeThreshold", 0.91, -1050, 570)
    slope_diff = make_node(mat, unreal.MaterialExpressionSubtract, -820, 430)
    connect(slope_threshold, ["", "Output"], slope_diff, ["A"])
    connect(normal_z, ["", "B", "RGB"], slope_diff, ["B"])
    slope_sharpness = scalar(mat, "SlopeSharpness", 8.0, -820, 570)
    slope_raw = multiply(mat, slope_diff, ["", "Output"],
                         slope_sharpness, ["", "Output"], -600, 430)
    slope_alpha = saturate(mat, slope_raw, -390, 430)
    rock_alpha_raw = make_node(mat, unreal.MaterialExpressionAdd, -390, 250)
    connect(mask_rock_alpha, ["", "Output"], rock_alpha_raw, ["A"])
    connect(slope_alpha, ["", "Output"], rock_alpha_raw, ["B"])
    rock_alpha = saturate(mat, rock_alpha_raw, -160, 250)

    final_color = lerp_node(mat, with_grass, ["", "RGB"], granite_col, ["", "RGB"],
                            rock_alpha, ["", "Output"], 80, -500)
    for out in ["", "RGB", "RGBA"]:
        try:
            if mel.connect_material_property(final_color, out, unreal.MaterialProperty.MP_BASE_COLOR):
                break
        except Exception:
            continue
    else:
        raise RuntimeError("failed to connect base color")

    rough_soil = scalar(mat, "SoilRoughness", 0.95, 80, -180)
    rough_rock = scalar(mat, "RockRoughness", 0.84, 80, -50)
    rough = lerp_node(mat, rough_soil, ["", "Output"], rough_rock, ["", "Output"],
                      rock_alpha, ["", "Output"], 320, -120)
    for out in ["", "Output"]:
        try:
            if mel.connect_material_property(rough, out, unreal.MaterialProperty.MP_ROUGHNESS):
                break
        except Exception:
            continue
    else:
        raise RuntimeError("failed to connect roughness")

    spec = scalar(mat, "MatteSpecular", 0.08, 320, 80)
    for out in ["", "Output"]:
        try:
            if mel.connect_material_property(spec, out, unreal.MaterialProperty.MP_SPECULAR):
                break
        except Exception:
            continue
    else:
        raise RuntimeError("failed to connect specular")

    try:
        mel.set_material_usage(mat, unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES, True)
    except Exception as e:
        w("USAGE_FLAG_WARN=%s" % e)

    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    w("MATERIAL_REBUILT=%s nodes=%d" % (MAT_PATH, node_count[0]))
    w("MATERIAL_BASE_COLOR=%s" % mel.get_material_property_input_node(
        mat, unreal.MaterialProperty.MP_BASE_COLOR).get_name())
    w("MATERIAL_ROUGHNESS=%s" % mel.get_material_property_input_node(
        mat, unreal.MaterialProperty.MP_ROUGHNESS).get_name())
    used = mel.get_used_textures(mat)
    w("MATERIAL_USED_TEXTURES=%s" % [t.get_path_name() for t in used] if used else [])
    return mat


def main():
    w("SOIL_UPGRADE_BEGIN")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    textures = {
        "soil": import_texture(generate_soil(), "T_HampiSoilLaterite_Albedo"),
        "gravel": import_texture(generate_gravel(), "T_HampiGravel_Albedo"),
        "grass": import_texture(generate_dry_grass(), "T_HampiDryGrassPatch_Albedo"),
        "granite": unreal.EditorAssetLibrary.load_asset(
            TEX_DIR + "/T_HampiGranite_Albedo"),
        "mask": import_texture(generate_mask(), "T_HampiGroundMask", linear=True),
    }
    if not all(textures.values()):
        raise RuntimeError("one or more textures failed to load")
    rebuild_material(textures)

    world = unreal.EditorLevelLibrary.get_editor_world()
    landscapes = [a for a in unreal.EditorLevelLibrary.get_all_level_actors()
                  if isinstance(a, unreal.Landscape)]
    w("LANDSCAPE_COUNT=%d" % len(landscapes))
    if landscapes:
        assigned = landscapes[0].get_editor_property("landscape_material")
        w("LANDSCAPE_MATERIAL=%s" % (assigned.get_path_name() if assigned else "None"))
    try:
        unreal.SystemLibrary.execute_console_command(world, "MAP CHECKDEP NOCLEARLOG")
        w("MAPCHECK_SENT=True")
    except Exception as e:
        w("MAPCHECK_ERR=%s" % e)
    w("SOIL_UPGRADE_DONE")


try:
    main()
except Exception as e:
    w("SOIL_UPGRADE_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("SOIL_UPGRADE_WRITTEN")
