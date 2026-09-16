from ultralytics.data.converter import convert_coco

# This script reads your JSON files and generates YOLO .txt files
convert_coco(
    labels_dir="CarDD_release/CarDD_COCO/annotations/",
    save_dir="CarDD_YOLO_Format/",
    use_segments=True,  # Critical: Ensures polygon masks are extracted for YOLOv8-Seg
    cls91to80=False     # CarDD has 6 classes, not standard COCO 80
)
