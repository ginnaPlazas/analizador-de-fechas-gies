import calendar
from datetime import timedelta

from Token import Token
from GestorReglas import GestorReglas
from TokenizarFechas import parsear_fecha

DIAS_SEMANA = [
    "lunes", "martes", "miércoles", "jueves",
    "viernes", "sábado", "domingo",
]


def dias_calendario(fecha1, fecha2):
    """Días de calendario entre dos fechas, sin importar el orden."""
    return abs((fecha2 - fecha1).days)


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

    # --- Núcleo recursivo: un "valor" puede ser un literal o una llamada anidada ---

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

    def llamada(self):
        operacion = self.consumir("PALABRA").valor.upper()
        regla = self.gestorReglas.obtenerRegla(operacion)

        if regla is None:
            raise SyntaxError(f"No existe una operación llamada '{operacion}'")

        metodo = getattr(self, regla["metodo"], None)
        if metodo is None:
            raise SyntaxError(f"La regla '{regla['nombreRegla']}' apunta a un método inexistente")

        self.consumir("PARENTESISIZQUI")
        return metodo()

    # --- Reglas originales de manejo de fechas ---

    def revisarMostrar(self):
        valor = self.valor()
        self.consumir("PARENTESISDER")
        print(valor)
        return valor

    def revisarSumarDias(self):
        fecha = self.valor()
        self.consumir("COMA")
        dias = self.valor()
        self.consumir("PARENTESISDER")
        return fecha + timedelta(days=int(dias))

    def revisarRestarDias(self):
        fecha = self.valor()
        self.consumir("COMA")
        dias = self.valor()
        self.consumir("PARENTESISDER")
        return fecha - timedelta(days=int(dias))

    def revisarDiasEntre(self):
        fecha1 = self.valor()
        self.consumir("COMA")
        fecha2 = self.valor()
        self.consumir("PARENTESISDER")
        return abs((fecha2 - fecha1).days)

    def revisarDiaSemana(self):
        fecha = self.valor()
        self.consumir("PARENTESISDER")
        return DIAS_SEMANA[fecha.weekday()]

    def revisarEsBisiesto(self):
        fecha = self.valor()
        self.consumir("PARENTESISDER")
        anio = fecha.year
        return (anio % 4 == 0 and anio % 100 != 0) or (anio % 400 == 0)

    def revisarCerrar(self):
        self.consumir("PARENTESISDER")
        return False

    # --- A. Deducciones de nómina ---

    def revisarDeduccionSalud(self):
        salario = self.valor()
        self.consumir("PARENTESISDER")
        return salario * 0.04

    def revisarDeduccionPension(self):
        salario = self.valor()
        self.consumir("PARENTESISDER")
        return salario * 0.04

    def revisarDescuentoAusencias(self):
        dias_ausencia = self.valor()
        self.consumir("COMA")
        valor_dia = self.valor()
        self.consumir("PARENTESISDER")
        return dias_ausencia * valor_dia

    def revisarSalarioNeto(self):
        salario_bruto = self.valor()
        self.consumir("COMA")
        deducciones = self.valor()
        self.consumir("PARENTESISDER")
        return salario_bruto - deducciones

    # --- B. Prestaciones sociales proporcionales ---

    def revisarCesantiasProporcionales(self):
        fecha_inicio = self.valor()
        self.consumir("COMA")
        fecha_fin = self.valor()
        self.consumir("COMA")
        salario = self.valor()
        self.consumir("PARENTESISDER")
        dias = dias_calendario(fecha_inicio, fecha_fin)
        return salario * dias / 360

    def revisarInteresesCesantias(self):
        cesantias = self.valor()
        self.consumir("COMA")
        fecha_inicio = self.valor()
        self.consumir("COMA")
        fecha_fin = self.valor()
        self.consumir("PARENTESISDER")
        dias = dias_calendario(fecha_inicio, fecha_fin)
        return cesantias * dias / 360 * 0.12

    def revisarPrimaProporcional(self):
        fecha_inicio = self.valor()
        self.consumir("COMA")
        fecha_fin = self.valor()
        self.consumir("COMA")
        salario = self.valor()
        self.consumir("PARENTESISDER")
        dias = dias_calendario(fecha_inicio, fecha_fin)
        return salario * dias / 360

    def revisarVacacionesProporcionales(self):
        fecha_inicio = self.valor()
        self.consumir("COMA")
        fecha_fin = self.valor()
        self.consumir("COMA")
        salario = self.valor()
        self.consumir("PARENTESISDER")
        dias = dias_calendario(fecha_inicio, fecha_fin)
        return salario * dias / 720

    # --- C. Gestión del contrato en el tiempo ---

    def revisarFechaPagoQuincena(self):
        fecha = self.valor()
        self.consumir("PARENTESISDER")
        if fecha.day <= 15:
            return fecha.replace(day=15)
        ultimo_dia = calendar.monthrange(fecha.year, fecha.month)[1]
        return fecha.replace(day=ultimo_dia)

    def revisarDiasRestantesContrato(self):
        fecha_actual = self.valor()
        self.consumir("COMA")
        fecha_fin = self.valor()
        self.consumir("PARENTESISDER")
        return (fecha_fin - fecha_actual).days

    # --- D. Cálculo de nómina regular ---

    def revisarValorDia(self):
        salario_mensual = self.valor()
        self.consumir("PARENTESISDER")
        return salario_mensual / 30

    def revisarValorHora(self):
        salario_mensual = self.valor()
        self.consumir("PARENTESISDER")
        return salario_mensual / 240

    def revisarSalarioProporcional(self):
        fecha_inicio = self.valor()
        self.consumir("COMA")
        fecha_fin = self.valor()
        self.consumir("COMA")
        salario_mensual = self.valor()
        self.consumir("PARENTESISDER")
        dias = dias_calendario(fecha_inicio, fecha_fin)
        return dias * (salario_mensual / 30)

    def revisarHoraExtraDiurna(self):
        horas = self.valor()
        self.consumir("COMA")
        valor_hora = self.valor()
        self.consumir("PARENTESISDER")
        return horas * valor_hora * 1.25

    def revisarHoraExtraNocturna(self):
        horas = self.valor()
        self.consumir("COMA")
        valor_hora = self.valor()
        self.consumir("PARENTESISDER")
        return horas * valor_hora * 1.75

    def revisarLiquidarNomina(self):
        fecha_inicio = self.valor()
        self.consumir("COMA")
        fecha_fin = self.valor()
        self.consumir("COMA")
        salario_mensual = self.valor()
        self.consumir("COMA")
        horas_extra_diurnas = self.valor()
        self.consumir("COMA")
        horas_extra_nocturnas = self.valor()
        self.consumir("COMA")
        dias_ausencia = self.valor()
        self.consumir("PARENTESISDER")

        dias = dias_calendario(fecha_inicio, fecha_fin)
        valor_dia = salario_mensual / 30
        valor_hora = salario_mensual / 240

        salario_proporcional = dias * valor_dia
        extra_diurna = horas_extra_diurnas * valor_hora * 1.25
        extra_nocturna = horas_extra_nocturnas * valor_hora * 1.75
        descuento_ausencias = dias_ausencia * valor_dia

        salario_bruto = salario_proporcional + extra_diurna + extra_nocturna - descuento_ausencias
        deduccion_salud = salario_bruto * 0.04
        deduccion_pension = salario_bruto * 0.04
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

    # --- E. Liquidación final de contrato ---

    def revisarLiquidacionFinal(self):
        fecha_inicio = self.valor()
        self.consumir("COMA")
        fecha_fin = self.valor()
        self.consumir("COMA")
        salario_mensual = self.valor()
        self.consumir("PARENTESISDER")

        dias = dias_calendario(fecha_inicio, fecha_fin)

        cesantias = salario_mensual * dias / 360
        intereses_cesantias = cesantias * dias / 360 * 0.12
        prima = salario_mensual * dias / 360
        vacaciones = salario_mensual * dias / 720

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