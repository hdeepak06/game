import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "Task04FullAudit")
OUT = os.path.join(OUT_DIR, "audit.txt")
os.makedirs(OUT_DIR, exist_ok=True)

lines = []


def w(s=""):
    lines.append(str(s))


def safe(fn, default=None):
    try:
        return fn()
    except Exception as e:
        return default if default is not None else "ERR:%s" % e


def vec(v):
    if v is None:
        return "None"
    return "X=%.2f Y=%.2f Z=%.2f" % (float(v.x), float(v.y), float(v.z))


def rot(r):
    if r is None:
        return "None"
    return "P=%.2f Y=%.2f R=%.2f" % (float(r.pitch), float(r.yaw), float(r.roll))


def ground_z(world, x, y, fallback=-100000.0):
    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world,
            unreal.Vector(float(x), float(y), 30000.0),
            unreal.Vector(float(x), float(y), -5000.0),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True, [], unreal.DrawDebugTrace.NONE, True)
        if hit:
            return float(hit.to_tuple()[4].z)
    except Exception:
        pass
    return fallback


w("TASK04_FULL_AUDIT_BEGIN")
unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
world = unreal.EditorLevelLibrary.get_editor_world()
w("WORLD=%s" % world.get_path_name() if world else "WORLD=None")

actors = unreal.EditorLevelLibrary.get_all_level_actors()
w("ACTOR_COUNT=%d" % len(actors))
for a in actors:
    try:
        tags = ",".join([str(t) for t in a.tags])
    except Exception:
        tags = "?"
    w("ACTOR label=%s class=%s tags=%s loc=%s rot=%s hidden=%s folder=%s" % (
        a.get_actor_label(), a.get_class().get_name(), tags,
        vec(a.get_actor_location()), rot(a.get_actor_rotation()),
        safe(lambda: a.is_hidden_ed()), safe(lambda: a.get_folder_path())))
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        mesh = safe(lambda: c.static_mesh)
        w("  SMC comp=%s mesh=%s collision=%s visible=%s cast_shadow=%s" % (
            c.get_name(), mesh.get_path_name() if mesh else "None",
            safe(lambda: c.get_editor_property("collision_enabled")),
            safe(lambda: c.is_visible()),
            safe(lambda: c.cast_shadow)))

w("--- LANDSCAPE ---")
landscapes = [a for a in actors if isinstance(a, unreal.Landscape)]
w("LANDSCAPE_COUNT=%d" % len(landscapes))
for ls in landscapes:
    w("LANDSCAPE %s loc=%s scale=%s" % (ls.get_name(), vec(ls.get_actor_location()), vec(ls.get_actor_scale3d())))
    comp = safe(lambda: ls.get_component_by_class(unreal.LandscapeComponent))
    if comp and comp != "ERR:":
        w("  COMPONENT_INFO=%s" % safe(lambda: comp.get_editor_property("component_x")))
    w("  BOUNDS=%s" % str(safe(lambda: ls.get_actor_bounds(False))))
    layers = safe(lambda: ls.get_editor_property("layer_infos"), [])
    if isinstance(layers, list):
        w("  LAYER_COUNT=%d" % len(layers))
        for li in layers:
            w("    LAYER=%s" % (li.get_path_name() if li else "None"))
    for c in ls.get_components_by_class(unreal.LandscapeComponent):
        w("  LCOMP %s absolute=%s" % (c.get_name(), safe(lambda: c.get_editor_property("absolute_section_offset_x"))))
        break

