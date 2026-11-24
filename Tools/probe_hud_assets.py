import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\hud_asset_probe.txt"
paths = [
    "/Engine/EngineResources/WhiteSquareTexture",
    "/Engine/EngineResources/DefaultTexture",
    "/Engine/MobileResources/HUD/DefaultVirtualJoysticks.DefaultVirtualJoysticks",
]
lines = []
for p in paths:
    obj = unreal.load_asset(p)
    lines.append("%s loaded=%s class=%s" % (p, bool(obj), obj.get_class().get_name() if obj else "None"))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("HUD_ASSET_PROBE_WRITTEN")
