"""
Analizador sintáctico del lenguaje GIES (cálculos de fechas y nómina).

Este archivo está organizado según los 4 pasos del pensamiento computacional:

  1. ABSTRACCIÓN ............ constantes con nombre (sección 1) y tipos de
                              argumento (sección 2): lo importante, en un solo lugar.
  2. DESCOMPOSICIÓN ......... funciones de cálculo pequeñas y reutilizables
                              (sección 3), en vez de fórmulas repetidas.
  3. IDENTIFICACIÓN DE PATRONES  la tabla FIRMAS (sección 4): todas las operaciones
                              leen "N valores separados por coma"; solo cambia la lista.
  4. ALGORITMIA ............. leer_argumentos() y llamada() (sección 6): la secuencia
                              de pasos que se repite igual para TODAS las operaciones.
"""

import calendar
from datetime import timedelta, date

from GestorReglas import GestorReglas
from TokenizarFechas import parsear_fecha


# ============================================================
# 1. ABSTRACCIÓN: constantes de negocio (antes eran números
#    "mágicos" repetidos por todo el código)
# ============================================================
TASA_SALUD = 0.04
TASA_PENSION = 0.04
TASA_INTERESES_CESANTIAS = 0.12
RECARGO_EXTRA_DIURNA = 1.25
RECARGO_EXTRA_NOCTURNA = 1.75

DIAS_MES = 30                # mes comercial
HORAS_MES = 240              # horas de trabajo al mes
DIAS_ANIO = 360              # año comercial (cesantías y prima)
DIAS_ANIO_VACACIONES = 720   # vacaciones: 15 días hábiles por año

DIAS_SEMANA = [
    "lunes", "martes", "miércoles", "jueves",
    "viernes", "sábado", "domingo",
]


# ============================================================
# 2. ABSTRACCIÓN: tipos de argumento que entiende el lenguaje
# ============================================================
FECHA = "fecha"
NUMERO = "número"
VALOR = "valor"                 # cualquier cosa (fecha, número, texto...)
FECHA_O_ANIO = "fecha o año"    # es_bisiesto acepta 2026 o 26/08/2026

NOMBRES_TIPO = {
    FECHA: "una fecha",
    NUMERO: "un número",
    VALOR: "un valor",
    FECHA_O_ANIO: "una fecha o un año",
}


def es_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def cumple_tipo(valor, tipo):
    if tipo == FECHA:
        return isinstance(valor, date)
    if tipo == NUMERO:
        return es_numero(valor)
    if tipo == FECHA_O_ANIO:
        return isinstance(valor, date) or es_numero(valor)
    return True


def describir_valor(valor):
    """Texto legible de lo que el usuario escribió, para los mensajes de error."""
    if isinstance(valor, bool):
        return "un valor lógico (verdadero/falso)"
    if isinstance(valor, date):
        return "una fecha"
    if es_numero(valor):
        return f"el número {valor:g}"
    if isinstance(valor, str):
        return f"el texto '{valor}'"
    return "un valor vacío"


# ============================================================
# 3. DESCOMPOSICIÓN: cálculos pequeños, cada uno hace UNA cosa.
#    Las operaciones sueltas Y las liquidaciones completas los
#    reutilizan (antes cada liquidación repetía las fórmulas).
# ============================================================
def dias_calendario(fecha1, fecha2):
    """Días de calendario entre dos fechas, sin importar el orden."""
    return abs((fecha2 - fecha1).days)


def calcular_valor_dia(salario_mensual):
    return salario_mensual / DIAS_MES


def calcular_valor_hora(salario_mensual):
    return salario_mensual / HORAS_MES


def calcular_salario_proporcional(dias, salario_mensual):
    return dias * calcular_valor_dia(salario_mensual)


def calcular_pago_extra(horas, valor_por_hora, recargo):
    return horas * valor_por_hora * recargo


def calcular_prestacion(salario_mensual, dias, divisor):
    """Cesantías, prima y vacaciones: misma fórmula, cambia solo el divisor."""
    return salario_mensual * dias / divisor


def calcular_intereses_cesantias(cesantias, dias):
    return cesantias * dias / DIAS_ANIO * TASA_INTERESES_CESANTIAS


def calcular_deducciones(base):
    """Devuelve (salud, pensión) sobre una base salarial."""
    return base * TASA_SALUD, base * TASA_PENSION


def es_anio_bisiesto(anio):
    return (anio % 4 == 0 and anio % 100 != 0) or (anio % 400 == 0)


def ultimo_dia_del_mes(fecha):
    return calendar.monthrange(fecha.year, fecha.month)[1]


