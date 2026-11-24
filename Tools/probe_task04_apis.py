import unreal
import os

OUT = r"C:\UnrealProjects\Battleground\Saved\Task04FullAudit\api_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def doc(obj):
    return getattr(obj, "__doc__", None)


w("TASK04_API_PROBE_BEGIN")
esml = unreal.EditorStaticMeshLibrary
for name in ["add_simple_collisions", "add_simple_collisions_with_notification",
             "set_convex_decomposition_collisions", "remove_collisions",
             "get_simple_collision_count", "get_convex_collision_count",
             "get_lod_count", "set_lods", "set_lod_from_static_mesh",
             "get_lod_reduction_settings", "get_lod_screen_sizes"]:
    f = getattr(esml, name, None)
    w("ESML.%s=%s" % (name, doc(f) if f else "MISSING"))

w("SCRIPTING_COLLISION_SHAPE_TYPES=%s" % [x for x in dir(unreal) if "CollisionShape" in x])
for cname in ["ScriptingCollisionShapeType", "CollisionTraceFlag"]:
    cls = getattr(unreal, cname, None)
    w("ENUM %s=%s" % (cname, [x for x in dir(cls) if not x.startswith("_")] if cls else "MISSING"))

w("TRANSFORM_DOC=%s" % doc(unreal.Transform))
w("TRANSFORM_INIT_DOC=%s" % doc(unreal.Transform.__init__))

for cname in ["Actor", "HierarchicalInstancedStaticMeshComponent", "InstancedStaticMeshComponent", "StaticMeshComponent"]:
    cls = getattr(unreal, cname, None)
    w("CLASS %s=%s" % (cname, bool(cls)))
    if cls:
        names = [m for m in dir(cls) if any(tok in m.lower() for tok in
                 ["component", "static_mesh", "instance", "collision", "cull", "transform"])]
        w("  METHODS=%s" % ",".join(names[:160]))
        for m in ["add_instance", "add_instances", "add_instance_world_space",
                  "set_static_mesh", "add_component_by_class", "add_instance_component",
                  "set_collision_enabled", "set_cull_distances", "set_cull_distance"]:
            f = getattr(cls, m, None)
            if f:
                w("  DOC %s=%s" % (m, doc(f)))

mel = unreal.MaterialEditingLibrary
for m in ["create_material_expression", "connect_material_expressions", "connect_material_property",
          "get_material_property_input_node", "get_all_material_expressions",
          "get_num_material_expressions", "recompile_material", "update_material_instance",
          "set_material_instance_texture_parameter_value", "set_material_instance_scalar_parameter_value",
          "get_texture_parameter_names", "get_scalar_parameter_names", "delete_all_material_expressions"]:
    f = getattr(mel, m, None)
    w("MEL.%s=%s" % (m, doc(f) if f else "MISSING"))

for cname in ["AssetImportTask", "TextureFactory", "Texture2D", "MaterialExpressionTextureSampleParameter2D"]:
    cls = getattr(unreal, cname, None)
    w("CLASS %s=%s" % (cname, bool(cls)))

# Probe minimal HISM creation on a temporary actor in a scratch level; do not save.
try:
    unreal.EditorLevelLibrary.new_level("/Temp/Task04ApiProbe")
    world = unreal.EditorLevelLibrary.get_editor_world()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    w("TEMP_ACTOR=%s" % actor)
    if actor:
        comp = None
        for meth in ["add_instance_component", "add_component_by_class"]:
            f = getattr(actor, meth, None)
            w("ACTOR_METHOD %s=%s" % (meth, doc(f) if f else "MISSING"))
            if f and comp is None:
                try:
                    comp = f(unreal.HierarchicalInstancedStaticMeshComponent)
                    w("  HISM_CREATE via %s=%s" % (meth, comp))
                except Exception as e:
                    w("  HISM_CREATE_ERR via %s=%s" % (meth, e))
        if not comp:
            try:
                comp = unreal.HierarchicalInstancedStaticMeshComponent(actor)
                w("HISM_CREATE direct=%s" % comp)
            except Exception as e:
                w("HISM_CREATE_DIRECT_ERR=%s" % e)
        if comp:
            mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
            w("HISM_SET_MESH=%s" % doc(getattr(comp, "set_static_mesh", None)))
            try:
                comp.set_static_mesh(mesh)
                w("HISM_MESH_SET=%s" % comp.static_mesh.get_path_name())
            except Exception as e:
                w("HISM_MESH_SET_ERR=%s" % e)
            try:
                t = unreal.Transform(location=unreal.Vector(0, 0, 0), rotation=unreal.Rotator(0, 0, 0), scale=unreal.Vector(1, 1, 1))
                w("TRANSFORM_CREATED=%s" % t)
                idx = comp.add_instance(t)
                w("HISM_ADD_INSTANCE=%s count=%s" % (idx, comp.get_instance_count()))
            except Exception as e:
                w("HISM_ADD_INSTANCE_ERR=%s" % e)
except Exception as e:
    w("TEMP_LEVEL_PROBE_ERR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("TASK04_API_PROBE_WRITTEN")
