import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\Task04FullAudit\persistent_components_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


actor_methods = [m for m in dir(unreal.Actor) if any(t in m.lower() for t in [
    "component", "root", "attach"])]
w("ACTOR_COMPONENT_METHODS=%s" % actor_methods)

comp_methods = [m for m in dir(unreal.ActorComponent) if any(t in m.lower() for t in [
    "register", "attach", "creation", "outer", "owner"])]
w("COMPONENT_METHODS=%s" % comp_methods)

desc_methods = [m for m in dir(unreal.StaticMeshDescription) if "vert" in m.lower() or "tri" in m.lower()]
w("DESC_METHODS=%s" % desc_methods)

w("CREATION_METHOD_ENUM=%s" % getattr(unreal, "ComponentCreationMethod", None))
try:
    w("CREATION_METHOD_VALUES=%s" % [x for x in dir(unreal.ComponentCreationMethod) if not x.startswith("_")])
except Exception as e:
    w("CREATION_METHOD_VALUES_ERR=%s" % e)

w("MAPCHECK_API=%s" % [m for m in dir(unreal.EditorLevelLibrary) if "map" in m.lower() or "valid" in m.lower()])

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("PERSISTENT_COMPONENTS_PROBE_WRITTEN")
