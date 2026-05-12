import io
import matplotlib.pyplot as plt
from PIL import Image


def stitch_figures(figs: list[plt.Figure]) -> bytes:
    images = []
    for fig in figs:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        images.append(Image.open(buf).copy())

    target_height = max(img.height for img in images)

    resized = []
    for img in images:
        scale = target_height / img.height
        new_w = int(img.width * scale)
        resized.append(img.resize((new_w, target_height), Image.LANCZOS))

    total_width = sum(img.width for img in resized)
    combined = Image.new('RGB', (total_width, target_height), (255, 255, 255))

    x_offset = 0
    for img in resized:
        combined.paste(img, (x_offset, 0))
        x_offset += img.width

    out = io.BytesIO()
    combined.save(out, format='png')
    out.seek(0)
    return out.getvalue()
