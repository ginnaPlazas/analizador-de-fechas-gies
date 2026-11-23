"""
Genera el INFORME en PDF de una sesión de GIES: datos del empleado,
resumen de operaciones, detalle de cada una, observaciones y firmas.

Usa fpdf2 con las fuentes incluidas (Helvetica y Courier), así que no
necesita archivos de fuentes extra dentro del contenedor.
"""

import re
from datetime import datetime
from fpdf import FPDF

# Se importan las constantes del lenguaje para que las observaciones del
# informe siempre coincidan con lo que realmente calcula el compilador.
from Sintactico import DIAS_MES, DIAS_ANIO, HORAS_MES


AZUL = (23, 37, 84)
AZUL_CLARO = (232, 238, 250)
GRIS = (100, 116, 139)
GRIS_CLARO = (203, 213, 225)
GRIS_FONDO = (245, 247, 250)
NEGRO = (30, 41, 59)

MARGEN = 18
ANCHO = 210 - 2 * MARGEN   # 174 mm útiles

NOMBRES_OPERACION = {
    "mostrar": "Mostrar valor",
    "sumar_dias": "Suma de días a una fecha",
    "restar_dias": "Resta de días a una fecha",
    "dias_entre": "Días entre dos fechas",
    "dia_semana": "Día de la semana",
    "es_bisiesto": "Verificación de año bisiesto",
    "cerrar": "Cierre de sesión",
    "deduccion_salud": "Deducción de salud",
    "deduccion_pension": "Deducción de pensión",
    "descuento_ausencias": "Descuento por ausencias",
    "salario_neto": "Salario neto",
    "cesantias_proporcionales": "Cesantías proporcionales",
    "intereses_cesantias": "Intereses sobre cesantías",
    "prima_proporcional": "Prima de servicios proporcional",
    "vacaciones_proporcionales": "Vacaciones proporcionales",
    "fecha_pago_quincena": "Fecha de pago de quincena",
    "dias_restantes_contrato": "Días restantes de contrato",
    "valor_dia": "Valor del día de trabajo",
    "valor_hora": "Valor de la hora de trabajo",
    "salario_proporcional": "Salario proporcional",
    "hora_extra_diurna": "Horas extra diurnas",
    "hora_extra_nocturna": "Horas extra nocturnas",
    "liquidar_nomina": "Liquidación de nómina",
    "liquidacion_final": "Liquidación final de contrato",
}

# Operaciones cuyo resultado simple es dinero (se muestra como $ 1.234,00)
MONETARIAS = {
    "deduccion_salud", "deduccion_pension", "descuento_ausencias", "salario_neto",
    "cesantias_proporcionales", "intereses_cesantias", "prima_proporcional",
    "vacaciones_proporcionales", "valor_dia", "valor_hora", "salario_proporcional",
    "hora_extra_diurna", "hora_extra_nocturna",
}


# ------------------------------------------------------------
# Utilidades de formato (formato colombiano)
# ------------------------------------------------------------
def limpiar(texto, maximo=None):
    """Las fuentes base solo soportan latin-1 (tildes y ñ sí; emojis no)."""
    texto = str(texto if texto is not None else "").strip()
    if maximo and len(texto) > maximo:
        texto = texto[:maximo - 3] + "..."
    return texto.encode("latin-1", "replace").decode("latin-1")


def miles_colombiano(numero_texto):
    """'7,650,000.50' -> '7.650.000,50'"""
    return numero_texto.replace(",", "\0").replace(".", ",").replace("\0", ".")


def formatear_dinero(valor):
    """Acepta '7,650,000.00' o '50000.0' y devuelve '$ 7.650.000,00'."""
    texto = str(valor).strip()
    negativo = texto.startswith("-")
    try:
        numero = float(texto.replace(",", "").lstrip("-"))
    except ValueError:
        return texto
    cuerpo = miles_colombiano(f"{numero:,.2f}")
    return f"-$ {cuerpo}" if negativo else f"$ {cuerpo}"


def fechas_iso_a_colombiano(texto):
    """'2026-05-28' -> '28/05/2026'"""
    return re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3/\2/\1", texto)


