import os
import unreal

PROJECT = r"C:\UnrealProjects\Battleground"
OUT = os.path.join(PROJECT, "Saved", "CurrentStateAudit", "map_components_final.txt")
lines = []


def w(s=""):
    lines.append(str(s))


try:
    unreal.load_module("Battleground")
    unreal.EditorLevelLibrary.load_level("/Game/Maps/LV_HampiBattleground")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    w("ACTORS=%d" % len(actors))
    w("LANDSCAPES=%d" % len([a for a in actors if isinstance(a, unreal.Landscape)]))
    w("PLAYER_STARTS=%d" % len([a for a in actors if isinstance(a, unreal.PlayerStart)]))

    static = 0
    instanced = 0
    with_cull = 0
    no_mesh = 0
    cull_values = []
    for actor in actors:
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            static += 1
            if isinstance(comp, unreal.InstancedStaticMeshComponent):
                instanced += 1
            mesh = comp.get_editor_property("static_mesh")
            if not mesh:
                no_mesh += 1
            try:
                dist = comp.get_editor_property("cached_max_draw_distance")
            except Exception:
                dist = 0
            if dist and dist > 0:
                with_cull += 1
                cull_values.append(int(dist))
    w("STATIC_MESH_COMPONENTS=%d INSTANCED=%d WITH_CULL=%d NO_MESH=%d" % (
        static, instanced, with_cull, no_mesh))
    w("CULL_MIN=%s CULL_MAX=%s UNIQUE_CULL=%s" % (
        min(cull_values) if cull_values else 0,
        max(cull_values) if cull_values else 0,
        sorted(set(cull_values))))

    skeletal = 0
    soldier_comps = 0
    for actor in actors:
        for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            skeletal += 1
            mesh = comp.get_editor_property("skeletal_mesh_asset")
            if mesh and "HampiSoldier" in mesh.get_name():
                soldier_comps += 1
    w("SKELETAL_COMPONENTS=%d SOLDIER_COMPONENTS=%d" % (skeletal, soldier_comps))

    bp = unreal.EditorAssetLibrary.load_asset("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter")
    cdo = unreal.get_default_object(bp.generated_class())
    comp = cdo.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    w("BP_MESH=%s" % comp.get_editor_property("skeletal_mesh_asset"))
    w("BP_ANIM_MODE=%s" % comp.get_editor_property("animation_mode"))
    w("BP_LOCOMOTION=%s" % cdo.get_editor_property("locomotion_asset"))
    for prop in ["cached_max_draw_distance", "min_lod", "visibility_based_update", "cast_shadow"]:
        try:
            w("BP_MESH_PROP %s=%s" % (prop, comp.get_editor_property(prop)))
        except Exception as e:
            w("BP_MESH_PROP %s ERR=%s" % (prop, str(e)[:100]))
    w("DONE")
except Exception as e:
    w("ERROR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("MAP_COMPONENTS_FINAL_WRITTEN")
