import numpy as np
from PIL import Image
import os

width = 505
height = 505

# Coordinates normalized [0, 1]
x = np.linspace(0.0, 1.0, width)
y = np.linspace(0.0, 1.0, height)
xx, yy = np.meshgrid(x, y)

# Baseline elevation in cm: 0.0
height_cm = np.zeros((height, width), dtype=np.float32)

def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

# 1. Region A: Hampi Rocky Hills (North-West: xx in [0, 0.45], yy in [0, 0.45])
# High granite plateau + boulder ridges
dist_nw = np.sqrt((xx - 0.20)**2 + (yy - 0.20)**2)
hampi_mask = np.clip(1.0 - (dist_nw / 0.28), 0.0, 1.0)
hampi_mask = hampi_mask * hampi_mask * (3.0 - 2.0 * hampi_mask)

# Organic granite boulder noise for Hampi
boulder_noise = (
    np.sin(xx * 25.0 + np.cos(yy * 20.0)) * 600.0 +
    np.cos(yy * 32.0 + np.sin(xx * 28.0)) * 400.0 +
    np.sin(xx * 60.0 + yy * 50.0) * 200.0
)
hampi_base_elevation = 4500.0 # +45 meters
hampi_hills = hampi_mask * (hampi_base_elevation + boulder_noise)
height_cm += hampi_hills

# 2. Region B: Kamalapur Village (Center-North: xx in [0.45, 0.80], yy in [0.15, 0.45])
# Flat village terrace at +18m
dist_village = np.sqrt(((xx - 0.60) / 0.22)**2 + ((yy - 0.30) / 0.16)**2)
village_mask = np.clip(1.0 - dist_village, 0.0, 1.0)
village_mask = smoothstep(0.0, 1.0, village_mask)
village_elevation = 1800.0 # +18 meters
height_cm = np.maximum(height_cm, village_mask * village_elevation)

# 3. Region C: Hosapete Outskirts (South-West: xx in [0.08, 0.48], yy in [0.55, 0.92])
# Gentle rolling plains at +8m to +14m
dist_hosapete = np.sqrt(((xx - 0.28) / 0.24)**2 + ((yy - 0.72) / 0.22)**2)
hosapete_mask = np.clip(1.0 - dist_hosapete, 0.0, 1.0)
hosapete_mask = smoothstep(0.0, 1.0, hosapete_mask)
gentle_rolls = np.sin(xx * 12.0) * np.cos(yy * 10.0) * 250.0
hosapete_elevation = 1000.0 + gentle_rolls
height_cm = np.maximum(height_cm, hosapete_mask * hosapete_elevation)

# 4. Region E: Military Training Ground (South-Center: xx in [0.48, 0.75], yy in [0.65, 0.88])
# Extremely flat parade ground and shooting range at +12m
dist_military = np.sqrt(((xx - 0.62) / 0.16)**2 + ((yy - 0.76) / 0.14)**2)
military_mask = np.clip(1.0 - dist_military, 0.0, 1.0)
military_mask = smoothstep(0.0, 1.0, military_mask)
military_elevation = 1200.0 # +12 meters flat
height_cm = np.maximum(height_cm, military_mask * military_elevation)

# 5. Region D: Tungabhadra Riverside Corridor (East / South-East: xx in [0.72, 0.98])
# Depressed river basin and canyon down to -12m (-1200 cm)
# River spline path from North-East (xx=0.90, yy=0.05) winding down to South-East (xx=0.88, yy=0.95)
river_center_x = 0.86 + 0.06 * np.sin(yy * 6.0)
river_dist = np.abs(xx - river_center_x)
river_corridor_mask = np.clip(1.0 - (river_dist / 0.14), 0.0, 1.0)
river_corridor_mask = smoothstep(0.0, 1.0, river_corridor_mask)

# Carve the river depth
river_depression = -1400.0 * river_corridor_mask
height_cm += river_depression

# Ensure base terrain is smooth and natural
height_cm = np.clip(height_cm, -2000.0, 8000.0)

# Convert height in cm to 16-bit uint16
# Height16 = 32768 + (height_cm * 1.28)
height_u16 = np.clip(32768.0 + (height_cm * 1.28), 0, 65535).astype(np.uint16)

# Ensure output directory exists
out_dir = r'C:\UnrealProjects\Battleground\Content\Landscape'
os.makedirs(out_dir, exist_ok=True)

# 1. Save 16-bit PNG
png_path = os.path.join(out_dir, 'Hampi_Heightmap_505.png')
img = Image.fromarray(height_u16, mode='I;16')
img.save(png_path)
print(f'Saved 16-bit PNG to: {png_path}')

# 2. Save 16-bit RAW (.r16) Little Endian
raw_path = os.path.join(out_dir, 'Hampi_Heightmap_505.r16')
height_u16.tofile(raw_path)
print(f'Saved 16-bit RAW to: {raw_path}')

# 3. Save 8-bit visual preview
preview_path = os.path.join(out_dir, 'Hampi_Heightmap_Preview.png')
preview_data = ((height_u16 - height_u16.min()) / (height_u16.max() - height_u16.min()) * 255.0).astype(np.uint8)
img_preview = Image.fromarray(preview_data, mode='L')
img_preview.save(preview_path)
print(f'Saved 8-bit preview to: {preview_path}')

print(f'Height stats: min={height_cm.min():.1f}cm, max={height_cm.max():.1f}cm, mean={height_cm.mean():.1f}cm')
