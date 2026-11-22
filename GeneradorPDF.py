"""
Genera el PDF con el resultado de una ejecución de GIES.
Usa fpdf2 y solo las fuentes incluidas (Helvetica y Courier), así que no
necesita archivos de fuentes extra dentro del contenedor.
"""

from datetime import datetime
from fpdf import FPDF


AZUL_OSCURO = (23, 37, 84)
AZUL = (37, 99, 235)
GRIS = (100, 116, 139)
FONDO_CODIGO = (15, 23, 42)
TEXTO_CODIGO = (226, 232, 240)
VERDE = (74, 222, 128)


def limpiar(texto):
    """Las fuentes base solo soportan latin-1 (tildes y ñ sí; símbolos raros no)."""
    return str(texto).encode("latin-1", "replace").decode("latin-1")


def bloque_oscuro(pdf, etiqueta, texto, color_texto):
    """Dibuja una caja oscura tipo terminal con una etiqueta arriba."""
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 6, etiqueta, new_x="LMARGIN", new_y="NEXT")

    pdf.set_fill_color(*FONDO_CODIGO)
    pdf.set_text_color(*color_texto)
    pdf.set_font("Courier", "", 10)
    pdf.multi_cell(0, 6, limpiar(texto), fill=True, border=0,
                   new_x="LMARGIN", new_y="NEXT", padding=4)
    pdf.ln(6)


def generar_pdf(codigo, resultado):
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Encabezado
    pdf.set_fill_color(*AZUL_OSCURO)
    pdf.rect(0, 0, 210, 28, style="F")
    pdf.set_xy(15, 8)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 8, "GIES", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Lenguaje formal para calculos de fechas y nomina",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(38)
    pdf.set_text_color(*AZUL_OSCURO)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, "Resultado de la ejecucion", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*GRIS)
    pdf.set_font("Helvetica", "", 9)
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 6, f"Generado el {ahora}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    bloque_oscuro(pdf, "INSTRUCCION", "GIES> " + codigo, TEXTO_CODIGO)
    bloque_oscuro(pdf, "RESULTADO", resultado, VERDE)

    # Pie de página
    pdf.set_y(-28)
    pdf.set_draw_color(*AZUL)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.set_text_color(*GRIS)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 8, "Documento generado automaticamente por GIES",
             align="C")

    return bytes(pdf.output())