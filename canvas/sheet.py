import math
import copy
from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsView, QGraphicsLineItem,
    QGraphicsEllipseItem, QInputDialog
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QPainter, QFont, QKeySequence

from components.base import ElectricalComponent, Wire
from components.library import get_next_available_label, AUTO_NUMBER_CLASSES
from engine.storage import serialize_scene_to_dict, restore_scene_from_dict, COMP_CLASSES


class SchematicScene(QGraphicsScene):
    MIN_W = 1600
    MIN_H = 1100

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, self.MIN_W, self.MIN_H)
        self.meta_project = "ARRANQUE DIRECTO MOTOR TRIFASICO"
        self.meta_author = "ALUMNO / PROFESOR"
        self.meta_system = "CADe Linx"

    def ensure_margin_for_point(self, pt: QPointF):
        """Amplía automáticamente la hoja si se coloca un elemento cerca del borde derecho o inferior."""
        r = self.sceneRect()
        w, h = r.width(), r.height()
        changed = False
        if pt.x() > w - 180:
            w = int(((pt.x() + 400) // 100) * 100)
            changed = True
        if pt.y() > h - 180:
            h = int(((pt.y() + 400) // 100) * 100)
            changed = True
        if changed:
            self.setSceneRect(0, 0, w, h)
            self.update()

    def fit_sheet_to_content(self):
        """Adapta el tamaño del formato al contenido real dibujado (respetando el mínimo 1600x1100)."""
        max_x, max_y = 0, 0
        for item in self.items():
            if isinstance(item, ElectricalComponent) and not getattr(item, "_is_ghost", False):
                br = item.sceneBoundingRect()
                max_x = max(max_x, br.right())
                max_y = max(max_y, br.bottom())
            elif isinstance(item, Wire):
                max_x = max(max_x, item.p1.x(), item.p2.x())
                max_y = max(max_y, item.p1.y(), item.p2.y())

        new_w = max(self.MIN_W, int(((max_x + 220) // 100) * 100))
        new_h = max(self.MIN_H, int(((max_y + 200) // 100) * 100))
        self.setSceneRect(0, 0, new_w, new_h)
        self.update()

    def title_block_rect(self) -> QRectF:
        r = self.sceneRect()
        w, h = int(r.width()), int(r.height())
        return QRectF(w - 620, h - 100, 600, 80)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, QColor("#FFFFFF"))

        sr = self.sceneRect()
        W, H = int(sr.width()), int(sr.height())

        left = int(rect.left()) - (int(rect.left()) % 10)
        top = int(rect.top()) - (int(rect.top()) % 10)

        painter.setPen(QPen(QColor("#F2F2F2"), 1.0))
        for x in range(left, int(rect.right()), 50):
            if 20 <= x <= W - 20:
                painter.drawLine(x, 20, x, H - 20)
        for y in range(top, int(rect.bottom()), 50):
            if 20 <= y <= H - 20:
                painter.drawLine(20, y, W - 20, y)

        painter.setPen(QPen(QColor("#CCCCCC"), 1.5))
        for x in range(left, int(rect.right()), 10):
            for y in range(top, int(rect.bottom()), 10):
                if 20 < x < W - 20 and 20 < y < H - 20:
                    painter.drawPoint(x, y)

        # Marco normalizado dinámico y cajetín técnico en la esquina inferior derecha
        painter.setPen(QPen(QColor("#111111"), 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(20, 20, W - 40, H - 40)

        tb_x, tb_y, tb_w, tb_h = W - 620, H - 100, 600, 80
        painter.setBrush(QBrush(QColor("#FAFAFA")))
        painter.drawRect(tb_x, tb_y, tb_w, tb_h)
        painter.drawLine(tb_x, tb_y + 28, tb_x + tb_w, tb_y + 28)
        painter.drawLine(tb_x, tb_y + 54, tb_x + tb_w, tb_y + 54)
        painter.drawLine(tb_x + 380, tb_y + 28, tb_x + 380, tb_y + tb_h)

        painter.setFont(QFont("SansSerif", 9, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#002266"), 1.2))
        painter.drawText(tb_x + 12, tb_y + 19, f"PROYECTO: {self.meta_project}")

        painter.setFont(QFont("SansSerif", 8))
        painter.setPen(QPen(QColor("#222222"), 1.0))
        painter.drawText(tb_x + 12, tb_y + 46, f"AUTOR: {self.meta_author}")
        painter.drawText(tb_x + 390, tb_y + 46, "NORMA: UNE-EN 60617")
        painter.drawText(tb_x + 12, tb_y + 71, f"SISTEMA: {self.meta_system}")
        painter.drawText(tb_x + 390, tb_y + 71, f"FORMATO: {W}x{H} (Doble clic)")


class SchematicView(QGraphicsView):
    def __init__(self, scene: SchematicScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        self.active_tool = None
        self.is_simulating = False
        self.show_guides = True
        self.guide_pos = QPointF(0, 0)

        self.wire_start = None
        self.preview_line = None
        self.preview_lines_3ph = []
        self.snap_marker = None
        self.ghost_item = None

        self._last_3ph_wires = None
        self._last_3ph_dir = None
        self._last_single_wire = None

        self.undo_stack = []
        self.redo_stack = []
        self._clipboard = None

    def fit_and_adapt_sheet(self):
        """Ajusta el tamaño del formato al contenido y adapta el zoom de la ventana."""
        self.scene().fit_sheet_to_content()
        self.fitInView(self.scene().sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    # --- HISTORIAL DESHACER / REHACER ---
    def push_undo(self):
        if self.is_simulating:
            return
        state = serialize_scene_to_dict(self.scene())
        if self.undo_stack and self.undo_stack[-1] == state:
            return
        self.undo_stack.append(copy.deepcopy(state))
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if self.is_simulating or not self.undo_stack:
            return
        current = serialize_scene_to_dict(self.scene())
        self.redo_stack.append(copy.deepcopy(current))
        prev_state = self.undo_stack.pop()
        restore_scene_from_dict(self.scene(), prev_state)

    def redo(self):
        if self.is_simulating or not self.redo_stack:
            return
        current = serialize_scene_to_dict(self.scene())
        self.undo_stack.append(copy.deepcopy(current))
        next_state = self.redo_stack.pop()
        restore_scene_from_dict(self.scene(), next_state)

    # --- COPIAR Y PEGAR MÚLTIPLE CON AUTONUMERACIÓN Y AUTOEXPANSIÓN ---
    def copy_selected(self):
        if self.is_simulating:
            return
        selected = self.scene().selectedItems()
        if not selected:
            return
        comps, wires = [], []
        for item in selected:
            if isinstance(item, ElectricalComponent) and not getattr(item, "_is_ghost", False):
                c_data = {
                    "type": item.__class__.__name__,
                    "label": item.label,
                    "x": item.pos().x(),
                    "y": item.pos().y(),
                }
                if hasattr(item, "delay_sec"):
                    c_data["delay_sec"] = float(item.delay_sec)
                if hasattr(item, "lamp_color"):
                    c_data["lamp_color"] = item.lamp_color
                comps.append(c_data)
            elif isinstance(item, Wire):
                wires.append({
                    "x1": item.p1.x(),
                    "y1": item.p1.y(),
                    "x2": item.p2.x(),
                    "y2": item.p2.y(),
                    "wire_type": item.wire_type,
                    "j1": item.junction_p1,
                    "j2": item.junction_p2,
                })
        self._clipboard = {"components": comps, "wires": wires}

    def paste_clipboard(self):
        if self.is_simulating or not self._clipboard:
            return
        self.push_undo()
        for it in self.scene().selectedItems():
            it.setSelected(False)

        offset = QPointF(40, 40)
        label_map = {}
        for c in self._clipboard.get("components", []):
            cls = COMP_CLASSES.get(c["type"])
            if cls:
                orig_lbl = c["label"]
                if orig_lbl in label_map:
                    new_lbl = label_map[orig_lbl]
                else:
                    new_lbl = get_next_available_label(self.scene(), orig_lbl)
                    label_map[orig_lbl] = new_lbl
                item = cls()
                item.label = new_lbl
                new_pos = QPointF(c["x"], c["y"]) + offset
                item.setPos(new_pos)
                if "delay_sec" in c:
                    item.delay_sec = float(c["delay_sec"])
                    item.remaining_sec = float(c["delay_sec"])
                if "lamp_color" in c:
                    item.lamp_color = c["lamp_color"]
                self.scene().addItem(item)
                item.setSelected(True)
                self.scene().ensure_margin_for_point(new_pos)

        for w_data in self._clipboard.get("wires", []):
            p1 = QPointF(w_data["x1"], w_data["y1"]) + offset
            p2 = QPointF(w_data["x2"], w_data["y2"]) + offset
            w = Wire(p1, p2, w_data.get("wire_type", "PHASE"))
            w.junction_p1 = w_data.get("j1", False)
            w.junction_p2 = w_data.get("j2", False)
            self.scene().addItem(w)
            w.setSelected(True)
            self.scene().ensure_margin_for_point(p1)
            self.scene().ensure_margin_for_point(p2)

        for c in self._clipboard.get("components", []):
            c["x"] += 40
            c["y"] += 40
        for w_data in self._clipboard.get("wires", []):
            w_data["x1"] += 40
            w_data["y1"] += 40
            w_data["x2"] += 40
            w_data["y2"] += 40

    # --- VÍNCULO ELÁSTICO DE CABLES ---
    def _bind_elastic_wires(self):
        wires = [it for it in self.scene().items() if isinstance(it, Wire)]
        for item in self.scene().items():
            if isinstance(item, ElectricalComponent) and not getattr(item, "_is_ghost", False):
                item._last_elastic_pos = QPointF(item.pos())
                item._attached_wires_p1 = []
                item._attached_wires_p2 = []
                term_pts = [t.scene_pos() for t in item.terminals]
                for w in wires:
                    for tp in term_pts:
                        if (w.p1 - tp).manhattanLength() < 3:
                            item._attached_wires_p1.append(w)
                        elif (w.p2 - tp).manhattanLength() < 3:
                            item._attached_wires_p2.append(w)

    # --- GESTIÓN DE HERRAMIENTAS Y VISTA PREVIA FANTASMA ---
    def set_active_tool(self, tool):
        self._cancel_wire()
        self.active_tool = tool
        if tool is None:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self._update_ghost_item()
        self.viewport().update()

    def _update_ghost_item(self):
        if self.ghost_item and self.ghost_item.scene():
            self.scene().removeItem(self.ghost_item)
        self.ghost_item = None
        if not self.is_simulating and isinstance(self.active_tool, type) and issubclass(self.active_tool, ElectricalComponent):
            self.ghost_item = self.active_tool()
            self.ghost_item._is_ghost = True
            if isinstance(self.ghost_item, AUTO_NUMBER_CLASSES):
                self.ghost_item.label = get_next_available_label(self.scene(), self.ghost_item.label)
            self.ghost_item.setOpacity(0.45)
            self.ghost_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.ghost_item.setFlag(ElectricalComponent.GraphicsItemFlag.ItemIsSelectable, False)
            self.ghost_item.setFlag(ElectricalComponent.GraphicsItemFlag.ItemIsMovable, False)
            self.scene().addItem(self.ghost_item)
            self.ghost_item.setPos(self.guide_pos)

    def _clear_3ph_preview(self):
        for ln in self.preview_lines_3ph:
            if ln.scene():
                self.scene().removeItem(ln)
        self.preview_lines_3ph.clear()

    def _cancel_wire(self):
        self.wire_start = None
        self._last_3ph_wires = None
        self._last_3ph_dir = None
        self._last_single_wire = None
        if self.preview_line and self.preview_line.scene():
            self.scene().removeItem(self.preview_line)
        self.preview_line = None
        self._clear_3ph_preview()

    # --- IMÁN INTELIGENTE A BORNES Y CABLES ---
    def _snap_smart(self, raw_pt: QPointF, start_pt: QPointF = None, free_angle: bool = False):
        for item in self.scene().items():
            if isinstance(item, ElectricalComponent) and not getattr(item, "_is_ghost", False):
                for t in item.terminals:
                    tp = t.scene_pos()
                    if (tp - raw_pt).manhattanLength() <= 14:
                        return tp, "TERMINAL"

        grid_pt = QPointF(round(raw_pt.x() / 10) * 10, round(raw_pt.y() / 10) * 10)
        if start_pt is not None and not free_angle:
            if abs(grid_pt.x() - start_pt.x()) >= abs(grid_pt.y() - start_pt.y()):
                ortho_pt = QPointF(grid_pt.x(), start_pt.y())
            else:
                ortho_pt = QPointF(start_pt.x(), grid_pt.y())
        else:
            ortho_pt = grid_pt

        for item in self.scene().items():
            if isinstance(item, Wire):
                x1, y1, x2, y2 = item.p1.x(), item.p1.y(), item.p2.x(), item.p2.y()
                if abs(x1 - x2) < 1 and min(y1, y2) <= ortho_pt.y() <= max(y1, y2):
                    if abs(ortho_pt.x() - x1) <= 10:
                        return QPointF(x1, ortho_pt.y()), "WIRE"
                elif abs(y1 - y2) < 1 and min(x1, x2) <= ortho_pt.x() <= max(x1, x2):
                    if abs(ortho_pt.y() - y1) <= 10:
                        return QPointF(ortho_pt.x(), y1), "WIRE"

        return ortho_pt, "GRID"

    def _split_wires_at(self, pt: QPointF) -> bool:
        created_junction = False
        wires = [it for it in self.scene().items() if isinstance(it, Wire)]
        for w in wires:
            if (w.p1 - pt).manhattanLength() < 2 or (w.p2 - pt).manhattanLength() < 2:
                continue
            x1, y1, x2, y2 = w.p1.x(), w.p1.y(), w.p2.x(), w.p2.y()
            on_vert = abs(x1 - x2) < 1 and abs(pt.x() - x1) < 2 and min(y1, y2) < pt.y() < max(y1, y2)
            on_horz = abs(y1 - y2) < 1 and abs(pt.y() - y1) < 2 and min(x1, x2) < pt.x() < max(x1, x2)
            if on_vert or on_horz:
                old_p2 = QPointF(w.p2)
                old_j2 = w.junction_p2
                w.prepareGeometryChange()
                w.p2 = QPointF(pt)
                w.junction_p2 = True
                w.update()
                w2 = Wire(QPointF(pt), old_p2, w.wire_type)
                w2.junction_p2 = old_j2
                self.scene().addItem(w2)
                created_junction = True
        return created_junction

    def _update_3ph_preview(self, p1: QPointF, p2: QPointF):
        self._clear_3ph_preview()
        dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
        cur_dir = "H" if abs(dx) >= abs(dy) else "V"
        for idx, off in enumerate((-20, 0, 20)):
            if cur_dir == "H":
                a = QPointF(p1.x(), p1.y() + off)
                b = QPointF(p2.x(), p1.y() + off)
            else:
                a = QPointF(p1.x() + off, p1.y())
                b = QPointF(p1.x() + off, p2.y())
            if self._last_3ph_wires and self._last_3ph_dir and self._last_3ph_dir != cur_dir:
                prev_w = self._last_3ph_wires[idx]
                a = QPointF(prev_w.p1.x(), a.y()) if self._last_3ph_dir == "V" else QPointF(a.x(), prev_w.p1.y())
            ln = QGraphicsLineItem(a.x(), a.y(), b.x(), b.y())
            ln.setPen(QPen(QColor("#8B4513"), 1.5, Qt.PenStyle.DashLine))
            self.scene().addItem(ln)
            self.preview_lines_3ph.append(ln)

    # --- EVENTOS DE RATÓN Y TECLADO ---
    def mouseMoveEvent(self, event):
        raw_pt = self.mapToScene(event.pos())
        free_angle = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        snapped_pt, snap_type = self._snap_smart(raw_pt, self.wire_start, free_angle)
        self.guide_pos = snapped_pt

        if self.ghost_item:
            self.ghost_item.setPos(snapped_pt)

        if self.snap_marker and self.snap_marker.scene():
            self.scene().removeItem(self.snap_marker)
        self.snap_marker = None

        if not self.is_simulating and snap_type in ("TERMINAL", "WIRE"):
            self.snap_marker = QGraphicsEllipseItem(snapped_pt.x() - 5, snapped_pt.y() - 5, 10, 10)
            col = QColor("#00AA00") if snap_type == "TERMINAL" else QColor("#FF8800")
            self.snap_marker.setPen(QPen(col, 2.0))
            self.snap_marker.setZValue(10)
            self.scene().addItem(self.snap_marker)

        if self.wire_start is not None:
            if self.active_tool == "WIRE_3PHASE":
                self._update_3ph_preview(self.wire_start, snapped_pt)
            elif self.preview_line:
                self.preview_line.setLine(
                    self.wire_start.x(), self.wire_start.y(),
                    snapped_pt.x(), snapped_pt.y()
                )

        if hasattr(self.window(), "update_coords"):
            self.window().update_coords(snapped_pt.x(), snapped_pt.y())

        self.viewport().update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            if self.wire_start is not None:
                self._cancel_wire()
            else:
                self.set_active_tool(None)
                if hasattr(self.window(), "reset_tool_selection"):
                    self.window().reset_tool_selection()
            return

        if self.is_simulating:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            raw_pt = self.mapToScene(event.pos())
            free_angle = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

            if self.active_tool is None:
                self._pre_drag_state = serialize_scene_to_dict(self.scene())
                self._bind_elastic_wires()
                super().mousePressEvent(event)
                return

            if isinstance(self.active_tool, type) and issubclass(self.active_tool, ElectricalComponent):
                self.push_undo()
                pt = QPointF(round(raw_pt.x() / 10) * 10, round(raw_pt.y() / 10) * 10)
                comp = self.active_tool()
                if isinstance(comp, AUTO_NUMBER_CLASSES):
                    comp.label = get_next_available_label(self.scene(), comp.label)
                comp.setPos(pt)
                self.scene().addItem(comp)
                self.scene().ensure_margin_for_point(pt)
                self._update_ghost_item()
                return

            if self.active_tool in ("WIRE_PHASE", "WIRE_NEUTRAL", "WIRE_PE"):
                w_map = {"WIRE_PHASE": "PHASE", "WIRE_NEUTRAL": "NEUTRAL", "WIRE_PE": "PE"}
                w_type = w_map[self.active_tool]
                pt, snap_type = self._snap_smart(raw_pt, self.wire_start, free_angle)

                if self.wire_start is None:
                    self.wire_start = pt
                    self.preview_line = QGraphicsLineItem(pt.x(), pt.y(), pt.x(), pt.y())
                    self.preview_line.setPen(QPen(Wire.COLOR_MAP[w_type], 1.8, Qt.PenStyle.DashLine))
                    self.scene().addItem(self.preview_line)
                else:
                    if (pt - self.wire_start).manhattanLength() >= 5:
                        self.push_undo()
                        self.scene().ensure_margin_for_point(pt)
                        last_w = self._last_single_wire
                        if last_w and last_w.scene() == self.scene() and last_w.p2 == self.wire_start:
                            same_h = abs(last_w.p1.y() - last_w.p2.y()) < 1 and abs(pt.y() - self.wire_start.y()) < 1
                            same_v = abs(last_w.p1.x() - last_w.p2.x()) < 1 and abs(pt.x() - self.wire_start.x()) < 1
                            if same_h or same_v:
                                last_w.prepareGeometryChange()
                                last_w.p2 = pt
                                last_w.junction_p2 = self._split_wires_at(pt)
                                last_w.update()
                                if snap_type in ("TERMINAL", "WIRE"):
                                    self._cancel_wire()
                                else:
                                    self.wire_start = pt
                                    self.preview_line.setLine(pt.x(), pt.y(), pt.x(), pt.y())
                                return

                        j1 = self._split_wires_at(self.wire_start)
                        j2 = self._split_wires_at(pt)
                        w = Wire(self.wire_start, pt, w_type)
                        w.junction_p1 = j1
                        w.junction_p2 = j2
                        self.scene().addItem(w)
                        self._last_single_wire = w

                        if snap_type in ("TERMINAL", "WIRE"):
                            self._cancel_wire()
                        else:
                            self.wire_start = pt
                            self.preview_line.setLine(pt.x(), pt.y(), pt.x(), pt.y())
                return

            if self.active_tool == "WIRE_3PHASE":
                pt, snap_type = self._snap_smart(raw_pt, self.wire_start, False)
                if self.wire_start is None:
                    self.wire_start = pt
                    self._last_3ph_wires = None
                    self._last_3ph_dir = None
                else:
                    dx, dy = pt.x() - self.wire_start.x(), pt.y() - self.wire_start.y()
                    if abs(dx) + abs(dy) >= 5:
                        self.push_undo()
                        self.scene().ensure_margin_for_point(pt)
                        cur_dir = "H" if abs(dx) >= abs(dy) else "V"
                        new_wires = []
                        for idx, off in enumerate((-20, 0, 20)):
                            if cur_dir == "H":
                                a = QPointF(self.wire_start.x(), self.wire_start.y() + off)
                                b = QPointF(pt.x(), self.wire_start.y() + off)
                            else:
                                a = QPointF(self.wire_start.x() + off, self.wire_start.y())
                                b = QPointF(self.wire_start.x() + off, pt.y())

                            if self._last_3ph_wires and self._last_3ph_dir and self._last_3ph_dir != cur_dir:
                                prev_w = self._last_3ph_wires[idx]
                                corner = QPointF(prev_w.p1.x(), a.y()) if self._last_3ph_dir == "V" else QPointF(a.x(), prev_w.p1.y())
                                prev_w.prepareGeometryChange()
                                prev_w.p2 = corner
                                prev_w.update()
                                a = corner

                            j1 = self._split_wires_at(a)
                            j2 = self._split_wires_at(b)
                            w = Wire(a, b, "PHASE")
                            w.junction_p1 = j1
                            w.junction_p2 = j2
                            self.scene().addItem(w)
                            new_wires.append(w)

                        if snap_type in ("TERMINAL", "WIRE"):
                            self._cancel_wire()
                        else:
                            self.wire_start = QPointF(pt.x(), self.wire_start.y()) if cur_dir == "H" else QPointF(self.wire_start.x(), pt.y())
                            self._last_3ph_wires = new_wires
                            self._last_3ph_dir = cur_dir
                return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if not self.is_simulating and self.active_tool is None and hasattr(self, "_pre_drag_state"):
            for it in self.scene().selectedItems():
                if isinstance(it, ElectricalComponent):
                    self.scene().ensure_margin_for_point(it.pos())
            cur_state = serialize_scene_to_dict(self.scene())
            if cur_state != self._pre_drag_state:
                self.undo_stack.append(self._pre_drag_state)
                self.redo_stack.clear()
            delattr(self, "_pre_drag_state")

    def mouseDoubleClickEvent(self, event):
        pt = self.mapToScene(event.pos())
        if self.scene().title_block_rect().contains(pt):
            sc = self.scene()
            p, ok1 = QInputDialog.getText(self, "Cajetín - Proyecto", "Título del proyecto:", text=sc.meta_project)
            if ok1 and p.strip():
                sc.meta_project = p.strip().upper()
            a, ok2 = QInputDialog.getText(self, "Cajetín - Autor", "Autor / Alumno:", text=sc.meta_author)
            if ok2 and a.strip():
                sc.meta_author = a.strip().upper()
            sc.update()
            return

        closest_cable = None
        min_distance = float("inf")
        for item in self.scene().items():
            if isinstance(item, Wire):
                dist = self.point_to_segment_distance(pt, item.p1, item.p2)
                if dist < 10 and dist < min_distance:
                    min_distance = dist
                    closest_cable = item

        if closest_cable is not None:
            current_lbl = getattr(closest_cable, "label", "")
            text, ok = QInputDialog.getText(
                self,
                "Numeración de Cable",
                "Introduce la identificación del cable (ej. 1, L1, N):",
                text=current_lbl
            )
            if ok:
                self.push_undo()
                closest_cable.label = text.strip()
                closest_cable.update()
            return

        super().mouseDoubleClickEvent(event)

    def point_to_segment_distance(self, p, p1, p2):
        l2 = (p2.x() - p1.x())**2 + (p2.y() - p1.y())**2
        if l2 == 0:
            return math.hypot(p.x() - p1.x(), p.y() - p1.y())
        t = max(0, min(1, ((p.x() - p1.x()) * (p2.x() - p1.x()) + (p.y() - p1.y()) * (p2.y() - p1.y())) / l2))
        proj_x = p1.x() + t * (p2.x() - p1.x())
        proj_y = p1.y() + t * (p2.y() - p1.y())
        return math.hypot(p.x() - proj_x, p.y() - proj_y)

    def drawForeground(self, painter: QPainter, rect: QRectF):
        super().drawForeground(painter, rect)
        if self.show_guides and not self.is_simulating and self.active_tool is not None:
            pen = QPen(QColor(0, 120, 215, 130), 1.0, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            gx, gy = self.guide_pos.x(), self.guide_pos.y()
            painter.drawLine(int(rect.left()), int(gy), int(rect.right()), int(gy))
            painter.drawLine(int(gx), int(rect.top()), int(gx), int(rect.bottom()))

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Undo):
            self.undo()
            return
        if event.matches(QKeySequence.StandardKey.Redo):
            self.redo()
            return
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selected()
            return
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste_clipboard()
            return
        if event.key() == Qt.Key.Key_Escape:
            if self.wire_start is not None:
                self._cancel_wire()
            else:
                self.set_active_tool(None)
                if hasattr(self.window(), "reset_tool_selection"):
                    self.window().reset_tool_selection()
            return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace) and not self.is_simulating:
            selected = self.scene().selectedItems()
            if selected:
                self.push_undo()
                for item in selected:
                    self.scene().removeItem(item)
            return
        super().keyPressEvent(event)
