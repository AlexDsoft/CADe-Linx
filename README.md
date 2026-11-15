# CADe Linx - Simulador de Automatismos Eléctricos para Linux

**CADe Linx** es un software educativo de diseño y simulación interactiva de esquemas eléctricos de fuerza y maniobra para sistemas Linux, desarrollado en Python 3 y PyQt6 bajo la normativa europea **UNE-EN 60617 (IEC 60617)**, **EN 50005** y **UNE-EN 81346**.

## Características Principales
* **Simbología Normalizada UNE-EN 60617:** Alimentaciones monofásicas y trifásicas, fusibles, disyuntores magnetotérmicos (Q), contactores (KM), relés térmicos (F), motores trifásicos (3 bornes y 6 bornes Y/D), pulsadores con retorno automático, seta de emergencia, finales de carrera, contactos auxiliares instantáneos/térmicos/temporizados (TON/TOF), bobinas y pilotos luminosos.
* **Autonumeración Correlativa y Sincronización:** Numeración automática al insertar o pegar bloques (Q1 -> Q2, KM1 -> KM2, F1 -> F2, M1 -> M2) y actualización automática de contactos asociados al renombrar con doble clic.
* **Cableado Inteligente y Trifásico sin Nudos:** Trazado ortogonal a 90 grados con puntos de empalme automáticos y arrastre elástico de cables al mover componentes.
* **Lienzo Auto-Expansible y Adaptable:** El formato crece automáticamente al colocar componentes en los extremos y se ajusta al contenido con el botón Adaptar.
* **Exportación y Almacenamiento:** Guardado nativo en formato .cade y exportación directa de planos a PDF y PNG.

## Instalación y Ejecución en Linux

    git clone https://github.com/TU_USUARIO/CADe-Linx.git
    cd CADe-Linx
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python3 main.py

## Generar Ejecutable Portable (Opcional)

    pip install pyinstaller
    pyinstaller --noconfirm --onefile --windowed --name "CADe_Linx" main.py

El ejecutable independiente se generará dentro de la carpeta dist/CADe_Linx.
