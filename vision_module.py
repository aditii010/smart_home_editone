# vision_module.py
from ultralytics import YOLO

class VisionModule:
    """
    Lightweight wrapper around YOLOv8 for single-frame object detection
    and simple proximity (nearby) relationships.
    """
    def __init__(self, model_path="yolov8n.pt"):
        # Auto-downloads the first time. Small + fast.
        self.model = YOLO(model_path)

    def analyze_frame(self, image_path):
        """
        Run detection on a single image file.
        Returns:
            {
              "detections": [{"label": str, "confidence": float, "bbox": (x1,y1,x2,y2)}...],
              "relations": [{"subject":"person","relation":"near","object":"oven", "distance": float}, ...]
            }
        """
        results = self.model(image_path)
        if not results or not results[0].boxes:
            return {"detections": [], "relations": []}

        names = results[0].names
        boxes = results[0].boxes.data.tolist()

        dets = []
        for x1, y1, x2, y2, conf, cls_id in boxes:
            label = names[int(cls_id)]
            dets.append({
                "label": label,
                "confidence": float(conf),
                "bbox": (float(x1), float(y1), float(x2), float(y2))
            })

        relations = self._build_relations(dets)
        return {"detections": dets, "relations": relations}

    # -------- helpers --------
    def _center(self, box):
        x1, y1, x2, y2 = box
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def _dist(self, a, b):
        ax, ay = self._center(a)
        bx, by = self._center(b)
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

    def _build_relations(self, dets, near_thresh=120.0):
        """
        Build simple 'near' relations between key objects.
        """
        people = [d for d in dets if d["label"] == "person"]
        ovens  = [d for d in dets if d["label"] in ["oven", "microwave", "stove"]]
        tvs    = [d for d in dets if d["label"] in ["tv", "monitor", "laptop"]]
        locks  = [d for d in dets if d["label"] in ["door", "door handle"]]
        remotes= [d for d in dets if d["label"] in ["remote", "cell phone"]]
        tables = [d for d in dets if d["label"] in ["dining table", "couch", "sofa"]]

        relations = []
        def add_near(subjects, objects, obj_name):
            for s in subjects:
                for o in objects:
                    d = self._dist(s["bbox"], o["bbox"])
                    if d <= near_thresh:
                        relations.append({
                            "subject": "person",
                            "relation": "near",
                            "object": obj_name,
                            "distance": float(d)
                        })
        add_near(people, ovens, "oven")
        add_near(people, tvs, "tv")
        add_near(people, locks, "door")
        add_near(people, remotes, "remote")
        add_near(people, tables, "seating_area")

        return relations
