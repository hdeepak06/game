import json
import os
import struct

GLB = r"C:\UnrealProjects\Battleground\Saved\ThirdParty\Grab3D_Soldier\soldier-rigged.glb"
OUT_DIR = r"C:\UnrealProjects\Battleground\Saved\ThirdParty\Grab3D_Soldier\Extracted"
os.makedirs(OUT_DIR, exist_ok=True)

with open(GLB, "rb") as f:
    data = f.read()

magic, version, length = struct.unpack_from("<4sII", data, 0)
print("GLB magic=%s version=%d length=%d actual=%d" % (magic, version, length, len(data)))
assert magic == b"glTF"

offset = 12
chunks = []
while offset < length:
    clen, ctype = struct.unpack_from("<II", data, offset)
    offset += 8
    chunks.append((ctype, data[offset:offset + clen]))
    offset += clen

j = None
binary = None
for ctype, payload in chunks:
    if ctype == 0x4E4F534A:
        j = json.loads(payload.decode("utf-8").strip())
    elif ctype == 0x004E4942:
        binary = payload

print("SCENE nodes=%d meshes=%d skins=%d animations=%d images=%d textures=%d materials=%d accessors=%d" % (
    len(j.get("nodes", [])), len(j.get("meshes", [])), len(j.get("skins", [])),
    len(j.get("animations", [])), len(j.get("images", [])), len(j.get("textures", [])),
    len(j.get("materials", [])), len(j.get("accessors", []))))

print("ANIMATIONS:")
for anim in j.get("animations", []):
    print("  name=%s channels=%d samplers=%d" % (
        anim.get("name"), len(anim.get("channels", [])), len(anim.get("samplers", []))))

for skin in j.get("skins", []):
    joints = skin.get("joints", [])
    names = [j["nodes"][idx].get("name", "?") for idx in joints]
    print("SKIN joints=%d names=%s" % (len(joints), names))

print("MESH PRIMITIVES:")
for mesh in j.get("meshes", []):
    for p in mesh.get("primitives", []):
        acc = j["accessors"][p["attributes"].get("POSITION", 0)]
        inds = j["accessors"][p["indices"]] if "indices" in p else None
        print("  mesh=%s verts=%d tris=%d material=%s attrs=%s" % (
            mesh.get("name"), acc.get("count"),
            (inds.get("count", 0) // 3 if inds else acc.get("count", 0) // 3),
            p.get("material"), sorted(p.get("attributes", {}).keys())))

print("MATERIALS:")
for m in j.get("materials", []):
    print("  %s" % m.get("name"))
    print("    %s" % m)

print("IMAGES:")
for i, img in enumerate(j.get("images", [])):
    name = img.get("name") or "image_%d" % i
    mime = img.get("mimeType", "image/png")
    ext = "png" if "png" in mime else "jpg"
    if "bufferView" in img:
        bv = j["bufferViews"][img["bufferView"]]
        start = bv.get("byteOffset", 0)
        raw = binary[start:start + bv["byteLength"]]
    elif "uri" in img:
        import base64
        uri = img["uri"]
        raw = base64.b64decode(uri.split(",", 1)[1]) if uri.startswith("data:") else b""
    else:
        raw = b""
    path = os.path.join(OUT_DIR, "%s.%s" % (name.replace(" ", "_"), ext))
    with open(path, "wb") as f:
        f.write(raw)
    print("  %s -> %s bytes=%d mime=%s" % (name, path, len(raw), mime))

print("TEXTURES:")
for t in j.get("textures", []):
    print("  %s" % t)

print("GLB_PARSE_DONE")
