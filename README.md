# Single-View Planar Reconstruction and Perspective Rectification

**Pavel Stepanov**  
**pas273@miami.edu**

---

![MATLAB](https://img.shields.io/badge/MATLAB-%23ED8B00.svg?style=for-the-badge&logo=MathWorks&logoColor=white)
![Computer Vision](https://img.shields.io/badge/Computer_Vision-0078D4?style=for-the-badge)
![Mathematics](https://img.shields.io/badge/Linear_Algebra-CC0000?style=for-the-badge)

---

## Overview

**This toolkit provides a robust framework for geometric image rectification. By leveraging homogeneous coordinates and projective geometry, the system removes perspective distortion from single-view photographs, enabling accurate planar measurements and world-coordinate reconstruction.**

## Core Technical Components

### 1. Geometric Primitive Manipulation

- **hcross.m:** Performs cross products in homogeneous coordinates to find intersections of lines or the line passing through two points, normalized to the $z=1$ plane.
- **homoTrans.m:** Executes 3x3 transformation matrices on $n$-dimensional point sets.
- **hline.m:** A visualization utility for plotting 2D homogeneous lines within the current axis limits.

### 2. Image Warping and Transformation

- **imTrans.m:** The primary engine for applying geometric transformations to image data. It handles both grayscale and RGB channels, managing origin shifts and bounding box calculations.
- **Bilinear Interpolation:** Utilizes `interp2` to ensure smooth pixel mapping during the inverse transformation process, preventing aliasing and gaps in the rectified output.

### 3. Projective Rectification Workflow

**The main implementation script (`proj2affine.m`) follows a standard computer vision pipeline:**

- **Point Selection:** User identifies four points forming a world-plane rectangle.
- **Vanishing Point Estimation:** Calculates the intersection of parallel lines in the image plane using homogeneous cross products.
- **Vanishing Line Calculation:** Defines the line at infinity ($L_\infty$) within the projected image.
- **Homography Application:** Constructs and applies the transformation matrix $H$ to map the vanishing line back to infinity, effectively removing the projective component.

## Usage

**1. Load the target image (e.g., architectural photography).**
**2. Identify two sets of parallel lines on a single plane.**
**3. Execute the rectification script to compute the homography.**
**4. The system outputs a rectified image where parallel world lines are parallel in the image plane, and aspect ratios are restored.**

## License

**This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.**
