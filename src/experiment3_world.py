"""
Experiment 3: World Plane Reconstruction (CORRECTED)
ECE 738 - Project 2

Reconstructs 3D world coordinates from 2D image coordinates using
point correspondences and homography estimation with proper validation.

Usage:
    python experiment3_world.py <image_path> <width> <height> [unit]
    
Example:
    python experiment3_world.py ../images/3.jpg 40.15748 40.15748 inches
"""

import sys
import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from utils import (compute_homography_dlt, homoTrans, select_points_interactive)


def world_reconstruction(image_path, world_width, world_height, unit='cm', output_dir='../results'):
    """
    Reconstruct world coordinates from an image with proper validation.
    
    Args:
        image_path: Path to input image
        world_width: Actual width of object in world units
        world_height: Actual height of object in world units
        unit: Unit of measurement (e.g., 'cm', 'inches', 'm')
        output_dir: Directory to save results
    
    Returns:
        Results dictionary with images and metrics
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load image
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    print("\n" + "="*70)
    print("EXPERIMENT 3: WORLD PLANE RECONSTRUCTION")
    print("="*70)
    print("\nGoal: Measure real-world coordinates from a 2D image")
    print(f"\nObject dimensions: {world_width} × {world_height} {unit}")
    print("\nInstructions:")
    print("  Select AT LEAST 6 points with known world coordinates")
    print("  - First 4 points will be used to compute the homography")
    print("  - Remaining points will be used to TEST accuracy")
    print("\nClick in this order:")
    print("  1. Top-left corner")
    print("  2. Top-right corner")
    print("  3. Bottom-right corner")
    print("  4. Bottom-left corner")
    print("  5-8. Additional points (e.g., midpoints, center)")
    print("\nGood objects: paper, book, door, poster, floor tile")
    print("="*70 + "\n")
    
    # Interactive point selection - GET AT LEAST 6 POINTS
    points_list = select_points_interactive(img, 8, "Select 8 Points (4 corners + 4 test points)")
    
    if len(points_list) < 6:
        print(f"Error: Need at least 6 points for proper validation, got {len(points_list)}")
        return None
    
    num_points = len(points_list)
    print(f"\nTotal points selected: {num_points}")
    
    # Define ALL world coordinates
    # You need to specify world coordinates for ALL selected points
    # Example: 4 corners + midpoints + center
    world_points_all = np.array([
        [0, 0],                          # 1. Top-left
        [world_width, 0],                # 2. Top-right
        [world_width, world_height],     # 3. Bottom-right
        [0, world_height],               # 4. Bottom-left
        [world_width/2, 0],              # 5. Top-middle
        [world_width, world_height/2],   # 6. Right-middle
        [world_width/2, world_height],   # 7. Bottom-middle
        [0, world_height/2],             # 8. Left-middle
    ])
    
    # Use only as many world points as image points selected
    world_points_all = world_points_all[:num_points]
    
    print("\nWorld coordinates for selected points:")
    for i, pt in enumerate(world_points_all):
        print(f"  Point {i+1}: ({pt[0]:.2f}, {pt[1]:.2f}) {unit}")
    
    # Prepare image points
    image_points_all = np.array(points_list, dtype=np.float32)
    
    # SPLIT: First 4 for training, rest for testing
    train_world = world_points_all[:4]
    train_image = image_points_all[:4]
    
    test_world = world_points_all[4:]
    test_image = image_points_all[4:]
    
    print("\n" + "="*70)
    print("TRAINING SET: Using first 4 points to compute homography")
    print("="*70)
    for i in range(4):
        print(f"  Point {i+1}: Image ({train_image[i][0]:.1f}, {train_image[i][1]:.1f}) → "
              f"World ({train_world[i][0]:.2f}, {train_world[i][1]:.2f}) {unit}")
    
    # Compute homography using ONLY first 4 points
    print("\nComputing homography using Direct Linear Transform (DLT)...")
    H = compute_homography_dlt(train_world, train_image)
    
    print("\nHomography H (world → image):")
    print(H)
    
    # For reconstruction, we need the inverse (image → world)
    H_inv = np.linalg.inv(H)
    
    print("\nInverse H (image → world):")
    print(H_inv)
    
    # VERIFY WITH TRAINING POINTS (should be near-zero)
    print("\n" + "="*70)
    print("TRAINING VERIFICATION (Expected: ~0 error)")
    print("="*70)
    
    train_image_homo = np.column_stack([train_image, np.ones(len(train_image))]).T
    train_reconstructed = homoTrans(H_inv, train_image_homo)
    
    train_errors = []
    print(f"\n{'Pt':<4} {'World (actual)':<25} {'Reconstructed':<25} {'Error':<15}")
    print("-"*70)
    
    for i in range(len(train_world)):
        actual = train_world[i]
        recon = train_reconstructed[:2, i]
        error = np.linalg.norm(actual - recon)
        train_errors.append(error)
        print(f"{i+1:<4} ({actual[0]:>6.2f}, {actual[1]:>6.2f}){'':<5} "
              f"({recon[0]:>6.2f}, {recon[1]:>6.2f}){'':<5} "
              f"{error:>6.3f} {unit}")
    
    train_mean_error = np.mean(train_errors)
    print("-"*70)
    print(f"Training mean error: {train_mean_error:.3f} {unit} (should be ~0)")
    
    # TEST WITH HELD-OUT POINTS (the real validation!)
    print("\n" + "="*70)
    print(f"TEST VERIFICATION: {len(test_world)} held-out points (REAL ERROR!)")
    print("="*70)
    
    test_image_homo = np.column_stack([test_image, np.ones(len(test_image))]).T
    test_reconstructed = homoTrans(H_inv, test_image_homo)
    
    test_errors = []
    print(f"\n{'Pt':<4} {'World (actual)':<25} {'Reconstructed':<25} {'Error':<15}")
    print("-"*70)
    
    for i in range(len(test_world)):
        actual = test_world[i]
        recon = test_reconstructed[:2, i]
        error = np.linalg.norm(actual - recon)
        test_errors.append(error)
        print(f"{i+5:<4} ({actual[0]:>6.2f}, {actual[1]:>6.2f}){'':<5} "
              f"({recon[0]:>6.2f}, {recon[1]:>6.2f}){'':<5} "
              f"{error:>6.3f} {unit}")
    
    test_mean_error = np.mean(test_errors)
    test_max_error = np.max(test_errors)
    print("-"*70)
    print(f"Test mean error: {test_mean_error:.3f} {unit}")
    print(f"Test max error:  {test_max_error:.3f} {unit}")
    
    # Visualize on image
    vis_img = img.copy()
    train_colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0)]  # Red, green, blue, yellow
    test_color = (255, 0, 255)  # Magenta for test points
    
    # Draw training points (corners)
    for i, (img_pt, world_pt) in enumerate(zip(train_image, train_world)):
        pt = (int(img_pt[0]), int(img_pt[1]))
        cv2.circle(vis_img, pt, 10, train_colors[i], -1)
        cv2.circle(vis_img, pt, 12, (255, 255, 255), 2)
        cv2.putText(vis_img, f"{i+1}", (pt[0]+15, pt[1]-15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, train_colors[i], 3)
        cv2.putText(vis_img, f"({world_pt[0]:.1f},{world_pt[1]:.1f})", 
                   (pt[0]+15, pt[1]+25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Draw test points
    for i, (img_pt, world_pt) in enumerate(zip(test_image, test_world)):
        pt = (int(img_pt[0]), int(img_pt[1]))
        cv2.circle(vis_img, pt, 10, test_color, -1)
        cv2.circle(vis_img, pt, 12, (255, 255, 255), 2)
        cv2.putText(vis_img, f"{i+5}", (pt[0]+15, pt[1]-15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, test_color, 3)
        cv2.putText(vis_img, f"({world_pt[0]:.1f},{world_pt[1]:.1f})", 
                   (pt[0]+15, pt[1]+25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Draw rectangle connecting corners
    pts = train_image.astype(np.int32)
    cv2.polylines(vis_img, [pts], True, (0, 255, 255), 3)
    
    # Add info text
    h, w = img.shape[:2]
    cv2.putText(vis_img, f"Object: {world_width}x{world_height} {unit}", (20, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(vis_img, f"Test Error: {test_mean_error:.2f} {unit}", (20, h-60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.putText(vis_img, f"Train: 4 corners, Test: {len(test_world)} points", (20, h-20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Create world coordinate visualization
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # Image space
    axes[0].imshow(cv2.cvtColor(vis_img, cv2.COLOR_BGR2RGB))
    axes[0].set_title('Image Space\n(Corners=Training, Magenta=Test)', 
                     fontsize=14, fontweight='bold')
    axes[0].axis('off')
    
    # World space
    axes[1].set_xlim(-world_width*0.1, world_width*1.1)
    axes[1].set_ylim(-world_height*0.1, world_height*1.1)
    axes[1].set_aspect('equal')
    axes[1].invert_yaxis()
    
    # Plot training points
    for i, pt in enumerate(train_world):
        axes[1].plot(pt[0], pt[1], 'o', color=np.array(train_colors[i][::-1])/255, 
                    markersize=15, markeredgecolor='white', markeredgewidth=2,
                    label=f'Train {i+1}' if i == 0 else '')
        axes[1].text(pt[0]+world_width*0.03, pt[1], f"{i+1}", 
                    fontsize=14, fontweight='bold',
                    color=np.array(train_colors[i][::-1])/255)
    
    # Plot test points
    for i, pt in enumerate(test_world):
        axes[1].plot(pt[0], pt[1], 'o', color=np.array(test_color[::-1])/255, 
                    markersize=15, markeredgecolor='white', markeredgewidth=2,
                    label='Test' if i == 0 else '')
        axes[1].text(pt[0]+world_width*0.03, pt[1], f"{i+5}", 
                    fontsize=14, fontweight='bold',
                    color=np.array(test_color[::-1])/255)
    
    # Draw rectangle
    rect = plt.Polygon(train_world, fill=False, edgecolor='cyan', linewidth=3)
    axes[1].add_patch(rect)
    
    axes[1].set_xlabel(f'X ({unit})', fontsize=12, fontweight='bold')
    axes[1].set_ylabel(f'Y ({unit})', fontsize=12, fontweight='bold')
    axes[1].set_title(f'World Space ({world_width} × {world_height} {unit})\n'
                     f'Test Mean Error: {test_mean_error:.2f} {unit}', 
                     fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3, linestyle='--')
    axes[1].legend(loc='upper right')
    
    plt.tight_layout()
    
    # Save results
    base_name = Path(image_path).stem
    cv2.imwrite(f'{output_dir}/exp3_{base_name}_annotated.jpg', vis_img)
    plt.savefig(f'{output_dir}/exp3_{base_name}_comparison.png', 
                dpi=150, bbox_inches='tight')
    plt.close()
    
    # Save numerical results
    with open(f'{output_dir}/exp3_{base_name}_results.txt', 'w') as f:
        f.write("="*70 + "\n")
        f.write("EXPERIMENT 3: WORLD PLANE RECONSTRUCTION (WITH VALIDATION)\n")
        f.write("="*70 + "\n\n")
        f.write(f"Image: {image_path}\n")
        f.write(f"Object dimensions: {world_width} × {world_height} {unit}\n")
        f.write(f"Total points: {num_points} (4 training, {len(test_world)} test)\n\n")
        
        f.write("HOMOGRAPHY MATRIX (world → image):\n")
        f.write(str(H) + "\n\n")
        f.write("INVERSE HOMOGRAPHY (image → world):\n")
        f.write(str(H_inv) + "\n\n")
        
        f.write("TRAINING POINTS VERIFICATION:\n")
        f.write(f"{'Pt':<4} {'World (actual)':<25} {'Reconstructed':<25} {'Error':<15}\n")
        f.write("-"*70 + "\n")
        for i in range(len(train_world)):
            actual = train_world[i]
            recon = train_reconstructed[:2, i]
            error = train_errors[i]
            f.write(f"{i+1:<4} ({actual[0]:>6.2f}, {actual[1]:>6.2f}){'':<5} "
                   f"({recon[0]:>6.2f}, {recon[1]:>6.2f}){'':<5} "
                   f"{error:>6.3f} {unit}\n")
        f.write("-"*70 + "\n")
        f.write(f"Training mean error: {train_mean_error:.3f} {unit}\n\n")
        
        f.write("TEST POINTS VERIFICATION (REAL ERROR):\n")
        f.write(f"{'Pt':<4} {'World (actual)':<25} {'Reconstructed':<25} {'Error':<15}\n")
        f.write("-"*70 + "\n")
        for i in range(len(test_world)):
            actual = test_world[i]
            recon = test_reconstructed[:2, i]
            error = test_errors[i]
            f.write(f"{i+5:<4} ({actual[0]:>6.2f}, {actual[1]:>6.2f}){'':<5} "
                   f"({recon[0]:>6.2f}, {recon[1]:>6.2f}){'':<5} "
                   f"{error:>6.3f} {unit}\n")
        f.write("-"*70 + "\n")
        f.write(f"Test mean error: {test_mean_error:.3f} {unit}\n")
        f.write(f"Test max error:  {test_max_error:.3f} {unit}\n")
        f.write(f"Relative error: {(test_mean_error/world_width)*100:.2f}%\n")
    
    print("\n" + "="*70)
    print("✓ EXPERIMENT 3 COMPLETE!")
    print("="*70)
    print(f"\nResults saved to {output_dir}/")
    print(f"  • exp3_{base_name}_annotated.jpg")
    print(f"  • exp3_{base_name}_comparison.png")
    print(f"  • exp3_{base_name}_results.txt")
    print("\nWhat happened:")
    print("  • Selected 4 corners (training) + additional test points")
    print("  • Computed homography H using ONLY 4 training points")
    print("  • Verified accuracy on HELD-OUT test points")
    print(f"  • Training error: {train_mean_error:.3f} {unit} (expected ~0)")
    print(f"  • Test error: {test_mean_error:.3f} {unit} (REAL accuracy!)")
    print(f"  • Relative test error: {(test_mean_error/world_width)*100:.2f}%")
    
    if test_mean_error / world_width < 0.05:
        print("\n✓ EXCELLENT! Test error < 5% of object size")
    elif test_mean_error / world_width < 0.1:
        print("\n✓ GOOD! Test error < 10% of object size")
    else:
        print("\n⚠️  High test error - check:")
        print("    • Did you click the exact positions?")
        print("    • Are the world coordinates correct?")
        print("    • Is the object truly planar (flat)?")
        print("    • Camera distortion could affect accuracy")
    
    print("="*70 + "\n")
    
    return {
        'image': vis_img,
        'homography': H,
        'train_mean_error': train_mean_error,
        'test_mean_error': test_mean_error,
        'test_max_error': test_max_error,
        'test_errors': test_errors,
        'world_points': world_points_all,
        'image_points': image_points_all
    }


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("\nUsage: python experiment3_world.py <image_path> <width> <height> [unit]")
        print("\nArguments:")
        print("  image_path : Path to image file")
        print("  width      : Real-world width of object")
        print("  height     : Real-world height of object")
        print("  unit       : Unit of measurement (default: cm)")
        print("\nNote: You'll be asked to select 8 points:")
        print("  - 4 corners (for computing homography)")
        print("  - 4 test points (for validation)")
        sys.exit(1)
    
    image_path = sys.argv[1]
    world_width = float(sys.argv[2])
    world_height = float(sys.argv[3])
    unit = sys.argv[4] if len(sys.argv) > 4 else 'cm'
    
    try:
        world_reconstruction(image_path, world_width, world_height, unit)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)