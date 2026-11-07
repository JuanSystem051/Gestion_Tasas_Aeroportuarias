"""Hallazgo: vuelo operado que no tiene declaración de la aerolínea."""

from hallazgo import Hallazgo, IMPACTO_FALTANTE
from validaciones import validar_entero_positivo


class VueloSinDeclaracion(Hallazgo):
    """El vuelo ocurrió, pero nadie declaró sus pasajeros."""

    def __init__(self, codigo_vuelo, fecha, tarifa_por_pasajero, pasajeros_operados):
        super().__init__(codigo_vuelo, fecha, tarifa_por_pasajero)
        self.__pasajeros_operados = validar_entero_positivo(
            pasajeros_operados, "pasajeros_operados"
        )

    @property
    def pasajeros_operados(self):
        return self.__pasajeros_operados

    def calcular_valor_en_riesgo(self):
        # Recaudo que no llegó: todos los pasajeros operados por la tarifa.
        return round(self.__pasajeros_operados * self.tarifa_por_pasajero, 2)

    def impacto(self):
        return IMPACTO_FALTANTE

    def recomendar_accion(self):
        return "Solicitar a la aerolínea la declaración del vuelo y verificar la fecha de operación."

    def describir(self):
        return (
            f"{super().describir()} | Operado sin declaración: "
            f"{self.__pasajeros_operados} pasajeros."
        )
