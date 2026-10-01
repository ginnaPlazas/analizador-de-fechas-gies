import sys
import os

from TokenizarFechas import tokenizar
from Sintactico import AnalizadorSintactico

EXTENSION = ".gies"

def ejecutar_linea(texto):
    texto = texto.strip()
    if not texto:
        return True
    try:
        tokens = tokenizar(texto)
        print("Tokens:", tokens)
        analizador = AnalizadorSintactico(tokens)
        resultado = analizador.revisarSintaxis()
        if resultado is not False:
            print("Resultado:", resultado)
        return resultado is not False
    except SyntaxError as error:
        print(f"Error de sintaxis: {error}")
        return True


def ejecutar_archivo(ruta):
    if not os.path.exists(ruta):
        print(f"Error: el archivo '{ruta}' no existe")
        return False

    if not ruta.lower().endswith(EXTENSION):
        print(f"Error: el archivo debe tener la extensión {EXTENSION}")
        return False

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            contenido = archivo.readlines()
    except Exception as error:
        print(f"Error leyendo el archivo: {error}")
        return False

    if not contenido:
        print("El archivo está vacío")
        return False

    print(f"Ejecutando: {ruta}")
    for numero_linea, linea in enumerate(contenido, start=1):
        if not linea.strip():
            continue
        print(f"\n--- Línea {numero_linea}: {linea.strip()} ---")
        continuar = ejecutar_linea(linea)
        if not continuar:
            break
    return True


def modo_interactivo():
    print("BIENVENIDO A TU LENGUAJE DE FECHAS")
    print("Escribe una operación, por ejemplo: sumar_dias(26/08/2026, 30) o liquidar_nomina(2026-08-26, 2026/09/25)")
    print("Escribe cerrar() para salir")

    while True:
        try:
            texto = input("GIES > ")
        except KeyboardInterrupt:
            print("\nPrograma terminado")
            break
        except EOFError:
            print("\nPrograma terminado.")
            break

        continuar = ejecutar_linea(texto)
        if not continuar:
            break


def mostrar_ayuda():
    print("Lenguaje nómina mediante manipulación de fechas - FACULTAD SECCIONAL SOGAMOSO")
    print("Uso:")
    print("  python main.py                 -> modo interactivo")
    print(f"  python main.py archivo{EXTENSION}   -> ejecutar un archivo")
    print(f"Extensión soportada: {EXTENSION}")


def main():
    if len(sys.argv) == 1:
        modo_interactivo()
        return

    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
        mostrar_ayuda()
        return

    if len(sys.argv) == 2:
        ruta = sys.argv[1]
        ejecutar_archivo(ruta)
        return

    print("Error: cantidad de argumentos incorrecta")
    mostrar_ayuda()


if __name__ == "__main__":
    main()