# Single-View Image Rectification and World Reconstruction

**Pavel Stepanov**  
University of Miami  
Department of Electrical and Computer Engineering  
pas273@miami.edu

---

![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=flat-square)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg?style=flat-square)
![NumPy](https://img.shields.io/badge/NumPy-1.x-orange.svg?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg?style=flat-square)

---

## Interactive photo reconstruction prototype

The browser app in [`room-simulator/`](room-simulator/README.md) adds local object detection, monocular relative-depth reconstruction, and a virtual head aimed by clicking a photograph. It shows object outlines, a grayscale background, an eyesight oval, and an orbitable 3D point cloud. See its README for the Python analysis service and browser startup commands. The furnished 3D room demo remains available too.

## Overview

This project implements three fundamental techniques for geometric image rectification using projective geometry and homogeneous coordinates. The toolkit removes perspective and affine distortions from single-view photographs and enables metric reconstruction from images with known reference objects.

### Key Capabilities

- **Projective rectification:** Removes perspective distortion by mapping the vanishing line to infinity
- **Affine rectification:** Restores parallelism using vanishing point computation from parallel lines
- **Metric reconstruction:** Computes world coordinates from image points using Direct Linear Transform (DLT)

## Project Structure

```
single-view-image-rectification/
├── src/
│   ├── experiment1_projective.py    # Projective rectification
│   ├── experiment2_affine.py        # Affine rectification
│   ├── experiment3_world.py         # World plane reconstruction
│   └── utils.py                     # Core geometric functions
├── images/                          # Input images
├── results/                         # Output images and data
├── docs/                           # LaTeX report
└── requirements.txt                # Python dependencies
```

## Technical Implementation

### Core Functions

**Homogeneous Coordinate Operations:**

- `hcross()` - Computes cross product in homogeneous coordinates for line/point intersections
- `homoTrans()` - Applies 3×3 transformation matrices to point sets
- `compute_homography_dlt()` - Estimates planar homography using Direct Linear Transform

**Image Transformation:**

- `transform_image()` - Applies homography with automatic bounds calculation
- `draw_line_homogeneous()` - Visualizes lines in homogeneous representation
- `select_points_interactive()` - User interface for point selection

### Experiment 1: Projective Rectification

Removes perspective distortion by identifying the vanishing line from a rectangular object and mapping it to infinity.

**Method:**

1. Select four corners of a world-plane rectangle (e.g., TV screen, picture frame)
2. Compute two pairs of lines from opposite edges
3. Find vanishing points where parallel lines intersect
4. Calculate vanishing line through vanishing points
5. Apply homography H = [I | 0; l∞ᵀ] to move vanishing line to infinity

**Result:** Previously converging parallel lines become parallel in the rectified image.

### Experiment 2: Affine Rectification

Restores parallelism using two pairs of parallel lines to compute the vanishing line.

**Method:**

1. Select two pairs of parallel lines (four lines, eight endpoints)
2. Compute vanishing points for each parallel pair
3. Calculate vanishing line l∞ = v₁ × v₂
4. Apply homography to map vanishing line to canonical form [0, 0, 1]ᵀ

**Implementation Note:** This project uses parallel line pairs rather than orthogonal pairs, which provides improved robustness for architectural features with nearly-vertical edges.

**Result:** Architectural features (doorways, windows) maintain parallelism throughout the image.

### Experiment 3: World Plane Reconstruction

Computes metric properties using point correspondences between image and world coordinates.

**Method:**

1. Identify object with known dimensions (e.g., poster, paper, door)
2. Select training points (corners) and test points (edge midpoints)
3. Compute homography using DLT on training points
4. Validate reconstruction accuracy on independent test points

**Validation Results:**

- Training points: 0.000 inch error (perfect fit)
- Test points: 3.337 inch mean error (8.31% relative error)
- Performance consistent with literature for uncalibrated single-view metrology

## Installation

### Requirements

- Python 3.8+
- NumPy
- OpenCV (cv2)
- Matplotlib

### Setup

```bash
# Clone repository
git clone https://github.com/pstepanovum/single-view-image-rectification.git
cd single-view-image-rectification

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Interactive browser workflow

Use the [photo reconstruction app](room-simulator/README.md) for click-to-aim and depth visualization. There is no `src/main.py` launcher in this checkout. The original experiments below are standalone scripts and require a graphical display for mouse point selection.

### Individual Experiments

**Experiment 1: Projective Rectification**

```bash
python experiment1_projective.py ../images/your_image.jpg
```

Click 4 corners of a rectangular object to remove perspective distortion.

**Experiment 2: Affine Rectification**

```bash
python experiment2_affine.py ../images/your_image.jpg
```

Click 8 points defining two pairs of parallel lines to restore parallelism.

**Experiment 3: World Reconstruction**

```bash
python experiment3_world.py ../images/your_image.jpg width height unit
# Example: python experiment3_world.py ../images/poster.jpg 40.16 40.16 inches
```

Click 8 points (4 training + 4 test) to reconstruct world coordinates.

## Results

All outputs are saved to the `results/` directory:

- **Original images:** Annotated with selected points and computed geometry
- **Rectified images:** Transformed outputs showing corrected geometry
- **Comparison figures:** Side-by-side visualizations
- **Data files:** Numerical results and reconstruction accuracy (Experiment 3)

### Performance Benchmarks

| Experiment    | Input                    | Output                   | Key Metric                 |
| ------------- | ------------------------ | ------------------------ | -------------------------- |
| 1: Projective | TV screen (3648×5472 px) | Rectified (2115×5588 px) | Vanishing line → [0, 0, 1] |
| 2: Affine     | Wall/doorway             | Parallel edges restored  | VP₂ = [776.6, -35725.2]    |
| 3: Metric     | 40.16" poster            | World coordinates        | 8.31% test error           |

## Mathematical Background

### Projective Transformation

Points transform under homography **H** as:

```
λx' = Hx
```

where **x** = [x, y, 1]ᵀ in homogeneous coordinates.

### Direct Linear Transform (DLT)

For point correspondences (**xᵢ**, **Xᵢ**), the homography is estimated by solving:

```
Ah = 0
```

using Singular Value Decomposition (SVD).

### Vanishing Line Rectification

The homography that maps vanishing line **l**∞ to [0, 0, 1]ᵀ is:

```
H = [I | 0]
    [l∞ᵀ  ]
```

## Applications

- Architectural photography correction
- Document scanning and perspective removal
- Augmented reality marker tracking
- Real-world dimension measurement from photographs
- 3D reconstruction from calibrated images
- Building facade analysis

## Validation Methodology

Experiment 3 employs proper machine learning validation:

- **Training set:** 4 corner points used to compute homography
- **Test set:** 4 independent edge midpoints for validation
- **Cross-validation:** Ensures generalization beyond training data

This approach provides realistic error estimates compared to testing on training data.

## References

1. Hartley, R. & Zisserman, A. (2003). _Multiple View Geometry in Computer Vision_. Cambridge University Press.
2. Szeliski, R. (2022). _Computer Vision: Algorithms and Applications_. Springer.
3. Criminisi, A., Reid, I., & Zisserman, A. (2000). "Single view metrology." _International Journal of Computer Vision_, 40(2), 123-148.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
