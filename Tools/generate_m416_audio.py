import math
import os
import random
import struct
import wave

OUT_DIR = r"C:\UnrealProjects\Battleground\Saved\ThirdParty\ProceduralAudio"
os.makedirs(OUT_DIR, exist_ok=True)
RATE = 22050


def write_wav(name, samples):
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = bytearray()
        for value in samples:
            value = max(-1.0, min(1.0, value))
            frames.extend(struct.pack("<h", int(value * 32767)))
        w.writeframes(bytes(frames))
    print(path)


def fire():
    random.seed(416)
    n = int(RATE * 0.13)
    out = []
    for i in range(n):
        t = i / RATE
        decay = math.exp(-38.0 * t)
        body = math.sin(2 * math.pi * (95.0 - 45.0 * t) * t) * 0.35
        noise = random.uniform(-1.0, 1.0) * 0.75
        crack = (noise + body) * decay
        out.append(crack * 0.65)
    return out


def reload():
    random.seed(7416)
    n = int(RATE * 0.42)
    out = [0.0] * n
    clicks = [(0.04, 0.05, 1500.0, 0.65), (0.19, 0.06, 2100.0, 0.55), (0.34, 0.05, 1200.0, 0.45)]
    for start, length, freq, amp in clicks:
        s = int(start * RATE)
        e = min(n, int((start + length) * RATE))
        for i in range(s, e):
            t = (i - s) / RATE
            decay = math.exp(-24.0 * t)
            metallic = math.sin(2 * math.pi * freq * t) * 0.45
            noise = random.uniform(-1.0, 1.0) * 0.55
            out[i] += (metallic + noise) * decay * amp
    return out


write_wav("S_M416_Fire.wav", fire())
write_wav("S_M416_Reload.wav", reload())
