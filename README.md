# Architecture Analysis of Rice Panicle using Deep Learning

Collaborators: **Lam Thai Nguyen** and **Trung Kien Pham**

## Folder/File/Script description

- dataset
  - original: 100 rice panicle images.
  - original_512x512: 100 rice panicle images resized to (512, 512).
  - vertex_coordinates: rice panicle's vertices coordinates (100 corresponding .ricepr files).
  - annotated: 2 versions of 100 x (binary image, json file).
    - annotated-T: annotated by **Lam Thai Nguyen**
    - annotated-K: annotated by **Trung Kien Pham**
  - bbox: bounding boxes results for grains/junctions detection.
- utils: tools/utils.