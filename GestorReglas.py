import json
import os
import sys


class GestorReglas:
    def __init__(self, ruta="reglas.json"):

        if getattr(sys, 'frozen', False):
            ruta = os.path.join(sys._MEIPASS, "reglas.json")
        else:
            ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), ruta)

        with open(ruta, "r", encoding="utf-8") as archivo:
            self.reglas = json.load(archivo)

    def obtenerRegla(self, operacion):
        for regla in self.reglas:
            if operacion in regla["palabras"]:
                return regla
        return None