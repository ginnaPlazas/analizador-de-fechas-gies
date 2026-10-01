import re
from datetime import datetime

from Token import Token

# 5 formatos de fecha aceptados. Puedes agregar/quitar formatos aqui.
PATRONES_FECHA = [
    r"\d{2}/\d{2}/\d{4}",   # DD/MM/AAAA
    r"\d{2}-\d{2}-\d{4}",   # DD-MM-AAAA
    r"\d{4}/\d{2}/\d{2}",   # AAAA/MM/DD
    r"\d{4}-\d{2}-\d{2}",   # AAAA-MM-DD
    r"\d{2}\.\d{2}\.\d{4}",  # DD.MM.AAAA
]

# Los formatos deben quedar en el MISMO ORDEN que PATRONES_FECHA de arriba,
# porque parsear_fecha() los prueba en orden hasta que uno funcione.
FORMATOS_FECHA = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%Y-%m-%d",
    "%d.%m.%Y",
]


def tokenizar(texto):
    tokens = []
    i = 0
    n = len(texto)
    simbolos = {
        "(": "PARENTESISIZQUI",
        ")": "PARENTESISDER",
        ",": "COMA",
    }

    while i < n:
        char = texto[i]

        if char.isspace():
            i += 1
            continue

        if char.isdigit():
            # Antes de asumir que es un NUMERO suelto, probamos si calza
            # con alguno de los 5 formatos de FECHA permitidos.
            coincidencia_fecha = None
            for patron in PATRONES_FECHA:
                m = re.match(patron, texto[i:])
                if m:
                    coincidencia_fecha = m.group(0)
                    break

            if coincidencia_fecha:
                tokens.append(Token("FECHA", coincidencia_fecha))
                i += len(coincidencia_fecha)
                continue

            inicio = i
            while i < n and (texto[i].isdigit() or texto[i] == "."):
                i += 1
            tokens.append(Token("NUMERO", texto[inicio:i]))
            continue

        if char == '"':
            i += 1
            inicio = i
            while i < n and texto[i] != '"':
                i += 1
            if i >= n:
                raise SyntaxError("Cadena sin cerrar (falta la comilla final)")
            cadena = texto[inicio:i]
            i += 1  
            tokens.append(Token("CADENA", cadena))
            continue

        if char.isalpha() or char == "_":
            inicio = i
            while i < n and (texto[i].isalnum() or texto[i] == "_"):
                i += 1
            palabra = texto[inicio:i]
            tokens.append(Token("PALABRA", palabra))
            continue

        if char in simbolos:
            tokens.append(Token(simbolos[char], char))
            i += 1
            continue

        raise SyntaxError(f"Carácter inesperado: {char!r} en la posición {i}")

    return tokens


def parsear_fecha(texto):
    """Convierte un texto tipo '26/08/2026' en un objeto date real de Python."""
    for formato in FORMATOS_FECHA:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise SyntaxError(f"Formato de fecha no reconocido: {texto!r}")


if __name__ == "__main__":
    ejemplos = [
        "sumar_dias(26/08/2026, 30)",
        'mostrar("Plazo próximo a vencer")',
        "dias_entre(2026-08-26, 2026/09/25)",
        "cerrar()",
    ]
    for expresion in ejemplos:
        print(f"\nExpresión: {expresion}")
        for t in tokenizar(expresion):
            print(f"  {t}")