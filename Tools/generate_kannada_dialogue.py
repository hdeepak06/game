"""Generate North Karnataka-style Kannada battle dialogue WAVs for UE import.

Tool attribution is written to Saved/ThirdParty/KannadaDialogue/LICENSE.txt.
edge-tts is LGPLv3 (https://github.com/rany2/edge-tts); the kn-IN neural voices
are provided by Microsoft Edge's online TTS service. Generated WAVs are
synthesized output, not downloaded third-party audio files.
"""
import asyncio
import os
import subprocess

import edge_tts
import imageio_ffmpeg

OUT = r"C:\UnrealProjects\Battleground\Saved\ThirdParty\KannadaDialogue"
os.makedirs(OUT, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# cue, Kannada line, English gloss, voice
LINES = [
    ("MatchStart", "ಯುದ್ಧ ಶುರು ಆಯ್ತು! ಹಾಂಪಿ ಕದನಕ್ಕೆ ಸ್ವಾಗತ.",
     "The battle has started! Welcome to the Hampi fight.", "kn-IN-GaganNeural"),
    ("WeaponEquipped", "ಎಂ ನಾಲ್ಕು ರೈಫಲ್ ಸಿಕ್ಕಿತು. ಸಿದ್ಧರಾಗಿ.",
     "The M416 rifle is acquired. Get ready.", "kn-IN-GaganNeural"),
    ("EnemySpotted", "ಶತ್ರುಗಳು ಹತ್ತಿರ ಇದ್ದಾರೆ! ಎಚ್ಚರ ಇರಿ.",
     "Enemies are nearby! Stay alert.", "kn-IN-GaganNeural"),
    ("ZoneWarning", "ಸೇಫ್ ಜೋನ್ ಕುಗ್ಗುತ್ತಿದೆ, ಒಳಗೆ ಬನ್ನಿ!",
     "The safe zone is shrinking, come inside!", "kn-IN-SapnaNeural"),
    ("LowHealth", "ಜೀವ ಕಡಿಮೆ ಆಗಿದೆ! ಮೆಡ್ಕಿಟ್ ಬಳಸಿ.",
     "Health is low! Use a medkit.", "kn-IN-SapnaNeural"),
    ("Healing", "ಗಾಯಗಳು ವಾಸಿ ಆಗುತ್ತಿವೆ.",
     "The wounds are healing.", "kn-IN-SapnaNeural"),
    ("Victory", "ಗೆಲುವು ನಮ್ಮದು! ಕೊನೆಯವರೆಗೂ ಉಳಿದಿದ್ದೀರಿ.",
     "Victory is ours! You stayed until the end.", "kn-IN-GaganNeural"),
    ("Defeat", "ಸೋತಿದ್ದೀರಿ. ಮತ್ತೆ ಪ್ರಯತ್ನ ಮಾಡಿ.",
     "You have lost. Try again.", "kn-IN-GaganNeural"),
]


async def generate(cue, text, voice):
    mp3 = os.path.join(OUT, "VO_%s.mp3" % cue)
    wav = os.path.join(OUT, "VO_%s.wav" % cue)
    await edge_tts.Communicate(text, voice).save(mp3)
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error", "-i", mp3,
        "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", wav,
    ], check=True)
    return cue, os.path.getsize(wav)


async def main():
    for cue, text, gloss, voice in LINES:
        name, size = await generate(cue, text, voice)
        print("DIALOGUE %s %d bytes voice=%s" % (name, size, voice))


if __name__ == "__main__":
    asyncio.run(main())
    with open(os.path.join(OUT, "dialogue_lines.txt"), "w", encoding="utf-8") as f:
        for cue, text, gloss, voice in LINES:
            f.write("%s|%s|%s|%s\n" % (cue, text, gloss, voice))
    with open(os.path.join(OUT, "LICENSE.txt"), "w", encoding="utf-8") as f:
        f.write(
            "Kannada dialogue WAVs were synthesized for HAMPI BATTLEGROUND with:\n"
            "- edge-tts 7.3.1, LGPLv3: https://github.com/rany2/edge-tts\n"
            "- License: https://github.com/rany2/edge-tts/blob/master/LICENSE\n"
            "- Voices: kn-IN-GaganNeural, kn-IN-SapnaNeural (Microsoft Edge online TTS)\n"
            "- MP3 to WAV conversion: imageio-ffmpeg (BSD-2-Clause) bundled FFmpeg (LGPL)\n"
            "No third-party audio recording was downloaded. Review Microsoft's service\n"
            "terms before commercial distribution of the generated speech.\n"
            "Dialect note: the script uses North Karnataka colloquial Kannada forms;\n"
            "the available kn-IN neural voices are standard Kannada. A native-speaker\n"
            "review is recommended before a commercial release.\n"
        )
