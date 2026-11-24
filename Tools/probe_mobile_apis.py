import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\mobile_api_probe.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def methods(obj):
    return sorted(m for m in dir(obj) if not m.startswith("__"))


for name in ["BlueprintEditorLibrary", "MaterialEditingLibrary", "EditorStaticMeshLibrary",
             "EditorAssetLibrary", "TextureCompressionSettings", "TextureMipGenSettings",
             "MaterialExpression", "SkeletalMeshComponent", "AnimationMode"]:
    obj = getattr(unreal, name, None)
    w("CLASS %s exists=%s" % (name, bool(obj)))
    if obj:
        w("  %s" % ",".join(methods(obj) if isinstance(obj, object) and hasattr(obj, "mro") else dir(obj)))

for name in dir(unreal):
    if any(k in name.lower() for k in ["materialexpressionpixelnormal", "materialexpressionworldnormal",
                                       "materialexpressionlandscape", "materialexpressionabs",
                                       "materialExpressionOneMinus".lower(), "materialexpressionlinearinterpolate",
                                       "materialexpressionclamp", "materialexpressionpower",
                                       "materialexpressiontexturecoordinate"]):
        w("EXPR_CLASS %s" % name)

mesh = unreal.EditorAssetLibrary.load_asset(
    "/Game/Environment/Task05/Virupaksha/Meshes/SM_T05_VirupakshaGopuram")
if mesh:
    w("STATICMESH_METHODS=%s" % ",".join(m for m in methods(mesh) if any(
        k in m.lower() for k in ["lod", "section", "triangle", "vertex", "source"])))
    try:
        w("SOURCE_MODELS=%d" % len(mesh.get_editor_property("source_models")))
    except Exception as e:
        w("SOURCE_MODELS_ERR=%s" % e)
    try:
        w("RENDER_DATA_LODS=%s" % mesh.get_editor_property("render_data"))
    except Exception as e:
        w("RENDER_DATA_ERR=%s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("MOBILE_API_PROBE_WRITTEN")
