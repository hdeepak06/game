import unreal

OUT = r"C:\UnrealProjects\Battleground\Saved\CurrentStateAudit\blendspace_props.txt"
lines = []


def w(s=""):
    lines.append(str(s))


def props(obj, label):
    w("--- PROPS %s ---" % label)
    for n in sorted(x for x in dir(obj) if not x.startswith("_")):
        try:
            if callable(getattr(obj, n)):
                continue
        except Exception:
            continue
        try:
            v = obj.get_editor_property(n)
            w("  %s=%s" % (n, str(v)[:300]))
        except Exception:
            pass


for clsname in ["BlendSpace1D", "BlendSpace", "BlendSpaceBase", "BlendSample", "BlendSpaceAxisSettings", "BlendSpaceAxis"]:
    cls = getattr(unreal, clsname, None)
    w("CLASS %s exists=%s" % (clsname, bool(cls)))
    if cls:
        try:
            cdo = unreal.get_default_object(cls)
            props(cdo, clsname + "_CDO")
        except Exception as e:
            w("  CDO_ERR=%s" % e)
        for n in sorted(dir(cls)):
            if any(k in n.lower() for k in ["sample", "axis", "rate", "blend"]):
                w("  MEMBER %s callable=%s" % (n, callable(getattr(cls, n, None))))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("BLENDSPACE_PROPS_WRITTEN")