w("--- MATERIALS ---")
for path in [
    "/Game/Environment/Materials/M_HampiSoil_Mobile",
    "/Game/Materials/M_HampiLandscape",
    "/Game/Environment/Materials/M_HampiGranite_Mobile",
    "/Game/Environment/Materials/M_HampiMudPlaster_Mobile",
    "/Game/Environment/Materials/M_HampiClayRoof_Mobile",
    "/Game/Environment/Materials/M_HampiWoodDark_Mobile",
]:
    m = unreal.EditorAssetLibrary.load_asset(path)
    if not m:
        w("MATERIAL_MISSING %s" % path)
        continue
    w("MATERIAL %s class=%s blend=%s two_sided=%s shading=%s" % (
        path, m.get_class().get_name(),
        safe(lambda: m.get_editor_property("blend_mode")),
        safe(lambda: m.get_editor_property("two_sided")),
        safe(lambda: m.get_editor_property("shading_model"))))
    mel = unreal.MaterialEditingLibrary
    for prop in ["base_color", "roughness", "metallic", "specular", "normal", "opacity"]:
        enum_name = "MP_" + prop.upper()
        enum = getattr(unreal.MaterialProperty, enum_name, None)
        if enum is None:
            continue
        node = safe(lambda: mel.get_material_property_input_node(m, enum))
        if node and str(node).startswith("<Object"):
            w("  %s=%s" % (prop.upper(), safe(lambda: node.get_name())))
    exprs = safe(lambda: m.get_editor_property("expressions"), [])
    if isinstance(exprs, list):
        names = []
        for e in exprs:
            names.append(e.get_class().get_name() if e else "None")
        w("  EXPRESSIONS=%d types=%s" % (len(exprs), ",".join(sorted(set(names)))))

w("--- TEXTURES ---")
for path in unreal.EditorAssetLibrary.list_assets("/Game/Environment/Terrain", recursive=False, include_folder=False):
    t = unreal.EditorAssetLibrary.load_asset(path)
    if not t:
        w("TEXTURE_MISSING %s" % path)
        continue
    w("TEXTURE %s size=%s compression=%s srgb=%s" % (
        path,
        safe(lambda: (t.blueprint_get_size_x(), t.blueprint_get_size_y())),
        safe(lambda: t.get_editor_property("compression_settings")),
        safe(lambda: t.get_editor_property("srgb"))))

w("--- STATIC MESHES ---")
paths = []
for folder in ["/Game/Environment/Houses", "/Game/Environment/Rocks"]:
    paths.extend(unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False))
for path in sorted(set(paths)):
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not mesh:
        w("MESH_MISSING %s" % path)
        continue
    desc = safe(lambda: mesh.get_static_mesh_description(0))
    verts = safe(lambda: desc.get_vertex_count()) if desc and not str(desc).startswith("ERR") else "?"
    tris = safe(lambda: desc.get_triangle_count()) if desc and not str(desc).startswith("ERR") else "?"
    static_materials = safe(lambda: mesh.get_editor_property("static_materials"), [])
    mats = [m.get_path_name() if m else "None" for m in static_materials] if isinstance(static_materials, list) else []
    esml = unreal.EditorStaticMeshLibrary
    w("MESH %s verts=%s tris=%s slots=%d materials=%s nanite_enabled=%s collision_complexity=%s simple_collisions=%s convex_collisions=%s lods=%s" % (
        path, verts, tris, len(mats), mats,
        safe(lambda: mesh.get_editor_property("nanite_settings").enabled),
        safe(lambda: esml.get_collision_complexity(mesh)),
        safe(lambda: esml.get_simple_collision_count(mesh)),
        safe(lambda: esml.get_convex_collision_count(mesh)),
        safe(lambda: esml.get_lod_count(mesh))))

w("--- API PROBES FOR PLANNING ---")
for cls_name in ["HierarchicalInstancedStaticMeshComponent", "InstancedStaticMeshComponent", "StaticMeshActor"]:
    cls = getattr(unreal, cls_name, None)
    w("CLASS %s=%s" % (cls_name, bool(cls)))
    if cls:
        names = [m for m in dir(cls) if "instance" in m.lower() or "cull" in m.lower() or "collision" in m.lower()]
        w("  METHODS=%s" % ",".join(names[:80]))
for cls_name in ["EditorStaticMeshLibrary", "StaticMeshEditorSubsystem"]:
    cls = getattr(unreal, cls_name, None)
    w("CLASS %s=%s" % (cls_name, bool(cls)))
    if cls:
        names = [m for m in dir(cls) if "lod" in m.lower() or "collision" in m.lower() or "normal" in m.lower()]
        w("  METHODS=%s" % ",".join(names[:100]))

