"""Clase Vuelo.

Trabajo académico con datos ficticios.

Un Vuelo es un vuelo REALMENTE operado: es el dato propio de quien cobra.
Se asocia con el Aeropuerto donde operó (asociación: conoce al aeropuerto,
pero no lo contiene ni lo crea).
"""

from aeropuerto import Aeropuerto
from validaciones import validar_codigo, validar_entero_positivo, validar_fecha, validar_instancia


class Vuelo:
    """Vuelo operado en una fecha, en un aeropuerto, con un número de pasajeros."""

    def __init__(self, codigo, fecha, aeropuerto, pasajeros_operados):
        self.__codigo = validar_codigo(codigo, "codigo")
        self.__fecha = validar_fecha(fecha, "fecha")
        self.__aeropuerto = validar_instancia(aeropuerto, Aeropuerto, "aeropuerto")
        self.__pasajeros_operados = validar_entero_positivo(
            pasajeros_operados, "pasajeros_operados"
        )

    @property
    def codigo(self):
        return self.__codigo

    @property
    def fecha(self):
        return self.__fecha

    @property
    def aeropuerto(self):
        return self.__aeropuerto

    @property
    def pasajeros_operados(self):
        return self.__pasajeros_operados

    @property
    def clave(self):
        """Identifica el vuelo dentro de una aerolínea: (código, fecha)."""
        return (self.__codigo, self.__fecha)

    def cobro_esperado(self):
        """Cobro ficticio que le corresponde a este vuelo según la tarifa del aeropuerto."""
        return self.__aeropuerto.cobro_estimado(self.__pasajeros_operados)

    def __str__(self):
        return (
            f"Vuelo {self.__codigo} del {self.__fecha:%Y-%m-%d} en {self.__aeropuerto.codigo} "
            f"con {self.__pasajeros_operados} pasajeros"
        )
