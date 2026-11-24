import os
import unreal

SRC = r"C:\UnrealProjects\Battleground\Saved\ThirdParty\KannadaDialogue"
DST = "/Game/Audio/Dialogue"
OUT = r"C:\UnrealProjects\Battleground\Saved\Voice\import_report.txt"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []

unreal.EditorAssetLibrary.make_directory(DST)
tasks = []
for name in sorted(os.listdir(SRC)):
    if not name.lower().endswith(".wav"):
        continue
    task = unreal.AssetImportTask()
    task.filename = os.path.join(SRC, name)
    task.destination_path = DST
    task.destination_name = os.path.splitext(name)[0]
    task.automated = True
    task.save = True
    task.replace_existing = True
    tasks.append(task)

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for task in tasks:
    asset_path = "%s/%s" % (DST, task.destination_name)
    obj = unreal.EditorAssetLibrary.load_asset(asset_path)
    lines.append("SOUND=%s loaded=%s class=%s" % (
        asset_path, bool(obj), obj.get_class().get_name() if obj else "None"))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("KANNADA_DIALOGUE_IMPORT_DONE")
