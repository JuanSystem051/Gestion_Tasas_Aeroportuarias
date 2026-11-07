"""Clase abstracta Hallazgo.

Trabajo académico con datos ficticios.

Un Hallazgo es una diferencia detectada al comparar lo que declaró una
aerolínea contra lo que realmente se operó. Esta clase NO se puede
instanciar: obliga a cada tipo de hallazgo a decir cómo se valora, qué
impacto tiene y qué acción se recomienda.
"""

from abc import ABC, abstractmethod

from validaciones import validar_fecha, validar_numero_positivo, validar_texto_no_vacio

# Las dos únicas categorías de impacto posibles.
IMPACTO_FALTANTE = "Faltante de recaudo"
IMPACTO_EXCESO = "Posible cobro en exceso"


class Hallazgo(ABC):
    """Datos y comportamiento comunes a todos los tipos de diferencia."""

    def __init__(self, codigo_vuelo, fecha, tarifa_por_pasajero):
        # Atributos privados (doble guion bajo): solo se leen por propiedades.
        self.__codigo_vuelo = validar_texto_no_vacio(codigo_vuelo, "codigo_vuelo")
        self.__fecha = validar_fecha(fecha, "fecha")
        self.__tarifa_por_pasajero = validar_numero_positivo(
            tarifa_por_pasajero, "tarifa_por_pasajero"
        )

    # ---- Acceso de solo lectura (encapsulamiento) ----
    @property
    def codigo_vuelo(self):
        return self.__codigo_vuelo

    @property
    def fecha(self):
        return self.__fecha

    @property
    def tarifa_por_pasajero(self):
        return self.__tarifa_por_pasajero

    # ---- Comportamiento que cada hija DEBE implementar ----
    @abstractmethod
    def calcular_valor_en_riesgo(self):
        """Valor en pesos (ficticios) que está en juego por esta diferencia."""

    @abstractmethod
    def impacto(self):
        """Devuelve IMPACTO_FALTANTE o IMPACTO_EXCESO."""

    @abstractmethod
    def recomendar_accion(self):
        """Texto con la acción sugerida al funcionario."""

    # ---- Comportamiento común que las hijas amplían con super() ----
    def describir(self):
        """Descripción base: vuelo, fecha y tarifa aplicada."""
        return (
            f"Vuelo {self.__codigo_vuelo} del {self.__fecha:%Y-%m-%d} "
            f"(tarifa aplicada: ${self.__tarifa_por_pasajero:,.2f} por pasajero)"
        )
