"""Clase Declaracion.

Trabajo académico con datos ficticios.

Una Declaracion es lo que REPORTÓ la aerolínea sobre un vuelo. Se asocia con
la Aerolinea que la presentó (asociación). Es la clase responsable de saber si
se presentó a tiempo y de lanzar DeclaracionExtemporaneaError si no.
"""

from aerolinea import Aerolinea
from excepciones import DatosInconsistentesError, DeclaracionExtemporaneaError
from validaciones import validar_codigo, validar_entero_positivo, validar_fecha, validar_instancia

# Plazo máximo FICTICIO, en días después del vuelo. No corresponde a ninguna norma real.
PLAZO_MAXIMO_DIAS = 3


class Declaracion:
    """Reporte de pasajeros de un vuelo, presentado por una aerolínea."""

    def __init__(self, aerolinea, codigo_vuelo, fecha_vuelo, fecha_presentacion, pasajeros_declarados):
        self.__aerolinea = validar_instancia(aerolinea, Aerolinea, "aerolinea")
        self.__codigo_vuelo = validar_codigo(codigo_vuelo, "codigo_vuelo")
        self.__fecha_vuelo = validar_fecha(fecha_vuelo, "fecha_vuelo")
        self.__fecha_presentacion = validar_fecha(fecha_presentacion, "fecha_presentacion")
        self.__pasajeros_declarados = validar_entero_positivo(
            pasajeros_declarados, "pasajeros_declarados"
        )
        # Una declaración no puede presentarse antes de que ocurra el vuelo.
        if self.__fecha_presentacion < self.__fecha_vuelo:
            raise DatosInconsistentesError(
                "La fecha de presentación no puede ser anterior a la fecha del vuelo."
            )

    @property
    def aerolinea(self):
        return self.__aerolinea

    @property
    def codigo_vuelo(self):
        return self.__codigo_vuelo

    @property
    def fecha_vuelo(self):
        return self.__fecha_vuelo

    @property
    def fecha_presentacion(self):
        return self.__fecha_presentacion

    @property
    def pasajeros_declarados(self):
        return self.__pasajeros_declarados

    @property
    def clave(self):
        """Identifica el vuelo declarado dentro de una aerolínea: (código, fecha)."""
        return (self.__codigo_vuelo, self.__fecha_vuelo)

    @property
    def dias_de_presentacion(self):
        """Días transcurridos entre el vuelo y la presentación de la declaración."""
        return (self.__fecha_presentacion - self.__fecha_vuelo).days

    def verificar_plazo(self):
        """Lanza DeclaracionExtemporaneaError si se presentó fuera del plazo máximo."""
        if self.dias_de_presentacion > PLAZO_MAXIMO_DIAS:
            raise DeclaracionExtemporaneaError(
                f"La declaración del vuelo {self.__codigo_vuelo} de la aerolínea "
                f"{self.__aerolinea.codigo} se presentó {self.dias_de_presentacion} días "
                f"después del vuelo; el plazo máximo es de {PLAZO_MAXIMO_DIAS} días."
            )

    def __str__(self):
        return (
            f"Declaración de {self.__aerolinea.codigo}: vuelo {self.__codigo_vuelo} del "
            f"{self.__fecha_vuelo:%Y-%m-%d}, {self.__pasajeros_declarados} pasajeros"
        )
