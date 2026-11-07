"""Clase Aeropuerto.

Trabajo académico con datos ficticios.

Identifica el aeropuerto y guarda su tarifa ficticia por pasajero.
Además sabe calcular cuánto correspondería cobrar por un número de pasajeros.
"""

from validaciones import validar_codigo, validar_entero_no_negativo, validar_numero_positivo, validar_texto_no_vacio


class Aeropuerto:
    """Lugar donde operan los vuelos y que define la tarifa ficticia por pasajero."""

    def __init__(self, codigo, nombre, tarifa_por_pasajero):
        self.__codigo = validar_codigo(codigo, "codigo")
        self.__nombre = validar_texto_no_vacio(nombre, "nombre")
        self.__tarifa_por_pasajero = validar_numero_positivo(
            tarifa_por_pasajero, "tarifa_por_pasajero"
        )

    @property
    def codigo(self):
        return self.__codigo

    @property
    def nombre(self):
        return self.__nombre

    @property
    def tarifa_por_pasajero(self):
        return self.__tarifa_por_pasajero

    def cobro_estimado(self, pasajeros):
        """Valor ficticio que correspondería cobrar por `pasajeros` pasajeros."""
        pasajeros = validar_entero_no_negativo(pasajeros, "pasajeros")
        return round(pasajeros * self.__tarifa_por_pasajero, 2)

    def __str__(self):
        return f"{self.__nombre} ({self.__codigo})"
