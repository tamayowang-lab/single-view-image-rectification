"""
ECE 738 - Project 2: Image Rectification and World Reconstruction
1. Projective Rectification
2. Affine Rectification  
3. World Plane Reconstruction
"""

__version__ = '1.0.0'
__author__ = 'ECE 738 Student'

from .utils import (
    hcross,
    homoTrans,
    compute_homography_dlt,
    transform_image,
    draw_line_homogeneous,
    select_points_interactive,
    compute_line_angle,
    save_comparison
)

from .experiment1_projective import projective_rectification
from .experiment2_affine import affine_rectification
from .experiment3_world import world_reconstruction

__all__ = [
    'hcross',
    'homoTrans',
    'compute_homography_dlt',
    'transform_image',
    'draw_line_homogeneous',
    'select_points_interactive',
    'compute_line_angle',
    'save_comparison',
    'projective_rectification',
    'affine_rectification',
    'world_reconstruction'
]