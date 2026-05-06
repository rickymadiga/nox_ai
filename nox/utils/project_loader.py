import zipfile
import io

def extract_zip_to_dict(zip_bytes: bytes):
    files = {}

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for name in z.namelist():
            if not name.endswith("/"):
                try:
                    files[name] = z.read(name).decode("utf-8")
                except:
                    pass

    return files