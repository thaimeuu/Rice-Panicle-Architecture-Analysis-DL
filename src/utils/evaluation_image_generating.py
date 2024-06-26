###########################
# Author: Lam Thai Nguyen #
###########################

import cv2
import numpy as np
import matplotlib.pyplot as plt
from .ricepr_manipulate import resize_junction


def generate_y_true(junction: dict, main_axis: bool = False, high_order: bool = False) -> np.ndarray:
    """
    ## Description
    Generates y_true for evaluation
    
    ## Arguments
    - junction: dict
    - main_axis: bool = False
    - high_order: bool = False
    
    # Returns
    - y_true: np.ndarray
    """
    generating = junction.get('generating')
    generating = [sorted(generating, key=lambda x: x[0])[-1]]  # Remove end generating point
    primary = junction.get('primary')
    main_axis_junction = generating + primary
    
    y_true_main_axis = np.zeros((512, 512))
    
    for y, x in main_axis_junction:
        y_true_main_axis[x, y] = 255
            
    if main_axis and not high_order:
        return y_true_main_axis

    secondary = junction.get('secondary')
    tertiary = junction.get('tertiary')
    quaternary = junction.get('quaternary')
    high_order_junction = secondary + tertiary + quaternary

    y_true_high_order = np.zeros((512, 512))
    
    for y, x in high_order_junction:
        y_true_high_order[x, y] = 255
            
    if high_order and not main_axis:
        return y_true_high_order
    
    if main_axis and high_order or not main_axis and not high_order:
        return y_true_main_axis + y_true_high_order
    

def generate_skeleton_main_axis(skeleton_img: np.ndarray, ricepr_path: str) -> np.ndarray:
    """
    # Description
    Generates a sub-skeleton image from the original skeleton -> It's a main axis skeleton
    
    # Arguments
    - skeleton_img: np.ndarray
    - ricepr_path: str | example: data/original_ricepr/O. glaberrima/1_2_1_1_1_DSC01251.ricepr
    
    # Returns
    skeleton_main_axis: np.ndarray
    """
    # Extract information ==================================================
    junction_resized = resize_junction(ricepr_path)
    y_true_main_axis = generate_y_true(junction_resized, main_axis=True)
    white_px = np.argwhere(y_true_main_axis > 0)
    # ======================================================================
    
    # Creating boundary ==============================================
    x_min, x_max = np.min(white_px[:, 1]), np.max(white_px[:, 1])
    y_min, y_max = np.min(white_px[:, 0]), np.max(white_px[:, 0])
    # ================================================================
    
    # Processing ===================================================
    skeleton_main_axis = np.copy(skeleton_img)
    skeleton_main_axis[:y_min-4, :] = 0
    skeleton_main_axis[y_max+5:, :] = 0
    skeleton_main_axis[:, :x_min-4] = 0
    skeleton_main_axis[:, x_max+5:] = 0
    
    return skeleton_main_axis   


def _pruning(skeleton_img: np.ndarray, min_length: int) -> np.ndarray:
    """
    ## Description
    - Performs PRUNING postprocessing on a skeleton image to remove all branches with length shorter than min_length

    ## Arguments:
    - skeleton_img: (np.ndarray)
    - min_length: (int) minimum number of pixels allowed that make up a branch

    ## Returns:
    - post_processed_skeleton: All short branches are removed
    """
    print(f"==========POST-PROCESSING METHOD: <PRUNING_{min_length}>==========")
    raw_skeleton = np.copy(skeleton_img)
    raw_skeleton[:, 0] = 0
    raw_skeleton[:, -1] = 0
    raw_skeleton[0, :] = 0
    raw_skeleton[-1, :] = 0

    # Initiating end_points
    white_px = np.argwhere(raw_skeleton > 0)
    end_points = []  # Tip of the skeleton
    debris = []  # Isolated pixel
    for i in white_px:
        neighbors_mat = raw_skeleton[i[0]-1:i[0]+2, i[1]-1:i[1]+2]
        neighbors = len(np.argwhere(neighbors_mat > 0)) - 1
        if neighbors == 1:
            end_points.append(tuple(i))
        if neighbors == 0:
            debris.append(tuple(i))

    # Get coordinates of points according to their roles
    parents = {}  # parents[child] = parent
    children = []
    for child in end_points:
        while True:
            # Update children
            children.append(child)
            
            # Find parent
            parent = _get_parent(raw_skeleton, child, children)
            parents[child] = parent
            
            # Handle None when there are random isolated white dot in binary image (e.g. RUC_NET images)
            if parent is None:
                break
            
            # Check if parent is a junction
            neighbors_mat = raw_skeleton[parent[0]-1:parent[0]+2, parent[1]-1:parent[1]+2]
            if np.sum(neighbors_mat) > 255 * 3:
                parents[parent] = None  # Assume junctions don't have parents
                break
            
            # Update child
            child = parent

    # Finding branches' paths
    branches = []
    for end_point in end_points:
        path = [end_point]
        current_point = end_point
        
        while True:
            parent = parents[current_point] 
            if parent is None:
                break
            path.append(parent)
            current_point = parent

        branches.append(path)
        
    # PRUNING
    post_processed_skeleton = np.copy(skeleton_img)
    for branch in branches:
        if len(branch) < min_length:
            for pts in branch:
                post_processed_skeleton[pts[0], pts[1]] = 0
                
    # SWEEPING
    for pts in debris:
        post_processed_skeleton[pts[0], pts[1]] = 0
    
    return post_processed_skeleton

def _get_parent(skeleton_img: np.ndarray, end_point: tuple, children: list[tuple]) -> tuple:
    """
    Find the neighbor of end_point
    """
    neighbors_mat = skeleton_img[end_point[0]-1:end_point[0]+2, end_point[1]-1:end_point[1]+2]
    for i in range(3):
        for j in range(3):
            if neighbors_mat[i, j] > 0:
                parent = tuple((end_point[0] + (i - 1), end_point[1] + (j - 1)))
                if parent not in children:
                    return parent
    return None
