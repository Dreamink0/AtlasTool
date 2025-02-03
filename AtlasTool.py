import re
import os
from PIL import Image

def parse_atlas(atlas_path):
    regions = []
    current_region = None

    bounds_pattern = re.compile(r"bounds:\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)")
    offsets_pattern = re.compile(r"offsets:\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)")
    rotate_pattern = re.compile(r"rotate:\s*(\d+)")

    with open(atlas_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    i = 0
    while i < len(lines):
        if any(tag in lines[i] for tag in ["size:", "format:", "filter:", "scale:"]):
            i += 1
            continue
        else:
            break

    while i < len(lines):
        line = lines[i]

        if not any(tag in line for tag in ["bounds:", "offsets:", "rotate:"]):
            if current_region:
                regions.append(current_region)
            current_region = {
                "name": line,
                "bounds": None,
                "rotate": 0,
                "offsets": None
            }
        else:
            m_bounds = bounds_pattern.search(line)
            if m_bounds:
                x, y, w, h = map(int, m_bounds.groups())
                current_region["bounds"] = (x, y, w, h)

            m_offsets = offsets_pattern.search(line)
            if m_offsets:
                ox, oy, ow, oh = map(int, m_offsets.groups())
                current_region["offsets"] = (ox, oy, ow, oh)

            m_rotate = rotate_pattern.search(line)
            if m_rotate:
                angle = int(m_rotate.group(1))
                if angle == 90:
                    angle = 270
                elif angle == 270:
                    angle = 90
                current_region["rotate"] = angle

        i += 1

    if current_region:
        regions.append(current_region)

    return regions


def export_regions_from_texture(texture_path, atlas_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    big_image = Image.open(texture_path)

    regions = parse_atlas(atlas_path)

    for region in regions:
        name = region["name"]

        if region["bounds"] is None:
            print(f"Warning: region '{name}' has no bounds, skipped.")
            continue

        x, y, w, h = region["bounds"]
        rotate_angle = region["rotate"]
        offsets = region["offsets"]

        cropped = big_image.crop((x, y, x + w, y + h))
        if rotate_angle in [90, 180, 270]:
            cropped = cropped.rotate(rotate_angle, expand=True)

        if offsets:
            offset_x, offset_y, orig_w, orig_h = offsets

            if rotate_angle == 90:
                new_offset_x = orig_w - (offset_y + cropped.height)
                new_offset_y = offset_x
            elif rotate_angle == 180:
                new_offset_x = orig_w - (offset_x + cropped.width)
                new_offset_y = orig_h - (offset_y + cropped.height)
            elif rotate_angle == 270:
                new_offset_x = offset_y
                new_offset_y = orig_h - (offset_x + cropped.width)
            else:
                new_offset_x = offset_x
                new_offset_y = offset_y

            final_img = Image.new("RGBA", (orig_w, orig_h), (0, 0, 0, 0))
            final_img.paste(cropped, (new_offset_x, new_offset_y))
        else:
            final_img = cropped

        output_path = os.path.join(output_dir, f"{name}.png")
        final_img.save(output_path, format="PNG")
        print(f"Exported: {output_path}")


def find_matching_files(directory):
    atlas_files = [f for f in os.listdir(directory) if f.endswith('.atlas')]
    png_files = [f for f in os.listdir(directory) if f.endswith('.png')]

    matched_files = []
    for atlas_file in atlas_files:
        base_name = os.path.splitext(atlas_file)[0]
        matching_png = f"{base_name}.png"
        if matching_png in png_files:
            matched_files.append((atlas_file, matching_png))

    return matched_files


if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.abspath(__file__))

    matched_files = find_matching_files(current_directory)

    for atlas_file, png_file in matched_files:
        print(f"Processing: {atlas_file} and {png_file}")
        output_directory = os.path.join(current_directory, "output_sprites")
        export_regions_from_texture(png_file, atlas_file, output_directory)