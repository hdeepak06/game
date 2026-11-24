import os
import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\hism_cull.txt"
lines = []
unreal.load_module("Battleground")
unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
total_instances = 0
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    for comp in actor.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
        try:
            count = comp.get_instance_count()
        except Exception:
            count = "?"
        if isinstance(count, int):
            total_instances += count
        start = comp.get_editor_property("instance_start_cull_distance")
        end = comp.get_editor_property("instance_end_cull_distance")
        lines.append("%s start=%s end=%s instances=%s" % (actor.get_name(), start, end, count))
lines.append("GROUPS=%d TOTAL_INSTANCES=%s" % (len(lines), total_instances))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("HISM_CULL_WRITTEN")