# ============================================================
# 4. IDENTIFICACIÓN DE PATRONES: la "firma" de cada operación.
#    Patrón 1: casi todas leen N valores separados por coma.
#    Patrón 2: cesantías, prima, vacaciones, salario proporcional y
#              liquidación final comparten (fecha_inicio, fecha_fin, salario).
# ============================================================
PERIODO = [("fecha_inicio", FECHA), ("fecha_fin", FECHA)]

FIRMAS = {
    # --- Fechas ---
    "revisarMostrar":          [("valor", VALOR)],
    "revisarSumarDias":        [("fecha", FECHA), ("dias", NUMERO)],
    "revisarRestarDias":       [("fecha", FECHA), ("dias", NUMERO)],
    "revisarDiasEntre":        [("fecha1", FECHA), ("fecha2", FECHA)],
    "revisarDiaSemana":        [("fecha", FECHA)],
    "revisarEsBisiesto":       [("fecha_o_anio", FECHA_O_ANIO)],
    "revisarCerrar":           [],
    # --- Deducciones ---
    "revisarDeduccionSalud":   [("salario", NUMERO)],
    "revisarDeduccionPension": [("salario", NUMERO)],
    "revisarDescuentoAusencias": [("dias_ausencia", NUMERO), ("valor_dia", NUMERO)],
    "revisarSalarioNeto":      [("salario_bruto", NUMERO), ("deducciones", NUMERO)],
    # --- Prestaciones (patrón: período + salario) ---
    "revisarCesantiasProporcionales":  PERIODO + [("salario", NUMERO)],
    "revisarPrimaProporcional":        PERIODO + [("salario", NUMERO)],
    "revisarVacacionesProporcionales": PERIODO + [("salario", NUMERO)],
    "revisarInteresesCesantias": [("cesantias", NUMERO)] + PERIODO,
    # --- Contrato ---
    "revisarFechaPagoQuincena":     [("fecha", FECHA)],
    "revisarDiasRestantesContrato": [("fecha_actual", FECHA), ("fecha_fin", FECHA)],
    # --- Nómina regular ---
    "revisarValorDia":    [("salario_mensual", NUMERO)],
    "revisarValorHora":   [("salario_mensual", NUMERO)],
    "revisarSalarioProporcional": PERIODO + [("salario_mensual", NUMERO)],
    "revisarHoraExtraDiurna":   [("horas", NUMERO), ("valor_hora", NUMERO)],
    "revisarHoraExtraNocturna": [("horas", NUMERO), ("valor_hora", NUMERO)],
    "revisarLiquidarNomina": PERIODO + [
        ("salario_mensual", NUMERO),
        ("horas_extra_diurnas", NUMERO),
        ("horas_extra_nocturnas", NUMERO),
        ("dias_ausencia", NUMERO),
    ],
    "revisarLiquidacionFinal": PERIODO + [("salario_mensual", NUMERO)],
}


def texto_firma(operacion, firma):
    """Ej: SUMAR_DIAS(fecha, dias)"""
    nombres = ", ".join(nombre for nombre, _ in firma)
    return f"{operacion}({nombres})"


def verificar_tipo(operacion, posicion, nombre, tipo, valor):
    if not cumple_tipo(valor, tipo):
        raise SyntaxError(
            f"{operacion}: el argumento {posicion} ('{nombre}') debe ser "
            f"{NOMBRES_TIPO[tipo]}, pero recibió {describir_valor(valor)}"
        )


