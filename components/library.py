import re
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QPainter, QFont, QPolygonF
from PyQt6.QtWidgets import QInputDialog, QMessageBox
from components.base import ElectricalComponent


# ==========================================
# 1. ALIMENTACIÓN (UNE-EN 60617-02)
# ==========================================
class PowerSupply1P(ElectricalComponent):
    def __init__(self, label: str = "L-N"):
        super().__init__(label)
        self.t_l = self.add_terminal("L", -10, 20)
        self.t_n = self.add_terminal("N", 10, 20)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#8B4513"), 2.0))
        painter.drawLine(-10, -15, -10, 20)
        painter.drawEllipse(QPointF(-10, -18), 3, 3)
        painter.setPen(QPen(QColor("#0055CC"), 2.0))
        painter.drawLine(10, -15, 10, 20)
        painter.drawEllipse(QPointF(10, -18), 3, 3)
        painter.setFont(QFont("SansSerif", 8, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#111111"), 1.2))
        painter.drawText(QPointF(-14, -25), "L")
        painter.drawText(QPointF(6, -25), "N")
        self.draw_terminals_and_label(painter, QPointF(-42, 0))


class PowerSupply3P(ElectricalComponent):
    def __init__(self, label: str = "L1-L3"):
        super().__init__(label)
        self.t_l1 = self.add_terminal("L1", -20, 20)
        self.t_l2 = self.add_terminal("L2", 0, 20)
        self.t_l3 = self.add_terminal("L3", 20, 20)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for x, name in [(-20, "L1"), (0, "L2"), (20, "L3")]:
            painter.setPen(QPen(QColor("#8B4513"), 2.0))
            painter.drawLine(x, -15, x, 20)
            painter.drawEllipse(QPointF(x, -18), 3, 3)
            painter.setFont(QFont("SansSerif", 8, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#111111"), 1.2))
            painter.drawText(QPointF(x - 7, -25), name)
        self.draw_terminals_and_label(painter, QPointF(-58, 0))


class PowerSupply3PN(ElectricalComponent):
    def __init__(self, label: str = "3P+N+PE"):
        super().__init__(label)
        self.t_l1 = self.add_terminal("L1", -30, 20)
        self.t_l2 = self.add_terminal("L2", -10, 20)
        self.t_l3 = self.add_terminal("L3", 10, 20)
        self.t_n = self.add_terminal("N", 30, 20)
        self.t_pe = self.add_terminal("PE", 50, 20)

    def boundingRect(self) -> QRectF:
        return QRectF(-75, -50, 145, 100)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for x, name, col in [
            (-30, "L1", "#8B4513"), (-10, "L2", "#8B4513"), (10, "L3", "#8B4513"),
            (30, "N", "#0055CC"), (50, "PE", "#228B22")
        ]:
            painter.setPen(QPen(QColor(col), 2.0))
            painter.drawLine(x, -15, x, 20)
            painter.drawEllipse(QPointF(x, -18), 3, 3)
            painter.setFont(QFont("SansSerif", 7, QFont.Weight.Bold))
            painter.setPen(QPen(QColor("#111111"), 1.2))
            painter.drawText(QPointF(x - 7, -25), name)
        self.draw_terminals_and_label(painter, QPointF(-70, 0))


class GroundPE(ElectricalComponent):
    def __init__(self, label: str = "PE"):
        super().__init__(label)
        self.t_pe = self.add_terminal("PE", 0, -20)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#228B22"), 2.0))
        painter.drawLine(0, -20, 0, 0)
        painter.drawLine(-14, 0, 14, 0)
        painter.drawLine(-9, 5, 9, 5)
        painter.drawLine(-4, 10, 4, 10)
        self.draw_terminals_and_label(painter, QPointF(-35, 5))


# ==========================================
# 2. FUSIBLES Y DISYUNTORES MAGNETOTÉRMICOS (UNE-EN 60617-07)
# ==========================================
class Fuse1P(ElectricalComponent):
    def __init__(self, label: str = "F1"):
        super().__init__(label)
        self.add_terminal("1", 0, -30)
        self.add_terminal("2", 0, 30)
        self.active_state = True

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#111111"), 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(-6, -15, 12, 30)
        painter.drawLine(0, -30, 0, 30)
        self.draw_terminals_and_label(painter, QPointF(-35, 5))

    def internal_connections(self):
        return [(self.terminals[0], self.terminals[1])] if self.active_state else []


class Breaker1P(ElectricalComponent):
    def __init__(self, label: str = "Q1"):
        super().__init__(label)
        self.add_terminal("1", 0, -30)
        self.add_terminal("2", 0, 30)

    def mousePressEvent(self, event):
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            self.active_state = not self.active_state
            self.update()
            return
        super().mousePressEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        painter.setPen(QPen(col, 2.0))
        painter.drawLine(0, -30, 0, -12)
        painter.drawLine(0, 12, 0, 30)
        painter.drawLine(-3, -15, 3, -9)
        painter.drawLine(-3, -9, 3, -15)
        if self.active_state:
            painter.drawLine(0, 12, 0, -12)
        else:
            painter.drawLine(0, 12, -10, -10)
        painter.setPen(QPen(QColor("#333333"), 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(-12, 0, -5, 0)
        painter.setPen(QPen(QColor("#111111"), 1.4))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRect(-26, -12, 14, 24)
        painter.drawLine(-26, 0, -12, 0)
        painter.drawLine(-22, -6, -19, -6)
        painter.drawLine(-19, -6, -19, -9)
        painter.drawLine(-19, -9, -16, -9)
        painter.setFont(QFont("SansSerif", 6, QFont.Weight.Bold))
        painter.drawText(QPointF(-24, 9), "I>")
        self.draw_terminals_and_label(painter, QPointF(-48, 5))

    def internal_connections(self):
        return [(self.terminals[0], self.terminals[1])] if self.active_state else []


class Breaker3P(ElectricalComponent):
    def __init__(self, label: str = "Q1"):
        super().__init__(label)
        for idx, x in enumerate((-20, 0, 20)):
            self.add_terminal(str(idx * 2 + 1), x, -30)
            self.add_terminal(str(idx * 2 + 2), x, 30)

    def mousePressEvent(self, event):
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            self.active_state = not self.active_state
            self.update()
            for it in (self.scene().items() if self.scene() else []):
                if isinstance(it, ElectricalComponent) and it is not self and it.label.upper() == self.label.upper():
                    it.active_state = self.active_state
                    it.update()
            return
        super().mousePressEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        painter.setPen(QPen(col, 2.0))
        for x in (-20, 0, 20):
            painter.drawLine(x, -30, x, -12)
            painter.drawLine(x, 12, x, 30)
            painter.drawLine(x - 3, -15, x + 3, -9)
            painter.drawLine(x - 3, -9, x + 3, -15)
            if self.active_state:
                painter.drawLine(x, 12, x, -12)
            else:
                painter.drawLine(x, 12, x - 10, -10)
        painter.setPen(QPen(QColor("#333333"), 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(-30, 0, 16, 0)
        painter.setPen(QPen(QColor("#111111"), 1.4))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRect(-44, -12, 14, 24)
        painter.drawLine(-44, 0, -30, 0)
        painter.drawLine(-40, -6, -37, -6)
        painter.drawLine(-37, -6, -37, -9)
        painter.drawLine(-37, -9, -34, -9)
        painter.setFont(QFont("SansSerif", 6, QFont.Weight.Bold))
        painter.drawText(QPointF(-42, 9), "I>")
        self.draw_terminals_and_label(painter, QPointF(-68, 5))

    def internal_connections(self):
        if not self.active_state:
            return []
        return [
            (self.terminals[0], self.terminals[1]),
            (self.terminals[2], self.terminals[3]),
            (self.terminals[4], self.terminals[5]),
        ]


# ==========================================
# 3. CONTACTORES, RELÉ TÉRMICO (F1) Y MOTORES (UNE-EN 60617-07 / 06)
# ==========================================
class Contactor3P(ElectricalComponent):
    def __init__(self, label: str = "KM1"):
        super().__init__(label)
        for idx, x in enumerate((-20, 0, 20)):
            self.add_terminal(str(idx * 2 + 1), x, -30)
            self.add_terminal(str(idx * 2 + 2), x, 30)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        painter.setPen(QPen(col, 2.0))
        for x in (-20, 0, 20):
            painter.drawLine(x, -30, x, -12)
            painter.drawLine(x, 12, x, 30)
            painter.drawArc(x - 4, -15, 8, 6, 0, -180 * 16)
            if self.active_state:
                painter.drawLine(x, 12, x, -12)
            else:
                painter.drawLine(x, 12, x - 10, -10)
        painter.setPen(QPen(QColor("#333333"), 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(-25, 0, 16, 0)
        self.draw_terminals_and_label(painter, QPointF(-58, 5))

    def internal_connections(self):
        if not self.active_state:
            return []
        return [
            (self.terminals[0], self.terminals[1]),
            (self.terminals[2], self.terminals[3]),
            (self.terminals[4], self.terminals[5]),
        ]


class ThermalRelay3P(ElectricalComponent):
    def __init__(self, label: str = "F1"):
        super().__init__(label)
        for idx, x in enumerate((-20, 0, 20)):
            self.add_terminal(str(idx * 2 + 1), x, -30)
            self.add_terminal(str(idx * 2 + 2), x, 30)

    def mousePressEvent(self, event):
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            self.active_state = not self.active_state
            self.update()
            for it in (self.scene().items() if self.scene() else []):
                if isinstance(it, ElectricalComponent) and it is not self and it.label.upper() == self.label.upper():
                    it.active_state = self.active_state
                    it.update()
            return
        super().mousePressEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#FF6600") if self.active_state else QColor("#111111")
        painter.setPen(QPen(col, 2.0))
        for x in (-20, 0, 20):
            painter.drawLine(x, -30, x, -10)
            painter.drawLine(x, -10, x - 6, -10)
            painter.drawLine(x - 6, -10, x - 6, 4)
            painter.drawLine(x - 6, 4, x, 4)
            painter.drawLine(x, 4, x, 30)
        painter.setPen(QPen(QColor("#333333"), 1.2, Qt.PenStyle.DashLine))
        painter.drawLine(-32, -3, 18, -3)
        painter.setPen(QPen(col, 1.4))
        painter.setBrush(QBrush(QColor("#FFE0B2") if self.active_state else QColor("#FFFFFF")))
        painter.drawRect(-44, -11, 12, 16)
        self.draw_terminals_and_label(painter, QPointF(-66, 5))

    def internal_connections(self):
        return [
            (self.terminals[0], self.terminals[1]),
            (self.terminals[2], self.terminals[3]),
            (self.terminals[4], self.terminals[5]),
        ]


class Motor3P(ElectricalComponent):
    def __init__(self, label: str = "M1"):
        super().__init__(label)
        self.add_terminal("U1", -20, -30)
        self.add_terminal("V1", 0, -30)
        self.add_terminal("W1", 20, -30)
        self.add_terminal("PE", 30, 5)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pots = {self.terminals[i].potential for i in (0, 1, 2) if self.terminals[i].potential in ("L1", "L2", "L3")}
        running = len(pots) >= 3
        painter.setPen(QPen(QColor("#111111"), 2.0))
        painter.drawLine(-20, -30, -20, -14)
        painter.drawLine(0, -30, 0, -19)
        painter.drawLine(20, -30, 20, -14)
        painter.drawLine(24, 5, 30, 5)
        painter.setBrush(QBrush(QColor("#B9F6CA") if running else QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(0, 5), 24, 24)
        painter.setFont(QFont("SansSerif", 10, QFont.Weight.Bold))
        painter.drawText(QRectF(-20, -12, 40, 20), Qt.AlignmentFlag.AlignCenter, "M")
        painter.drawText(QRectF(-20, 4, 40, 20), Qt.AlignmentFlag.AlignCenter, "3~")
        self.draw_terminals_and_label(painter, QPointF(-54, 10))


class Motor3P_YD(ElectricalComponent):
    def __init__(self, label: str = "M1"):
        super().__init__(label)
        self.add_terminal("U1", -20, -30)
        self.add_terminal("V1", 0, -30)
        self.add_terminal("W1", 20, -30)
        self.add_terminal("W2", -20, 30)
        self.add_terminal("U2", 0, 30)
        self.add_terminal("V2", 20, 30)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pots_top = {self.terminals[i].potential for i in (0, 1, 2) if self.terminals[i].potential in ("L1", "L2", "L3")}
        pots_bot = {self.terminals[i].potential for i in (3, 4, 5) if self.terminals[i].potential is not None}
        running = len(pots_top) >= 3 and len(pots_bot) >= 1
        painter.setPen(QPen(QColor("#111111"), 2.0))
        for x in (-20, 0, 20):
            painter.drawLine(x, -30, x, -15)
            painter.drawLine(x, 15, x, 30)
        painter.setBrush(QBrush(QColor("#B9F6CA") if running else QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(0, 0), 22, 22)
        painter.setFont(QFont("SansSerif", 9, QFont.Weight.Bold))
        painter.drawText(QRectF(-20, -14, 40, 18), Qt.AlignmentFlag.AlignCenter, "M")
        painter.drawText(QRectF(-20, 0, 40, 18), Qt.AlignmentFlag.AlignCenter, "3~")
        self.draw_terminals_and_label(painter, QPointF(-54, 5))


# ==========================================
# 4. PULSADORES CON RETORNO AUTOMÁTICO, SETA Y FINALES DE CARRERA (UNE-EN 60617-07)
# ==========================================
def _draw_no_contact(painter: QPainter, active: bool, col: QColor):
    painter.setPen(QPen(col, 2.0))
    painter.drawLine(0, -30, 0, -12)
    painter.drawLine(0, 12, 0, 30)
    bx = 0 if active else -11
    painter.drawLine(0, 12, bx, -11)
    return bx // 2


def _draw_nc_contact(painter: QPainter, active: bool, col: QColor):
    painter.setPen(QPen(col, 2.0))
    painter.drawLine(0, -30, 0, -12)
    painter.drawLine(0, -12, 7, -12)
    painter.drawLine(0, 12, 0, 30)
    bx = -9 if active else 5
    painter.drawLine(0, 12, bx, -14)
    return bx // 2


def _draw_pushbutton_actuator(painter: QPainter, mid_x: int, col: QColor):
    """
    Símbolo normalizado UNE-EN 60617 (07-02-02 + 02-12-07) de Pulsador manual por empuje
    con retorno automático:
    - Corchete de empuje ']' cuyas alas apuntan HACIA el contacto (derecha), no hacia afuera.
    - Enlace mecánico discontinuo con triángulo de retorno automático hacia la izquierda.
    """
    painter.setPen(QPen(QColor("#333333"), 1.3, Qt.PenStyle.DashLine))
    painter.drawLine(-18, 0, mid_x, 0)
    painter.setPen(QPen(col, 2.0))
    # Pared vertical del botón en x=-18 y alas hacia la derecha (x=-14) envolviendo el vástago (empuje)
    painter.drawLine(-18, -7, -18, 7)
    painter.drawLine(-18, -7, -14, -7)
    painter.drawLine(-18, 7, -14, 7)


class PushButtonNO(ElectricalComponent):
    def __init__(self, label: str = "S1"):
        super().__init__(label)
        self.add_terminal("13", 0, -30)
        self.add_terminal("14", 0, 30)

    def mousePressEvent(self, event):
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            # Con Shift se enclava/desenclava; con clic normal actúa con retorno automático al soltar
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.active_state = not self.active_state
            else:
                self.active_state = True
            self._sync_same_label()
            self.update()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.active_state = False
                self._sync_same_label()
                self.update()
            return
        super().mouseReleaseEvent(event)

    def _sync_same_label(self):
        for it in (self.scene().items() if self.scene() else []):
            if isinstance(it, ElectricalComponent) and it is not self and it.label.upper() == self.label.upper():
                it.active_state = self.active_state
                it.update()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#009900") if self.active_state else QColor("#111111")
        mid_x = _draw_no_contact(painter, self.active_state, col)
        _draw_pushbutton_actuator(painter, mid_x, col)
        self.draw_terminals_and_label(painter, QPointF(-46, 5))

    def internal_connections(self):
        return [(self.terminals[0], self.terminals[1])] if self.active_state else []


class PushButtonNC(ElectricalComponent):
    def __init__(self, label: str = "S0"):
        super().__init__(label)
        self.add_terminal("11", 0, -30)
        self.add_terminal("12", 0, 30)

    def mousePressEvent(self, event):
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.active_state = not self.active_state
            else:
                self.active_state = True
            self._sync_same_label()
            self.update()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.active_state = False
                self._sync_same_label()
                self.update()
            return
        super().mouseReleaseEvent(event)

    def _sync_same_label(self):
        for it in (self.scene().items() if self.scene() else []):
            if isinstance(it, ElectricalComponent) and it is not self and it.label.upper() == self.label.upper():
                it.active_state = self.active_state
                it.update()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        mid_x = _draw_nc_contact(painter, self.active_state, col)
        _draw_pushbutton_actuator(painter, mid_x, col)
        self.draw_terminals_and_label(painter, QPointF(-46, 5))

    def internal_connections(self):
        return [] if self.active_state else [(self.terminals[0], self.terminals[1])]


class EmergencyStopNC(PushButtonNC):
    def __init__(self, label: str = "S_EM"):
        super().__init__(label)

    def mousePressEvent(self, event):
        # El paro de emergencia tiene enclavamiento mecánico: queda pulsado al hacer clic
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            self.active_state = not self.active_state
            self._sync_same_label()
            self.update()
            return
        super(PushButtonNC, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_simulating:
            return
        super(PushButtonNC, self).mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        mid_x = _draw_nc_contact(painter, self.active_state, col)
        # Vástago con muesca en V de enclavamiento mecánico + cabeza de seta UNE-EN 60617
        painter.setPen(QPen(QColor("#333333"), 1.3, Qt.PenStyle.DashLine))
        painter.drawLine(-16, 0, -10, 0)
        painter.drawLine(-10, 0, -8, -4)
        painter.drawLine(-8, -4, -6, 0)
        painter.drawLine(-6, 0, mid_x, 0)
        painter.setPen(QPen(QColor("#CC0000"), 2.0))
        painter.setBrush(QBrush(QColor("#FF3333")))
        painter.drawChord(-23, -8, 12, 16, 90 * 16, 180 * 16)
        self.draw_terminals_and_label(painter, QPointF(-52, 5))


class LimitSwitchNO(PushButtonNO):
    def __init__(self, label: str = "BG1"):
        super().__init__(label)

    def mousePressEvent(self, event):
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            self.active_state = not self.active_state
            self._sync_same_label()
            self.update()
            return
        super(PushButtonNO, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_simulating:
            return
        super(PushButtonNO, self).mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#009900") if self.active_state else QColor("#111111")
        mid_x = _draw_no_contact(painter, self.active_state, col)
        painter.setPen(QPen(QColor("#333333"), 1.3, Qt.PenStyle.DashLine))
        painter.drawLine(-14, 0, mid_x, 0)
        painter.setPen(QPen(col, 1.8))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(-18, 0), 4, 4)
        self.draw_terminals_and_label(painter, QPointF(-48, 5))


class LimitSwitchNC(PushButtonNC):
    def __init__(self, label: str = "BG2"):
        super().__init__(label)

    def mousePressEvent(self, event):
        if self.is_simulating and event.button() == Qt.MouseButton.LeftButton:
            self.active_state = not self.active_state
            self._sync_same_label()
            self.update()
            return
        super(PushButtonNC, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_simulating:
            return
        super(PushButtonNC, self).mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        mid_x = _draw_nc_contact(painter, self.active_state, col)
        painter.setPen(QPen(QColor("#333333"), 1.3, Qt.PenStyle.DashLine))
        painter.drawLine(-14, 0, mid_x, 0)
        painter.setPen(QPen(col, 1.8))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(-18, 0), 4, 4)
        self.draw_terminals_and_label(painter, QPointF(-48, 5))


# ==========================================
# 5. CONTACTOS AUXILIARES (MANIOBRA, TÉRMICOS Y TEMPORIZADOS UNE-EN 60617-07)
# ==========================================
class AuxContactNO(ElectricalComponent):
    def __init__(self, label: str = "KM1"):
        super().__init__(label)
        self.add_terminal("13", 0, -30)
        self.add_terminal("14", 0, 30)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        _draw_no_contact(painter, self.active_state, col)
        self.draw_terminals_and_label(painter, QPointF(-42, 5))

    def internal_connections(self):
        return [(self.terminals[0], self.terminals[1])] if self.active_state else []


class AuxContactNC(ElectricalComponent):
    def __init__(self, label: str = "KM1"):
        super().__init__(label)
        self.add_terminal("21", 0, -30)
        self.add_terminal("22", 0, 30)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        _draw_nc_contact(painter, self.active_state, col)
        self.draw_terminals_and_label(painter, QPointF(-42, 5))

    def internal_connections(self):
        return [] if self.active_state else [(self.terminals[0], self.terminals[1])]


class AuxThermalNO(AuxContactNO):
    def __init__(self, label: str = "F1"):
        super().__init__(label)
        self.terminals[0].name = "97"
        self.terminals[1].name = "98"

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#FF6600") if self.active_state else QColor("#111111")
        mid_x = _draw_no_contact(painter, self.active_state, col)
        painter.setPen(QPen(col, 1.5))
        painter.drawLine(mid_x, 0, -10, 0)
        painter.drawLine(-10, 0, -10, -4)
        painter.drawLine(-10, -4, -15, -4)
        painter.drawLine(-15, -4, -15, 0)
        painter.drawLine(-15, 0, -19, 0)
        self.draw_terminals_and_label(painter, QPointF(-45, 5))


class AuxThermalNC(AuxContactNC):
    def __init__(self, label: str = "F1"):
        super().__init__(label)
        self.terminals[0].name = "95"
        self.terminals[1].name = "96"

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#FF6600") if self.active_state else QColor("#111111")
        mid_x = _draw_nc_contact(painter, self.active_state, col)
        painter.setPen(QPen(col, 1.5))
        painter.drawLine(mid_x, 0, -10, 0)
        painter.drawLine(-10, 0, -10, -4)
        painter.drawLine(-10, -4, -15, -4)
        painter.drawLine(-15, -4, -15, 0)
        painter.drawLine(-15, 0, -19, 0)
        self.draw_terminals_and_label(painter, QPointF(-45, 5))


def _draw_parachute_ton(painter: QPainter, mid_x: int):
    painter.setPen(QPen(QColor("#0055AA"), 1.4))
    painter.drawLine(-14, -2, mid_x, -2)
    painter.drawLine(-14, 2, mid_x, 2)
    painter.drawArc(-22, -7, 10, 14, 90 * 16, 180 * 16)


def _draw_parachute_tof(painter: QPainter, mid_x: int):
    painter.setPen(QPen(QColor("#0055AA"), 1.4))
    painter.drawLine(-15, -2, mid_x, -2)
    painter.drawLine(-15, 2, mid_x, 2)
    painter.drawArc(-20, -7, 10, 14, -90 * 16, 180 * 16)


class TimerContactTON_NO(AuxContactNO):
    def __init__(self, label: str = "-KT1"):
        super().__init__(label)
        self.terminals[0].name = "55"
        self.terminals[1].name = "56"

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        mid_x = _draw_no_contact(painter, self.active_state, col)
        _draw_parachute_ton(painter, mid_x)
        self.draw_terminals_and_label(painter, QPointF(-52, 5))


class TimerContactTON_NC(AuxContactNC):
    def __init__(self, label: str = "-KT1"):
        super().__init__(label)
        self.terminals[0].name = "65"
        self.terminals[1].name = "66"

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        mid_x = _draw_nc_contact(painter, self.active_state, col)
        _draw_parachute_ton(painter, mid_x)
        self.draw_terminals_and_label(painter, QPointF(-52, 5))


class TimerContactTOF_NO(AuxContactNO):
    def __init__(self, label: str = "-KT1"):
        super().__init__(label)
        self.terminals[0].name = "57"
        self.terminals[1].name = "58"

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        mid_x = _draw_no_contact(painter, self.active_state, col)
        _draw_parachute_tof(painter, mid_x)
        self.draw_terminals_and_label(painter, QPointF(-52, 5))


class TimerContactTOF_NC(AuxContactNC):
    def __init__(self, label: str = "-KT1"):
        super().__init__(label)
        self.terminals[0].name = "67"
        self.terminals[1].name = "68"

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor("#CC0000") if self.active_state else QColor("#111111")
        mid_x = _draw_nc_contact(painter, self.active_state, col)
        _draw_parachute_tof(painter, mid_x)
        self.draw_terminals_and_label(painter, QPointF(-52, 5))


# ==========================================
# 6. BOBINAS, TEMPORIZADORES Y PILOTOS LUMINOSOS (UNE-EN 60617-07 / 08)
# ==========================================
class ContactorCoil(ElectricalComponent):
    def __init__(self, label: str = "KM1"):
        super().__init__(label)
        self.add_terminal("A1", 0, -30)
        self.add_terminal("A2", 0, 30)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#111111"), 2.0))
        painter.drawLine(0, -30, 0, -12)
        painter.drawLine(0, 12, 0, 30)
        painter.setBrush(QBrush(QColor("#FF9999") if self.energized else QColor("#FFFFFF")))
        painter.drawRect(-16, -12, 32, 24)
        self.draw_terminals_and_label(painter, QPointF(-48, 5))


class TimerCoilTON(ContactorCoil):
    def __init__(self, label: str = "-KT1"):
        super().__init__(label)
        self.delay_sec = 3.0
        self.remaining_sec = 3.0

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#111111"), 1.5))
        painter.drawLine(-6, -12, -6, 12)
        painter.drawLine(-16, -12, -6, 12)
        painter.drawLine(-6, -12, -16, 12)
        painter.setFont(QFont("SansSerif", 7, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#0044AA"), 1.2))
        txt = f"{self.remaining_sec:.1f}s" if self.is_simulating else f"TON {self.delay_sec:.1f}s"
        painter.drawText(QPointF(20, 4), txt)


class TimerCoilTOF(ContactorCoil):
    def __init__(self, label: str = "-KT1"):
        super().__init__(label)
        self.delay_sec = 3.0
        self.remaining_sec = 3.0

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setBrush(QBrush(QColor("#222222")))
        painter.drawRect(-16, -12, 10, 24)
        painter.setFont(QFont("SansSerif", 7, QFont.Weight.Bold))
        painter.setPen(QPen(QColor("#0044AA"), 1.2))
        txt = f"{self.remaining_sec:.1f}s" if self.is_simulating else f"TOF {self.delay_sec:.1f}s"
        painter.drawText(QPointF(20, 4), txt)


class PilotLamp(ElectricalComponent):
    COLOR_PALETTE = {
        "verde": ("#C8E6C9", "#00E676"),
        "rojo": ("#FFCDD2", "#FF1744"),
        "amarillo": ("#FFF9C4", "#FFEA00"),
        "azul": ("#BBDEFB", "#2979FF"),
    }

    def __init__(self, label: str = "H1"):
        super().__init__(label)
        self.lamp_color = "verde"
        self.add_terminal("X1", 0, -30)
        self.add_terminal("X2", 0, 30)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        off_hex, on_hex = self.COLOR_PALETTE.get(self.lamp_color, ("#C8E6C9", "#00E676"))
        painter.setPen(QPen(QColor("#111111"), 2.0))
        painter.drawLine(0, -30, 0, -14)
        painter.drawLine(0, 14, 0, 30)
        painter.setBrush(QBrush(QColor(on_hex if self.energized else off_hex)))
        painter.drawEllipse(QPointF(0, 0), 14, 14)
        painter.drawLine(-10, -10, 10, 10)
        painter.drawLine(-10, 10, 10, -10)
        self.draw_terminals_and_label(painter, QPointF(-42, 5))


# ==========================================
# 7. AUTONUMERACIÓN CORRELATIVA Y SINCRONIZACIÓN RÁPIDA DE CONTACTOS
# ==========================================
def get_next_available_label(scene, base_label: str) -> str:
    existing = {
        item.label.strip().upper()
        for item in scene.items()
        if isinstance(item, ElectricalComponent) and hasattr(item, "label") and not getattr(item, "_is_ghost", False)
    }
    clean_base = base_label.strip()
    if clean_base.upper() not in existing:
        return clean_base
    m = re.match(r"^(.*?)(\d+)$", clean_base)
    if m:
        prefix = m.group(1)
        num = int(m.group(2)) + 1
    else:
        prefix = clean_base
        num = 1
    while f"{prefix}{num}".upper() in existing:
        num += 1
    return f"{prefix}{num}"


AUTO_NUMBER_CLASSES = (
    Fuse1P, Breaker1P, Breaker3P, Contactor3P, ThermalRelay3P,
    Motor3P, Motor3P_YD, PushButtonNO, PushButtonNC, EmergencyStopNC,
    LimitSwitchNO, LimitSwitchNC, ContactorCoil, TimerCoilTON, TimerCoilTOF, PilotLamp
)


def _synced_double_click(self, event):
    if self.is_simulating:
        return
    old_label = self.label
    if isinstance(self, PilotLamp):
        colores = ["verde", "rojo", "amarillo", "azul"]
        idx = colores.index(self.lamp_color) if self.lamp_color in colores else 0
        col_sel, ok_c = QInputDialog.getItem(
            None, "Color de la Bombilla", "Selecciona el color del piloto:", colores, idx, False
        )
        if ok_c and col_sel:
            self.lamp_color = col_sel
            self.update()

    if hasattr(self, "delay_sec"):
        new_label, ok = QInputDialog.getText(
            None, "Renombrar Temporizador", "Identificador (ej. -KT1):", text=self.label
        )
        if ok and new_label.strip():
            self.label = new_label.strip().upper()
        val, ok2 = QInputDialog.getDouble(
            None, "Tiempo del Temporizador", "Segundos (TON/TOF):",
            value=float(self.delay_sec), min=0.5, max=3600.0, decimals=1
        )
        if ok2:
            self.delay_sec = val
            self.remaining_sec = val
        self.update()
    else:
        new_label, ok = QInputDialog.getText(
            None, "Renombrar Componente", "Identificador (ej. KM1, Q1, S1, F1):", text=self.label
        )
        if ok and new_label.strip():
            self.label = new_label.strip().upper()
            self.update()

    if self.label != old_label and self.scene():
        associated = [
            it for it in self.scene().items()
            if isinstance(it, ElectricalComponent) and it is not self
            and not getattr(it, "_is_ghost", False) and it.label.upper() == old_label.upper()
        ]
        if associated:
            resp = QMessageBox.question(
                None,
                "Sincronizar contactos asociados",
                f"Se han encontrado {len(associated)} elemento(s) asociado(s) con el nombre '{old_label}'.\n"
                f"¿Deseas actualizarlos todos automáticamente a '{self.label}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if resp == QMessageBox.StandardButton.Yes:
                for it in associated:
                    it.label = self.label
                    it.update()


ElectricalComponent.mouseDoubleClickEvent = _synced_double_click
