import struct
import zlib
import os

def create_shield_png(size, output_path):
    """Generates a clean RGBA PNG shield icon without third-party dependencies."""
    width = size
    height = size
    
    # Create raw pixel buffer (RGBA)
    raw_data = bytearray()
    
    # Shield shape parameters
    center_x = width / 2.0
    center_y = height / 2.0
    
    for y in range(height):
        raw_data.append(0) # Filter type 0 (None)
        for x in range(width):
            # Distance from center
            nx = (x - center_x) / (width / 2.0)
            ny = (y - center_y) / (height / 2.0)
            
            # Simple shield curve equation: |nx| <= 0.85 and ny >= -0.85 and ny <= 0.85 - 0.5 * (nx * nx)
            in_shield = abs(nx) <= 0.82 and ny >= -0.82 and ny <= (0.90 - 0.75 * (nx * nx))
            
            if in_shield:
                # Blue/indigo shield fill
                r = int(37 + (1.0 - ny) * 20)
                g = int(99 + (1.0 - ny) * 30)
                b = int(235 + (1.0 - ny) * 15)
                a = 255
                
                # Highlight checkmark inside
                if size >= 48:
                    if abs(nx + 0.15 - ny * 0.5) < 0.12 and ny > -0.2 and ny < 0.4 and nx < 0.2:
                        r, g, b = 255, 255, 255
                    elif abs(nx - 0.1 - ny * 0.8) < 0.12 and ny > -0.4 and ny < 0.4 and nx >= -0.1:
                        r, g, b = 255, 255, 255
            else:
                r, g, b, a = 0, 0, 0, 0
                
            raw_data.extend([min(r, 255), min(g, 255), min(b, 255), a])

    # Compress IDAT chunk
    compressed = zlib.compress(bytes(raw_data), 9)

    def make_chunk(chunk_type, data):
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xffffffff)

    png_header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_chunk = make_chunk(b"IHDR", ihdr_data)
    idat_chunk = make_chunk(b"IDAT", compressed)
    iend_chunk = make_chunk(b"IEND", b"")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(png_header + ihdr_chunk + idat_chunk + iend_chunk)

if __name__ == "__main__":
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "extension", "assets")
    create_shield_png(16, os.path.join(assets_dir, "icon16.png"))
    create_shield_png(48, os.path.join(assets_dir, "icon48.png"))
    create_shield_png(128, os.path.join(assets_dir, "icon128.png"))
    print("PNG icons created successfully in", assets_dir)
