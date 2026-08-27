import os
import zipfile

def package_extension():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extension_dir = os.path.join(base_dir, "extension")
    static_dir = os.path.join(base_dir, "backend", "static")
    os.makedirs(static_dir, exist_ok=True)
    zip_path = os.path.join(static_dir, "lenderlens-extension.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(extension_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extension_dir)
                zf.write(file_path, rel_path)

    print(f"Extension packaged successfully into {zip_path}")
    return zip_path

if __name__ == "__main__":
    package_extension()
