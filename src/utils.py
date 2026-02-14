import numpy as np
import cv2


def hcross(a, b):
    """
    Homogeneous cross product, normalized to z=1.
    
    Args:
        a, b: 3D homogeneous vectors (can be points or lines)
    
    Returns:
        Normalized cross product (line through two points, or intersection of two lines)
    """
    c = np.cross(a.flatten(), b.flatten())
    if abs(c[2]) > 1e-10:
        c = c / c[2]
    return c.reshape(-1, 1)


def homoTrans(H, points):
    """
    Apply homogeneous transformation to points.
    
    Args:
        H: 3x3 transformation matrix
        points: 3xN matrix of homogeneous points
    
    Returns:
        Transformed points, normalized to z=1
    """
    transformed = H @ points
    # Normalize to z=1 plane
    transformed[0, :] = transformed[0, :] / transformed[2, :]
    transformed[1, :] = transformed[1, :] / transformed[2, :]
    transformed[2, :] = np.ones(points.shape[1])
    return transformed


def compute_homography_dlt(world_points, image_points):
    """
    Compute homography using Direct Linear Transform (DLT).
    Maps world coordinates to image coordinates.
    
    Args:
        world_points: Nx2 array of world coordinates
        image_points: Nx2 array of image coordinates
    
    Returns:
        3x3 homography matrix H such that image = H * world
    """
    X = world_points[:, 0]
    Y = world_points[:, 1]
    x = image_points[:, 0]
    y = image_points[:, 1]
    
    # Build the A matrix (2n x 9)
    # We want to solve: [x, y, 1]^T = H [X, Y, 1]^T
    A = []
    for i in range(len(X)):
        A.append([-X[i], -Y[i], -1, 0, 0, 0, x[i]*X[i], x[i]*Y[i], x[i]])
        A.append([0, 0, 0, -X[i], -Y[i], -1, y[i]*X[i], y[i]*Y[i], y[i]])
    
    A = np.array(A)
    
    # Solve using SVD
    U, S, Vt = np.linalg.svd(A)
    h = Vt[-1, :]
    
    # Reshape to 3x3
    H = h.reshape(3, 3)
    
    # Normalize
    H = H / H[2, 2]
    
    return H


def transform_image(img, H, output_size=None):
    """
    Apply homogeneous transformation to an image with proper bounds calculation.
    
    Args:
        img: Input image
        H: 3x3 transformation matrix
        output_size: Optional (width, height) for output
    
    Returns:
        Transformed image, adjusted homography with translation
    """
    h, w = img.shape[:2]
    
    # Find where the corners of the image end up after transformation
    corners = np.array([
        [0, 0, 1],
        [w, 0, 1],
        [w, h, 1],
        [0, h, 1]
    ]).T
    
    # Transform corners
    transformed_corners = H @ corners
    # Normalize
    transformed_corners[0, :] = transformed_corners[0, :] / transformed_corners[2, :]
    transformed_corners[1, :] = transformed_corners[1, :] / transformed_corners[2, :]
    
    # Find bounding box of transformed image
    min_x = np.min(transformed_corners[0, :])
    max_x = np.max(transformed_corners[0, :])
    min_y = np.min(transformed_corners[1, :])
    max_y = np.max(transformed_corners[1, :])
    
    # Calculate translation to bring image into view
    tx = -min_x
    ty = -min_y
    
    # Translation matrix
    T = np.array([
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1]
    ])
    
    # Combine translation with homography
    H_adjusted = T @ H
    
    # Calculate output size
    out_w = int(np.ceil(max_x - min_x))
    out_h = int(np.ceil(max_y - min_y))
    
    if output_size is not None:
        # Scale to fit requested size
        scale = min(output_size[0] / out_w, output_size[1] / out_h)
        S = np.array([
            [scale, 0, 0],
            [0, scale, 0],
            [0, 0, 1]
        ])
        H_adjusted = S @ H_adjusted
        out_w = output_size[0]
        out_h = output_size[1]
    
    # Apply transformation
    result = cv2.warpPerspective(img, H_adjusted, (out_w, out_h))
    
    return result, H_adjusted


def draw_line_homogeneous(img, line, color=(0, 0, 255), thickness=2):
    """
    Draw a line defined in homogeneous coordinates.
    
    Args:
        img: Image to draw on (will be modified)
        line: 3x1 homogeneous line [a, b, c] where ax + by + c = 0
        color: Line color (B, G, R)
        thickness: Line thickness
    
    Returns:
        Image with line drawn
    """
    h, w = img.shape[:2]
    line = line.flatten()
    
    # Normalize
    if abs(line[2]) > 1e-10:
        line = line / line[2]
    
    points = []
    
    # Find intersections with image borders
    # Left border (x=0)
    if abs(line[1]) > 1e-6:
        y = -line[2] / line[1]
        if 0 <= y <= h:
            points.append((0, int(y)))
    
    # Right border (x=w)
    if abs(line[1]) > 1e-6:
        y = -(line[0] * w + line[2]) / line[1]
        if 0 <= y <= h:
            points.append((w, int(y)))
    
    # Top border (y=0)
    if abs(line[0]) > 1e-6:
        x = -line[2] / line[0]
        if 0 <= x <= w:
            points.append((int(x), 0))
    
    # Bottom border (y=h)
    if abs(line[0]) > 1e-6:
        x = -(line[1] * h + line[2]) / line[0]
        if 0 <= x <= w:
            points.append((int(x), h))
    
    # Draw line if we have at least 2 points
    if len(points) >= 2:
        # Remove duplicates and take first two
        unique_points = []
        for p in points:
            if not any(abs(p[0]-up[0]) < 2 and abs(p[1]-up[1]) < 2 for up in unique_points):
                unique_points.append(p)
        
        if len(unique_points) >= 2:
            cv2.line(img, unique_points[0], unique_points[1], color, thickness)
    
    return img


