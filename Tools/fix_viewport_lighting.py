"""Make the existing Hampi level visible without a lighting rebuild.

Does not spawn a second copy of a light that already exists.
Does not modify the Landscape actor or its material.
"""

import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

directional = None
skylight = None
atmosphere = None
fog = None
post_process = None

unreal.log("=== EXISTING LEVEL ACTORS ===")
for actor in actors:
    kind = actor.get_class().get_name()
    unreal.log(f"  {kind}  {actor.get_name()}")
    if isinstance(actor, unreal.DirectionalLight) and directional is None:
        directional = actor
    elif isinstance(actor, unreal.SkyLight) and skylight is None:
        skylight = actor
    elif isinstance(actor, unreal.SkyAtmosphere) and atmosphere is None:
        atmosphere = actor
    elif isinstance(actor, unreal.ExponentialHeightFog) and fog is None:
        fog = actor
    elif isinstance(actor, unreal.PostProcessVolume) and post_process is None:
        post_process = actor


def component(actor, component_class):
    return actor.get_component_by_class(component_class) if actor else None


if directional:
    light = component(directional, unreal.DirectionalLightComponent)
    directional.set_actor_rotation(unreal.Rotator(-50.0, 40.0, 0.0), False)
    if light:
        light.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.set_editor_property("intensity", 10.0)
        light.set_editor_property("atmosphere_sun_light", True)
        light.set_editor_property("cast_shadows", True)
        light.set_visibility(True)
        unreal.log(
            f"DirectionalLight mobility={light.get_editor_property('mobility')} "
            f"intensity={light.get_editor_property('intensity')}"
        )
else:
    unreal.log("ERROR: No DirectionalLight in the level. Not spawning one.")

if skylight:
    sky = component(skylight, unreal.SkyLightComponent)
    if sky:
        sky.set_mobility(unreal.ComponentMobility.MOVABLE)
        sky.set_editor_property("intensity", 1.0)
        sky.set_editor_property("real_time_capture", True)
        sky.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
        sky.set_visibility(True)
        sky.recapture_sky()
        unreal.log(
            f"SkyLight mobility={sky.get_editor_property('mobility')} "
            f"intensity={sky.get_editor_property('intensity')} "
            f"realtime={sky.get_editor_property('real_time_capture')}"
        )
else:
    unreal.log("ERROR: No SkyLight in the level. Not spawning one.")

if atmosphere:
    unreal.log(f"SkyAtmosphere kept: {atmosphere.get_name()}")
else:
    unreal.log("ERROR: No SkyAtmosphere in the level. Not spawning one.")

if fog:
    fog_comp = component(fog, unreal.ExponentialHeightFogComponent)
    if fog_comp:
        fog_comp.set_editor_property("fog_density", 0.002)
        fog_comp.set_visibility(True)
        unreal.log(f"Fog density={fog_comp.get_editor_property('fog_density')}")
else:
    unreal.log("ERROR: No ExponentialHeightFog in the level. Not spawning one.")

if post_process:
    post_process.set_editor_property("unbound", True)
    post_process.set_editor_property("enabled", True)
    settings = post_process.get_editor_property("settings")
    settings.set_editor_property("override_auto_exposure_method", True)
    settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM)
    settings.set_editor_property("override_auto_exposure_bias", True)
    settings.set_editor_property("auto_exposure_bias", 1.0)
    settings.set_editor_property("override_auto_exposure_min_brightness", True)
    settings.set_editor_property("auto_exposure_min_brightness", 0.5)
    settings.set_editor_property("override_auto_exposure_max_brightness", True)
    settings.set_editor_property("auto_exposure_max_brightness", 2.0)
    settings.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
    settings.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
    post_process.set_editor_property("settings", settings)
    unreal.log("PostProcessVolume set unbound with histogram auto exposure")
else:
    unreal.log("ERROR: No PostProcessVolume in the level. Not spawning one.")

world_settings = world.get_world_settings()
world_settings.set_editor_property("b_force_no_precomputed_lighting", True)
unreal.log("WorldSettings Force No Precomputed Lighting = True")

saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
unreal.log(f"Level saved: {saved}")
unreal.log("=== LIGHTING FIX DONE ===")
