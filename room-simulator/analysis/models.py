"""Local, CPU-only COCO detection and MiDaS relative inverse depth."""
import io
import os
from pathlib import Path
import sys
import urllib.request
import zipfile

import numpy as np
from PIL import Image
import timm
import torch
from torchvision.models.detection import (
    SSDLite320_MobileNet_V3_Large_Weights, ssdlite320_mobilenet_v3_large,
)

MIDAS_REV = "454597711a62eabcbf7d1e89f3fb9f569051ac9b"


def midas_source():
    """Fetch the official source at an immutable commit, retaining TLS verification."""
    root = Path(torch.hub.get_dir()) / f"midas-source-{MIDAS_REV}"
    if (root / "midas" / "midas_net_custom.py").exists():
        return root
    url = f"https://codeload.github.com/isl-org/MiDaS/zip/{MIDAS_REV}"
    with urllib.request.urlopen(url, timeout=90) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    root.mkdir(parents=True, exist_ok=True)
    # Extract only Python sources and the license, with explicit path containment.
    for entry in archive.infolist():
        relative = Path(*Path(entry.filename).parts[1:])
        target = root / relative
        if entry.is_dir() or (relative.suffix != ".py" and relative.name != "LICENSE"):
            continue
        if not target.resolve().is_relative_to(root.resolve()):
            raise ValueError("Unsafe model source archive path")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(entry))
    return root


class VisionModels:
    def __init__(self):
        torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
        weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
        self.detector = ssdlite320_mobilenet_v3_large(weights=weights).eval()
        self.categories = weights.meta["categories"]
        sys.path.insert(0, str(midas_source()))
        from midas import blocks
        from midas.midas_net_custom import MidasNet_small
        from midas.transforms import Resize, NormalizeImage, PrepareForNet
        # Use the same EfficientNet architecture from installed timm. No remote
        # backbone weights: the full official MiDaS checkpoint supplies them all.
        def backbone(_pretrained, exportable=False):
            network = timm.create_model("tf_efficientnet_lite3", pretrained=False, exportable=exportable)
            # timm 0.6 folds the stem activation into bn1; keep the old
            # parameter-free slot so checkpoint layer indices remain identical.
            network.act1 = torch.nn.Identity()
            return blocks._make_efficientnet_backbone(network)
        blocks._make_pretrained_efficientnet_lite3 = backbone
        self.depth = MidasNet_small(
            None, features=64, backbone="efficientnet_lite3", exportable=True,
            non_negative=True, blocks={"expand": True},
        ).eval()
        state = torch.hub.load_state_dict_from_url(
            "https://github.com/isl-org/MiDaS/releases/download/v2_1/midas_v21_small_256.pt",
            map_location="cpu", check_hash=True, weights_only=True,
        )
        self.depth.load_state_dict(state, strict=True)
        import cv2
        self.transforms = [
            Resize(256, 256, resize_target=None, keep_aspect_ratio=True,
                   ensure_multiple_of=32, resize_method="upper_bound", image_interpolation_method=cv2.INTER_CUBIC),
            NormalizeImage(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            PrepareForNet(),
        ]

    @torch.inference_mode()
    def infer(self, image: Image.Image):
        rgb = np.asarray(image.convert("RGB")).copy()
        tensor = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255
        detections = self.detector([tensor])[0]
        sample = {"image": rgb.astype(np.float32) / 255}
        for transform in self.transforms:
            sample = transform(sample)
        prediction = self.depth(torch.from_numpy(sample["image"]).unsqueeze(0))
        grid_w = 160
        grid_h = max(32, round(grid_w * image.height / image.width))
        depth = torch.nn.functional.interpolate(
            prediction.unsqueeze(1), size=(grid_h, grid_w), mode="bicubic", align_corners=False,
        ).squeeze().numpy()
        if not np.isfinite(depth).all():
            raise ValueError("Depth model returned non-finite values")
        low, high = float(depth.min()), float(depth.max())
        depth = (depth - low) / max(high - low, 1e-6)
        objects = []
        for bbox, score, label in zip(detections["boxes"], detections["scores"], detections["labels"]):
            if float(score) < 0.45 or len(objects) >= 20:
                continue
            x1, y1, x2, y2 = bbox.tolist()
            box = [max(0, x1 / image.width), max(0, y1 / image.height),
                   min(1, x2 / image.width), min(1, y2 / image.height)]
            # Central patch reduces background contamination; this remains an estimate.
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            rx, ry = (box[2] - box[0]) * .15, (box[3] - box[1]) * .15
            left, right = max(0, int((cx-rx)*grid_w)), min(grid_w, int((cx+rx)*grid_w)+1)
            top, bottom = max(0, int((cy-ry)*grid_h)), min(grid_h, int((cy+ry)*grid_h)+1)
            objects.append({
                "label": self.categories[int(label)], "confidence": round(float(score), 3),
                "box": box, "relative_inverse_depth": float(np.median(depth[top:bottom, left:right])),
            })
        png = io.BytesIO()
        Image.fromarray(np.uint8(depth * 255)).save(png, format="PNG")
        import base64
        return {
            "width": image.width, "height": image.height, "objects": objects,
            "depth": {"width": grid_w, "height": grid_h, "values": depth.round(5).ravel().tolist(),
                      "image": "data:image/png;base64," + base64.b64encode(png.getvalue()).decode()},
            "models": {"objects": "SSDLite320 MobileNetV3 / COCO", "depth": "MiDaS v2.1 small"},
        }


if __name__ == "__main__":
    VisionModels()
    print("Object and depth models downloaded and loaded successfully.")
