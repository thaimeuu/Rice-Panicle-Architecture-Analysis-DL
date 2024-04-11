import os
import numpy as np  
import cv2
import xml.etree.ElementTree as ET


def generate_bbox_grains_junctions(original_img_path, vertex_coordinates_path):
    """
    Create bounding boxes for grains and junctions

    Args:
        original_img_path (str): dataset/original/2_2_1_1_3_DSC09839.JPG
        vertex_coordinates_path (str): dataset/vertex_coordinates/2_2_1_1_3_DSC09839.ricepr
    """
    img = cv2.imread(original_img_path)
    
    # ========= Bounding boxes for junctions ===========
    generating, end, primary, secondary, tertiary, quaternary = _get_vertex(vertex_coordinates_path)
    
    for x, y in generating:
        cv2.rectangle(img, pt1=(x - 10, y - 10), pt2=(x + 10, y + 10), color=(255, 0, 0), thickness=2)
    for x, y in primary:
        cv2.rectangle(img, pt1=(x - 10, y - 10), pt2=(x + 10, y + 10), color=(255, 0, 0), thickness=2)
    for x, y in secondary:
        cv2.rectangle(img, pt1=(x - 10, y - 10), pt2=(x + 10, y + 10), color=(255, 0, 0), thickness=2)
    for x, y in tertiary:
        cv2.rectangle(img, pt1=(x - 10, y - 10), pt2=(x + 10, y + 10), color=(255, 0, 0), thickness=2)
    for x, y in quaternary:
        cv2.rectangle(img, pt1=(x - 10, y - 10), pt2=(x + 10, y + 10), color=(255, 0, 0), thickness=2)
    # for x, y in end:
    #     cv2.circle(img, (x, y), 6, (0, 0, 255), -1)
        
    # ========= Bounding boxes for grains =========
    edges = _get_edges(vertex_coordinates_path)
    
    for x1, y1, x2, y2 in edges:
        if [x1, y1] in generating and [x2, y2] in end:
            # cv2.rectangle(img, pt1=(x1, y1), pt2=(x2, y2), color=(0, 0, 255), thickness=2)
            _bounding_box(img, x1, y1, x2, y2)
            
        if [x1, y1] in primary and [x2, y2] in end:
            # cv2.rectangle(img, pt1=(x1, y1), pt2=(x2, y2), color=(0, 0, 255), thickness=2)
            _bounding_box(img, x1, y1, x2, y2)
            
        if [x1, y1] in secondary and [x2, y2] in end:
            _bounding_box(img, x1, y1, x2, y2)
            
        if [x1, y1] in tertiary and [x2, y2] in end:
            # cv2.rectangle(img, pt1=(x1, y1), pt2=(x2, y2), color=(0, 0, 255), thickness=2)
            _bounding_box(img, x1, y1, x2, y2)
    
        if [x1, y1] in quaternary and [x2, y2] in end:
            # cv2.rectangle(img, pt1=(x1, y1), pt2=(x2, y2), color=(0, 0, 255), thickness=2)
            _bounding_box(img, x1, y1, x2, y2)

    save_path = "dataset/bbox"
    index = len("dataset/original/")
    cv2.imwrite(save_path + "/" + original_img_path[index:], img)
    
    
def generate_bbox_pb(original_img_path, vertex_coordinates_path):
    """
    Create bounding boxes for primary branches (Pb)
    """
    img = cv2.imread(original_img_path)
    generating, end, primary, secondary, tertiary, quaternary = _get_vertex(vertex_coordinates_path)
    edges = _get_edges(vertex_coordinates_path)
    parent = {}
    
    for x1, y1, x2, y2 in edges:
        if [x2, y2] not in primary:
            parent[(x2, y2)] = (x1, y1)
        
    root_list = set()
    for x1, y1, x2, y2 in edges:
        if [x2, y2] in end:
            root = _get_root(x2, y2, parent)
            root_list.add(root)
            
    Pb_root = [pb_root for pb_root in list(root_list) if list(pb_root) in primary]
                
    children = {root: [] for root in Pb_root}
    
    for x1, y1, x2, y2 in edges:
        if [x2, y2] in end:
            root = _get_root(x2, y2, parent)
            # if root is primary node rather than generating node
            if root in children.keys():
                children[root].append((x2, y2))
          
    for parent in children:
        age = []
        for child in children[parent]:
            age.append(np.linalg.norm(np.array(parent) - np.array(child)))
        
        age_mean = np.mean(age)
        
        old_children_pos = np.argwhere(age >= age_mean)
        old_children_pos = [int(index_) for index_ in old_children_pos[0]]
        
        old_children = [children[parent][pos] for pos in old_children_pos]
        for old_child in old_children:
            # print(old_child)
            cv2.rectangle(img, parent, old_child, (0, 0, 255), 2)
        
        # break
            
    
    cv2.imwrite("test.jpg", img)
            

def inspect_edges(original_img_path, vertex_coordinates_path):
    """
    Inspect all the edges of an image (Optional - Only for visualization purpose)
    """
    img = cv2.imread(original_img_path)
    edges = _get_edges(vertex_coordinates_path)
    for x1, y1, x2, y2 in edges:
        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.circle(img, (x1, y1), 5, (0, 0, 255), -1)
        cv2.circle(img, (x2, y2), 5, (0, 0, 255), -1)
        
    index = len("dataset/original/")
    cv2.imwrite(f"inspect_{original_img_path[index:]}", img)


