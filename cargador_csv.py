"""Clase CargadorCSV.

Trabajo académico con datos ficticios.

Lee los dos archivos CSV del sistema y construye los objetos del dominio:
  - vuelos_operados.csv : vuelos realmente operados (crea Aerolinea y Vuelo).
  - declaraciones.csv   : lo que declararon las aerolíneas (crea Declaracion).

Reglas de la carga (carga ESTRICTA):
  - Si una sola fila es inválida, se rechaza TODO el archivo con
    DatosInconsistentesError, indicando archivo y número de línea.
  - Un archivo rechazado no deja nada a medias: no se registra ni una fila.
  - Un archivo rechazado no afecta lo ya cargado: el sistema sigue funcionando.
  - Un archivo sin filas de datos también se rechaza, porque casi siempre es
    un error de exportación y daría resultados engañosos al conciliar.

Las aerolíneas no tienen archivo propio: se crean a partir de las columnas
'aerolinea' y 'nombre_aerolinea' de cualquiera de los dos archivos.
"""

import csv
import os
import re
from datetime import date

from aerolinea import Aerolinea
from aeropuerto import Aeropuerto
from declaracion import Declaracion
from excepciones import DatosInconsistentesError
from validaciones import validar_codigo, validar_instancia, validar_texto_no_vacio
from vuelo import Vuelo

COLUMNAS_VUELOS = ("aerolinea", "nombre_aerolinea", "codigo_vuelo", "fecha", "pasajeros_operados")
COLUMNAS_DECLARACIONES = (
    "aerolinea", "nombre_aerolinea", "codigo_vuelo",
    "fecha_vuelo", "fecha_presentacion", "pasajeros_declarados",
)

_ENTERO = re.compile(r"[0-9]+")
_FECHA = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_MAX_DIGITOS = 9


