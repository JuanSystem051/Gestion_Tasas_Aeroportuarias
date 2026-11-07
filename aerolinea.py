"""Clase Aerolinea.

Trabajo académico con datos ficticios.

Una Aerolinea AGREGA sus vuelos operados: los vuelos se crean por fuera y se
le entregan. Si la aerolínea desapareciera, los vuelos seguirían existiendo
como objetos. Por eso es agregación y no composición.
"""

from validaciones import validar_codigo, validar_fecha, validar_instancia, validar_texto_no_vacio
from vuelo import Vuelo
from excepciones import DatosInconsistentesError


class Aerolinea:
    """Empresa que declara sus vuelos y a la que se le atribuyen vuelos operados."""

    def __init__(self, codigo, nombre):
        self.__codigo = validar_codigo(codigo, "codigo")
        self.__nombre = validar_texto_no_vacio(nombre, "nombre")
        self.__vuelos = []          # lista privada: nadie la modifica desde fuera

    @property
    def codigo(self):
        return self.__codigo

    @property
    def nombre(self):
        return self.__nombre

    @property
    def vuelos(self):
        """Copia inmutable (tupla): se puede recorrer, pero no alterar la lista interna."""
        return tuple(self.__vuelos)

    def agregar_vuelo(self, vuelo):
        """Atribuye un vuelo operado a esta aerolínea. No admite repetidos."""
        validar_instancia(vuelo, Vuelo, "vuelo")
        if self.buscar_vuelo(vuelo.codigo, vuelo.fecha) is not None:
            raise DatosInconsistentesError(
                f"La aerolínea {self.__codigo} ya tiene registrado el vuelo "
                f"{vuelo.codigo} del {vuelo.fecha:%Y-%m-%d}."
            )
        self.__vuelos.append(vuelo)

    def buscar_vuelo(self, codigo, fecha):
        """Devuelve el vuelo con ese código y fecha, o None si no existe."""
        codigo = validar_codigo(codigo, "codigo")
        fecha = validar_fecha(fecha, "fecha")
        for vuelo in self.__vuelos:
            if vuelo.clave == (codigo, fecha):
                return vuelo
        return None

    def __str__(self):
        return f"{self.__nombre} ({self.__codigo})"