def formatear_documento(numero):
    solo_digitos = re.sub(r"\D", "", numero)
    if solo_digitos and solo_digitos == numero.strip():
        return miles_colombiano(f"{int(solo_digitos):,}")
    return numero


def texto_documento(empleado):
    tipo = limpiar(empleado.get("tipo_documento"), 10)
    numero = formatear_documento(limpiar(empleado.get("numero_documento"), 20))
    return f"{tipo} {numero}".strip()


def funciones_en(codigo):
    return [f.lower() for f in re.findall(r"([A-Za-z_]+)\s*\(", codigo)]


def nombre_operacion(codigo):
    funciones = funciones_en(codigo)
    if not funciones:
        return "Operación"
    return NOMBRES_OPERACION.get(funciones[0], funciones[0].replace("_", " ").capitalize())


def funcion_para_formato(codigo):
    """mostrar(dias_entre(...)) se formatea según dias_entre, no según mostrar."""
    funciones = funciones_en(codigo)
    if len(funciones) > 1 and funciones[0] == "mostrar":
        return funciones[1]
    return funciones[0] if funciones else ""


PATRON_LINEA = re.compile(r"^(.*?):\s+(-?[\d,]+(?:\.\d+)?)$")
PATRON_DINERO = re.compile(r"^-?[\d,]+\.\d{2}$")


def analizar_resultado(resultado):
    """
    Devuelve (subtitulo, filas) si el resultado es una liquidación con líneas
    'Etiqueta: valor'; o (None, None) si es un resultado simple.
    """
    lineas = [l for l in str(resultado).strip().splitlines() if l.strip()]
    if len(lineas) < 2:
        return None, None

    subtitulo = None
    filas = []
    for linea in lineas:
        if linea.startswith("---"):
            subtitulo = linea.strip("- ").strip()
            continue
        m = PATRON_LINEA.match(linea.strip())
        if not m:
            return None, None
        etiqueta, valor = m.group(1).strip(), m.group(2)
        if PATRON_DINERO.match(valor):
            valor = formatear_dinero(valor)
        filas.append((etiqueta, valor))
    return (subtitulo, filas) if filas else (None, None)


def formatear_resultado_simple(codigo, resultado):
    texto = str(resultado).strip()
    funcion = funcion_para_formato(codigo)

    if funcion in MONETARIAS:
        return formatear_dinero(texto)
    if funcion == "es_bisiesto":
        return "Sí, es bisiesto" if texto == "True" else "No, no es bisiesto"
    if funcion in ("dias_entre", "dias_restantes_contrato"):
        return f"{texto} días"
    if funcion == "dia_semana":
        return texto.capitalize()
    return fechas_iso_a_colombiano(texto)


def resumen_corto(codigo, resultado):
    """Lo que aparece en la tabla de resumen: el dato principal de cada operación."""
    _, filas = analizar_resultado(resultado)
    if filas:
        etiqueta, valor = filas[-1]
        return f"{etiqueta.capitalize()}: {valor}"
    return formatear_resultado_simple(codigo, resultado)


# ------------------------------------------------------------
# Documento
# ------------------------------------------------------------
class Informe(FPDF):

    def __init__(self, numero, nombre_empleado):
        super().__init__(format="A4")
        self.numero = numero
        self.nombre_empleado = nombre_empleado
        self.set_margins(MARGEN, MARGEN, MARGEN)
        self.set_auto_page_break(auto=True, margin=22)
        self.alias_nb_pages()

    def header(self):
        # La primera página tiene encabezado completo (se dibuja en el cuerpo).
        # Las siguientes llevan un encabezado compacto.
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*GRIS)
        self.cell(ANCHO / 2, 6, limpiar(f"Informe {self.numero}"))
        self.cell(ANCHO / 2, 6, limpiar(f"Empleado: {self.nombre_empleado}"), align="R")
        self.ln(8)
        self.set_draw_color(*GRIS_CLARO)
        self.line(MARGEN, self.get_y() - 2, 210 - MARGEN, self.get_y() - 2)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*GRIS_CLARO)
        self.line(MARGEN, self.get_y(), 210 - MARGEN, self.get_y())
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRIS)
        self.cell(ANCHO / 2, 8, limpiar("Generado con GIES - Lenguaje de cálculos laborales"))
        self.cell(ANCHO / 2, 8, limpiar(f"Página {self.page_no()} de {{nb}}"), align="R")


