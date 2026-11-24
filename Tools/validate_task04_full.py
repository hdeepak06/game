import os
import sys
import unreal

sys.path.insert(0, os.path.dirname(__file__))
import task04_layout as layout

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "Task04FullAudit", "full_validation.txt")
MAP = "/Game/Maps/LV_HampiBattleground"
lines = []


def w(s=""):
    lines.append(str(s))


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


def tags_of(actor):
    return [str(t) for t in actor.tags]


def main():
    unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("WORLD=%s" % world.get_path_name())
    w("ACTOR_COUNT=%d" % len(actors))

    tag_counts = {}
    for a in actors:
        for t in tags_of(a):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    for t in sorted(tag_counts):
        w("TAG %s=%d" % (t, tag_counts[t]))

    landscapes = [a for a in actors if isinstance(a, unreal.Landscape)]
    w("LANDSCAPE_COUNT=%d" % len(landscapes))
    for ls in landscapes:
        origin, extent = ls.get_actor_bounds(False)
        w("LANDSCAPE_BOUNDS origin=%s extent=%s" % (origin, extent))
        comps = ls.get_components_by_class(unreal.LandscapeComponent)
        w("LANDSCAPE_COMPONENTS=%d" % len(comps))
        mat = None
        if comps:
            try:
                mat = comps[0].get_material(0)
            except Exception:
                for prop in ["material", "landscape_material", "override_materials"]:
                    try:
                        value = comps[0].get_editor_property(prop)
                        if isinstance(value, list):
                            value = value[0] if value else None
                        if value:
                            mat = value
                            break
                    except Exception:
                        continue
        w("LANDSCAPE_MATERIAL=%s" % (mat.get_path_name() if mat else "None"))

    player = [a for a in actors if isinstance(a, unreal.PlayerStart)]
    w("PLAYER_START_COUNT=%d" % len(player))
    for p in player:
        loc = p.get_actor_location()
        w("PLAYER_START_LOC=%s" % loc)

    w("--- STAGE1 PRESERVATION ---")
    stage1 = [a for a in actors if "Task04_Stage1" in tags_of(a)]
    w("STAGE1_ACTORS=%d" % len(stage1))
    for a in stage1:
        w("  %s loc=%s" % (a.get_actor_label(), a.get_actor_location()))

    w("--- STRUCTURES ---")
    structures = [a for a in actors if "Task04_Structures" in tags_of(a)]
    w("STRUCTURE_ACTORS=%d" % len(structures))
    offsets = []
    for a in structures:
        loc = a.get_actor_location()
        dz = loc.z - ground_z(world, loc.x, loc.y)
        offsets.append(dz)
        if abs(dz - 5.0) > 12.0:
            w("  FLOAT_WARN %s dz=%.2f" % (a.get_actor_label(), dz))
    if offsets:
        w("STRUCTURE_GROUND_OFFSET min=%.2f max=%.2f avg=%.2f" % (
            min(offsets), max(offsets), sum(offsets) / len(offsets)))
    if structures:
        comp = structures[0].get_component_by_class(unreal.StaticMeshComponent)
        if comp:
            try:
                w("STRUCTURE_COLLISION_PROFILE=%s" % comp.get_collision_profile_name())
            except Exception:
                w("STRUCTURE_COLLISION_PROFILE=unavailable")
            try:
                w("STRUCTURE_COLLISION_ENABLED=%s" % comp.get_collision_enabled())
            except Exception:
                w("STRUCTURE_COLLISION_ENABLED=unavailable")

    w("--- ROCK MATERIAL / COLLISION CHECK ---")
    for idx in range(1, 6):
        path = "/Game/Environment/Rocks/SM_HampiBoulder_%02d" % idx
        mesh = unreal.EditorAssetLibrary.load_asset(path)
        if not mesh:
            w("ROCK_MESH_MISSING=%s" % path)
            continue
        for sm in mesh.get_editor_property("static_materials"):
            mat = None
            try:
                mat = sm.get_editor_property("material_interface")
            except Exception:
                pass
            blend = "unavailable"
            two_sided = "unavailable"
            if mat:
                try:
                    blend = str(mat.get_editor_property("blend_mode"))
                except Exception:
                    pass
                try:
                    two_sided = mat.get_editor_property("two_sided")
                except Exception:
                    pass
            w("ROCK_MATERIAL mesh=%s material=%s blend=%s two_sided=%s" % (
                mesh.get_name(), mat.get_name() if mat else "None", blend, two_sided))
    rock_actors = [a for a in stage1 if "Boulder" in a.get_actor_label()]
    for a in rock_actors:
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        profile = "unavailable"
        enabled = "unavailable"
        if comp:
            try:
                profile = comp.get_collision_profile_name()
            except Exception:
                pass
            try:
                enabled = comp.get_collision_enabled()
            except Exception:
                pass
        w("ROCK_ACTOR %s collision=%s profile=%s" % (a.get_actor_label(), enabled, profile))

    w("--- HISM VEGETATION ---")
    total_instances = 0
    hism_actors = 0
    for a in actors:
        comps = a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)
        if comps:
            hism_actors += 1
            for c in comps:
                count = c.get_instance_count()
                total_instances += count
                mesh = c.static_mesh
                try:
                    cull = str(c.get_cull_distances())
                except Exception:
                    cull = "unavailable"
                w("HISM %s instances=%d mesh=%s cull=%s" % (
                    a.get_actor_label(), count,
                    mesh.get_name() if mesh else "None",
                    cull))
    w("HISM_ACTORS=%d TOTAL_INSTANCES=%d" % (hism_actors, total_instances))

    w("--- ROADS / RIVER ---")
    roads = [a for a in actors if "Task04_Roads" in tags_of(a)]
    river = [a for a in actors if "Task04_River" in tags_of(a)]
    w("ROAD_ACTORS=%d RIVER_ACTORS=%d" % (len(roads), len(river)))
    road_mesh_errors = 0
    for a in roads + [r for r in river if isinstance(r, unreal.StaticMeshActor)]:
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh = c.static_mesh if c else None
        if not mesh:
            w("MESH_MISSING_ACTOR=%s" % a.get_actor_label())
            road_mesh_errors += 1
            continue
    w("ROAD_RIVER_MESH_MISSING=%d" % road_mesh_errors)

    # Road conformance: compare road mesh vertices with terrain where possible.
    for a in roads[:3]:
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh = c.static_mesh if c else None
        desc = mesh.get_static_mesh_description(0) if mesh else None
        if not desc:
            continue
        diffs = []
        for vertex_index in range(desc.get_vertex_count()):
            p = desc.get_vertex_position(unreal.VertexID(vertex_index))
            g = ground_z(world, p.x, p.y)
            if g > -90000:
                diffs.append(p.z - g)
        if diffs:
            w("ROAD_CONFORM %s min=%.1f max=%.1f avg=%.1f samples=%d" % (
                a.get_actor_label(), min(diffs), max(diffs), sum(diffs) / len(diffs), len(diffs)))

    w("--- ASSET / MATERIAL CHECK ---")
    asset_paths = []
    for folder in ["Houses", "Rocks", "Vegetation", "Props", "Temples", "Terrain"]:
        asset_paths.extend(unreal.EditorAssetLibrary.list_assets("/Game/Environment/" + folder, recursive=False, include_folder=False))
    asset_paths = sorted(set(asset_paths))
    w("ENVIRONMENT_ASSETS=%d" % len(asset_paths))
    missing_material_assets = []
    bad_mesh_assets = []
    for path in asset_paths:
        obj = unreal.EditorAssetLibrary.load_asset(path)
        if not obj:
            missing_material_assets.append(path)
            continue
        if isinstance(obj, unreal.StaticMesh):
            mats = obj.get_editor_property("static_materials")
            if not mats:
                bad_mesh_assets.append(path)
            for sm in mats:
                mat_obj = None
                try:
                    mat_obj = sm.get_editor_property("material_interface")
                except Exception:
                    try:
                        mat_obj = sm.material_interface
                    except Exception:
                        mat_obj = None
                mat_path = mat_obj.get_path_name() if mat_obj else "None"
                if "DefaultMaterial" in mat_path or not mat_obj:
                    bad_mesh_assets.append(path + " -> " + mat_path)
            desc = obj.get_static_mesh_description(0)
            if desc and desc.get_triangle_count() <= 0:
                bad_mesh_assets.append(path + " EMPTY")
            bs = obj.get_editor_property("body_setup")
            if bs:
                agg = bs.get_editor_property("agg_geom")
                boxes = agg.get_editor_property("box_elems") if agg else []
                convex = agg.get_editor_property("convex_elems") if agg else []
                try:
                    box_count = len(boxes) if boxes is not None else 0
                except Exception:
                    box_count = -1
                try:
                    convex_count = len(convex) if convex is not None else 0
                except Exception:
                    convex_count = -1
                w("MESH %s tris=%s collision_boxes=%d collision_convex=%d nanite=%s" % (
                    path.split("/")[-1], desc.get_triangle_count() if desc else "?",
                    box_count, convex_count,
                    obj.get_editor_property("nanite_settings").enabled))
    w("MISSING_ASSETS=%d %s" % (len(missing_material_assets), missing_material_assets))
    w("BAD_MESH_MATERIALS=%d %s" % (len(bad_mesh_assets), bad_mesh_assets[:20]))

    w("--- LIGHTING ---")
    for cls in [unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere,
                unreal.ExponentialHeightFog, unreal.PostProcessVolume]:
        w("%s=%d" % (getattr(cls, "__name__", str(cls)), len([a for a in actors if isinstance(a, cls)])))

    w("VALIDATION_DONE")


try:
    main()
except Exception as e:
    w("VALIDATION_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK04_FULL_VALIDATION_WRITTEN")
