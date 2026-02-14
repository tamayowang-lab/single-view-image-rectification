"""
Experiment 1: Projective Rectification
ECE 738 - Project 2

Removes perspective distortion by identifying vanishing points and transforming
the vanishing line to infinity.

Usage:
    python experiment1_projective.py <image_path>
    
Example:
    python experiment1_projective.py ../images/1.jpg
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from utils import hcross, draw_line_homogeneous, transform_image, select_points_interactive, save_comparison


def projective_rectification(image_path, output_dir='../results'):
    """
    Perform projective rectification on an image.
    
    Args:
        image_path: Path to input image
        output_dir: Directory to save results
    
    Returns:
        (original_annotated, rectified) images
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    print("\n" + "="*70)
    print("EXPERIMENT 1: PROJECTIVE RECTIFICATION")
    print("="*70)
    print("\nGoal: Remove perspective distortion")
    print("\nInstructions:")
    print("  Select 4 corners of a RECTANGLE in 3D space")
    print("  (e.g., corners of a building, door, window)")
    print("\nFor RAILWAY TRACKS:")
    print("  Pick 4 points that form a rectangle between the rails:")
    print("    • Points 1 & 2: On left rail (near and far)")
    print("    • Points 3 & 4: On right rail (far and near)")
    print("  OR pick corners of a railway sleeper (tie) at two locations")
    print("\nClick in this order:")
    print("  1. Top-left corner")
    print("  2. Top-right corner")
    print("  3. Bottom-right corner")
    print("  4. Bottom-left corner")
    print("\nThese should form two pairs of PARALLEL lines in real world")
    print("="*70 + "\n")
    
    # Interactive point selection
    points_list = select_points_interactive(img, 4, "Select 4 Corners of Rectangle")
    
    if len(points_list) != 4:
        print(f"Error: Need exactly 4 points, got {len(points_list)}")
        return None, None
    
    # Convert to homogeneous coordinates
    p = np.array([[pt[0], pt[1], 1] for pt in points_list]).T
    
    print("\nSelected points:")
    for i, pt in enumerate(points_list):
        print(f"  Point {i+1}: ({pt[0]}, {pt[1]})")
    
    # Visualize selected points
    vis_original = img.copy()
    colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0)]
    labels = ['TL', 'TR', 'BR', 'BL']
    
    for i in range(4):
        pt = (int(p[0, i]), int(p[1, i]))
        cv2.circle(vis_original, pt, 8, colors[i], -1)
        cv2.putText(vis_original, f"{i+1}({labels[i]})", (pt[0]+15, pt[1]-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, colors[i], 2)
    
    # Compute lines through opposite edges
    print("\nComputing lines...")
    l1 = hcross(p[:, 0:1], p[:, 1:2])  # Top edge (1-2)
    l2 = hcross(p[:, 2:3], p[:, 3:4])  # Bottom edge (3-4)
    m1 = hcross(p[:, 1:2], p[:, 2:3])  # Right edge (2-3)
    m2 = hcross(p[:, 3:4], p[:, 0:1])  # Left edge (4-1)
    
    # Draw lines on visualization
    vis_original = draw_line_homogeneous(vis_original, l1, (255, 0, 0), 2)
    vis_original = draw_line_homogeneous(vis_original, l2, (255, 0, 0), 2)
    vis_original = draw_line_homogeneous(vis_original, m1, (0, 255, 0), 2)
    vis_original = draw_line_homogeneous(vis_original, m2, (0, 255, 0), 2)
    
    # Compute vanishing points (where parallel lines meet)
    print("Computing vanishing points...")
    van1 = hcross(l1, l2)  # Horizontal vanishing point
    van2 = hcross(m1, m2)  # Vertical vanishing point
    
    print(f"\nVanishing Point 1 (horizontal): [{van1[0, 0]:.1f}, {van1[1, 0]:.1f}]")
    print(f"Vanishing Point 2 (vertical): [{van2[0, 0]:.1f}, {van2[1, 0]:.1f}]")
    
    # Draw vanishing points if within reasonable bounds
    h, w = img.shape[:2]
    for vp, color, label in [(van1, (255, 0, 255), 'VP1'), 
                              (van2, (0, 255, 255), 'VP2')]:
        x, y = int(vp[0, 0]), int(vp[1, 0])
        if -2000 < x < w+2000 and -2000 < y < h+2000:
            if 0 <= x < w and 0 <= y < h:
                cv2.circle(vis_original, (x, y), 12, color, -1)
                cv2.circle(vis_original, (x, y), 14, (255, 255, 255), 2)
                cv2.putText(vis_original, label, (x+20, y-15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    
    # Compute vanishing line (horizon)
    print("Computing vanishing line...")
    l_vanishing = hcross(van1, van2)
    l_vanishing = l_vanishing / l_vanishing[2, 0]
    
    print(f"Vanishing Line: [{l_vanishing[0, 0]:.6f}, {l_vanishing[1, 0]:.6f}, {l_vanishing[2, 0]:.6f}]")
    
    # Draw vanishing line
    vis_original = draw_line_homogeneous(vis_original, l_vanishing, (255, 255, 255), 3)
    cv2.putText(vis_original, "Vanishing Line", (20, h-20),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    
    # Construct homography to move vanishing line to infinity
    # H maps l_vanishing to [0, 0, 1] (line at infinity)
    H = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [l_vanishing[0, 0], l_vanishing[1, 0], l_vanishing[2, 0]]
    ])
    
    print("\nHomography H:")
    print(H)
    
    # Apply transformation
    print("\nApplying transformation...")
    # Don't constrain output size - let it be as large as needed
    rectified, H_adjusted = transform_image(img, H, output_size=None)
    
    print(f"\nOutput image size: {rectified.shape[1]} × {rectified.shape[0]} pixels")
    print(f"Original image size: {w} × {h} pixels")
    
    # Save results
    base_name = Path(image_path).stem
    cv2.imwrite(f'{output_dir}/exp1_{base_name}_original.jpg', vis_original)
    cv2.imwrite(f'{output_dir}/exp1_{base_name}_rectified.jpg', rectified)
    save_comparison(vis_original, rectified, 
                   'Original (Perspective Distortion)', 
                   'Rectified (Parallel Lines)',
                   f'{output_dir}/exp1_{base_name}_comparison.png')
    
    print("\n" + "="*70)
    print("✓ EXPERIMENT 1 COMPLETE!")
    print("="*70)
    print(f"\nResults saved to {output_dir}/")
    print(f"  • exp1_{base_name}_original.jpg")
    print(f"  • exp1_{base_name}_rectified.jpg")
    print(f"  • exp1_{base_name}_comparison.png")
    print("\nWhat happened:")
    print("  • Identified vanishing points where parallel lines converge")
    print("  • Computed vanishing line (horizon)")
    print("  • Applied transformation to move vanishing line to infinity")
    print("  • Result: Previously converging lines are now parallel!")
    print("="*70 + "\n")
    
    return vis_original, rectified


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUsage: python experiment1_projective.py <image_path>")
        print("\nExample:")
        print("  python experiment1_projective.py ../images/1.jpg")
        print("\nOr use relative path from src directory:")
        print("  cd src")
        print("  python experiment1_projective.py ../images/1.jpg\n")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        projective_rectification(image_path)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)