# Head and eye movement beside the photograph

The photo page now has a procedural Three.js mannequin with independently articulated eyes. Clicking a pixel chooses a target direction from the original camera. The animation coordinates the eyes and head while the oval, photo crosshair, numeric readouts, and reconstructed-scene cone follow the **actual combined gaze**.

## Controls

- **Head + eyes**: eyes turn quickly toward the target; the head follows a larger shift after a short delay. Eye rotation is recomputed relative to the moving head so gaze stays near the target as the head catches up.
- **Eyes only**: the head returns to neutral and stays there. Eye rotation is limited to ±35° horizontally and ±25° vertically. When a requested target exceeds those demonstration limits, the crosshair and oval stop at the actual gaze and the amber marker shows the requested point. The phase label reports **Eye limit**.
- **Front ¾ / Behind / Side**: change the external observer camera. In front view, the mannequin faces you, so its right appears on your left. Dragging the avatar orbits the observer; it does not move the head's gaze target.
- **Spatial visual search**: a click seeds an exploratory sequence of saccades and fixations, weighted by objects, contrast, angular proximity and history. It finishes at candidate coverage. See [the attention policy](spatial-attention.md) for phases, inhibition of return, completion, and limits. Disable click-search for direct aiming. Manual arrow-key, pointer-following, or listed-object aiming interrupts search.
- **Instant motion**: removes transition animation. It defaults on when the browser requests reduced motion.

The avatar's green lines show the left and right gaze directions; the amber line shows head-forward. The numeric head angles are relative to the original photo camera. Each eye's angles are relative to the head. Yaw is positive right and pitch positive up. Roll and head translation are not modeled.

## Depth and binocular convergence

The camera is the midpoint between the two eyes. The illustrative interpupillary distance is **64 mm**. For a metric-calibrated target at camera distance D:

1. Build the common target point from the selected pixel ray multiplied by D.
2. Rotate each eye origin by the current head orientation.
3. Compute each eye's own direction to the same target and express it in head coordinates.
4. Apply the eye rotation limits and animate each eye independently.

This gives stronger convergence for nearer targets. Without valid metric depth, both eyes use parallel directions; the system does not treat arbitrary reconstruction units as meters. Estimated targets closer than 0.2 m, farther than 150 m, or outside the positive calibrated range do not enable convergence. Depth uncertainty still affects the convergence estimate. The binocular gaze displayed in the photo uses the normalized mean of the two eye directions.

## Animation assumptions

These parameters are transparent demonstration choices. They have not been fitted to human recordings:

| Parameter | Value |
| --- | --- |
| Head share of target yaw / pitch when recruited | 65% / 60% |
| Head rotation limits | ±60° yaw / ±40° pitch |
| Head onset delay after a substantial target change | 90 ms |
| Head smoothing time constant / speed cap | 240 ms / 110° per second |
| Eye smoothing time constant / speed cap | 25 ms / 700° per second |
| Eye rotation limits | ±35° yaw / ±25° pitch |
| Interpupillary distance | 64 mm |

The controller includes compensation for head rotation by continuously recalculating the required local eye direction. It does not implement the full vestibular system, visual suppression during saccades, microsaccade statistics, accommodation, a physiological retinal sensitivity map, or biomechanical muscles. The face is a stylized procedural mannequin, and its shape is not a subject-specific anatomical reconstruction.

## EyeSyn and ScanDy references

The requested projects were reviewed as references; this implementation is independent and does not run their models or copy their code.

- [EyeSyn / EyeSynResource](https://github.com/EyeSyn/EyeSynResource), reviewed at `f0c6117eccbfcd432949916464e1ee2ffe191bef`. Lan, Scargill & Gorlatova, *EyeSyn: Psychology-inspired Eye Movement Synthesis for Gaze-based Activity Recognition*, IPSN 2022. Its [README](https://github.com/EyeSyn/EyeSynResource/blob/f0c6117eccbfcd432949916464e1ee2ffe191bef/README.md) describes activity-dependent gaze generation. The static-scene MATLAB example separates selected fixation locations, sampled fixation durations, and small gaze perturbations. This is useful for a future realistic fixation/noise generator; the present explicit-target controller does not reproduce that generator.
- [ScanDy](https://github.com/rederoth/ScanDy), reviewed at `a672ebf4072dd37e455ac794ef9d64a011b4a9c7`. Roth, Rolfs, Hellwich & Obermayer, *Objects guide human gaze behavior in dynamic real-world scenes*, PLOS Computational Biology 2023. Its [model base](https://github.com/rederoth/ScanDy/blob/a672ebf4072dd37e455ac794ef9d64a011b4a9c7/scandy/models/model.py) separates decision-making and gaze updates, tracks scanpath history, and accounts for saccade duration. Its object-based gaze selection is a useful reference for a future scanpath controller. The current exploratory attention controller uses its own candidate weighting and fixation timing; it is not ScanDy's evidence-accumulation model.

For the immediate interactive task, a small browser controller keeps the local Windows setup unchanged. The target-selection layer can later accept actual EyeSyn/ScanDy trajectories without replacing the rig or reconstruction.

## How the current 3D reconstruction works

This project uses **MiDaS v2.1 small plus pinhole-camera back-projection**, rendered with Three.js. Bayes3D is not a dependency.

1. SSDLite320 MobileNetV3 detects object categories and 2D boxes.
2. MiDaS predicts relative inverse depth from the photograph.
3. Convert the relative map to axial Z depth. Without calibration the scale is arbitrary; two known-distance references optionally fit inverse-depth scale and offset.
4. Use the original camera's assumed or configured field of view to compute focal lengths. Back-project each sampled pixel:

   ```text
   X = (pixel_x - center_x) × Z / focal_x
   Y = (center_y - pixel_y) × Z / focal_y
   point = (X, Y, -Z)
   ```

5. Assign image colors to those 3D points and display the visible-surface point cloud.

This is a 2.5D reconstruction: there are no inferred backs of objects, complete meshes, object pose inference, or recovered absolute world camera pose. For more accurate geometry, calibrated multi-view photographs or measured RGB-D input would be the next useful upgrade. Head/eye simulation is separate from the choice of reconstruction method.

## Validation

`npm test` includes controller tests for eyes leading the head, coordinated target alignment, eye limits, independent binocular rays intersecting the metric target, parallel uncalibrated gaze, pixel projection, and reset behavior. Browser checks exercise the same states alongside real photo analysis, finite attention search and interruption, initial image painting, observer presets, reduced motion, and responsive layout. Passing these verifies implementation behavior; it does not validate the model against human eye-tracking data.
