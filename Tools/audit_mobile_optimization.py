import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "CurrentStateAudit", "mobile_optimization_audit.txt")
lines = []


def w(s=""):
    lines.append(str(s))


ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/Game", recursive=True)

w("--- TEXTURES ---")
for a in assets:
    if str(a.asset_class_path.asset_name) != "Texture2D":
        continue
    tex = unreal.EditorAssetLibrary.load_asset(str(a.package_name))
    if not tex:
        continue
    try:
        sx = tex.blueprint_get_size_x()
        sy = tex.blueprint_get_size_y()
    except Exception:
        sx = sy = "?"
    w("%s size=%sx%s srgb=%s comp=%s group=%s mips=%s" % (
        a.package_name, sx, sy, tex.get_editor_property("srgb"),
        tex.get_editor_property("compression_settings"),
        tex.get_editor_property("lod_group"),
        tex.get_editor_property("mip_gen_settings")))

w("--- STATIC MESH LODS ---")
sm_count = 0
for a in assets:
    if str(a.asset_class_path.asset_name) != "StaticMesh":
        continue
    sm = unreal.EditorAssetLibrary.load_asset(str(a.package_name))
    if not sm:
        continue
    sm_count += 1
    try:
        lods = len(sm.get_editor_property("source_models") or [])
    except Exception:
        lods = "?"
    try:
        num_lods = unreal.EditorStaticMeshLibrary.get_lod_count(sm)
    except Exception:
        num_lods = "?"
    try:
        tris = unreal.EditorStaticMeshLibrary.get_number_verts(sm, 0)
    except Exception:
        tris = "?"
    w("%s source_models=%s lod_count=%s verts_lod0=%s" % (
        a.package_name, lods, num_lods, tris))
w("STATIC_MESH_COUNT=%d" % sm_count)

w("--- SKELETAL MESH LODS ---")
for a in assets:
    if str(a.asset_class_path.asset_name) != "SkeletalMesh":
        continue
    sk = unreal.EditorAssetLibrary.load_asset(str(a.package_name))
    if not sk:
        continue
    try:
        lod_count = unreal.EditorSkeletalMeshLibrary.get_lod_count(sk)
    except Exception:
        lod_count = "?"
    w("%s lod_count=%s" % (a.package_name, lod_count))

w("--- MAP COMPONENT COVERAGE ---")
world = unreal.EditorLevelLibrary.get_editor_world()
w("WORLD=%s" % world.get_path_name() if world else "WORLD=None")
if world:
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTORS=%d" % len(actors))
    comp_counts = {"static": 0, "skeletal": 0, "with_cull": 0}
    for actor in actors:
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            comp_counts["static"] += 1
            try:
                dist = comp.get_editor_property("cached_max_draw_distance")
                if dist and dist > 0:
                    comp_counts["with_cull"] += 1
            except Exception:
                pass
        for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            comp_counts["skeletal"] += 1
    w("COMPONENTS=%s" % comp_counts)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("MOBILE_OPTIMIZATION_AUDIT_WRITTEN")
