class Token:
    def __init__(self, tipo, valor):
        self.tipo = tipo
        self.valor = valor

    def to_json(self):
        return self.__dict__

    def __repr__(self):
        return f"Token({self.tipo}, {self.valor!r})"