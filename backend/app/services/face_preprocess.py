"""
Optional face preprocessing using insightface.
If insightface/onnxruntime are not installed, the module provides a no-op fallback.
"""
from __future__ import annotations
from functools import lru_cache
from typing import Optional, Any

try:
    from insightface.app import FaceAnalysis  # type: ignore
    import numpy as np
    from PIL import Image
    _INSIGHTFACE_AVAILABLE = True
except Exception:  # pragma: no cover
    _INSIGHTFACE_AVAILABLE = False
    FaceAnalysis = None  # type: ignore
    Image = None  # type: ignore


@lru_cache(maxsize=1)
def _get_detector():
    if not _INSIGHTFACE_AVAILABLE:
        return None
    # CPU providers by default
    app = FaceAnalysis(name='buffalo_l')
    app.prepare(ctx_id=-1, det_size=(640, 640))
    return app


def preprocess_face(image: Any) -> Optional[Any]:
    """Return aligned face image if detected, else None.
    Picks the largest face.
    """
    if not _INSIGHTFACE_AVAILABLE:
        return None
    import numpy as np  # local import to avoid global dependency if unused

    app = _get_detector()
    if app is None:
        return None

    img_np = np.array(image)
    faces = app.get(img_np)
    if not faces:
        return None

    # pick the largest bbox
    faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    best = faces[0]
    # get aligned face chip (112x112 default), convert to PIL
    # use normed cropping function from face object
    try:
        chip = app.get(img_np, max_num=1, det_size=(640, 640), ret_crop=True)[0].normed
        chip = (chip[:, :, ::-1] * 255).astype('uint8')  # BGR->RGB if needed
        return Image.fromarray(chip)
    except Exception:
        # fallback to bbox crop
        x1, y1, x2, y2 = map(int, best.bbox)
        x1, y1 = max(x1, 0), max(y1, 0)
        x2, y2 = min(x2, img_np.shape[1]), min(y2, img_np.shape[0])
        crop = image.crop((x1, y1, x2, y2))
        return crop