w("--- VEGETATION SEARCH ---")
veg_tokens = ["tree", "grass", "bush", "shrub", "palm", "coconut", "neem", "banyan", "tamarind", "acacia", "foliage", "plant"]
veg_actors = []
for a in actors:
    low = (a.get_actor_label() + " " + a.get_name()).lower()
    if any(tok in low for tok in veg_tokens):
        veg_actors.append(a.get_actor_label())
w("VEGETATION_ACTORS=%d labels=%s" % (len(veg_actors), ",".join(veg_actors)))
veg_assets = [p for p in unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False)
              if any(tok in p.lower() for tok in veg_tokens)]
w("VEGETATION_ASSETS=%d" % len(veg_assets))
for p in veg_assets[:40]:
    w("  VEG_ASSET=%s" % p)

w("--- LIGHTING / ENVIRONMENT ---")
for cls in [unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere, unreal.ExponentialHeightFog, unreal.PostProcessVolume]:
    found = [a for a in actors if isinstance(a, cls)]
    w("LIGHT_CLASS %s count=%d" % (getattr(cls, "__name__", str(cls)), len(found)))
    for a in found:
        w("  %s loc=%s rot=%s hidden=%s" % (a.get_actor_label(), vec(a.get_actor_location()), rot(a.get_actor_rotation()), safe(lambda: a.is_hidden_ed())))
        if isinstance(a, unreal.DirectionalLight):
            c = a.get_component_by_class(unreal.DirectionalLightComponent)
            w("    SUN intensity=%s mobility=%s atmos_sun=%s color=%s" % (
                safe(lambda: c.get_editor_property("intensity")),
                safe(lambda: c.get_editor_property("mobility")),
                safe(lambda: c.get_editor_property("atmosphere_sun_light")),
                safe(lambda: c.get_editor_property("light_color"))))
        if isinstance(a, unreal.SkyLight):
            c = a.get_component_by_class(unreal.SkyLightComponent)
            w("    SKY realtime=%s intensity=%s" % (
                safe(lambda: c.get_editor_property("real_time_capture")),
                safe(lambda: c.get_editor_property("intensity"))))
        if isinstance(a, unreal.ExponentialHeightFog):
            c = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
            w("    FOG density=%s fog_color=%s" % (
                safe(lambda: c.get_editor_property("fog_density")),
                safe(lambda: c.get_editor_property("fog_inscattering_color"))))
        if isinstance(a, unreal.PostProcessVolume):
            w("    PPV unbound=%s enabled=%s" % (
                safe(lambda: a.get_editor_property("unbound")),
                safe(lambda: a.get_editor_property("enabled"))))

w("--- TERRAIN SAMPLES ---")
sample_points = [
    ("MapCenter_Kamalapur", -29450, 0),
    ("Kamalapur_N", -29450, 4000),
    ("Kamalapur_S", -29450, -5000),
    ("Hampi_Hills_W", -43000, 9000),
    ("Hampi_Hills_NW", -47000, 16000),
    ("Anjanadri_N", -22000, 14000),
    ("Anjanadri_NE", -18000, 19000),
    ("Hosapete_SE", -15000, -12000),
    ("Military_E", -10000, 12000),
    ("River_W", -40000, -19000),
    ("River_C", -30000, -19000),
    ("River_E", -20000, -19000),
    ("River_S_W", -40000, -22500),
    ("River_S_C", -30000, -22500),
    ("River_S_E", -20000, -22500),
]
for name, x, y in sample_points:
    w("SAMPLE %s x=%d y=%d z=%.2f" % (name, x, y, ground_z(world, x, y)))

w("--- CVARS / RENDER FEATURES ---")
for cvar in ["r.Nanite", "r.Lumen", "r.PathTracing", "r.RayTracing", "r.DefaultFeature.AutoExposure", "r.Shadow.Virtual.Enable", "r.MobileContentUsed"]:
    w("CVAR %s=%s" % (cvar, safe(lambda: unreal.SystemLibrary.get_console_variable_int_value(cvar))))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("TASK04_FULL_AUDIT_WRITTEN")
