import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\hism_props.txt"
lines = []
unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
actor = next(a for a in unreal.EditorLevelLibrary.get_all_level_actors()
             if any(isinstance(c, unreal.HierarchicalInstancedStaticMeshComponent)
                    for c in a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)))
comp = [c for c in actor.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)][0]
for n in sorted(x for x in dir(comp) if "cull" in x.lower() or "distance" in x.lower()):
    try:
        lines.append("%s=%s" % (n, comp.get_editor_property(n)))
    except Exception as e:
        lines.append("%s ERR=%s" % (n, str(e)[:80]))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("HISM_PROPS_WRITTEN")