class CargadorCSV:
    """Convierte archivos CSV ficticios en objetos Aerolinea, Vuelo y Declaracion."""

    def __init__(self, aeropuerto):
        self.__aeropuerto = validar_instancia(aeropuerto, Aeropuerto, "aeropuerto")
        self.__aerolineas = {}            # código -> Aerolinea (en orden de aparición)
        self.__declaraciones = []

    @property
    def aeropuerto(self):
        return self.__aeropuerto

    @property
    def aerolineas(self):
        return tuple(self.__aerolineas.values())

    @property
    def declaraciones(self):
        return tuple(self.__declaraciones)

    # ------------------------------------------------------------------
    # Lectura y conversión de datos (privado)
    # ------------------------------------------------------------------
    @staticmethod
    def __leer_filas(ruta, columnas):
        """Devuelve [(número_de_línea, fila_dict)] o lanza DatosInconsistentesError."""
        try:
            ruta = os.fspath(ruta)
        except TypeError:
            ruta = None
        if not isinstance(ruta, str) or not ruta.strip():
            raise DatosInconsistentesError(
                "La ruta del archivo debe ser un texto o un objeto Path no vacío."
            )
        nombre = os.path.basename(ruta)
        filas = []
        try:
            with open(ruta, newline="", encoding="utf-8-sig") as archivo:
                lector = csv.DictReader(archivo)
                encabezado = lector.fieldnames
                if encabezado is None:
                    raise DatosInconsistentesError(f"{nombre}: el archivo está vacío.")
                if sorted(encabezado) != sorted(columnas):
                    raise DatosInconsistentesError(
                        f"{nombre}: columnas incorrectas. Se esperaban {list(columnas)} "
                        f"y se encontraron {list(encabezado)}."
                    )
                for fila in lector:
                    numero = lector.line_num
                    if None in fila:
                        raise DatosInconsistentesError(
                            f"{nombre}, línea {numero}: tiene más campos de los esperados."
                        )
                    if any(valor is None for valor in fila.values()):
                        raise DatosInconsistentesError(
                            f"{nombre}, línea {numero}: tiene menos campos de los esperados."
                        )
                    filas.append((numero, fila))
        except FileNotFoundError:
            raise DatosInconsistentesError(f"No se encontró el archivo '{nombre}'.") from None
        except UnicodeDecodeError:
            raise DatosInconsistentesError(
                f"{nombre}: el archivo no está codificado en UTF-8."
            ) from None
        except OSError:
            raise DatosInconsistentesError(f"No se pudo leer el archivo '{nombre}'.") from None
        except csv.Error as error:
            raise DatosInconsistentesError(f"{nombre}: formato CSV inválido ({error}).") from None
        if not filas:
            raise DatosInconsistentesError(f"{nombre}: el archivo no contiene filas de datos.")
        return nombre, filas

    @staticmethod
    def __a_fecha(texto, nombre):
        texto = texto.strip()
        if not _FECHA.fullmatch(texto):
            raise DatosInconsistentesError(
                f"el campo '{nombre}' debe tener el formato AAAA-MM-DD (se recibió '{texto}')."
            )
        try:
            return date.fromisoformat(texto)
        except ValueError:
            raise DatosInconsistentesError(
                f"el campo '{nombre}' no es una fecha real (se recibió '{texto}')."
            ) from None

    @staticmethod
    def __a_entero(texto, nombre):
        texto = texto.strip()
        if not _ENTERO.fullmatch(texto) or len(texto) > _MAX_DIGITOS:
            raise DatosInconsistentesError(
                f"el campo '{nombre}' debe ser un número entero positivo, sin signos ni "
                f"decimales (se recibió '{texto}')."
            )
        return int(texto)

    def __resolver_aerolinea(self, fila, nuevas):
        """Busca la aerolínea ya cargada o creada en esta carga; si no existe, la crea."""
        codigo = validar_codigo(fila["aerolinea"], "aerolinea")
        nombre = validar_texto_no_vacio(fila["nombre_aerolinea"], "nombre_aerolinea")
        aerolinea = self.__aerolineas.get(codigo)
        if aerolinea is None:
            aerolinea = nuevas.get(codigo)
        if aerolinea is None:
            aerolinea = Aerolinea(codigo, nombre)
            nuevas[codigo] = aerolinea
        elif aerolinea.nombre != nombre:
            raise DatosInconsistentesError(
                f"la aerolínea {codigo} figura como '{aerolinea.nombre}' y aquí como '{nombre}'."
            )
        return aerolinea

    # ------------------------------------------------------------------
    # Carga pública
    # ------------------------------------------------------------------
    def cargar_vuelos(self, ruta):
        """Carga vuelos_operados.csv. Devuelve cuántos vuelos cargó."""
        nombre, filas = self.__leer_filas(ruta, COLUMNAS_VUELOS)
        nuevas = {}            # aerolíneas creadas solo en esta carga
        pendientes = []        # (aerolinea, vuelo) validados, aún sin registrar
        vistos = {}            # clave -> línea de su primera aparición
        for numero, fila in filas:
            try:
                aerolinea = self.__resolver_aerolinea(fila, nuevas)
                fecha = self.__a_fecha(fila["fecha"], "fecha")
                pasajeros = self.__a_entero(fila["pasajeros_operados"], "pasajeros_operados")
                codigo_vuelo = validar_codigo(fila["codigo_vuelo"], "codigo_vuelo")
                vuelo = Vuelo(codigo_vuelo, fecha, self.__aeropuerto, pasajeros)
                clave = (aerolinea.codigo,) + vuelo.clave
                if clave in vistos:
                    raise DatosInconsistentesError(
                        f"el vuelo {vuelo.codigo} del {vuelo.fecha:%Y-%m-%d} de {aerolinea.codigo} "
                        f"ya aparece en la línea {vistos[clave]}."
                    )
                if aerolinea.buscar_vuelo(vuelo.codigo, vuelo.fecha) is not None:
                    raise DatosInconsistentesError(
                        f"el vuelo {vuelo.codigo} del {vuelo.fecha:%Y-%m-%d} de {aerolinea.codigo} "
                        f"ya había sido cargado."
                    )
            except DatosInconsistentesError as error:
                raise DatosInconsistentesError(f"{nombre}, línea {numero}: {error}") from error
            vistos[clave] = numero
            pendientes.append((aerolinea, vuelo))
        # Todo es válido: recién ahora se registra (así el rechazo no deja nada a medias).
        self.__aerolineas.update(nuevas)
        for aerolinea, vuelo in pendientes:
            aerolinea.agregar_vuelo(vuelo)
        return len(pendientes)

    def cargar_declaraciones(self, ruta):
        """Carga declaraciones.csv. Devuelve cuántas declaraciones cargó."""
        nombre, filas = self.__leer_filas(ruta, COLUMNAS_DECLARACIONES)
        nuevas = {}
        pendientes = []
        vistos = {(d.aerolinea.codigo,) + d.clave: None for d in self.__declaraciones}
        for numero, fila in filas:
            try:
                aerolinea = self.__resolver_aerolinea(fila, nuevas)
                fecha_vuelo = self.__a_fecha(fila["fecha_vuelo"], "fecha_vuelo")
                fecha_presentacion = self.__a_fecha(fila["fecha_presentacion"], "fecha_presentacion")
                pasajeros = self.__a_entero(fila["pasajeros_declarados"], "pasajeros_declarados")
                codigo_vuelo = validar_codigo(fila["codigo_vuelo"], "codigo_vuelo")
                declaracion = Declaracion(aerolinea, codigo_vuelo, fecha_vuelo,
                                          fecha_presentacion, pasajeros)
                clave = (aerolinea.codigo,) + declaracion.clave
                if clave in vistos:
                    anterior = vistos[clave]
                    donde = f"en la línea {anterior}" if anterior else "en una carga anterior"
                    raise DatosInconsistentesError(
                        f"el vuelo {declaracion.codigo_vuelo} del {declaracion.fecha_vuelo:%Y-%m-%d} "
                        f"de {aerolinea.codigo} ya fue declarado {donde}."
                    )
            except DatosInconsistentesError as error:
                raise DatosInconsistentesError(f"{nombre}, línea {numero}: {error}") from error
            vistos[clave] = numero
            pendientes.append(declaracion)
        self.__aerolineas.update(nuevas)
        self.__declaraciones.extend(pendientes)
        return len(pendientes)
