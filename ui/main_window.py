from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox, QButtonGroup,
    QDialog, QTextBrowser, QSizePolicy
)
from PyQt6.QtGui import QAction, QPainter, QImage, QPageLayout, QPageSize, QPdfWriter, QKeySequence, QIcon, QPixmap, QPen, QColor
from PyQt6.QtCore import Qt, QTimer, QRectF, QMarginsF, QSize

from canvas.sheet import SchematicScene, SchematicView
from engine.simulator import CircuitSimulator
from engine.storage import save_schematic, load_schematic
from components.library import (
    PowerSupply1P, PowerSupply3P, PowerSupply3PN, GroundPE,
    Fuse1P, Breaker1P, Breaker3P,
    Contactor3P, ThermalRelay3P, Motor3P, Motor3P_YD,
    PushButtonNO, PushButtonNC, EmergencyStopNC, LimitSwitchNO, LimitSwitchNC,
    AuxContactNO, AuxContactNC, AuxThermalNO, AuxThermalNC,
    TimerContactTON_NO, TimerContactTON_NC, TimerContactTOF_NO, TimerContactTOF_NC,
    ContactorCoil, TimerCoilTON, TimerCoilTOF, PilotLamp, TerminalBlock, CamSwitchI0D, CamSwitch0YD
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CADe Linx - Simulador de Automatismos Eléctricos")
        self.resize(1200, 760)
        self.setMinimumSize(640, 480)

        self.scene = SchematicScene(self)
        self.view = SchematicView(self.scene, self)
        self.simulator = CircuitSimulator(self.scene)

        self.sim_timer = QTimer(self)
        self.sim_timer.setInterval(100)
        self.sim_timer.timeout.connect(self.run_simulation_step)

        self.families = {
            "⚡ Alimentación": [
                ("Alim. 1P (L+N)", PowerSupply1P),
                ("Alim. 3P (L1-L3)", PowerSupply3P),
                ("Alim. 3P+N+PE", PowerSupply3PN),
                ("Toma Tierra (PE)", GroundPE),
                ("Borne Numerado (X)", TerminalBlock),
            ],
            "🛡️ Fusibles y Disyuntores": [
                ("Fusible 1P (F)", Fuse1P),
                ("Disyuntor 1P (Q)", Breaker1P),
                ("Disyuntor 3P (Q)", Breaker3P),
            ],
            "🧲 Contactores y Motores": [
                ("Contactor 3P (KM)", Contactor3P),
                ("Relé Térmico (F1)", ThermalRelay3P),
                ("Motor 3P (M)", Motor3P),
                ("Motor 6 Bornes Y/Δ", Motor3P_YD),
            ],
            "🔘 Pulsadores (Maniobra)": [
                ("Pulsador NA (S)", PushButtonNO),
                ("Pulsador NC (S)", PushButtonNC),
                ("Paro Emergencia", EmergencyStopNC),
                ("Final Carrera NA", LimitSwitchNO),
                ("Final Carrera NC", LimitSwitchNC),
                ("Conmutador Levas I-0-D", CamSwitchI0D),
                ("Conmutador Estrella-Triángulo (0-Y-Δ)", CamSwitch0YD),
            ],
            "🔗 Contactos Auxiliares": [
                ("Auxiliar NA (13-14)", AuxContactNO),
                ("Auxiliar NC (21-22)", AuxContactNC),
                ("Térmico NA (97-98)", AuxThermalNO),
                ("Térmico NC (95-96)", AuxThermalNC),
                ("Temp. TON NA (55-56)", TimerContactTON_NO),
                ("Temp. TON NC (65-66)", TimerContactTON_NC),
                ("Temp. TOF NA (57-58)", TimerContactTOF_NO),
                ("Temp. TOF NC (67-68)", TimerContactTOF_NC),
            ],
            "💡 Bobinas y Pilotos": [
                ("Bobina Contactor (KM)", ContactorCoil),
                ("Temporizador TON (-KT)", TimerCoilTON),
                ("Temporizador TOF (-KT)", TimerCoilTOF),
                ("Piloto Luminoso (H)", PilotLamp),
            ],
            "〰️ Cables": [
                ("➕ Cable Fase (L)", "WIRE_PHASE"),
                ("➕ Cable Neutro (N)", "WIRE_NEUTRAL"),
                ("➕ Cable Protección / Tierra (PE)", "WIRE_PE"),
                ("➕ Cable Trifásico (3 Fases)", "WIRE_3PHASE"),
            ],
        }

        self._build_menus()
        self._build_top_toolbar()
        self._build_central_layout()
        self._build_statusbar()

    def _build_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&Archivo")
        act_new = QAction("📄 Nuevo proyecto", self)
        act_new.setShortcut(QKeySequence.StandardKey.New)
        act_new.triggered.connect(self.new_project)
        file_menu.addAction(act_new)

        act_open = QAction("📂 Abrir (.cade)...", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self.open_project)
        file_menu.addAction(act_open)

        act_save = QAction("💾 Guardar (.cade)...", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self.save_project)
        file_menu.addAction(act_save)

        file_menu.addSeparator()
        act_export = QAction("🖼️ Exportar a PNG / JPG / PDF...", self)
        act_export.triggered.connect(self.export_sheet)
        file_menu.addAction(act_export)

        file_menu.addSeparator()
        act_exit = QAction("Salir", self)
        act_exit.setShortcut(QKeySequence.StandardKey.Quit)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        edit_menu = menubar.addMenu("&Edición")
        self.act_undo = QAction("↩ Deshacer", self)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_undo.triggered.connect(self.view.undo)
        edit_menu.addAction(self.act_undo)

        self.act_redo = QAction("↪ Rehacer", self)
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.act_redo.triggered.connect(self.view.redo)
        edit_menu.addAction(self.act_redo)

        edit_menu.addSeparator()
        self.act_copy = QAction("📋 Copiar", self)
        self.act_copy.setShortcut(QKeySequence.StandardKey.Copy)
        self.act_copy.triggered.connect(self.view.copy_selected)
        edit_menu.addAction(self.act_copy)

        self.act_paste = QAction("📌 Pegar", self)
        self.act_paste.setShortcut(QKeySequence.StandardKey.Paste)
        self.act_paste.triggered.connect(self.view.paste_clipboard)
        edit_menu.addAction(self.act_paste)

        view_menu = menubar.addMenu("&Ver")
        act_zi = QAction("🔍+ Acercar", self)
        act_zi.triggered.connect(lambda: self.view.scale(1.2, 1.2))
        view_menu.addAction(act_zi)

        act_zo = QAction("🔍- Alejar", self)
        act_zo.triggered.connect(lambda: self.view.scale(1 / 1.2, 1 / 1.2))
        view_menu.addAction(act_zo)

        act_zr = QAction("1:1 Restablecer Zoom", self)
        act_zr.triggered.connect(self.view.resetTransform)
        view_menu.addAction(act_zr)

        act_fit = QAction("📐 Adaptar Hoja y Encuadrar", self)
        act_fit.triggered.connect(self.view.fit_and_adapt_sheet)
        view_menu.addAction(act_fit)

        help_menu = menubar.addMenu("A&yuda")
        self.act_help = QAction("❓ Manual de Uso y Acerca de CADe Linx", self)
        self.act_help.setShortcut("F1")
        self.act_help.triggered.connect(self.show_help_dialog)
        help_menu.addAction(self.act_help)

    def _build_top_toolbar(self):
        tb = QToolBar("Barra Principal", self)
        tb.setMovable(False)
        tb.setStyleSheet("""
            QToolBar { background: #F4F5F7; border-bottom: 1px solid #CCCCCC; spacing: 2px; padding: 3px; }
            QToolButton { background: #FFFFFF; color: #111111; border: 1px solid #BBBBBB; border-radius: 4px; padding: 3px 5px; font-size: 11px; font-weight: bold; }
            QToolButton:hover { background: #E8F0FE; border-color: #1A73E8; }
        """)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        act_new = QAction("📄 Nuevo", self)
        act_new.triggered.connect(self.new_project)
        tb.addAction(act_new)

        act_ptr = QAction("↖ Seleccionar (Esc)", self)
        act_ptr.triggered.connect(self.reset_tool_selection)
        tb.addAction(act_ptr)

        act_open = QAction("📂 Abrir", self)
        act_open.triggered.connect(self.open_project)
        tb.addAction(act_open)

        act_save = QAction("💾 Guardar", self)
        act_save.triggered.connect(self.save_project)
        tb.addAction(act_save)

        act_exp = QAction("🖼️ Exportar", self)
        act_exp.triggered.connect(self.export_sheet)
        tb.addAction(act_exp)

        tb.addSeparator()

        act_zi = QAction("🔍+", self)
        act_zi.triggered.connect(lambda: self.view.scale(1.2, 1.2))
        tb.addAction(act_zi)

        act_zo = QAction("🔍-", self)
        act_zo.triggered.connect(lambda: self.view.scale(1 / 1.2, 1 / 1.2))
        tb.addAction(act_zo)

        act_zr = QAction("1:1", self)
        act_zr.triggered.connect(self.view.resetTransform)
        tb.addAction(act_zr)

        act_fit = QAction("📐 Adaptar", self)
        act_fit.setToolTip("Ajusta el tamaño del lienzo a los elementos dibujados y encuadra la vista")
        act_fit.triggered.connect(self.view.fit_and_adapt_sheet)
        tb.addAction(act_fit)

        tb.addSeparator()

        self.btn_sim = QPushButton("▶ SIMULAR")
        self.btn_sim.setStyleSheet("QPushButton { background: #E6F4EA; color: #137333; font-weight: bold; border: 1px solid #137333; border-radius: 4px; padding: 4px 8px; }")
        self.btn_sim.clicked.connect(self.start_simulation)
        tb.addWidget(self.btn_sim)

        self.btn_stop = QPushButton("■ STOP")
        self.btn_stop.setStyleSheet("QPushButton { background: #1976D2; color: #FFFFFF; font-weight: bold; border: 1px solid #0D47A1; border-radius: 4px; padding: 4px 8px; }")
        self.btn_stop.clicked.connect(self.stop_simulation)
        tb.addWidget(self.btn_stop)

        tb.addSeparator()

        self.chk_guides = QCheckBox("📐 Guía H/V")
        self.chk_guides.setChecked(True)
        self.chk_guides.setStyleSheet("QCheckBox { color: #111111; font-weight: bold; margin-left: 2px; padding: 2px; }")
        self.chk_guides.toggled.connect(self._toggle_guides)
        tb.addWidget(self.chk_guides)

        tb.addSeparator()
        tb.addAction(self.act_undo)
        tb.addAction(self.act_redo)
        tb.addSeparator()
        tb.addAction(self.act_copy)
        tb.addAction(self.act_paste)
        tb.addSeparator()

        act_help_btn = QAction("❓ Ayuda", self)
        act_help_btn.triggered.connect(self.show_help_dialog)
        tb.addAction(act_help_btn)

    def _build_central_layout(self):
        central = QWidget(self)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        fam_bar = QWidget()
        fam_bar.setStyleSheet("background: #ECEFF1; border-bottom: 1px solid #CFD8DC;")
        fam_bar.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        fam_layout = QHBoxLayout(fam_bar)
        fam_layout.setContentsMargins(8, 4, 8, 4)
        fam_layout.setSpacing(6)

        lbl_f = QLabel("Familias:")
        lbl_f.setStyleSheet("color: #111111; font-weight: bold;")
        fam_layout.addWidget(lbl_f)

        self.fam_group = QButtonGroup(self)
        self.fam_group.setExclusive(True)

        for idx, fam_name in enumerate(self.families.keys()):
            btn = QPushButton(fam_name)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background: #FFFFFF; color: #111111; border: 1px solid #B0BEC5; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold; }
                QPushButton:checked { background: #90CAF9; color: #0D47A1; border: 2px solid #1565C0; }
                QPushButton:hover { background: #E3F2FD; }
            """)
            btn.clicked.connect(lambda checked, fn=fam_name: self.populate_symbols(fn))
            self.fam_group.addButton(btn, idx)
            fam_layout.addWidget(btn)
            if idx == 0:
                btn.setChecked(True)

        fam_layout.addStretch()
        vbox.addWidget(fam_bar)

        self.sym_bar = QWidget()
        self.sym_bar.setStyleSheet("background: #F9FAFB; border-bottom: 1px solid #CFD8DC;")
        self.sym_bar.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.sym_layout = QHBoxLayout(self.sym_bar)
        self.sym_layout.setContentsMargins(8, 4, 8, 4)
        self.sym_layout.setSpacing(6)
        vbox.addWidget(self.sym_bar)

        self.sym_group = QButtonGroup(self)
        self.sym_group.setExclusive(True)

        vbox.addWidget(self.view, 1)
        self.setCentralWidget(central)

        first_family = list(self.families.keys())[0]
        self.populate_symbols(first_family)

    def _make_symbol_icon(self, tool_val):
        pm = QPixmap(36, 36)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if isinstance(tool_val, str):
            if tool_val == "WIRE_PHASE":
                p.setPen(QPen(QColor("#8B4513"), 3)); p.drawLine(4, 18, 32, 18)
            elif tool_val == "WIRE_NEUTRAL":
                p.setPen(QPen(QColor("#0055CC"), 3)); p.drawLine(4, 18, 32, 18)
            elif tool_val == "WIRE_PE":
                p.setPen(QPen(QColor("#2E7D32"), 3, Qt.PenStyle.DashLine)); p.drawLine(4, 18, 32, 18)
            else:
                p.setPen(QPen(QColor("#8B4513"), 2))
                for y in (10, 18, 26): p.drawLine(4, y, 32, y)
        else:
            comp = tool_val()
            br = comp.boundingRect()
            sc = min(30.0 / max(br.width(), 1.0), 30.0 / max(br.height(), 1.0))
            p.translate(18.0, 18.0); p.scale(sc, sc); p.translate(-br.center().x(), -br.center().y())
            comp.paint(p, None, None)
        p.end()
        return QIcon(pm)

    def populate_symbols(self, family_name: str):
        while self.sym_layout.count():
            item = self.sym_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for b in self.sym_group.buttons():
            self.sym_group.removeButton(b)

        lbl_s = QLabel("Símbolos:")
        lbl_s.setStyleSheet("color: #111111; font-weight: bold;")
        self.sym_layout.addWidget(lbl_s)

        for name, tool_val in self.families.get(family_name, []):
            btn = QPushButton()
            btn.setIcon(self._make_symbol_icon(tool_val))
            btn.setIconSize(QSize(30, 30))
            btn.setFixedSize(40, 38)
            btn.setToolTip(name)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background: #FFFFFF; color: #111111; border: 1px solid #B0BEC5; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold; }
                QPushButton:checked { background: #81D4FA; color: #01579B; border: 2px solid #0277BD; }
                QPushButton:hover { background: #E1F5FE; }
            """)
            btn.clicked.connect(lambda checked, tv=tool_val, fn=family_name: self._select_symbol(tv, fn))
            self.sym_group.addButton(btn)
            self.sym_layout.addWidget(btn)

        self.sym_layout.addStretch()
        if hasattr(self, "lbl_family"):
            self.lbl_family.setText(f"Familia: {family_name}")

    def _select_symbol(self, tool_val, family_name: str):
        if self.view.is_simulating:
            self.stop_simulation()
        self.view.set_active_tool(tool_val)

    def reset_tool_selection(self):
        self.view.set_active_tool(None)
        self.sym_group.setExclusive(False)
        for b in self.sym_group.buttons():
            b.setChecked(False)
        self.sym_group.setExclusive(True)

    def _toggle_guides(self, checked: bool):
        self.view.show_guides = checked
        self.view.viewport().update()

    def _build_statusbar(self):
        sb = QStatusBar(self)
        sb.setStyleSheet("QStatusBar { background: #ECEFF1; color: #111111; font-weight: bold; }")
        self.setStatusBar(sb)

        self.lbl_mode = QLabel("MODO: EDICIÓN (Clic izq: colocar | Clic der o Esc: puntero | Doble clic: renombrar | Supr: borrar)")
        self.lbl_mode.setStyleSheet("color: #0D47A1; font-weight: bold; padding-left: 6px;")
        sb.addWidget(self.lbl_mode, 1)

        self.lbl_family = QLabel("Familia: ⚡ Alimentación")
        self.lbl_family.setStyleSheet("color: #333333; padding-right: 12px;")
        sb.addPermanentWidget(self.lbl_family)

        self.lbl_coords = QLabel("X: 0000  Y: 0000")
        self.lbl_coords.setStyleSheet("color: #111111; font-family: monospace; padding-right: 10px;")
        sb.addPermanentWidget(self.lbl_coords)

    def update_coords(self, x: float, y: float):
        self.lbl_coords.setText(f"X: {int(x):04d}  Y: {int(y):04d}")

    # --- SIMULACIÓN ---
    def start_simulation(self):
        self.reset_tool_selection()
        self.view.is_simulating = True
        self.lbl_mode.setText("⚡ MODO: SIMULACIÓN ACTIVA (Clic en Q, F, S_EM o mantén pulsado S1/S0 para accionar | Shift+Clic enclava S)")
        self.lbl_mode.setStyleSheet("color: #1B5E20; font-weight: bold; padding-left: 6px;")
        self.btn_sim.setStyleSheet("QPushButton { background: #2E7D32; color: #FFFFFF; font-weight: bold; border: 2px solid #1B5E20; border-radius: 4px; padding: 4px 8px; }")
        self.btn_stop.setStyleSheet("QPushButton { background: #FFEBEE; color: #C62828; font-weight: bold; border: 1px solid #C62828; border-radius: 4px; padding: 4px 8px; }")
        self.run_simulation_step()
        self.sim_timer.start()

    def stop_simulation(self):
        self.sim_timer.stop()
        self.view.is_simulating = False
        self.simulator.reset()
        self.lbl_mode.setText("MODO: EDICIÓN (Clic izq: colocar | Clic der o Esc: puntero | Doble clic: renombrar | Supr: borrar)")
        self.lbl_mode.setStyleSheet("color: #0D47A1; font-weight: bold; padding-left: 6px;")
        self.btn_sim.setStyleSheet("QPushButton { background: #E6F4EA; color: #137333; font-weight: bold; border: 1px solid #137333; border-radius: 4px; padding: 4px 8px; }")
        self.btn_stop.setStyleSheet("QPushButton { background: #1976D2; color: #FFFFFF; font-weight: bold; border: 1px solid #0D47A1; border-radius: 4px; padding: 4px 8px; }")

    def run_simulation_step(self):
        self.simulator.step(0.1)

    # --- ARCHIVOS Y EXPORTACIÓN ---
    def new_project(self):
        self.stop_simulation()
        resp = QMessageBox.question(
            self, "Nuevo Proyecto",
            "¿Deseas limpiar el lienzo para iniciar un nuevo esquema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.view.push_undo()
            self.scene.clear()
            self.scene.setSceneRect(0, 0, self.scene.MIN_W, self.scene.MIN_H)
            self.view.resetTransform()
            self.scene.update()

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Esquema CADe Linx", "esquema.cade", "Archivos CADe Linx (*.cade)")
        if path:
            if not path.endswith(".cade"):
                path += ".cade"
            save_schematic(self.scene, path)

    def open_project(self):
        self.stop_simulation()
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Esquema CADe Linx", "", "Archivos CADe Linx (*.cade)")
        if path:
            self.view.push_undo()
            load_schematic(self.scene, path)

    def export_sheet(self):
        self.stop_simulation()
        self.reset_tool_selection()
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Esquema", "plano_cadelinx.pdf",
            "Documento PDF (*.pdf);;Imagen PNG (*.png);;Imagen JPG (*.jpg)"
        )
        if not path:
            return

        for it in self.scene.selectedItems():
            it.setSelected(False)

        sr = self.scene.sceneRect()
        W, H = int(sr.width()), int(sr.height())
        low = path.lower()

        if low.endswith(".png") or low.endswith(".jpg") or low.endswith(".jpeg"):
            if not (low.endswith(".png") or low.endswith(".jpg") or low.endswith(".jpeg")):
                path += ".png"
            img = QImage(W, H, QImage.Format.Format_ARGB32)
            img.fill(Qt.GlobalColor.white)
            painter = QPainter(img)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.scene.render(painter, QRectF(0, 0, W, H), QRectF(0, 0, W, H))
            painter.end()
            if low.endswith(".jpg") or low.endswith(".jpeg"):
                img.save(path, "JPG", 95)
            else:
                img.save(path, "PNG")
        else:
            if not low.endswith(".pdf"):
                path += ".pdf"
            writer = QPdfWriter(path)
            writer.setResolution(300)
            writer.setPageSize(QPageSize(QPageSize.PageSizeId.A3))
            writer.setPageOrientation(QPageLayout.Orientation.Landscape)
            writer.setPageMargins(QMarginsF(6, 6, 6, 6), QPageLayout.Unit.Millimeter)
            painter = QPainter(writer)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pw, ph = float(writer.width()), float(writer.height())
            scale = min(pw / max(1, W), ph / max(1, H))
            target_w, target_h = W * scale, H * scale
            off_x = (pw - target_w) / 2.0
            off_y = (ph - target_h) / 2.0
            self.scene.render(painter, QRectF(off_x, off_y, target_w, target_h), QRectF(0, 0, W, H))
            painter.end()

        QMessageBox.information(self, "Exportación completada", f"Plano exportado correctamente en:\n{path}")

    # --- VENTANA DE AYUDA DESLIZABLE Y CRÉDITOS DEL CREADOR ---
    def show_help_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Manual de Usuario y Acerca de CADe Linx")
        dlg.resize(860, 650)
        dlg.setStyleSheet("QDialog { background-color: #F4F6F8; }")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        browser = QTextBrowser(dlg)
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet("""
            QTextBrowser {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 16px;
                font-size: 13px;
            }
        """)

        browser.setHtml("""
        <div style="font-family: SansSerif, Arial;">
            <h1 style="color:#0D47A1; margin-bottom:2px;">⚡ CADe Linx — Simulador de Automatismos Eléctricos</h1>
            <p style="font-size:14px; margin-top:2px; color:#334155;">
                <b>Creador y Autor del Programa:</b> <span style="color:#1565C0; font-weight:bold;">Aleixandre Berlanga</span><br>
                <b>Normativa de Simbología y Referenciado:</b> UNE-EN 60617 (IEC 60617) &bull; EN 50005 &bull; UNE-EN 81346
            </p>
            <hr style="border: 1px solid #E2E8F0;">

            <h2 style="color:#0F172A;">1. ¿Cómo montar tu primer esquema paso a paso?</h2>
            <ol style="line-height:1.6;">
                <li><b>Elegir componentes:</b> Haz clic en una de las <b>Familias</b> de la barra superior (ej. <i>⚡ Alimentación</i> o <i>🧲 Contactores y Motores</i>) y luego selecciona el símbolo en la fila <b>Símbolos</b>.</li>
                <li><b>Colocar con guía visual:</b> Al mover el ratón por la hoja verás la silueta del componente y dos líneas guía azules (H/V) para alinearlo fácilmente con otros símbolos. Haz <b>clic izquierdo</b> para fijarlo.</li>
                <li><b>Autonumeración inteligente:</b> Si insertas varios elementos del mismo tipo, <b>CADe Linx</b> les asignará automáticamente el siguiente número correlativo libre (<i>Q1 &rarr; Q2 &rarr; Q3</i>, <i>KM1 &rarr; KM2</i>, <i>F1 &rarr; F2</i>, <i>M1 &rarr; M2</i>).</li>
                <li><b>Lienzo auto-expansible y botón 📐 Adaptar:</b> Si colocas o pegas componentes cerca del borde derecho o inferior de la hoja, el plano crecerá automáticamente para darte más espacio. Al pulsar el botón <b>📐 Adaptar</b> en la barra superior, el formato se ajustará limpiamente a tu dibujo y se encuadrará en pantalla.</li>
            </ol>

            <h2 style="color:#0F172A;">2. Cableado Monofásico y Trifásico sin Nudos</h2>
            <ul style="line-height:1.6;">
                <li><b>Cable simple (Fase L, Neutro N, Tierra PE):</b> Entra en la familia <b>〰️ Cables</b>. Haz clic en un borne (verás un círculo verde de imán) y luego haz clic en cada esquina por donde quieras doblar a 90&deg;. Cuando toques otro borne o cable existente, el cable se cerrará creando el punto de empalme automáticamente.</li>
                <li><b>Cable Trifásico (3 Fases simultáneas):</b> Selecciona <b>➕ Cable Trifásico (3 Fases)</b>. Con un solo clic inicial y otro final trazarás las tres líneas paralelas (<i>L1, L2, L3</i>). Si haces giros de vertical a horizontal o viceversa, el programa calcula automáticamente la esquina interior y exterior de cada fase para que <b>nunca se crucen ni hagan nudos</b>.</li>
                <li><b>Arrastre elástico de componentes:</b> Si seleccionas y mueves un componente que ya tiene cables conectados a sus bornes, los cables se estirarán solidariamente sin desconectarse.</li>
            </ul>

            <h2 style="color:#0F172A;">3. Renombrado, Sincronización de Contactos y Ajustes</h2>
            <ul style="line-height:1.6;">
                <li><b>Asociar contactos a una bobina o relé (Doble Clic):</b> Para que un contacto auxiliar (ej. <i>13-14</i>) se cierre cuando se active un contactor, ambos deben tener el <b>mismo nombre</b> (ej. <b>KM1</b>). Haz <b>doble clic</b> sobre cualquier componente para cambiar su nombre.</li>
                <li><b>Sincronización rápida:</b> Si renombras un contactor o bobina que ya tiene contactos asociados en el plano, <b>CADe Linx</b> te preguntará si deseas actualizar automáticamente todos los elementos que compartían ese nombre.</li>
                <li><b>Temporizadores (TON / TOF):</b> Haz doble clic sobre la bobina del temporizador (<i>-KT1</i>) para elegir su nombre y el <b>tiempo de retardo en segundos</b>.</li>
                <li><b>Color de Pilotos Luminosos (H1):</b> Haz doble clic sobre la bombilla para elegir entre color <b>verde, rojo, amarillo o azul</b>.</li>
                <li><b>Cajetín Técnico (abajo a la derecha):</b> Haz doble clic dentro del cajetín del plano para cambiar el título del <b>Proyecto</b> y el nombre del <b>Autor / Alumno</b> de la práctica.</li>
            </ul>

            <h2 style="color:#0F172A;">4. Simulación Interactiva (▶ SIMULAR y ■ STOP)</h2>
            <ul style="line-height:1.6;">
                <li>Pulsa el botón verde <b>▶ SIMULAR</b> en la barra superior para dar tensión a las fuentes de alimentación.</li>
                <li>Durante la simulación, interactúa con los elementos de maniobra y corte:
                    <ul>
                        <li><b>Pulsadores con retorno automático (S1, S0):</b> Actúan como pulsadores reales de cuadro eléctrico: permanecen accionados mientras mantienes pulsado el botón izquierdo del ratón y retornan solos al soltarlo (si necesitas dejarlos pulsados de forma fija durante una prueba, haz <b>Shift + Clic</b>).</li>
                        <li><b>Disyuntores (Q1), Paro de Emergencia (S_EM), Finales de Carrera (BG1) y Relés Térmicos (F1):</b> Tienen enclavamiento mecánico; haz un clic para cerrarlos/dispararlos y otro clic para rearmarlos.</li>
                    </ul>
                </li>
                <li>Pulsa <b>■ STOP</b> para detener la simulación y volver al modo de edición.</li>
            </ul>

            <h2 style="color:#0F172A;">5. Tabla de Simbología Normalizada (UNE-EN 60617 / EN 50005)</h2>
            <table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse; width:100%; border-color:#CBD5E1; font-size:12px;">
                <tr style="background-color:#E2E8F0; color:#0F172A; font-weight:bold;">
                    <td>Letra (UNE-EN 81346)</td>
                    <td>Componente</td>
                    <td>Bornes (EN 50005)</td>
                    <td>Rasgo Gráfico Normalizado (UNE-EN 60617)</td>
                </tr>
                <tr>
                    <td><b>Q1, Q2...</b></td>
                    <td>Disyuntor Magnetotérmico</td>
                    <td>1-2, 3-4, 5-6</td>
                    <td>Contacto con cruz (<b>X</b>) de corte automático y bloque lateral térmico (pulso) + magnético (<b>I&gt;</b>).</td>
                </tr>
                <tr>
                    <td><b>KM1, KM2...</b></td>
                    <td>Contactor (Potencia y Bobina)</td>
                    <td>Potencia: 1-2, 3-4, 5-6<br>Bobina: A1 - A2</td>
                    <td>Contactos principales con <b>semicírculo (arco)</b> en borne fijo; bobina rectangular.</td>
                </tr>
                <tr>
                    <td><b>F1, F2...</b></td>
                    <td>Relé Térmico y Fusible</td>
                    <td>Potencia: 1-2, 3-4, 5-6<br>Aux: 95-96 (NC), 97-98 (NA)</td>
                    <td>Pulso cuadrado bimetálico en cada fase; contactos auxiliares con pulso térmico lateral.</td>
                </tr>
                <tr>
                    <td><b>S0, S1, S_EM</b></td>
                    <td>Pulsadores y Paro Emergencia</td>
                    <td>NA: 13-14 &bull; NC: 11-12</td>
                    <td>Pulsador por empuje con retorno automático (corchete <b>]--</b> hacia el contacto); seta con enclavamiento en V.</td>
                </tr>
                <tr>
                    <td><b>-KT1, -KT2...</b></td>
                    <td>Temporizadores TON / TOF</td>
                    <td>Bobina: A1-A2<br>TON: 55-56 / 65-66<br>TOF: 57-58 / 67-68</td>
                    <td>Bobina TON con recuadro en X; TOF con bloque negro. Contactos con paracaídas temporizado.</td>
                </tr>
                <tr>
                    <td><b>M1, M2...</b></td>
                    <td>Motor Trifásico (3P y 6 bornes Y/&Delta;)</td>
                    <td>U1, V1, W1 (+ PE)<br>Y/&Delta;: + W2, U2, V2</td>
                    <td>Círculo con inscripción <b>M 3~</b> que se ilumina en verde al recibir las 3 fases.</td>
                </tr>
            </table>

            <hr style="border: 1px solid #E2E8F0; margin-top:16px;">
            <p style="text-align:center; color:#475569; font-size:12px;">
                <b>CADe Linx</b> — Software creado y desarrollado por <b>Aleixandre Berlanga</b>.<br>
                Reconocimiento de autoría reservado al creador de la aplicación.
            </p>
        </div>
        """)

        layout.addWidget(browser, 1)

        btn_close = QPushButton("Cerrar Manual de Ayuda", dlg)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: #FFFFFF;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1565C0; }
        """)
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignRight)

        dlg.exec()