def _get_vertex(vertex_coordinates_path):
    """
    Reads xml file and extracts vertices information
    
    Returns:
        generating (list[list]): coordinates of all generating vertices
        end: ...
        primary: ...
        secondary: ...
        tertiary: ...
    """
    tree = ET.parse(vertex_coordinates_path)
    root = tree.getroot()
    
    generating = []
    end = []
    primary = []
    secondary = []
    tertiary = []
    quaternary = []
    
    for vertex in root.iter('vertex'):
        x = int(vertex.attrib['x'])
        y = int(vertex.attrib['y'])
        type_ = vertex.attrib['type']
        if type_ == "Generating":
            generating.append([x, y])
        elif type_ == "End":
            end.append([x, y])
        elif type_ == "Primary":
            primary.append([x, y])
        elif type_ == "Seconday":
            secondary.append([x, y])
        elif type_ == "Tertiary":
            tertiary.append([x, y])
            
    return generating, end, primary, secondary, tertiary, quaternary


def _get_edges(vertex_coordinates_path):
    """
    Reads xml file and extracts edges information
    
    Returns: edges: [x1, y1, x2, y2] with (x_i, y_i) -> vertex_i
    """
    tree = ET.parse(vertex_coordinates_path)
    root = tree.getroot()
    
    edges = []
    for edge in root.iter('edge'):
        vertex1 = edge.attrib['vertex1']
        vertex2 = edge.attrib['vertex2']
        
        x1 = int(vertex1.split('=')[1].split(',')[0])
        y1 = int(vertex1.split('=')[2].split(']')[0])
        
        x2 = int(vertex2.split('=')[1].split(',')[0])
        y2 = int(vertex2.split('=')[2].split(']')[0])
        
        edges.append([x1, y1, x2, y2])

    return edges  


def _get_root(x, y, parent: dict) -> list:
    """
    Given a node, returns the root
    """
    while True:
        try:
            root = parent[(x, y)]
            x, y = root
        except:
            break
        
    return root


def _draw_bbox(img, x1, y1, x2, y2, condition: int) -> None:
    """
    Draw bounding box based on conditions (grains and junctions)
        condition = 1 (abs(x1 - x2) <= 5)
                  = 2 (5 < abs(x1 - x2) < 25)
                  = 3  (abs(y1 - y2) <= 5)
                  = 4  (5 < abs(y1 - y2) < 25)
    """  
    if condition == 1:
        if x1 > x2:
            cv2.rectangle(img, pt1=(x1 + 12, y1), pt2=(x2 - 12, y2), color=(0, 0, 255), thickness=2)
        elif x1 <= x2:
            cv2.rectangle(img, pt1=(x1 - 12, y1), pt2=(x2 + 12, y2), color=(0, 0, 255), thickness=2)
            
    if condition == 2:
        if x1 > x2:
            cv2.rectangle(img, pt1=(x1 + 7, y1), pt2=(x2 - 5, y2), color=(0, 0, 255), thickness=2)
        elif x1 <= x2:
            cv2.rectangle(img, pt1=(x1 - 7, y1), pt2=(x2 + 5, y2), color=(0, 0, 255), thickness=2)
     
    if condition == 3:
        if y1 > y2:
            cv2.rectangle(img, pt1=(x1, y1 + 12), pt2=(x2, y2 - 12), color=(0, 0, 255), thickness=2)
        elif y1 <= y2:
            cv2.rectangle(img, pt1=(x1, y1 - 12), pt2=(x2, y2 + 12), color=(0, 0, 255), thickness=2)
         
    if condition == 4:
        if y1 > y2:
            cv2.rectangle(img, pt1=(x1, y1 + 7), pt2=(x2, y2 - 5), color=(0, 0, 255), thickness=2)
        elif y1 <= y2:
            cv2.rectangle(img, pt1=(x1, y1 - 7), pt2=(x2, y2 + 5), color=(0, 0, 255), thickness=2)
        
    return None
    

def _bounding_box(img, x1, y1, x2, y2) -> None:
    """
    A shortcut for checking conditions and using _draw_bbox (grains and junctions)
    
    Returns: None
    """
    if abs(x1 - x2) <= 5:
        _draw_bbox(img, x1, y1, x2, y2, condition=1)
            
    elif abs(x1 - x2) < 25:
        _draw_bbox(img, x1, y1, x2, y2, condition=2)
        
    if abs(y1 - y2) <= 5:
        _draw_bbox(img, x1, y1, x2, y2, condition=3)
    
    elif abs(y1 - y2) < 25:
        _draw_bbox(img, x1, y1, x2, y2, condition=4) 
    
    if abs(x1 - x2) >= 25 and abs(y1 - y2) >= 25:
        cv2.rectangle(img, pt1=(x1, y1), pt2=(x2, y2), color=(0, 0, 255), thickness=2)

    return None

        
if __name__ == "__main__":
    # original_folder_path = "dataset/original"
    # img_names = os.listdir(original_folder_path)
    
    # xml_folder_path = "dataset/vertex_coordinates"
    
    # for img in img_names:
    #     img_path = original_folder_path + "/" + img
    #     xml_path = xml_folder_path + "/" + img[:-4] + ".ricepr"
    #     generate_bbox_grains_junctions(img_path, xml_path)
    #     print(f"\nSUCCESSFUL >>>> {img} <<<<")
    #     # break
    
    # =======Bounding boxes for Primary branches============
    generate_bbox_pb("dataset/original/2_2_1_1_3_DSC09839.JPG", "dataset/vertex_coordinates/2_2_1_1_3_DSC09839.ricepr")
    
    # ========Inspect edges============ (Optional)
    # inspect_edges("dataset/original/2_2_1_1_3_DSC09839.JPG", "dataset/vertex_coordinates/2_2_1_1_3_DSC09839.ricepr")
    