def encabezado(pdf, empleado, numero, emision):
    empresa = limpiar(empleado.get("empresa"), 70) or "GIES"
    nit = limpiar(empleado.get("nit"), 30)

    pdf.set_text_color(*AZUL)
    pdf.set_font("Helvetica", "B", 17)
    pdf.cell(ANCHO * 0.62, 8, empresa)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(ANCHO * 0.38, 8, limpiar(f"Informe No. {numero}"), align="R",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(ANCHO * 0.62, 5, limpiar(f"NIT {nit}") if nit else "")
    pdf.cell(ANCHO * 0.38, 5, limpiar(f"Emitido: {emision}"), align="R",
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_draw_color(*AZUL)
    pdf.set_line_width(0.8)
    pdf.line(MARGEN, pdf.get_y(), 210 - MARGEN, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(8)

    pdf.set_text_color(*NEGRO)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, limpiar("EXTRACTO DE CÁLCULOS LABORALES"), align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 5, limpiar("Liquidaciones de nómina, prestaciones sociales y cálculos de fechas"),
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(7)


def titulo_seccion(pdf, texto):
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*AZUL)
    pdf.set_fill_color(*AZUL_CLARO)
    pdf.cell(0, 7, limpiar(texto), fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def fila_dato(pdf, etiqueta, valor, ancho_valor, ancho_etiqueta=32, maximo=60):
    pdf.set_draw_color(*GRIS_CLARO)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*GRIS)
    pdf.set_fill_color(*GRIS_FONDO)
    pdf.cell(ancho_etiqueta, 7, limpiar(etiqueta), border=1, fill=True)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*NEGRO)
    pdf.cell(ancho_valor, 7, limpiar(valor, maximo), border=1)


def datos_empleado(pdf, empleado):
    titulo_seccion(pdf, "DATOS DEL EMPLEADO")

    fila_dato(pdf, "Nombre completo", empleado.get("nombre"), ANCHO - 32)
    pdf.ln(7)
    fila_dato(pdf, "Documento", texto_documento(empleado), 55)
    fila_dato(pdf, "Cargo", empleado.get("cargo") or "-", 55)
    pdf.ln(7)
    fila_dato(pdf, "Empresa", empleado.get("empresa") or "-", 76, maximo=44)
    fila_dato(pdf, "NIT", empleado.get("nit") or "-", 40, ancho_etiqueta=26)
    pdf.ln(12)


def tabla_resumen(pdf, operaciones):
    titulo_seccion(pdf, "RESUMEN DE OPERACIONES")

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(*AZUL)
    pdf.set_draw_color(*AZUL)
    pdf.cell(12, 7, "No.", border=1, fill=True, align="C")
    pdf.cell(68, 7, limpiar("Operación"), border=1, fill=True)
    pdf.cell(ANCHO - 80, 7, "Resultado principal", border=1, fill=True,
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*NEGRO)
    pdf.set_draw_color(*GRIS_CLARO)
    for i, op in enumerate(operaciones, start=1):
        pdf.set_fill_color(*(GRIS_FONDO if i % 2 == 0 else (255, 255, 255)))
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(12, 7, str(i), border=1, fill=True, align="C")
        pdf.cell(68, 7, limpiar(nombre_operacion(op["codigo"]), 38), border=1, fill=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(ANCHO - 80, 7, limpiar(resumen_corto(op["codigo"], op["resultado"]), 52),
                 border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)


def detalle_operacion(pdf, numero, op, primero=False):
    subtitulo, filas = analizar_resultado(op["resultado"])
    alto = 40 + (len(filas) * 7 if filas else 14) + (12 if primero else 0)

    # Si la operación no cabe completa en la página, pasa a la siguiente
    if pdf.will_page_break(alto):
        pdf.add_page()

    if primero:
        titulo_seccion(pdf, "DETALLE DE LAS OPERACIONES")
        pdf.ln(2)

    titulo_seccion(pdf, f"{numero}. {nombre_operacion(op['codigo']).upper()}")

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 5, limpiar("Instrucción ejecutada"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(*NEGRO)
    pdf.set_fill_color(*GRIS_FONDO)
    pdf.multi_cell(0, 5.5, limpiar(op["codigo"], 400), fill=True, padding=2,
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_draw_color(*GRIS_CLARO)

    if filas:
        if subtitulo:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*GRIS)
            pdf.cell(0, 6, limpiar(fechas_iso_a_colombiano(subtitulo)),
                     new_x="LMARGIN", new_y="NEXT")
        for etiqueta, valor in filas:
            destacada = etiqueta.isupper()
            pdf.set_font("Helvetica", "B" if destacada else "", 9.5)
            pdf.set_text_color(*(AZUL if destacada else NEGRO))
            pdf.set_fill_color(*(AZUL_CLARO if destacada else (255, 255, 255)))
            pdf.cell(ANCHO * 0.65, 7, limpiar(etiqueta.capitalize() if destacada else etiqueta),
                     border="B", fill=True)
            pdf.cell(ANCHO * 0.35, 7, limpiar(valor), border="B", fill=True, align="R",
                     new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*GRIS)
        pdf.cell(ANCHO * 0.35, 8, "Resultado", border="B")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*AZUL)
        pdf.cell(ANCHO * 0.65, 8,
                 limpiar(formatear_resultado_simple(op["codigo"], op["resultado"]), 70),
                 border="B", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(9)


def observaciones(pdf):
    if pdf.will_page_break(60):
        pdf.add_page()

    titulo_seccion(pdf, "OBSERVACIONES")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*GRIS)
    notas = [
        "Valores expresados en pesos colombianos (COP).",
        f"Base de cálculo: mes comercial de {DIAS_MES} días, año comercial de "
        f"{DIAS_ANIO} días y {HORAS_MES} horas laborales al mes.",
        "Este documento es informativo y fue generado automáticamente por el sistema GIES. "
        "No constituye comprobante oficial de pago ni sustituye la liquidación firmada "
        "por el empleador.",
    ]
    for nota in notas:
        pdf.multi_cell(0, 4.8, limpiar("- " + nota), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)


def firmas(pdf, empleado):
    if pdf.will_page_break(28):
        pdf.add_page()

    pdf.ln(12)
    y = pdf.get_y()
    pdf.set_draw_color(*NEGRO)
    pdf.line(MARGEN, y, MARGEN + 70, y)
    pdf.line(210 - MARGEN - 70, y, 210 - MARGEN, y)

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*NEGRO)
    pdf.set_xy(MARGEN, y + 1)
    pdf.cell(70, 5, "Empleador / Representante legal")
    pdf.set_xy(210 - MARGEN - 70, y + 1)
    pdf.cell(70, 5, limpiar("Empleado - Recibí conforme"))

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*GRIS)
    pdf.set_xy(210 - MARGEN - 70, y + 6)
    pdf.cell(70, 5, limpiar(empleado.get("nombre"), 38))
    pdf.set_xy(210 - MARGEN - 70, y + 11)
    pdf.cell(70, 5, limpiar(texto_documento(empleado)))


def generar_pdf(empleado, operaciones):
    """
    empleado: dict con nombre, tipo_documento, numero_documento, cargo, empresa, nit
    operaciones: lista de dicts {"codigo": str, "resultado": str}
    """
    ahora = datetime.now()
    numero = ahora.strftime("GIES-%Y%m%d-%H%M")
    emision = ahora.strftime("%d/%m/%Y %H:%M")

    pdf = Informe(numero, limpiar(empleado.get("nombre"), 50))
    pdf.add_page()

    encabezado(pdf, empleado, numero, emision)
    datos_empleado(pdf, empleado)

    if len(operaciones) > 1:
        tabla_resumen(pdf, operaciones)

    for i, op in enumerate(operaciones, start=1):
        detalle_operacion(pdf, i, op, primero=(i == 1))

    observaciones(pdf)
    firmas(pdf, empleado)

    return bytes(pdf.output())