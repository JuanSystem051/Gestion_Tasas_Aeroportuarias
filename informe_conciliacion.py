"""Clase InformeConciliacion.

Trabajo académico con datos ficticios.

COMPOSICIÓN: el informe CREA y CONTIENE sus propios hallazgos. Ningún método
recibe un Hallazgo ya construido: recibe datos simples y los fabrica por dentro.
Por eso un hallazgo no existe fuera de su informe (si el informe desaparece,
sus hallazgos desaparecen con él).

Esta clase solo guarda, prioriza y totaliza. No compara declaraciones contra
vuelos: eso lo hace el Conciliador.
"""

from declaracion_sin_vuelo import DeclaracionSinVuelo
from diferencia_pasajeros import DiferenciaPasajeros
from excepciones import InformeCerradoError
from hallazgo import IMPACTO_EXCESO, IMPACTO_FALTANTE
from validaciones import validar_texto_no_vacio
from vuelo_sin_declaracion import VueloSinDeclaracion


class InformeConciliacion:
    """Conjunto de hallazgos de una conciliación, que puede cerrarse."""

    def __init__(self, titulo):
        self.__titulo = validar_texto_no_vacio(titulo, "titulo")
        self.__hallazgos = []        # lista privada de objetos Hallazgo (composición)
        self.__cerrado = False

    # ---- Consulta ----
    @property
    def titulo(self):
        return self.__titulo

    @property
    def esta_cerrado(self):
        return self.__cerrado

    @property
    def cantidad_hallazgos(self):
        return len(self.__hallazgos)

    @property
    def hallazgos(self):
        """Tupla en orden de registro: se puede recorrer, pero no alterar la lista interna."""
        return tuple(self.__hallazgos)

    # ---- Control de estado ----
    def verificar_abierto(self):
        """Lanza InformeCerradoError si el informe ya fue cerrado."""
        if self.__cerrado:
            raise InformeCerradoError(
                f"El informe '{self.__titulo}' está cerrado y no admite cambios."
            )

    def cerrar(self):
        """Cierra el informe. Cerrar un informe ya cerrado también es un error."""
        self.verificar_abierto()
        self.__cerrado = True

    # ---- Creación de hallazgos (aquí está la composición) ----
    def registrar_vuelo_sin_declaracion(self, codigo_vuelo, fecha, tarifa_por_pasajero, pasajeros_operados):
        self.verificar_abierto()
        self.__hallazgos.append(
            VueloSinDeclaracion(codigo_vuelo, fecha, tarifa_por_pasajero, pasajeros_operados)
        )

    def registrar_declaracion_sin_vuelo(self, codigo_vuelo, fecha, tarifa_por_pasajero, pasajeros_declarados):
        self.verificar_abierto()
        self.__hallazgos.append(
            DeclaracionSinVuelo(codigo_vuelo, fecha, tarifa_por_pasajero, pasajeros_declarados)
        )

    def registrar_diferencia_pasajeros(self, codigo_vuelo, fecha, tarifa_por_pasajero,
                                       pasajeros_declarados, pasajeros_operados):
        self.verificar_abierto()
        self.__hallazgos.append(
            DiferenciaPasajeros(codigo_vuelo, fecha, tarifa_por_pasajero,
                                pasajeros_declarados, pasajeros_operados)
        )

    # ---- Priorización y totales (polimorfismo: nunca se pregunta el tipo) ----
    def hallazgos_priorizados(self):
        """Tupla ordenada de mayor a menor valor en riesgo; en empate, por código y fecha."""
        return tuple(sorted(
            self.__hallazgos,
            key=lambda h: (-h.calcular_valor_en_riesgo(), h.codigo_vuelo, h.fecha),
        ))

    def total_por_impacto(self):
        """Suma del valor en riesgo, separado por impacto (faltante o cobro en exceso).

        No se suman ambos impactos en un solo total porque significan cosas opuestas.
        """
        totales = {IMPACTO_FALTANTE: 0.0, IMPACTO_EXCESO: 0.0}
        for hallazgo in self.__hallazgos:
            totales[hallazgo.impacto()] += hallazgo.calcular_valor_en_riesgo()
        return {impacto: round(valor, 2) for impacto, valor in totales.items()}

    def __str__(self):
        estado = "cerrado" if self.__cerrado else "abierto"
        return f"Informe '{self.__titulo}' ({estado}): {len(self.__hallazgos)} hallazgos"
