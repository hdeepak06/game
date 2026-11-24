import os
import traceback

PROJECT = r"C:\UnrealProjects\Battleground"
OUT_DIR = os.path.join(PROJECT, "Saved", "Android")
REPORT = os.path.join(OUT_DIR, "graphics_profiles_validation.txt")
os.makedirs(OUT_DIR, exist_ok=True)

DEVICE_PROFILES = os.path.join(PROJECT, "Config", "DefaultDeviceProfiles.ini")
ANDROID_SCALABILITY = os.path.join(PROJECT, "Config", "Android", "AndroidScalability.ini")
DEFAULT_ENGINE = os.path.join(PROJECT, "Config", "DefaultEngine.ini")

EXPECTED_PROFILES = {
    "Android_Low DeviceProfile": {
        "r.MobileContentScaleFactor": "0.700000",
        "r.Mobile.AntiAliasing": "0",
        "sg.ViewDistanceQuality": "0",
        "sg.AntiAliasingQuality": "0",
        "sg.ShadowQuality": "0",
        "sg.GlobalIlluminationQuality": "0",
        "sg.ReflectionQuality": "0",
        "sg.PostProcessQuality": "0",
        "sg.TextureQuality": "0",
        "sg.EffectsQuality": "0",
        "sg.FoliageQuality": "0",
        "sg.ShadingQuality": "0",
    },
    "Android_Mid DeviceProfile": {
        "r.MobileContentScaleFactor": "0.850000",
        "r.Mobile.AntiAliasing": "1",
        "sg.ViewDistanceQuality": "1",
        "sg.AntiAliasingQuality": "1",
        "sg.ShadowQuality": "1",
        "sg.GlobalIlluminationQuality": "1",
        "sg.ReflectionQuality": "1",
        "sg.PostProcessQuality": "1",
        "sg.TextureQuality": "1",
        "sg.EffectsQuality": "1",
        "sg.FoliageQuality": "1",
        "sg.ShadingQuality": "1",
    },
    "Android_High DeviceProfile": {
        "r.MobileContentScaleFactor": "1.000000",
        "r.Mobile.AntiAliasing": "1",
        "sg.ViewDistanceQuality": "2",
        "sg.AntiAliasingQuality": "2",
        "sg.ShadowQuality": "2",
        "sg.GlobalIlluminationQuality": "2",
        "sg.ReflectionQuality": "2",
        "sg.PostProcessQuality": "2",
        "sg.TextureQuality": "2",
        "sg.EffectsQuality": "2",
        "sg.FoliageQuality": "2",
        "sg.ShadingQuality": "2",
    },
}

EXPECTED_SCALABILITY = {
    "ViewDistanceQuality@0": {"r.ViewDistanceScale": "0.650000"},
    "ViewDistanceQuality@1": {"r.ViewDistanceScale": "0.850000"},
    "ViewDistanceQuality@2": {"r.ViewDistanceScale": "1.000000"},
    "ShadowQuality@0": {"r.ShadowQuality": "0", "r.Shadow.MaxCSMResolution": "512", "r.Shadow.CSM.MaxCascades": "1"},
    "ShadowQuality@1": {"r.ShadowQuality": "1", "r.Shadow.MaxCSMResolution": "1024", "r.Shadow.CSM.MaxCascades": "1"},
    "ShadowQuality@2": {"r.ShadowQuality": "2", "r.Shadow.MaxCSMResolution": "2048", "r.Shadow.CSM.MaxCascades": "2"},
    "PostProcessQuality@0": {"r.Tonemapper.Quality": "1", "r.BloomQuality": "0", "r.EyeAdaptationQuality": "1"},
    "PostProcessQuality@1": {"r.Tonemapper.Quality": "2", "r.BloomQuality": "0", "r.EyeAdaptationQuality": "1"},
    "PostProcessQuality@2": {"r.Tonemapper.Quality": "2", "r.BloomQuality": "0", "r.EyeAdaptationQuality": "1"},
    "TextureQuality@0": {"r.MaxAnisotropy": "1"},
    "TextureQuality@1": {"r.MaxAnisotropy": "1"},
    "TextureQuality@2": {"r.MaxAnisotropy": "2"},
    "FoliageQuality@0": {"foliage.DensityScale": "0.500000"},
    "FoliageQuality@1": {"foliage.DensityScale": "0.800000"},
    "FoliageQuality@2": {"foliage.DensityScale": "1.000000"},
    "GlobalIlluminationQuality@0": {"r.Lumen.DiffuseIndirect.Allow": "0"},
    "GlobalIlluminationQuality@1": {"r.Lumen.DiffuseIndirect.Allow": "0"},
    "GlobalIlluminationQuality@2": {"r.Lumen.DiffuseIndirect.Allow": "0"},
    "ReflectionQuality@0": {"r.Lumen.Reflections.Allow": "0"},
    "ReflectionQuality@1": {"r.Lumen.Reflections.Allow": "0"},
    "ReflectionQuality@2": {"r.Lumen.Reflections.Allow": "0"},
}

