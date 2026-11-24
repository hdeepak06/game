import unreal
OUT = r"C:\UnrealProjects\Battleground\Saved\WeaponM416\factories.txt"
lines = [n for n in dir(unreal) if "Factory" in n and ("Input" in n or "Action" in n or "Mapping" in n)]
lines += ["---ALL INPUT---"]
lines += [n for n in dir(unreal) if "Input" in n]
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("FACTORIES_WRITTEN")