def select_points_interactive(image, num_points, title="Select Points"):
    """
    Interactive point selection on an image (for experiments 1 and 3).
    
    Args:
        image: Image to display
        num_points: Number of points to select
        title: Window title
    
    Returns:
        List of (x, y) tuples
    """
    points = []
    img_display = image.copy()
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < num_points:
            points.append((x, y))
            cv2.circle(img_display, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(img_display, str(len(points)), (x+10, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow(title, img_display)
            print(f"Point {len(points)}: ({x}, {y})")
    
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, 1200, 800)
    cv2.setMouseCallback(title, mouse_callback)
    cv2.imshow(title, img_display)
    
    print(f"\n{title}")
    print(f"Click {num_points} points on the image")
    print("Press any key when done")
    
    while len(points) < num_points:
        key = cv2.waitKey(1) & 0xFF
        if key != 255:
            break
    
    cv2.waitKey(100)
    cv2.destroyWindow(title)
    
    return points


def select_points_with_lines(image, title="Select 8 Points"):
    """
    Interactive point selection for Experiment 2 with live line preview.
    Shows lines as you complete each pair.
    """
    points = []
    img_display = image.copy()
    
    instructions = [
        "BLUE Vertical: Click TOP of vertical edge",
        "BLUE Vertical: Click BOTTOM of same vertical edge", 
        "BLUE Horizontal: Click LEFT of horizontal edge",
        "BLUE Horizontal: Click RIGHT of same horizontal edge",
        "RED Vertical: Click TOP of vertical edge (different tile)",
        "RED Vertical: Click BOTTOM of same vertical edge",
        "RED Horizontal: Click LEFT of horizontal edge", 
        "RED Horizontal: Click RIGHT of same horizontal edge"
    ]
    
    colors = [(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 0, 0),
              (0, 0, 255), (0, 0, 255), (0, 0, 255), (0, 0, 255)]
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 8:
            points.append((x, y))
            
            # Draw the point
            cv2.circle(img_display, (x, y), 8, colors[len(points)-1], -1)
            cv2.circle(img_display, (x, y), 10, (255, 255, 255), 2)
            cv2.putText(img_display, str(len(points)), (x+15, y-15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, colors[len(points)-1], 3)
            
            # Draw lines when we complete a pair
            if len(points) == 2:  # Blue vertical line
                cv2.line(img_display, points[0], points[1], (255, 0, 0), 3)
            elif len(points) == 4:  # Blue horizontal line
                cv2.line(img_display, points[2], points[3], (255, 0, 0), 3)
            elif len(points) == 6:  # Red vertical line
                cv2.line(img_display, points[4], points[5], (0, 0, 255), 3)
            elif len(points) == 8:  # Red horizontal line
                cv2.line(img_display, points[6], points[7], (0, 0, 255), 3)
            
            cv2.imshow(title, img_display)
            print(f"✓ Point {len(points)}: ({x}, {y})")
    
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, 1200, 800)
    cv2.setMouseCallback(title, mouse_callback)
    cv2.imshow(title, img_display)
    
    print("\n" + "="*70)
    print("INTERACTIVE POINT SELECTION")
    print("="*70)
    
    current_instruction = -1
    
    while len(points) < 8:
        # Show current instruction only once
        if len(points) != current_instruction:
            current_instruction = len(points)
            if len(points) < 8:
                print(f"\n→ {instructions[len(points)]}", flush=True)
        
        key = cv2.waitKey(50) & 0xFF
        if key == ord('q'):
            break
    
    print("\n" + "="*70)
    print("Selection complete! Press any key to continue...")
    print("="*70)
    cv2.waitKey(0)
    cv2.destroyWindow(title)
    
    return points


def compute_line_angle(line1, line2):
    """
    Compute angle between two lines in degrees.
    
    Args:
        line1, line2: Lines in homogeneous coordinates [a, b, c]
    
    Returns:
        Angle in degrees
    """
    l1 = line1.flatten()
    l2 = line2.flatten()
    
    # Direction vectors (perpendicular to line normals)
    v1 = np.array([-l1[1], l1[0]])
    v2 = np.array([-l2[1], l2[0]])
    
    # Normalize
    v1 = v1 / np.linalg.norm(v1)
    v2 = v2 / np.linalg.norm(v2)
    
    # Compute angle
    cos_angle = np.clip(np.dot(v1, v2), -1, 1)
    angle = np.arccos(np.abs(cos_angle)) * 180 / np.pi
    
    return angle


def save_comparison(img1, img2, title1, title2, filename):
    """
    Save a side-by-side comparison of two images.
    
    Args:
        img1, img2: Images to compare
        title1, title2: Titles for each image
        filename: Output filename
    """
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))
    
    axes[0].imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    axes[0].set_title(title1, fontsize=16, fontweight='bold', pad=20)
    axes[0].axis('off')
    
    axes[1].imshow(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))
    axes[1].set_title(title2, fontsize=16, fontweight='bold', pad=20)
    axes[1].axis('off')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved comparison: {filename}")