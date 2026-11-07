"""Hallazgo: declaración de un vuelo que no figura como operado."""

from hallazgo import Hallazgo, IMPACTO_EXCESO
from validaciones import validar_entero_positivo


class DeclaracionSinVuelo(Hallazgo):
    """La aerolínea declaró pasajeros, pero no hay registro de que el vuelo operó."""

    def __init__(self, codigo_vuelo, fecha, tarifa_por_pasajero, pasajeros_declarados):
        super().__init__(codigo_vuelo, fecha, tarifa_por_pasajero)
        self.__pasajeros_declarados = validar_entero_positivo(
            pasajeros_declarados, "pasajeros_declarados"
        )

    @property
    def pasajeros_declarados(self):
        return self.__pasajeros_declarados

    def calcular_valor_en_riesgo(self):
        # Lo que podría haberse cobrado de más por un vuelo que no ocurrió.
        return round(self.__pasajeros_declarados * self.tarifa_por_pasajero, 2)

    def impacto(self):
        return IMPACTO_EXCESO

    def recomendar_accion(self):
        return "Verificar en el registro de operaciones si el vuelo se realizó; si no, anular la declaración."

    def describir(self):
        return (
            f"{super().describir()} | Declarado sin vuelo operado: "
            f"{self.__pasajeros_declarados} pasajeros."
        )
