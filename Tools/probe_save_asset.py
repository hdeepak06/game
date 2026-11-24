import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\save_asset_doc.txt"
lines = []
for obj, label in [
    (unreal.EditorAssetLibrary.save_asset, "save_asset"),
    (unreal.EditorAssetLibrary.save_loaded_asset, "save_loaded_asset"),
]:
    lines.append("--- %s ---" % label)
    lines.append(str(getattr(obj, "__doc__", None)))
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SAVE_ASSET_DOC_WRITTEN")
