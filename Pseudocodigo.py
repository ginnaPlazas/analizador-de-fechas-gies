from Token import Token

def analisis(texto):
    tokens = []
    n = len(texto)
    i = 0

#ANÁLISIS LÉXICO
    while i < n:

        if texto[i] --> isEspacio():
            i = i + 1
            continue

        if texto[i] --> isDigito():
            coincidencia --> buscarFormatoFecha(texto, i)

            if coincidencia --> noEsNula():
                tokenNuevo = Token(coincidencia, "FECHA")
                tokens.append(tokenNuevo.__repr__)
                i = i + longitud(coincidencia)
                continue

            inicio = i
            while texto[i] --> isDigito() or texto[i] --> isPunto():
                i = i + 1
            tokenNuevo = Token(texto[inicio:i], "NUMERO")
            tokens.append(tokenNuevo.__repr__)
            continue

        if texto[i] --> isComilla():
            i = i + 1
            inicio = i
            while texto[i] --> noEsComilla():
                i = i + 1
            if i --> esFinDeTexto():
                error("Cadena sin cerrar")
            tokenNuevo = Token(texto[inicio:i], "CADENA")
            tokens.append(tokenNuevo.__repr__)
            i = i + 1
            continue

        if texto[i] --> isLetra() or texto[i] --> isGuionBajo():
            inicio = i
            while texto[i] --> isAlfanumerico() or texto[i] --> isGuionBajo():
                i = i + 1
            tokenNuevo = Token(texto[inicio:i], "PALABRA")
            tokens.append(tokenNuevo.__repr__)
            continue

        if texto[i] --> isParentesisIzquierdo():
            tokenNuevo = Token(texto[i], "PARENTESISIZQUI")
            tokens.append(tokenNuevo.__repr__)
            i = i + 1
            continue

        if texto[i] --> isParentesisDerecho():
            tokenNuevo = Token(texto[i], "PARENTESISDER")
            tokens.append(tokenNuevo.__repr__)
            i = i + 1
            continue

        if texto[i] --> isComa():
            tokenNuevo = Token(texto[i], "COMA")
            tokens.append(tokenNuevo.__repr__)
            i = i + 1
            continue

        error("Carácter inesperado: " + texto[i] + " en la posición " + i)

    return tokens