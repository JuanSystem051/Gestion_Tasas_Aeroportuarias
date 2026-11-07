"""Clase Conciliador.

Trabajo académico con datos ficticios.

Compara lo DECLARADO por las aerolíneas contra lo realmente OPERADO en un
aeropuerto, y le pide al informe que registre cada diferencia. El Conciliador
no guarda datos propios ni crea hallazgos: solo decide qué diferencia hay.

Supuestos del modelo (simplificaciones académicas):
  - Las declaraciones que se le entregan corresponden al aeropuerto del Conciliador.
  - Un vuelo se identifica por (aerolínea, código, fecha).
  - El plazo de presentación NO impide conciliar: una declaración tardía se
    concilia igual. El control del plazo lo hace Declaracion.verificar_plazo().
"""

from aerolinea import Aerolinea
from aeropuerto import Aeropuerto
from declaracion import Declaracion
from excepciones import DatosInconsistentesError
from informe_conciliacion import InformeConciliacion
from validaciones import validar_instancia


class Conciliador:
    """Cruza declaraciones contra vuelos operados de un aeropuerto."""

    def __init__(self, aeropuerto):
        self.__aeropuerto = validar_instancia(aeropuerto, Aeropuerto, "aeropuerto")

    @property
    def aeropuerto(self):
        return self.__aeropuerto

    # ---- Preparación y validación (todo se valida ANTES de registrar nada) ----
    @staticmethod
    def __como_lista(coleccion, clase, nombre):
        try:
            elementos = list(coleccion)
        except TypeError:
            raise DatosInconsistentesError(
                f"El campo '{nombre}' debe ser una colección de objetos {clase.__name__}."
            ) from None
        for elemento in elementos:
            validar_instancia(elemento, clase, f"elementos de '{nombre}'")
        return elementos

    def __indexar_operados(self, aerolineas):
        """Devuelve {(aerolínea, código, fecha): vuelo} solo de vuelos de este aeropuerto."""
        codigos_aerolinea = [a.codigo for a in aerolineas]
        if len(codigos_aerolinea) != len(set(codigos_aerolinea)):
            raise DatosInconsistentesError("Hay aerolíneas repetidas en la lista a conciliar.")
        operados = {}
        vistos = set()
        for aerolinea in aerolineas:
            for vuelo in aerolinea.vuelos:
                if vuelo.aeropuerto.codigo != self.__aeropuerto.codigo:
                    continue                      # operó en otro aeropuerto: no se concilia aquí
                if vuelo.clave in vistos:
                    raise DatosInconsistentesError(
                        f"El vuelo {vuelo.codigo} del {vuelo.fecha:%Y-%m-%d} aparece en más de "
                        f"una aerolínea; el informe no podría distinguirlos."
                    )
                vistos.add(vuelo.clave)
                operados[(aerolinea.codigo,) + vuelo.clave] = vuelo
        return operados

    @staticmethod
    def __indexar_declaraciones(declaraciones):
        """Devuelve {(aerolínea, código, fecha): declaración}; rechaza duplicadas."""
        declarados = {}
        for declaracion in declaraciones:
            clave = (declaracion.aerolinea.codigo,) + declaracion.clave
            if clave in declarados:
                raise DatosInconsistentesError(
                    f"La aerolínea {clave[0]} declaró dos veces el vuelo {clave[1]} "
                    f"del {clave[2]:%Y-%m-%d}."
                )
            declarados[clave] = declaracion
        return declarados

    # ---- Proceso principal ----
    def conciliar(self, aerolineas, declaraciones, informe):
        """Registra en `informe` cada diferencia y devuelve cuántas registró."""
        validar_instancia(informe, InformeConciliacion, "informe")
        informe.verificar_abierto()
        if informe.cantidad_hallazgos > 0:
            raise DatosInconsistentesError(
                "El informe ya contiene hallazgos; use un informe nuevo para cada conciliación."
            )
        operados = self.__indexar_operados(self.__como_lista(aerolineas, Aerolinea, "aerolineas"))
        declarados = self.__indexar_declaraciones(
            self.__como_lista(declaraciones, Declaracion, "declaraciones")
        )

        tarifa = self.__aeropuerto.tarifa_por_pasajero
        registrados = 0

        # 1) Cada vuelo operado: ¿tiene declaración? ¿coinciden los pasajeros?
        for clave, vuelo in operados.items():
            declaracion = declarados.get(clave)
            if declaracion is None:
                informe.registrar_vuelo_sin_declaracion(
                    vuelo.codigo, vuelo.fecha, tarifa, vuelo.pasajeros_operados)
                registrados += 1
            elif declaracion.pasajeros_declarados != vuelo.pasajeros_operados:
                informe.registrar_diferencia_pasajeros(
                    vuelo.codigo, vuelo.fecha, tarifa,
                    declaracion.pasajeros_declarados, vuelo.pasajeros_operados)
                registrados += 1

        # 2) Cada declaración sin vuelo operado.
        for clave, declaracion in declarados.items():
            if clave not in operados:
                informe.registrar_declaracion_sin_vuelo(
                    declaracion.codigo_vuelo, declaracion.fecha_vuelo, tarifa,
                    declaracion.pasajeros_declarados)
                registrados += 1

        return registrados