# ============================================================
# 5. ANALIZADOR
# ============================================================
class AnalizadorSintactico:

    def __init__(self, tokens, rutaReglas="reglas.json"):
        self.tokens = tokens
        self.pos = 0
        self.gestorReglas = GestorReglas(rutaReglas)

    def actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consumir(self, tipo):
        token = self.actual()
        if token is None:
            raise SyntaxError(f"Se esperaba {tipo} pero la línea terminó antes")
        if token.tipo != tipo:
            raise SyntaxError(f"Se esperaba {tipo} pero llegó {token.tipo} ({token.valor!r})")
        self.pos = self.pos + 1
        return token

    def revisarSintaxis(self):
        resultado = self.valor()
        if self.actual() is not None:
            sobrante = self.actual()
            raise SyntaxError(f"Sobra texto después de la operación: {sobrante.tipo} ({sobrante.valor!r})")
        return resultado

    # --------------------------------------------------------
    # Núcleo recursivo: un "valor" puede ser un literal o una llamada anidada
    # --------------------------------------------------------
    def valor(self):
        token = self.actual()
        if token is None:
            raise SyntaxError("Se esperaba un valor pero no quedan más tokens")

        if token.tipo == "PALABRA":
            return self.llamada()
        if token.tipo == "FECHA":
            self.pos += 1
            return parsear_fecha(token.valor)
        if token.tipo == "NUMERO":
            self.pos += 1
            return float(token.valor)
        if token.tipo == "CADENA":
            self.pos += 1
            return token.valor

        raise SyntaxError(f"Valor inesperado: {token.tipo} ({token.valor!r})")

    # --------------------------------------------------------
    # 6. ALGORITMIA: la secuencia de pasos de TODA llamada
    #    1. Leer el nombre de la operación
    #    2. Buscar su regla en reglas.json
    #    3. Buscar su método y su firma (argumentos esperados)
    #    4. Consumir "("
    #    5. Leer y validar los argumentos (cantidad y tipo)
    #    6. Consumir ")"
    #    7. Ejecutar el cálculo con los argumentos ya validados
    # --------------------------------------------------------
    def llamada(self):
        operacion = self.consumir("PALABRA").valor.upper()
        regla = self.gestorReglas.obtenerRegla(operacion)

        if regla is None:
            raise SyntaxError(f"No existe una operación llamada '{operacion}'")

        metodo = getattr(self, regla["metodo"], None)
        if metodo is None:
            raise SyntaxError(f"La regla '{regla['nombreRegla']}' apunta a un método inexistente")

        firma = FIRMAS.get(regla["metodo"])
        if firma is None:
            raise SyntaxError(f"La regla '{regla['nombreRegla']}' no tiene firma de argumentos definida")

        self.consumir("PARENTESISIZQUI")
        argumentos = self.leer_argumentos(operacion, firma)
        return metodo(*argumentos)

    def hay_mas_argumentos(self):
        token = self.actual()
        return token is not None and token.tipo != "PARENTESISDER"

    def leer_argumentos(self, operacion, firma):
        """Lee los argumentos de la firma, valida cantidad y tipo, y cierra el paréntesis."""
        valores = []
        total = len(firma)

        def faltan(recibidos):
            return SyntaxError(
                f"{texto_firma(operacion, firma)} necesita {total} argumento(s) "
                f"y solo recibió {recibidos}"
            )

        for posicion, (nombre, tipo) in enumerate(firma):
            if not self.hay_mas_argumentos():
                raise faltan(posicion)
            if posicion > 0:
                self.consumir("COMA")
                if not self.hay_mas_argumentos():
                    raise faltan(posicion)

            valor = self.valor()
            verificar_tipo(operacion, posicion + 1, nombre, tipo, valor)
            valores.append(valor)

        token = self.actual()
        if total == 0 and token is not None and token.tipo != "PARENTESISDER":
            raise SyntaxError(f"{operacion}() no recibe argumentos")
        if token is not None and token.tipo == "COMA":
            raise SyntaxError(
                f"{texto_firma(operacion, firma)} recibe solo {total} argumento(s), "
                f"pero se enviaron más"
            )

        self.consumir("PARENTESISDER")
        return valores

    # --------------------------------------------------------
    # Operaciones de fechas (solo calculan: los argumentos ya vienen validados)
    # --------------------------------------------------------
    def revisarMostrar(self, valor):
        print(valor)
        return valor

    def revisarSumarDias(self, fecha, dias):
        return fecha + timedelta(days=int(dias))

    def revisarRestarDias(self, fecha, dias):
        return fecha - timedelta(days=int(dias))

    def revisarDiasEntre(self, fecha1, fecha2):
        return dias_calendario(fecha1, fecha2)

    def revisarDiaSemana(self, fecha):
        return DIAS_SEMANA[fecha.weekday()]

    def revisarEsBisiesto(self, fecha_o_anio):
        anio = fecha_o_anio.year if isinstance(fecha_o_anio, date) else int(fecha_o_anio)
        return es_anio_bisiesto(anio)

    def revisarCerrar(self):
        return False

    # --------------------------------------------------------
    # A. Deducciones de nómina
    # --------------------------------------------------------
    def revisarDeduccionSalud(self, salario):
        return salario * TASA_SALUD

    def revisarDeduccionPension(self, salario):
        return salario * TASA_PENSION

    def revisarDescuentoAusencias(self, dias_ausencia, valor_dia):
        return dias_ausencia * valor_dia

    def revisarSalarioNeto(self, salario_bruto, deducciones):
        return salario_bruto - deducciones

    # --------------------------------------------------------
    # B. Prestaciones sociales proporcionales
    # --------------------------------------------------------
    def revisarCesantiasProporcionales(self, fecha_inicio, fecha_fin, salario):
        return calcular_prestacion(salario, dias_calendario(fecha_inicio, fecha_fin), DIAS_ANIO)

    def revisarInteresesCesantias(self, cesantias, fecha_inicio, fecha_fin):
        return calcular_intereses_cesantias(cesantias, dias_calendario(fecha_inicio, fecha_fin))

    def revisarPrimaProporcional(self, fecha_inicio, fecha_fin, salario):
        return calcular_prestacion(salario, dias_calendario(fecha_inicio, fecha_fin), DIAS_ANIO)

    def revisarVacacionesProporcionales(self, fecha_inicio, fecha_fin, salario):
        return calcular_prestacion(salario, dias_calendario(fecha_inicio, fecha_fin), DIAS_ANIO_VACACIONES)

    # --------------------------------------------------------
    # C. Gestión del contrato en el tiempo
    # --------------------------------------------------------
    def revisarFechaPagoQuincena(self, fecha):
        if fecha.day <= 15:
            return fecha.replace(day=15)
        return fecha.replace(day=ultimo_dia_del_mes(fecha))

    def revisarDiasRestantesContrato(self, fecha_actual, fecha_fin):
        return (fecha_fin - fecha_actual).days

    # --------------------------------------------------------
    # D. Cálculo de nómina regular
    # --------------------------------------------------------
    def revisarValorDia(self, salario_mensual):
        return calcular_valor_dia(salario_mensual)

    def revisarValorHora(self, salario_mensual):
        return calcular_valor_hora(salario_mensual)

    def revisarSalarioProporcional(self, fecha_inicio, fecha_fin, salario_mensual):
        return calcular_salario_proporcional(dias_calendario(fecha_inicio, fecha_fin), salario_mensual)

    def revisarHoraExtraDiurna(self, horas, valor_hora):
        return calcular_pago_extra(horas, valor_hora, RECARGO_EXTRA_DIURNA)

    def revisarHoraExtraNocturna(self, horas, valor_hora):
        return calcular_pago_extra(horas, valor_hora, RECARGO_EXTRA_NOCTURNA)

    def revisarLiquidarNomina(self, fecha_inicio, fecha_fin, salario_mensual,
                              horas_extra_diurnas, horas_extra_nocturnas, dias_ausencia):
        dias = dias_calendario(fecha_inicio, fecha_fin)
        valor_dia = calcular_valor_dia(salario_mensual)
        valor_hora = calcular_valor_hora(salario_mensual)

        salario_proporcional = calcular_salario_proporcional(dias, salario_mensual)
        extra_diurna = calcular_pago_extra(horas_extra_diurnas, valor_hora, RECARGO_EXTRA_DIURNA)
        extra_nocturna = calcular_pago_extra(horas_extra_nocturnas, valor_hora, RECARGO_EXTRA_NOCTURNA)
        descuento_ausencias = dias_ausencia * valor_dia

        salario_bruto = salario_proporcional + extra_diurna + extra_nocturna - descuento_ausencias
        deduccion_salud, deduccion_pension = calcular_deducciones(salario_bruto)
        salario_neto = salario_bruto - deduccion_salud - deduccion_pension

        return (
            f"--- Liquidación de nómina ({fecha_inicio} a {fecha_fin}) ---\n"
            f"Días del periodo:        {dias}\n"
            f"Salario proporcional:    {salario_proporcional:,.2f}\n"
            f"Horas extra diurnas:     {extra_diurna:,.2f}\n"
            f"Horas extra nocturnas:   {extra_nocturna:,.2f}\n"
            f"Descuento ausencias:     -{descuento_ausencias:,.2f}\n"
            f"Salario bruto:           {salario_bruto:,.2f}\n"
            f"Deducción salud (4%):    -{deduccion_salud:,.2f}\n"
            f"Deducción pensión (4%):  -{deduccion_pension:,.2f}\n"
            f"SALARIO NETO A PAGAR:    {salario_neto:,.2f}"
        )

    # --------------------------------------------------------
    # E. Liquidación final de contrato
    # --------------------------------------------------------
    def revisarLiquidacionFinal(self, fecha_inicio, fecha_fin, salario_mensual):
        dias = dias_calendario(fecha_inicio, fecha_fin)

        cesantias = calcular_prestacion(salario_mensual, dias, DIAS_ANIO)
        intereses_cesantias = calcular_intereses_cesantias(cesantias, dias)
        prima = calcular_prestacion(salario_mensual, dias, DIAS_ANIO)
        vacaciones = calcular_prestacion(salario_mensual, dias, DIAS_ANIO_VACACIONES)

        total = cesantias + intereses_cesantias + prima + vacaciones

        return (
            f"--- Liquidación final del contrato ({fecha_inicio} a {fecha_fin}) ---\n"
            f"Días a liquidar:         {dias}\n"
            f"Cesantías:               {cesantias:,.2f}\n"
            f"Intereses de cesantías:  {intereses_cesantias:,.2f}\n"
            f"Prima proporcional:      {prima:,.2f}\n"
            f"Vacaciones proporcionales: {vacaciones:,.2f}\n"
            f"TOTAL A PAGAR:           {total:,.2f}"
        )