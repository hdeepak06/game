import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\Task04FullAudit\add_component_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def safe(fn, default="ERR"):
    try:
        return fn()
    except Exception as e:
        return "%s:%s" % (default, e)


for cls_name in ["EditorActorSubsystem", "SubobjectDataSubsystem",
                 "SubobjectDataBlueprintFunctionLibrary", "EditorLevelLibrary"]:
    cls = getattr(unreal, cls_name, None)
    w("CLASS %s=%s" % (cls_name, bool(cls)))
    if cls:
        methods = [m for m in dir(cls) if any(t in m.lower() for t in [
            "component", "subobject", "add", "instance"])]
        w("  METHODS=%s" % methods)

actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
w("ACTOR=%s" % actor)
for prop in ["instance_components", "blueprint_created_components",
             "root_component", "actor_guid"]:
    w("ACTOR_PROP %s=%s" % (prop, safe(lambda: actor.get_editor_property(prop))))

mesh = unreal.EditorAssetLibrary.load_asset("/Game/Environment/Vegetation/SM_GrassTuft")
comp = unreal.HierarchicalInstancedStaticMeshComponent(actor)
w("COMP=%s" % comp)
for prop in ["creation_method", "is_root_component", "component_guid", "relative_location"]:
    w("COMP_PROP %s=%s" % (prop, safe(lambda: comp.get_editor_property(prop))))
w("SET_ROOT=%s" % safe(lambda: actor.set_editor_property("root_component", comp)))
w("ROOT_AFTER=%s" % actor.root_component)
w("SET_CREATION=%s" % safe(lambda: comp.set_editor_property("creation_method", 3)))
w("COMP_OWNER=%s" % comp.get_owner())
w("REGISTER=%s" % safe(lambda: comp.register_component()))
inst_comp = safe(lambda: actor.get_editor_property("instance_components"))
w("INSTANCE_COMPONENTS_AFTER=%s" % inst_comp)

unreal.EditorLevelLibrary.destroy_actor(actor)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ADD_COMPONENT_PROBE_WRITTEN")
