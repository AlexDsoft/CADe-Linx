import json
import inspect
from PyQt6.QtCore import QPointF
from components.base import ElectricalComponent, Wire
import components.library as _lib

COMP_CLASSES = {
    _name: _cls
    for _name, _cls in inspect.getmembers(_lib, inspect.isclass)
    if issubclass(_cls, ElectricalComponent) and _cls is not ElectricalComponent
}


def serialize_scene_to_dict(scene) -> dict:
    rect = scene.sceneRect()
    data = {
        "metadata": {
            "project": getattr(scene, "meta_project", "ARRANQUE DIRECTO MOTOR TRIFASICO"),
            "author": getattr(scene, "meta_author", "ALUMNO / PROFESOR"),
            "system": getattr(scene, "meta_system", "CADe Linx"),
            "width": int(rect.width()),
            "height": int(rect.height()),
        },
        "components": [],
        "wires": []
    }
    for item in scene.items():
        if isinstance(item, ElectricalComponent):
            if getattr(item, "_is_ghost", False) or item.opacity() < 0.9:
                continue
            comp_data = {
                "type": item.__class__.__name__,
                "label": item.label,
                "x": item.pos().x(),
                "y": item.pos().y(),
            }
            if hasattr(item, "delay_sec"):
                comp_data["delay_sec"] = float(item.delay_sec)
            if hasattr(item, "lamp_color"):
                comp_data["lamp_color"] = item.lamp_color
            data["components"].append(comp_data)
        elif isinstance(item, Wire):
            data["wires"].append({
                "x1": item.p1.x(),
                "y1": item.p1.y(),
                "x2": item.p2.x(),
                "y2": item.p2.y(),
                "wire_type": item.wire_type,
                "label": getattr(item, "label", ""),
                "j1": item.junction_p1,
                "j2": item.junction_p2,
            })
    return data


def restore_scene_from_dict(scene, data: dict):
    for v in scene.views():
        v.preview_line = None
        v.snap_marker = None
        v.wire_start = None
        v.ghost_item = None
        if hasattr(v, "preview_lines_3ph"):
            v.preview_lines_3ph = []
        v._last_3ph_wires = None
        v._last_3ph_dir = None

    scene.clear()
    meta = data.get("metadata", {})
    scene.meta_project = meta.get("project", "ARRANQUE DIRECTO MOTOR TRIFASICO")
    scene.meta_author = meta.get("author", "ALUMNO / PROFESOR")
    scene.meta_system = meta.get("system", "CADe Linx")
    w_sheet = max(1600, int(meta.get("width", 1600)))
    h_sheet = max(1100, int(meta.get("height", 1100)))
    scene.setSceneRect(0, 0, w_sheet, h_sheet)

    for c in data.get("components", []):
        cls_name = c.get("type")
        cls = COMP_CLASSES.get(cls_name)
        if cls:
            item = cls()
            item.label = c.get("label", getattr(item, "label", "X1"))
            item.setPos(QPointF(c.get("x", 0), c.get("y", 0)))
            if "delay_sec" in c:
                item.delay_sec = float(c["delay_sec"])
                item.remaining_sec = float(c["delay_sec"])
            if "lamp_color" in c:
                item.lamp_color = c["lamp_color"]
            scene.addItem(item)

    for w_data in data.get("wires", []):
        p1 = QPointF(w_data["x1"], w_data["y1"])
        p2 = QPointF(w_data["x2"], w_data["y2"])
        w = Wire(p1, p2, w_data.get("wire_type", "PHASE"))
        w.label = w_data.get("label", "")
        w.junction_p1 = w_data.get("j1", False)
        w.junction_p2 = w_data.get("j2", False)
        scene.addItem(w)

    scene.update()
    for v in scene.views():
        if hasattr(v, "_update_ghost_item"):
            v._update_ghost_item()


def save_schematic(scene, filepath: str):
    data = serialize_scene_to_dict(scene)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_schematic(scene, filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    restore_scene_from_dict(scene, data)
