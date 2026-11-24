import unreal

MAP = "/Game/Maps/LV_HampiBattleground"
OUT = r"C:\UnrealProjects\Battleground\Saved\Task04FullAudit\hism_persistence_probe.txt"
TAG = "Task04_HISMProbe"
lines = []


def w(s=""):
    lines.append(str(s))


def cleanup():
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if TAG in [str(t) for t in actor.tags]:
            unreal.EditorLevelLibrary.destroy_actor(actor)


def instance_count_for(actor):
    best = -1
    for comp in actor.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        best = max(best, comp.get_instance_count())
    return best


def main():
    unreal.EditorLevelLibrary.load_level(MAP)
    cleanup()
    mesh = unreal.EditorAssetLibrary.load_asset("/Game/Environment/Vegetation/SM_GrassTuft")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.Actor, unreal.Vector(-29450, 0, 510), unreal.Rotator(0, 0, 0))
    actor.set_actor_label("Task04_HISMProbe_Actor")
    actor.tags = [unreal.Name(TAG)]
    comp = unreal.HierarchicalInstancedStaticMeshComponent(actor)
    comp.set_static_mesh(mesh)
    actor.set_editor_property("root_component", comp)
    xform = unreal.Transform(
        location=unreal.Vector(0, 0, 0),
        rotation=unreal.Rotator(0, 0, 0),
        scale=unreal.Vector(1, 1, 1))
    comp.add_instance(xform, True)
    w("BEFORE_SAVE root=%s instances=%d comp_count=%d" % (
        actor.root_component.get_name(), comp.get_instance_count(),
        len(actor.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent))))
    unreal.EditorLoadingAndSavingUtils.save_current_level()

    unreal.EditorLevelLibrary.load_level(MAP)
    found = [a for a in unreal.EditorLevelLibrary.get_all_level_actors()
             if TAG in [str(t) for t in a.tags]]
    w("AFTER_RELOAD probe_actors=%d" % len(found))
    for a in found:
        w("AFTER_RELOAD actor=%s root=%s hism_comps=%d instances=%d" % (
            a.get_actor_label(), a.root_component.get_name() if a.root_component else "None",
            len(a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)),
            instance_count_for(a)))
    cleanup()
    unreal.EditorLoadingAndSavingUtils.save_current_level()

    desc_mesh = unreal.EditorAssetLibrary.load_asset("/Game/Environment/Terrain/SM_Road_Kamalapur_Hampi")
    desc = desc_mesh.get_static_mesh_description(0) if desc_mesh else None
    w("DESC=%s vertex_count=%s" % (bool(desc), desc.get_vertex_count() if desc else -1))
    if desc:
        for arg in [0, unreal.VertexID(0)]:
            try:
                p = desc.get_vertex_position(arg)
                w("VERTEX_POS arg=%s result=%s" % (type(arg).__name__, p))
            except Exception as e:
                w("VERTEX_POS_ERR arg=%s err=%s" % (type(arg).__name__, e))


try:
    main()
except Exception as e:
    w("PROBE_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("HISM_PERSISTENCE_PROBE_WRITTEN")
