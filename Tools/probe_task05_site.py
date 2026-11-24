import os
import unreal

MAP = "/Game/Maps/LV_HampiBattleground"
OUT = r"C:\UnrealProjects\Battleground\Saved\Task05Audit\site_probe.txt"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []


def w(s=""):
    lines.append(str(s))


def ground_z(world, x, y, fallback=100.0):
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


def main():
    unreal.EditorLevelLibrary.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    w("=== HEIGHT GRID ===")
    for cy in [10400, 11200, 12000, 12800, 13600]:
        row = []
        for cx in [-45000, -44400, -43800, -43200, -42600]:
            row.append("%d" % round(ground_z(world, cx, cy)))
        w("y=%d  %s" % (cy, " ".join(row)))
    w("=== NEARBY ACTORS ===")
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        loc = actor.get_actor_location()
        if abs(loc.x + 43800) < 4500 and abs(loc.y - 12000) < 4500:
            tags = ",".join(str(t) for t in actor.tags)
            w("%s | %s | (%.0f,%.0f,%.0f) | %s" % (
                actor.get_actor_label(), actor.get_class().get_name(),
                loc.x, loc.y, loc.z, tags))
    w("SITE_PROBE_DONE")


try:
    main()
except Exception as e:
    w("SITE_PROBE_ERROR=%s" % e)
finally:
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("TASK05_SITE_PROBE_WRITTEN")
