"""
Experiment 2: Affine Rectification from Parallel Lines
ECE 738 - Project 2

Removes affine distortion by identifying the vanishing line (line at infinity)
from two pairs of parallel lines.

Usage:
    python experiment2_affine.py <image_path>
    
Example:
    python experiment2_affine.py ../images/2.jpg
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from utils import (hcross, draw_line_homogeneous, transform_image, 
                   compute_line_angle, save_comparison)


def select_parallel_lines(image, title="Select Parallel Lines"):
    """
    Interactive selection of two pairs of parallel lines.
    """
    points = []
    img_display = image.copy()
    
    instructions = [
        "RED Line 1: Click START",
        "RED Line 1: Click END",
        "RED Line 2: Click START (parallel to Line 1)",
        "RED Line 2: Click END",
        "BLUE Line 3: Click START",
        "BLUE Line 3: Click END",
        "BLUE Line 4: Click START (parallel to Line 3)",
        "BLUE Line 4: Click END"
    ]
    
    colors = [(0, 0, 255), (0, 0, 255), (0, 0, 255), (0, 0, 255),
              (255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0)]
    
    current_instruction = -1
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 8:
            points.append((x, y))
            
            cv2.circle(img_display, (x, y), 8, colors[len(points)-1], -1)
            cv2.circle(img_display, (x, y), 10, (255, 255, 255), 2)
            cv2.putText(img_display, str(len(points)), (x+15, y-15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, colors[len(points)-1], 3)
            
            # Draw lines as they're completed
            if len(points) == 2:
                cv2.line(img_display, points[0], points[1], (0, 0, 255), 3)
            elif len(points) == 4:
                cv2.line(img_display, points[2], points[3], (0, 0, 255), 3)
            elif len(points) == 6:
                cv2.line(img_display, points[4], points[5], (255, 0, 0), 3)
            elif len(points) == 8:
                cv2.line(img_display, points[6], points[7], (255, 0, 0), 3)
            
            cv2.imshow(title, img_display)
            print(f"✓ Point {len(points)}: ({x}, {y})")
    
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, 1200, 800)
    cv2.setMouseCallback(title, mouse_callback)
    cv2.imshow(title, img_display)
    
    print("\n" + "="*70)
    print("SELECT PARALLEL LINES")
    print("="*70)
    
    while len(points) < 8:
        if len(points) != current_instruction:
            current_instruction = len(points)
            print(f"→ {instructions[len(points)]}", flush=True)
        
        key = cv2.waitKey(50) & 0xFF
        if key == ord('q'):
            break
    
    print("\n" + "="*70)
    print("Complete! Press any key to continue...")
    print("="*70)
    cv2.waitKey(0)
    cv2.destroyWindow(title)
    
    return points


def affine_rectification(image_path, output_dir='../results'):
    """
    Perform affine rectification from pairs of parallel lines.
    
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
    print("EXPERIMENT 2: AFFINE RECTIFICATION")
    print("="*70)
    print("\nGoal: Remove affine distortion using parallel lines")
    print("\nSelect TWO PAIRS of PARALLEL lines:")
    print("  RED PAIR: Lines 1 & 2 (parallel to each other)")
    print("  BLUE PAIR: Lines 3 & 4 (parallel to each other)")
    print("\nExamples:")
    print("  • Floor tiles: opposite edges are parallel")
    print("  • Railway tracks: two rails are parallel")
    print("  • Building: vertical/horizontal edges")
    print("="*70 + "\n")
    
    # Interactive line selection
    points_list = select_parallel_lines(img, "Select Parallel Lines")
    
    if len(points_list) != 8:
        print(f"Error: Need 8 points, got {len(points_list)}")
        return None, None
    
    print("\nSelected lines:")
    print(f"  RED:  Line 1: {points_list[0]} → {points_list[1]}")
    print(f"        Line 2: {points_list[2]} → {points_list[3]}")
    print(f"  BLUE: Line 3: {points_list[4]} → {points_list[5]}")
    print(f"        Line 4: {points_list[6]} → {points_list[7]}")
    
    # Convert to homogeneous coordinates and compute lines
    print("\nComputing vanishing points...")
    
    # Red pair
    p1 = np.array([points_list[0][0], points_list[0][1], 1]).reshape(-1, 1)
    p2 = np.array([points_list[1][0], points_list[1][1], 1]).reshape(-1, 1)
    line1 = hcross(p1, p2)
    
    p3 = np.array([points_list[2][0], points_list[2][1], 1]).reshape(-1, 1)
    p4 = np.array([points_list[3][0], points_list[3][1], 1]).reshape(-1, 1)
    line2 = hcross(p3, p4)
    
    # Blue pair
    p5 = np.array([points_list[4][0], points_list[4][1], 1]).reshape(-1, 1)
    p6 = np.array([points_list[5][0], points_list[5][1], 1]).reshape(-1, 1)
    line3 = hcross(p5, p6)
    
    p7 = np.array([points_list[6][0], points_list[6][1], 1]).reshape(-1, 1)
    p8 = np.array([points_list[7][0], points_list[7][1], 1]).reshape(-1, 1)
    line4 = hcross(p7, p8)
    
    # Compute vanishing points
    vp1 = hcross(line1, line2)
    vp2 = hcross(line3, line4)
    
    print(f"  VP1 (Red):  [{vp1[0, 0]:.1f}, {vp1[1, 0]:.1f}]")
    print(f"  VP2 (Blue): [{vp2[0, 0]:.1f}, {vp2[1, 0]:.1f}]")
    
    # Compute vanishing line
    l_infinity = hcross(vp1, vp2)
    l_infinity = l_infinity / l_infinity[2, 0]
    
    print(f"\nVanishing line: [{l_infinity[0, 0]:.6f}, {l_infinity[1, 0]:.6f}, {l_infinity[2, 0]:.6f}]")
    
    # Visualize
    vis_original = img.copy()
    
    # Draw lines
    vis_original = draw_line_homogeneous(vis_original, line1, (0, 0, 255), 3)
    vis_original = draw_line_homogeneous(vis_original, line2, (0, 0, 255), 3)
    vis_original = draw_line_homogeneous(vis_original, line3, (255, 0, 0), 3)
    vis_original = draw_line_homogeneous(vis_original, line4, (255, 0, 0), 3)
    
    # Draw vanishing points if visible
    h, w = img.shape[:2]
    for vp, color, label in [(vp1, (0, 0, 255), 'VP1 (Red)'), 
                              (vp2, (255, 0, 0), 'VP2 (Blue)')]:
        x, y = int(vp[0, 0]), int(vp[1, 0])
        if -2000 < x < w+2000 and -2000 < y < h+2000:
            if 0 <= x < w and 0 <= y < h:
                cv2.circle(vis_original, (x, y), 15, color, -1)
                cv2.circle(vis_original, (x, y), 18, (255, 255, 255), 3)
                cv2.putText(vis_original, label, (x+25, y-20),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
    
    # Draw vanishing line
    vis_original = draw_line_homogeneous(vis_original, l_infinity, (0, 255, 0), 4)
    
    # Add labels
    cv2.putText(vis_original, "RED: Parallel Lines 1 & 2", (30, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    cv2.putText(vis_original, "BLUE: Parallel Lines 3 & 4", (30, 100),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 3)
    cv2.putText(vis_original, "GREEN: Vanishing Line", (30, 150),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
    
    # Construct homography: H = [I | 0; l_infinity']
    H = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [l_infinity[0, 0], l_infinity[1, 0], l_infinity[2, 0]]
    ])
    
    print("\nHomography H:")
    print(H)
    
    # Verify
    H_inv_T = np.linalg.inv(H).T
    l_inf_canonical = H_inv_T @ l_infinity
    print(f"Mapped to: [{l_inf_canonical[0,0]:.6f}, {l_inf_canonical[1,0]:.6f}, {l_inf_canonical[2,0]:.6f}] (should be [0, 0, 1])")
    
    # Apply transformation
    print("\nApplying rectification...")
    rectified, H_adjusted = transform_image(img, H, output_size=None)
    
    # Add label to rectified image
    vis_rectified = rectified.copy()
    cv2.putText(vis_rectified, "Affine Rectified", (30, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    
    # Save results
    base_name = Path(image_path).stem
    cv2.imwrite(f'{output_dir}/exp2_{base_name}_original.jpg', vis_original)
    cv2.imwrite(f'{output_dir}/exp2_{base_name}_rectified.jpg', vis_rectified)
    save_comparison(vis_original, vis_rectified,
                   'Original (Affine Distorted)',
                   'Rectified (Parallel Lines Restored)',
                   f'{output_dir}/exp2_{base_name}_comparison.png')
    
    print("\n" + "="*70)
    print("✓ EXPERIMENT 2 COMPLETE!")
    print("="*70)
    print(f"\nResults saved to {output_dir}/")
    print(f"  • exp2_{base_name}_original.jpg")
    print(f"  • exp2_{base_name}_rectified.jpg")
    print(f"  • exp2_{base_name}_comparison.png")
    print("\nMethod:")
    print("  1. Found vanishing points from parallel lines")
    print("  2. Computed vanishing line")
    print("  3. Mapped vanishing line to infinity")
    print("  4. Parallel lines now appear parallel")
    print("="*70 + "\n")
    
    return vis_original, vis_rectified


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUsage: python experiment2_affine.py <image_path>")
        print("\nExample:")
        print("  python experiment2_affine.py ../images/IMG_6742.jpeg")
        print("\nOr use relative path from src directory:")
        print("  cd src")
        print("  python experiment2_affine.py ../images/IMG_6742.jpeg\n")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        affine_rectification(image_path)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


import sys
import cv2
import numpy as np
from pathlib import Path
from utils import (hcross, draw_line_homogeneous, transform_image, 
                   select_points_interactive, compute_line_angle, save_comparison)


def affine_rectification(image_path, output_dir='../results'):
    """
    Perform affine rectification to restore orthogonality.
    
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
    print("EXPERIMENT 2: AFFINE RECTIFICATION")
    print("="*70)
    print("\nGoal: Make perpendicular lines actually perpendicular (90°)")
    print("\n" + "="*70)
    print("WHAT TO CLICK:")
    print("="*70)
    print()
    print("Pick TWO tiles and click on their corners (L-shapes):")
    print()
    print("  BLUE (Tile 1):        RED (Tile 2):")
    print("       [1]                   [5]")
    print("        │                     │")
    print("        │  (vertical)         │  (vertical)")
    print("       [2]                   [6]")
    print("        │                     │")
    print("   [3]──┴──[4]           [7]──┴──[8]")
    print("     (horizontal)          (horizontal)")
    print()
    print("IMPORTANT:")
    print("  • Points 1-2: ONE line (vertical edge of tile)")
    print("  • Points 3-4: DIFFERENT line (horizontal edge, meets at corner)")
    print("  • Points 5-8: Same idea on a DIFFERENT tile")
    print("  • DON'T click the same point twice!")
    print()
    print("="*70)
    print("Starting point selection...")
    print("="*70 + "\n")
    
    # Interactive point selection with live line preview
    from utils import select_points_with_lines
    points_list = select_points_with_lines(img, "Floor Tiles - Select 8 Points")
    
    if len(points_list) != 8:
        print(f"Error: Need exactly 8 points, got {len(points_list)}")
        return None, None
    
    # Validate points
    print("\n" + "="*70)
    print("VALIDATING YOUR POINTS...")
    print("="*70)
    
    warnings = []
    
    # Check if points within each line pair are reasonable
    line_pairs = [
        (0, 1, "Blue vertical (1-2)"),
        (2, 3, "Blue horizontal (3-4)"),
        (4, 5, "Red vertical (5-6)"),
        (6, 7, "Red horizontal (7-8)")
    ]
    
    for i, j, name in line_pairs:
        dist = np.sqrt((points_list[i][0] - points_list[j][0])**2 + 
                      (points_list[i][1] - points_list[j][1])**2)
        
        # If points are too far apart (> 1/4 of image), probably wrong
        img_diag = np.sqrt(img.shape[0]**2 + img.shape[1]**2)
        if dist > img_diag * 0.4:
            warnings.append(f"⚠️  {name}: Points are {dist:.0f} pixels apart - TOO FAR!")
            warnings.append(f"   You should be clicking on edges of ONE tile, not across the whole image!")
        elif dist < 50:
            warnings.append(f"⚠️  {name}: Points are only {dist:.0f} pixels apart - too close!")
    
    # Check for duplicate points
    for i in range(len(points_list)):
        for j in range(i+1, len(points_list)):
            dist = np.sqrt((points_list[i][0] - points_list[j][0])**2 + 
                          (points_list[i][1] - points_list[j][1])**2)
            if dist < 10:
                warnings.append(f"⚠️  Points {i+1} and {j+1} are the same spot ({dist:.1f} pixels apart)!")
    
    if warnings:
        print("\n🚨 PROBLEMS DETECTED:")
        for w in warnings:
            print(w)
        print("\n" + "="*70)
        print("YOUR POINTS ARE WRONG! Here's what you should do:")
        print("="*70)
        print()
        print("Look at your floor tiles. Pick ONE tile.")
        print("Click on the CORNER of that tile like this:")
        print()
        print("      [1] ← Top of edge")
        print("       |")
        print("       |  (this is ONE tile edge, maybe 50-200 pixels)")
        print("       |")
        print("      [2] ← Bottom of SAME edge")
        print("       |")
        print("  [3]─┴─[4] ← Left and right of PERPENDICULAR edge")
        print()
        print("DO NOT click across the entire image!")
        print("DO click on edges of a SINGLE tile corner!")
        print()
        print("Continuing anyway, but results will be poor...")
        print("="*70)
    else:
        print("✓ Points look reasonable!")
    
    print("\nSelected points:")
    print("\nBLUE PAIR (Tile 1):")
    print(f"  Points 1-2 (Vertical edge):   {points_list[0]} to {points_list[1]}")
    print(f"  Points 3-4 (Horizontal edge): {points_list[2]} to {points_list[3]}")
    print("\nRED PAIR (Tile 2):")
    print(f"  Points 5-6 (Vertical edge):   {points_list[4]} to {points_list[5]}")
    print(f"  Points 7-8 (Horizontal edge): {points_list[6]} to {points_list[7]}")
    
    # Convert to homogeneous coordinates
    # Blue pair
    p1_l1 = np.array([points_list[0][0], points_list[0][1], 1])
    p2_l1 = np.array([points_list[1][0], points_list[1][1], 1])
    p1_m1 = np.array([points_list[2][0], points_list[2][1], 1])
    p2_m1 = np.array([points_list[3][0], points_list[3][1], 1])
    
    # Red pair
    p1_l2 = np.array([points_list[4][0], points_list[4][1], 1])
    p2_l2 = np.array([points_list[5][0], points_list[5][1], 1])
    p1_m2 = np.array([points_list[6][0], points_list[6][1], 1])
    p2_m2 = np.array([points_list[7][0], points_list[7][1], 1])
    
    # Compute the four lines
    print("\nComputing lines...")
    l1 = hcross(p1_l1.reshape(-1, 1), p2_l1.reshape(-1, 1))
    m1 = hcross(p1_m1.reshape(-1, 1), p2_m1.reshape(-1, 1))
    l2 = hcross(p1_l2.reshape(-1, 1), p2_l2.reshape(-1, 1))
    m2 = hcross(p1_m2.reshape(-1, 1), p2_m2.reshape(-1, 1))
    
    # Visualize
    vis_original = img.copy()
    
    # Draw blue pair with labels
    for i, pt in enumerate(points_list[0:2]):
        cv2.circle(vis_original, pt, 8, (255, 0, 0), -1)
        cv2.putText(vis_original, str(i+1), (pt[0]+12, pt[1]-12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    for i, pt in enumerate(points_list[2:4], start=2):
        cv2.circle(vis_original, pt, 8, (255, 0, 0), -1)
        cv2.putText(vis_original, str(i+1), (pt[0]+12, pt[1]-12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    vis_original = draw_line_homogeneous(vis_original, l1, (255, 0, 0), 3)
    vis_original = draw_line_homogeneous(vis_original, m1, (255, 0, 0), 3)
    
    # Add label for blue pair
    cv2.putText(vis_original, "BLUE PAIR (Tile 1)", (30, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 3)
    cv2.putText(vis_original, "Points 1-2: Vertical", (30, 90),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    cv2.putText(vis_original, "Points 3-4: Horizontal", (30, 120),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    # Draw red pair with labels
    for i, pt in enumerate(points_list[4:6], start=4):
        cv2.circle(vis_original, pt, 8, (0, 0, 255), -1)
        cv2.putText(vis_original, str(i+1), (pt[0]+12, pt[1]-12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    for i, pt in enumerate(points_list[6:8], start=6):
        cv2.circle(vis_original, pt, 8, (0, 0, 255), -1)
        cv2.putText(vis_original, str(i+1), (pt[0]+12, pt[1]-12),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    vis_original = draw_line_homogeneous(vis_original, l2, (0, 0, 255), 3)
    vis_original = draw_line_homogeneous(vis_original, m2, (0, 0, 255), 3)
    
    # Add label for red pair
    cv2.putText(vis_original, "RED PAIR (Tile 2)", (30, 180),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
    cv2.putText(vis_original, "Points 5-6: Vertical", (30, 220),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(vis_original, "Points 7-8: Horizontal", (30, 250),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Compute angles before rectification
    angle1_orig = compute_line_angle(l1, m1)
    angle2_orig = compute_line_angle(l2, m2)
    
    print(f"\nAngles BEFORE rectification:")
    print(f"  Blue pair (L1 ⊥ M1): {angle1_orig:.2f}°")
    print(f"  Red pair (L2 ⊥ M2): {angle2_orig:.2f}°")
    
    # Build constraint matrix F
    # For perpendicular lines l and m: l^T * S * m = 0
    # This gives: l1*m1*s11 + (l1*m2 + l2*m1)*s12 + l2*m2*s22 = 0
    
    print("\nComputing Image of Absolute Conic (S)...")
    F = np.zeros((2, 3))
    
    for i, (l, m) in enumerate([(l1, m1), (l2, m2)]):
        l_flat = l.flatten()
        m_flat = m.flatten()
        F[i, :] = [l_flat[0]*m_flat[0], 
                   l_flat[0]*m_flat[1] + l_flat[1]*m_flat[0], 
                   l_flat[1]*m_flat[1]]
    
    print("Constraint matrix F:")
    print(F)
    
    # Solve for s using cross product
    s = np.cross(F[0, :], F[1, :])
    
    # Form symmetric matrix S
    S = np.array([[s[0], s[1]], [s[1], s[2]]])
    
    # Check for numerical issues
    if np.linalg.norm(S) < 1e-10:
        print("\n" + "!"*70)
        print("⚠️  WARNING: S matrix is nearly zero!")
        print("!"*70)
        print("\nPossible causes:")
        print("  1. You clicked the same point twice (Points 1 and 3, or 5 and 7)")
        print("  2. Lines are already very close to perpendicular")
        print("  3. Points don't form proper L-shapes")
        print("\nCurrent angles:")
        print(f"  Blue pair: {angle1_orig:.1f}° (goal: 90°)")
        print(f"  Red pair: {angle2_orig:.1f}° (goal: 90°)")
        
        if abs(90 - angle1_orig) > 10 or abs(90 - angle2_orig) > 10:
            print("\n❌ Angles are NOT close to 90°, but S matrix is zero.")
            print("   This means your points don't form proper orthogonal pairs.")
            print("\n💡 SOLUTION: Re-run and make sure:")
            print("   • Points 1-2 are on ONE edge (vertical)")
            print("   • Points 3-4 are on a DIFFERENT edge (horizontal)")
            print("   • These two edges meet at a corner!")
            print("   • Same for points 5-8 on a different tile")
            print("\nApplying identity transformation (no change)...")
        else:
            print("\n✓ Angles are already close to 90° - minimal correction needed")
        
        S = np.eye(2)
    else:
        S = S / np.linalg.norm(S)
        # Ensure positive definite
        x = np.random.rand(2)
        if x @ S @ x.T < 0:
            S = -S
    
    print("\nImage of Absolute Conic S:")
    print(S)
    
    # Decompose S = K * K'
    print("\nDecomposing S = K * K'...")
    eigenvalues, eigenvectors = np.linalg.eig(S)
    
    # Handle negative eigenvalues
    if np.any(eigenvalues < 0):
        print("Warning: Negative eigenvalues detected, taking absolute values")
        eigenvalues = np.abs(eigenvalues)
    
    # Compute K
    E = np.sqrt(np.diag(eigenvalues))
    V = eigenvectors @ E
    
    # Hartley's rotation to diagonalize
    ct = V[1, 1] / np.sqrt(V[1, 0]**2 + V[1, 1]**2)
    st = -V[1, 0] / np.sqrt(V[1, 0]**2 + V[1, 1]**2)
    Q = np.array([[ct, -st], [st, ct]])
    
    K1 = V @ Q
    diag_rectify = np.diag(np.sign(np.diag(K1)))
    K = K1 @ diag_rectify
    
    print("\nRectification matrix K:")
    print(K)
    
    # Form homography
    H = np.vstack([np.hstack([K, np.zeros((2, 1))]), [0, 0, 1]])
    H = np.linalg.inv(H)
    
    print("\nHomography H:")
    print(H)
    
    # Apply transformation
    print("\nApplying transformation...")
    h, w = img.shape[:2]
    rectified, H_adjusted = transform_image(img, H, output_size=None)
    
    # Transform lines to verify using the adjusted homography
    l1_t = H_adjusted.T @ l1
    m1_t = H_adjusted.T @ m1
    l2_t = H_adjusted.T @ l2
    m2_t = H_adjusted.T @ m2
    
    # Visualize rectified
    vis_rectified = rectified.copy()
    vis_rectified = draw_line_homogeneous(vis_rectified, l1_t, (255, 0, 0), 2)
    vis_rectified = draw_line_homogeneous(vis_rectified, m1_t, (255, 0, 0), 2)
    vis_rectified = draw_line_homogeneous(vis_rectified, l2_t, (0, 0, 255), 2)
    vis_rectified = draw_line_homogeneous(vis_rectified, m2_t, (0, 0, 255), 2)
    
    # Compute angles after rectification
    angle1_rect = compute_line_angle(l1_t, m1_t)
    angle2_rect = compute_line_angle(l2_t, m2_t)
    
    print(f"\nAngles AFTER rectification:")
    print(f"  Blue pair (L1 ⊥ M1): {angle1_rect:.2f}°")
    print(f"  Red pair (L2 ⊥ M2): {angle2_rect:.2f}°")
    
    # Add angle info to images - make it prominent
    h_img = vis_original.shape[0]
    
    # Add white background box for text
    cv2.rectangle(vis_original, (10, h_img-100), (500, h_img-10), (255, 255, 255), -1)
    cv2.rectangle(vis_original, (10, h_img-100), (500, h_img-10), (0, 0, 0), 2)
    
    cv2.putText(vis_original, f"BEFORE Rectification:", (20, h_img-75),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(vis_original, f"Blue: {angle1_orig:.1f}deg  Red: {angle2_orig:.1f}deg", 
               (20, h_img-45),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(vis_original, f"(Goal: 90deg for both)", (20, h_img-20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 2)
    
    # Add to rectified image
    cv2.rectangle(vis_rectified, (10, h_img-100), (500, h_img-10), (255, 255, 255), -1)
    cv2.rectangle(vis_rectified, (10, h_img-100), (500, h_img-10), (0, 0, 0), 2)
    
    cv2.putText(vis_rectified, f"AFTER Rectification:", (20, h_img-75),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(vis_rectified, f"Blue: {angle1_rect:.1f}deg  Red: {angle2_rect:.1f}deg", 
               (20, h_img-45),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # Color code - green if good, red if bad
    color1 = (0, 200, 0) if abs(90 - angle1_rect) < 5 else (0, 0, 200)
    color2 = (0, 200, 0) if abs(90 - angle2_rect) < 5 else (0, 0, 200)
    
    if abs(90 - angle1_rect) < 5 and abs(90 - angle2_rect) < 5:
        cv2.putText(vis_rectified, f"SUCCESS!", (20, h_img-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
    else:
        cv2.putText(vis_rectified, f"Improvement: {abs(90-angle1_orig)-abs(90-angle1_rect):.1f}deg", 
                   (20, h_img-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 2)
    
    # Save results
    base_name = Path(image_path).stem
    cv2.imwrite(f'{output_dir}/exp2_{base_name}_original.jpg', vis_original)
    cv2.imwrite(f'{output_dir}/exp2_{base_name}_rectified.jpg', vis_rectified)
    save_comparison(vis_original, vis_rectified,
                   f'BEFORE: Angles {angle1_orig:.1f}° and {angle2_orig:.1f}° (Goal: 90°)',
                   f'AFTER: Angles {angle1_rect:.1f}° and {angle2_rect:.1f}°',
                   f'{output_dir}/exp2_{base_name}_comparison.png')
    
    print("\n" + "="*70)
    print("✓ EXPERIMENT 2 COMPLETE!")
    print("="*70)
    print(f"\nResults saved to {output_dir}/")
    print(f"  • exp2_{base_name}_original.jpg")
    print(f"  • exp2_{base_name}_rectified.jpg")
    print(f"  • exp2_{base_name}_comparison.png")
    print("\nWhat happened:")
    print("  • Identified two pairs of orthogonal lines")
    print("  • Computed Image of Absolute Conic (IAC)")
    print("  • Applied transformation to restore 90° angles")
    print(f"  • Improvement: {abs(90-angle1_orig):.1f}° → {abs(90-angle1_rect):.1f}° error")
    print("="*70 + "\n")
    
    return vis_original, vis_rectified


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUsage: python experiment2_affine.py <image_path>")
        print("\nExample:")
        print("  python experiment2_affine.py ../images/IMG_6742.jpeg")
        print("\nOr use relative path from src directory:")
        print("  cd src")
        print("  python experiment2_affine.py ../images/IMG_6742.jpeg\n")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        affine_rectification(image_path)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)