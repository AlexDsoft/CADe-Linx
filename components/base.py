from PyQt6.QtWidgets import QGraphicsItem, QGraphicsObject
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QPainter, QFont

class Terminal:
    def __init__(self, parent_comp, name: str, rel_x: float, rel_y: float):
        self.parent = parent_comp
        self.name = name
        self.rel_pos = QPointF(rel_x, rel_y)
        self.potential = None  # "L1", "L2", "L3", "N", "PE", None

    def scene_pos(self) -> QPointF:
        return self.parent.mapToScene(self.rel_pos)


class Wire(QGraphicsItem):
    COLOR_MAP = {
        "PHASE": QColor("#8B4513"),    # Marrón fase IEC
        "NEUTRAL": QColor("#0055CC"),  # Azul neutro IEC
        "PE": QColor("#228B22"),       # Verde/Amarillo protección
    }

    def __init__(self, p1: QPointF, p2: QPointF, wire_type: str = "PHASE"):
        super().__init__()
        self.p1 = QPointF(p1)
        self.p2 = QPointF(p2)
        self.wire_type = wire_type
        self.energized = False
        self.potential = None
        self.junction_p1 = False
        self.junction_p2 = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(1)

    def boundingRect(self) -> QRectF:
        x1, y1 = min(self.p1.x(), self.p2.x()), min(self.p1.y(), self.p2.y())
        x2, y2 = max(self.p1.x(), self.p2.x()), max(self.p1.y(), self.p2.y())
        return QRectF(x1 - 8, y1 - 8, (x2 - x1) + 16, (y2 - y1) + 16)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isSelected():
            pen = QPen(QColor("#FF8800"), 3.0, Qt.PenStyle.DashLine)
        elif self.energized:
            if self.potential == "N":
                pen = QPen(QColor("#0088FF"), 3.2)
            else:
                pen = QPen(QColor("#FF1111"), 3.2)
        else:
            base_col = self.COLOR_MAP.get(self.wire_type, QColor("#222222"))
            style = Qt.PenStyle.DashDotLine if self.wire_type == "PE" else Qt.PenStyle.SolidLine
            pen = QPen(base_col, 2.0, style)

        painter.setPen(pen)
        painter.drawLine(self.p1, self.p2)

        # Puntos de empalme (nodos rellenos en derivaciones en T)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(pen.color()))
        if self.junction_p1:
            painter.drawEllipse(self.p1, 3.5, 3.5)
        if self.junction_p2:
            painter.drawEllipse(self.p2, 3.5, 3.5)


class ElectricalComponent(QGraphicsObject):
    def __init__(self, label: str = "X1"):
        super().__init__()
        self.label = label
        self.terminals = []
        self.is_simulating = False
        self.energized = False
        self.active_state = False
        self._is_ghost = False
        self._last_elastic_pos = QPointF(0, 0)
        self._attached_wires_p1 = []
        self._attached_wires_p2 = []

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(2)

    def add_terminal(self, name: str, x: float, y: float) -> Terminal:
        t = Terminal(self, name, x, y)
        self.terminals.append(t)
        return t

    def boundingRect(self) -> QRectF:
        return QRectF(-60, -50, 120, 100)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value
            snapped = QPointF(round(new_pos.x() / 10) * 10, round(new_pos.y() / 10) * 10)
            return snapped
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.scene():
            old_pos = getattr(self, "_last_elastic_pos", None)
            new_pos = value
            if old_pos is not None and old_pos != new_pos and not getattr(self, "_is_ghost", False):
                delta = new_pos - old_pos
                for w in getattr(self, "_attached_wires_p1", []):
                    w.prepareGeometryChange()
                    w.p1 = w.p1 + delta
                    w.update()
                for w in getattr(self, "_attached_wires_p2", []):
                    w.prepareGeometryChange()
                    w.p2 = w.p2 + delta
                    w.update()
            self._last_elastic_pos = QPointF(new_pos)
        return super().itemChange(change, value)

    def draw_terminals_and_label(self, painter: QPainter, label_offset=QPointF(-42, 5)):
        # Dibujar bornes rojos y sus números
        painter.setFont(QFont("SansSerif", 7))
        for t in self.terminals:
            painter.setPen(QPen(QColor("#CC0000"), 1.2))
            painter.setBrush(QBrush(QColor("#FF3333")))
            painter.drawEllipse(t.rel_pos, 2.5, 2.5)
            painter.setPen(QPen(QColor("#555555"), 1.0))
            painter.drawText(QPointF(t.rel_pos.x() + 4, t.rel_pos.y() - 3), t.name)

        # Dibujar identificador del componente (KM1, Q1, F1, etc.)
        painter.setFont(QFont("SansSerif", 9, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#002266"), 1.2))
        painter.drawText(label_offset, self.label)

        if self.isSelected():
            painter.setPen(QPen(QColor("#FF8800"), 1.2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect().adjusted(4, 4, -4, -4))

    def internal_connections(self):
        return []
