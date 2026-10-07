import io

from omcore import lang


with lang.auto_proxy_import(globals()):
    from PIL import Image


##


def get_image_png_bytes(image: Image.Image) -> bytes:
    with io.BytesIO() as out:
        image.save(out, format='PNG')
        return out.getvalue()
