"""Hallazgo: el vuelo existe en ambos lados, pero los pasajeros no coinciden."""

from hallazgo import Hallazgo, IMPACTO_EXCESO, IMPACTO_FALTANTE
from validaciones import validar_entero_no_negativo
from excepciones import DatosInconsistentesError


class DiferenciaPasajeros(Hallazgo):
    """Declarados y operados son distintos para el mismo vuelo."""

    def __init__(self, codigo_vuelo, fecha, tarifa_por_pasajero,
                 pasajeros_declarados, pasajeros_operados):
        super().__init__(codigo_vuelo, fecha, tarifa_por_pasajero)
        declarados = validar_entero_no_negativo(pasajeros_declarados, "pasajeros_declarados")
        operados = validar_entero_no_negativo(pasajeros_operados, "pasajeros_operados")
        if declarados == operados:
            raise DatosInconsistentesError(
                "No hay diferencia de pasajeros: declarados y operados son iguales."
            )
        self.__pasajeros_declarados = declarados
        self.__pasajeros_operados = operados

    @property
    def pasajeros_declarados(self):
        return self.__pasajeros_declarados

    @property
    def pasajeros_operados(self):
        return self.__pasajeros_operados

    @property
    def diferencia(self):
        """Diferencia en valor absoluto, siempre mayor que cero."""
        return abs(self.__pasajeros_operados - self.__pasajeros_declarados)

    def __subdeclarado(self):
        """True si operaron más pasajeros de los que se declararon."""
        return self.__pasajeros_operados > self.__pasajeros_declarados

    def calcular_valor_en_riesgo(self):
        return round(self.diferencia * self.tarifa_por_pasajero, 2)

    def impacto(self):
        return IMPACTO_FALTANTE if self.__subdeclarado() else IMPACTO_EXCESO

    def recomendar_accion(self):
        if self.__subdeclarado():
            return "Solicitar a la aerolínea corregir la declaración: operaron más pasajeros de los declarados."
        return "Verificar el conteo: se declararon más pasajeros de los operados; evaluar posible devolución."

    def describir(self):
        return (
            f"{super().describir()} | Declarados: {self.__pasajeros_declarados}, "
            f"operados: {self.__pasajeros_operados} (diferencia de {self.diferencia})."
        )
