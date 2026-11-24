import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "CurrentStateAudit", "current_state.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
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
    return "(%.1f,%.1f,%.1f)" % (float(v.x), float(v.y), float(v.z))


def dump_obj(obj, props, prefix="  "):
    for prop in props:
        w("%s%s=%s" % (prefix, prop, safe(lambda p=prop: obj.get_editor_property(p))))


def cdo(bp):
    cls = safe(lambda: bp.generated_class())
    if cls and not isinstance(cls, str):
        return safe(lambda: unreal.get_default_object(cls))
    return None


def main():
    unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("WORLD=%s" % world.get_path_name())
    w("ACTOR_COUNT=%d" % len(actors))
    landscapes = [a for a in actors if isinstance(a, unreal.Landscape)]
    players = [a for a in actors if isinstance(a, unreal.PlayerStart)]
    w("LANDSCAPE_COUNT=%d PLAYERSTART_COUNT=%d" % (len(landscapes), len(players)))
    for a in landscapes:
        w("LANDSCAPE=%s loc=%s material=%s layer_count=%s" % (
            a.get_actor_label(), vec(a.get_actor_location()),
            safe(lambda: a.get_editor_property("landscape_material")),
            safe(lambda: len(a.get_editor_property("layer_infos") or []), "ERR")))
    for a in players:
        w("PLAYERSTART=%s loc=%s rot=%s" % (
            a.get_actor_label(), vec(a.get_actor_location()), a.get_actor_rotation()))

    w("--- MATERIAL API ---")
    mel = unreal.MaterialEditingLibrary
    w("MEL_METHODS=%s" % ",".join(sorted(
        m for m in dir(mel) if any(k in m.lower() for k in
        ["expression", "property", "recompile", "usage", "texture"]))))

    paths = [
        "/Game/Environment/Materials/M_HampiSoil_Mobile",
        "/Game/Materials/M_HampiLandscape",
        "/Game/Environment/Materials/M_HampiGranite_Mobile",
        "/Game/Environment/Materials/M_HampiGravelRoad_Mobile",
        "/Game/Environment/Materials/M_HampiDryGrass_Mobile",
    ]
    for path in paths:
        mat = unreal.EditorAssetLibrary.load_asset(path)
        w("MATERIAL %s loaded=%s" % (path, bool(mat)))
        if not mat:
            continue
        dump_obj(mat, ["blend_mode", "two_sided", "shading_model", "dithered_lod_transition",
                       "used_with_instanced_static_meshes"], "  ")
        for prop in ["MP_BASE_COLOR", "MP_ROUGHNESS", "MP_SPECULAR", "MP_NORMAL"]:
            enum = getattr(unreal.MaterialProperty, prop, None)
            node = safe(lambda e=enum: mel.get_material_property_input_node(mat, e))
            w("  %s=%s" % (prop, node.get_name() if node and not isinstance(node, str) else node))
        exprs = safe(lambda: mel.get_material_expressions(mat), [])
        w("  EXPR_COUNT=%s" % (len(exprs) if isinstance(exprs, list) else exprs))
        if isinstance(exprs, list):
            for e in exprs:
                tex = safe(lambda: e.get_editor_property("texture"))
                param = safe(lambda: e.get_editor_property("parameter_name"))
                w("    EXPR %s param=%s tex=%s" % (
                    e.get_class().get_name(), param,
                    tex.get_path_name() if tex and not isinstance(tex, str) else tex))

    w("--- TEXTURES ---")
    for path in [
        "/Game/Environment/Terrain/T_HampiSoil_Albedo",
        "/Game/Environment/Terrain/T_HampiGranite_Albedo",
        "/Game/Environment/Terrain/T_HampiRoad_Albedo",
        "/Game/Environment/Terrain/T_HampiGrass_Albedo",
    ]:
        tex = unreal.EditorAssetLibrary.load_asset(path)
        if tex:
            dump_obj(tex, ["srgb", "compression_settings", "mip_gen_settings",
                           "lod_group", "never_stream", "address_x", "address_y"], "  " + path + " ")

    w("--- CHARACTER BLUEPRINTS ---")
    for path in [
        "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter",
        "/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode",
    ]:
        bp = unreal.EditorAssetLibrary.load_asset(path)
        w("BLUEPRINT %s loaded=%s" % (path, bool(bp)))
        if not bp:
            continue
        obj = cdo(bp)
        w("  CDO=%s class=%s" % (obj, obj.get_class().get_name() if obj else "None"))
        if not obj:
            continue
        for prop in ["mesh", "character_movement", "capsule_component", "default_pawn_class"]:
            val = safe(lambda p=prop: obj.get_editor_property(p))
            w("  %s=%s" % (prop, val.get_path_name() if val and hasattr(val, "get_path_name") else val))
        for c in safe(lambda: obj.get_components_by_class(unreal.ActorComponent), []) or []:
            w("  COMPONENT %s class=%s" % (c.get_name(), c.get_class().get_name()))
            if isinstance(c, unreal.SkeletalMeshComponent):
                w("    SKM=%s anim=%s" % (
                    safe(lambda: c.skeletal_mesh),
                    safe(lambda: c.get_editor_property("animation_data"))))
            if isinstance(c, unreal.CapsuleComponent):
                w("    CAPSULE radius=%s half_height=%s" % (
                    safe(lambda: c.get_unscaled_capsule_radius()),
                    safe(lambda: c.get_unscaled_capsule_half_height())))
            if isinstance(c, unreal.CameraComponent):
                w("    CAMERA fov=%s arm=%s" % (
                    safe(lambda: c.field_of_view), safe(lambda: c.get_editor_property("target_arm"))))
        skeletal = safe(lambda: obj.get_component_by_class(unreal.SkeletalMeshComponent))
        if skeletal:
            w("  SKELETAL_TEMPLATE=%s mesh=%s" % (
                skeletal.get_name(), safe(lambda: skeletal.skeletal_mesh)))
            anim = safe(lambda: skeletal.get_editor_property("animation_data"))
            w("  ANIM_DATA=%s" % anim)
            materials = safe(lambda: skeletal.get_editor_property("override_materials"), []) or []
            w("  OVERRIDE_MATERIALS=%d %s" % (
                len(materials), [str(m) for m in materials]))

    w("--- SKELETAL MESHES ---")
    for path in [
        "/Game/Characters/Mannequins/Meshes/SKM_Manny",
        "/Game/Characters/Mannequins/Meshes/SKM_Quinn",
        "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple",
        "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple",
    ]:
        mesh = unreal.EditorAssetLibrary.load_asset(path)
        if not mesh:
            w("SKM_MISSING %s" % path)
            continue
        w("SKM %s lod_count=%s materials=%s skeleton=%s" % (
            path, safe(lambda: mesh.get_num_lods()),
            safe(lambda: [str(m) for m in mesh.get_editor_property("materials")]),
            safe(lambda: mesh.get_editor_property("skeleton"))))
        for i in range(int(safe(lambda: mesh.get_num_lods(), 1) or 1)):
            w("  LOD%d verts=%s tris=%s" % (
                i, safe(lambda i=i: mesh.get_num_vertices(i)),
                safe(lambda i=i: mesh.get_num_triangles(i))))
        w("  SOCKETS=%s" % safe(lambda: [str(s.get_name()) for s in mesh.get_editor_property("sockets")]))

    w("--- STATIC MESH LOD AUDIT ---")
    eal = unreal.EditorAssetLibrary
    esml = unreal.EditorStaticMeshLibrary
    w("ESML_LOD_METHODS=%s" % ",".join(sorted(
        m for m in dir(esml) if "lod" in m.lower())))
    count = 0
    for root, dirs, files in os.walk(os.path.join(PROJECT, "Content", "Environment")):
        for fname in files:
            if not fname.endswith(".uasset") or not fname.startswith("SM_"):
                continue
            rel = os.path.relpath(os.path.join(root, fname), os.path.join(PROJECT, "Content"))
            path = "/Game/" + rel.replace("\\", "/")[:-len(".uasset")]
            mesh = eal.load_asset(path)
            if not mesh:
                continue
            count += 1
            lods = safe(lambda: esml.get_lod_count(mesh), "ERR")
            tris = safe(lambda: esml.get_number_triangles(mesh, 0), "ERR")
            nanite = safe(lambda: mesh.get_editor_property("nanite_settings").enabled, "ERR")
            w("SM %s lods=%s tris=%s nanite=%s" % (path, lods, tris, nanite))
    w("STATIC_MESH_COUNT=%d" % count)
    w("--- DONE ---")


try:
    main()
except Exception as e:
    w("AUDIT_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("CURRENT_STATE_AUDIT_WRITTEN")