results = []
errors = []


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    if not condition:
        errors.append("%s :: %s" % (name, detail))


def parse_ini(path):
    sections = {}
    current = None
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith(";") or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current = line[1:-1]
                sections.setdefault(current, {})
                continue
            if current is None or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.split(";", 1)[0].strip()
            if key.startswith("+"):
                key = key[1:].strip()
                sections[current].setdefault(key, []).append(value)
            elif key.startswith("!"):
                sections[current][key[1:].strip()] = []
            else:
                sections[current][key] = [value]
    return sections


def cvar_map(values):
    out = {}
    for entry in values or []:
        if "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        out[key.strip()] = value.split(";", 1)[0].strip()
    return out


try:
    for path in (DEVICE_PROFILES, ANDROID_SCALABILITY, DEFAULT_ENGINE):
        check("file_exists:%s" % os.path.basename(path), os.path.isfile(path), path)

    profiles = parse_ini(DEVICE_PROFILES)
    for section, expected in EXPECTED_PROFILES.items():
        check("device_profile_section:%s" % section, section in profiles, "missing section")
        if section not in profiles:
            continue
        values = cvar_map(profiles[section].get("CVars", []))
        check("device_profile_basename:%s" % section, "Android" in profiles[section].get("BaseProfileName", []), profiles[section].get("BaseProfileName", []))
        for key, want in expected.items():
            got = values.get(key)
            check("device_cvar:%s:%s" % (section, key), got == want, "want=%s got=%s" % (want, got))

    scalability = parse_ini(ANDROID_SCALABILITY)
    for section, expected in EXPECTED_SCALABILITY.items():
        check("scalability_section:%s" % section, section in scalability, "missing section")
        if section not in scalability:
            continue
        for key, want in expected.items():
            got_list = scalability[section].get(key, [])
            got = got_list[-1] if got_list else None
            check("scalability_cvar:%s:%s" % (section, key), got == want, "want=%s got=%s" % (want, got))

    engine = parse_ini(DEFAULT_ENGINE)
    runtime = engine.get("/Script/AndroidRuntimeSettings.AndroidRuntimeSettings", {})
    for key, want in (
        ("bBuildForArm64", "True"),
        ("bBuildForArmV7", "False"),
        ("bBuildForX8664", "False"),
        ("MinSDKVersion", "26"),
        ("TargetSDKVersion", "34"),
        ("Orientation", "Landscape"),
        ("MaxAspectRatio", "2.400000"),
        ("bUseDisplayCutout", "True"),
    ):
        got_list = runtime.get(key, [])
        got = got_list[-1] if got_list else None
        check("android_runtime:%s" % key, got == want, "want=%s got=%s" % (want, got))

    all_device_text = open(DEVICE_PROFILES, "r", encoding="utf-8").read()
    check("no_frame_rate_cap", "t.MaxFPS" not in all_device_text, "t.MaxFPS must remain uncapped for optional 60 FPS")
except Exception:
    errors.append(traceback.format_exc())

passed = sum(1 for _, ok, _ in results if ok)
with open(REPORT, "w", encoding="utf-8") as f:
    f.write("GRAPHICS_PROFILES_VALIDATION_BEGIN\n")
    for name, ok, detail in results:
        f.write("CHECK %s=%s\n" % (name, "True" if ok else "False"))
        if not ok:
            f.write("  DETAIL %s\n" % detail)
    f.write("CHECKS=%d/%d\n" % (passed, len(results)))
    f.write("STATUS=%s\n" % ("PASS" if not errors else "FAIL"))
    f.write("ERRORS=%s\n" % errors)

print("GRAPHICS_PROFILES_VALIDATION CHECKS=%d/%d STATUS=%s" % (passed, len(results), "PASS" if not errors else "FAIL"))
