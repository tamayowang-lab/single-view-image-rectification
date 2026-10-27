# Headspace: photo reconstruction and click-to-aim

Open one 2D photograph, run local object detection and relative-depth inference, and click a pixel to direct a virtual head toward that surface. Recognized object bounding boxes retain their color; the remaining image is grayscale. An oval displays the simulated eyesight range, centered on the selected pixel. A separate orbitable 3D point cloud shows the reconstructed visible surfaces and the head's viewing cone.

A head-and-eyes mannequin now sits beside the photograph. Eyes lead a gaze shift, the head follows, and the eyes compensate as the head turns. **Eyes only**, observer-view controls, an optional object tour, and reduced-motion support are included. See [head/eye controls, research references, and reconstruction details](docs/head-eye-simulation.md).

The original furnished-room simulator is still available at `/room.html`.

## Run the photo workflow

Requirements: Node.js 20+, Python 3.10–3.12, and a browser with WebGL for the 3D preview. The 2D viewer and analysis still work without WebGL. CPU inference needs no GPU or API key.

From this directory, prepare the analysis service:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r analysis/requirements.txt
TORCH_HOME="$PWD/.cache/torch" .venv/bin/python -m uvicorn analysis.server:app --host 127.0.0.1 --port 8000
```

The first startup downloads official pretrained weights and pinned MiDaS source into the model cache. Later starts reuse them. Downloads use `download.pytorch.org`, `download-r2.pytorch.org`, `codeload.github.com`, `github.com`, and GitHub release asset hosts. Preserve normal TLS verification and inherited proxy settings.

In a second terminal, from this directory:

```sh
npm ci
npm run dev -- --port 5173
```

Open port 5173 through your environment's port forwarding, or the address Vite prints when running locally. The frontend proxies `/api` to the Python server; no browser API key or cross-origin configuration is needed. `npm run build` builds both pages, and `npm run preview` serves the production build with the same API proxy. A static deployment needs an equivalent `/api` proxy to the analysis service.

In the current cloud environment, the prepared Python is `/workspace/.venvs/panorama-analysis/bin/python` and the populated model cache is `/workspace/.cache/torch`. For example:

```sh
cd /workspace/single-view-image-rectification/room-simulator
TORCH_HOME=/workspace/.cache/torch /workspace/.venvs/panorama-analysis/bin/python -m uvicorn analysis.server:app --host 127.0.0.1 --port 8000
```

There is no `src/main.py` in the original Python project. Photo mode starts at `index.html` → `src/photo.js`; the room demo starts at `room.html` → `src/main.js`. The original Python experiments remain separate in `../src`.

## Use it

1. Choose **Open a photo**, or **Try example photo** to use the repository's courtyard image. Uploads accept JPEG, PNG, and WebP. Photos are resized to a maximum of 1024 pixels per side before analysis.
2. The local models identify COCO objects and predict relative inverse depth. The interface outlines detections, grays the background, and constructs the point cloud. It does not segment exact object silhouettes. Objects outside the model's 80 COCO categories may not be recognized; zero detections is a valid result.
3. Click the photo to choose a gaze target. The head and eyes animate beside it; the photo crosshair, eyesight oval, and scene cone follow actual gaze. A small amber marker indicates a requested target while the gaze catches up or is limited. Head and eye yaw/pitch are shown separately. Arrow keys adjust the focused photo's gaze; **Follow the cursor continuously** tracks pointer motion instead.
4. Adjust the horizontal and vertical eyesight ranges. These are configurable angular ranges, not a physiological eye model. The projected oval clips at the photograph's boundaries; unseen directions cannot be synthesized.
5. Orbit and zoom the point cloud to inspect the reconstruction. **Save view** downloads the annotated 2D image with the current oval.

Images are analyzed by your local Python service. They are not sent to a cloud vision provider or retained by the server. SSDLite320 MobileNetV3 (torchvision / COCO) detects objects; MiDaS v2.1 small predicts relative depth. MiDaS source is pinned at commit `454597711a62eabcbf7d1e89f3fb9f569051ac9b`. The full MiDaS checkpoint loads strictly against the installed EfficientNet backbone; its stem activation layout is adapted in memory without editing downloaded source.

## What the reconstruction means

This is **2.5D**, a back-projection of visible image pixels. It does not reconstruct object backs, fill occlusions, recover the original camera's absolute world position, or provide a complete solid 3D model. Distortions in the monocular prediction remain visible in the point cloud.

The original camera sits at the 3D origin and looks down −Z, with +X right and +Y up. Gaze angles are relative to the photo center. The original camera's vertical field of view defaults to an explicit **60° assumption**. Set it from camera calibration when possible; it affects pixel rays, the reconstruction, gaze angles, and size estimates.

Without calibration, depth is in **arbitrary units**, relative nearness is normalized within the image, and metric distances/sizes are withheld. The uncalibrated point cloud uses `Z = 1 / (0.15 + 0.85 × nearness)` purely for visualization; these numbers are not meters.

For approximate metric results:

- Pick two image points at different predicted depths, preferably on clearly visible surfaces.
- Enter each point's known straight-line distance from the original camera, in meters.
- The app converts those ray distances to axial depth using the camera intrinsics and fits `1/Z = a × relative_inverse_depth + b`. Invalid or reversed reference orderings are rejected.
- Distance at the selected pixel and estimated visible object width/height then become available. The width/height estimate uses the object's central depth patch and assumes a front-facing surface. Hidden thickness is unknown. The physical eyesight range is the viewing-cone footprint on a plane perpendicular to gaze at the selected surface distance.

Two references resolve an assumed scale and offset; they do not correct all monocular-depth errors. Regions outside the positive calibrated range stay unknown. Changing the photo, rerunning analysis, or changing the camera FOV clears calibration. These outputs are estimates, not measurement-grade dimensions.

## Checks

```sh
npm test
npm run build
.venv/bin/python -m pip install -r analysis/requirements-dev.txt
TORCH_HOME="$PWD/.cache/torch" .venv/bin/python -m unittest discover -s tests -p '*_test.py' -v
```

Geometry and controller tests cover image rays, gaze angles, depth sampling, two-point metric calibration, invalid references, the projected oval, head/eye coordination, eye limits, and binocular convergence. API tests run actual inference on the courtyard photo, verify chair detections and finite depth, and reject malformed/tiny uploads. Browser validation also covers file upload, grayscale rendering, clicking, cursor following, the point cloud, calibration invalidation, PNG downloads, and mobile layout.

## Original 3D room

At `/room.html`, drag to turn the virtual head or focus the scene and use arrow keys. R / Reset view restores the camera. Eye height and FOV are adjustable. The crosshair shows exact ray-to-surface distance and known scene dimensions. The overhead map shows direction. The furnished room measures 6 × 7 × 3 m; no model inference is used for those known scene measurements.
