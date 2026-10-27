# Click-seeded exploratory visual search

A click on the analyzed photo now starts a **finite exploratory attention search** at that location. The model visits selected regions rather than scanning every pixel. This is a psychology-inspired demonstration; no parameters have been fitted to eye-tracking data, and it does not run the published EyeSyn or ScanDy algorithms.

## Use

1. Open or analyze a photo.
2. Keep **Click starts an attention search** enabled and click the desired starting point.
3. Watch the **Saccade / Fixation** phase, numbered scanpath, current target, and candidate coverage.
4. **Pause / Resume** holds the attention sequence; the head/eyes may finish settling on the current target. **Stop** retains the path. A new click starts a fresh search.
5. Choose **Recognized objects only** to exclude unlabeled visual regions, or leave **Objects + visual regions** selected for broader exploration.
6. Uncheck the click-search option for direct aiming. Arrow keys, an object-list selection, or cursor-following interrupt search and aim manually. Calibration point picking takes precedence over starting search.

Changing the photo or rerunning analysis rebuilds the candidate pool and clears the scanpath. Changing the attention scope clears it too. Changing the original camera FOV or eyesight range stops the current search; restart to use the new geometry. Metric calibration changes stop search to avoid mixing target distances during a fixation.

## Policy and psychological concepts

| Concept | Implementation |
| --- | --- |
| Starting fixation | The clicked location is the first target. If it lies in a candidate region, that region can be inspected immediately. |
| Object attraction | Detector confidence and a modest object preference weight recognized candidates. |
| Bottom-up visual salience | Coarsely sampled local luminance contrast, with a small color-contrast boost, proposes up to six separated unlabeled regions. Flat images produce no contrast candidates. |
| Spatial attention | Nearby targets and targets inside the current elliptical eyesight receive higher weights. Peripheral targets remain eligible, so the search can look beyond its initial field. |
| Inhibition of return | Completed candidates are removed from selection; locations near the last four fixations receive a soft penalty. |
| Saccades | The motor controller shifts gaze to the selected region. Travel time does not count as fixation time. |
| Fixations | Dwell begins only when actual gaze is within 0.65° of the target and is not rotation-limited. Dwell lasts roughly 0.45–1.1 seconds, depending on candidate size, confidence, and bounded variability. |
| Within-object inspection | Large objects or lower-confidence detections receive one additional fixation inside their box. This is a small gaze shift, not continuous random shaking. |
| Head/eye coordination | Small, visible shifts hold head orientation and use the eyes. Targets outside current eyesight, or beyond comfortable local eye eccentricity (25° yaw / 18° pitch), recruit the head. The existing eye limits still apply. |
| Search completion | The search stops after each candidate has been inspected or explicitly skipped as unreachable. It does not cycle indefinitely. |

Selection uses seeded weighted sampling, combining salience, object preference, angular distance, visibility, and recent-location inhibition. The seed is fixed at 17 for reproducible demonstrations. The resulting order is not simply detection confidence order. The head follows a recruited target with the existing slower controller while the eyes lead and compensate for the moving head.

A candidate that cannot be reached for 2.5 seconds, or cannot sustain a stable fixation within a six-second target budget, is marked **skipped**, never counted as inspected. This matters in **Eyes only** mode. The progress display distinguishes these outcomes. The fixation history includes the starting fixation and any additional within-object fixations, so fixation count can exceed the candidate count.

**Complete means candidate coverage**, not that all real objects, every part of a scene, or a participant's cognitive search have been understood. The current task is free exploration; there is no target-identity task such as finding a particular missing item. It uses neither a learned human attention policy nor an inference of the user's intentions. The scanpath and timings are inspectable behavior, not evidence of psychological validity.

## Why trees, windows, and doors lack labels

The current local SSDLite320 MobileNetV3 detector is trained on the **80 COCO object categories**. Chairs are included. General **tree**, **window**, and **door** categories are not; a `potted plant` category is not a general tree detector. Lowering the 45% confidence threshold cannot add categories the model was never trained to predict.

Other supported objects can also be missed because of small size, occlusion, unusual viewpoints, low contrast, the detector's 320-pixel internal input, or confidence filtering.

Detection is separate from MiDaS depth reconstruction. All sampled photo surfaces contribute to the point cloud, including unlabeled walls, foliage, windows, and doors. Lack of a semantic box does not mean the surface was removed, although monocular depth can distort it.

**Dashed blue regions** are unlabeled contrast cues that can attract gaze outside the COCO vocabulary. They are not automatic tree/window/door labels, instance segmentation, or complete object extents. A texture patch or shadow boundary may be selected. They do not increase the recognized-object count or receive invented category names or confidence scores.

A future semantic upgrade could use a local open-vocabulary detector (for example, OWLv2 or Grounding DINO queried for tree/window/door) or a broader scene segmentation model. That needs different weights, dependencies and validation; it is independent of the attention controller.

## References and relationship to the existing rig

See [head/eye simulation references](head-eye-simulation.md#eyesyn-and-scandy-references) for the reviewed EyeSyn and ScanDy repositories and papers. EyeSyn's separation of fixation sites, fixation durations, and gaze perturbations and ScanDy's separation of scene features, history, decisions, and gaze updates motivate the modular design. This controller is an original approximation and does not reproduce either paper's quantitative results.

Implementation: `src/attention-candidates.js` generates candidates, `src/attention-search.js` handles attention decisions and timing, `src/visual-field.js` tests angular visibility, and `src/head-eye-model.js` handles the physical gaze directions and head recruitment. The existing calibration, parallel uncalibrated eyes, metric convergence, and actual-gaze oval remain in use.
