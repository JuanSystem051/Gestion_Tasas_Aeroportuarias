"""Funciones de apoyo para validar datos en los constructores.

Trabajo académico con datos ficticios.

Cada función devuelve el valor ya limpio o lanza DatosInconsistentesError.
Así, ningún objeto del sistema puede quedar creado con datos inválidos.
"""

import math
import re
from datetime import date, datetime

from excepciones import DatosInconsistentesError


def validar_texto_no_vacio(valor, nombre):
    """Exige un texto con contenido y lo devuelve sin espacios sobrantes."""
    if not isinstance(valor, str) or not valor.strip():
        raise DatosInconsistentesError(
            f"El campo '{nombre}' es obligatorio y debe ser un texto no vacío."
        )
    return valor.strip()


def validar_entero_no_negativo(valor, nombre):
    """Exige un entero mayor o igual a cero (bool no cuenta como entero)."""
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise DatosInconsistentesError(
            f"El campo '{nombre}' debe ser un número entero mayor o igual a cero."
        )
    return valor


def validar_entero_positivo(valor, nombre):
    """Exige un entero mayor que cero."""
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise DatosInconsistentesError(
            f"El campo '{nombre}' debe ser un número entero mayor que cero."
        )
    return valor


def validar_numero_positivo(valor, nombre):
    """Exige un número real finito mayor que cero y lo devuelve como float."""
    if (
        isinstance(valor, bool)
        or not isinstance(valor, (int, float))
        or not math.isfinite(valor)
        or valor <= 0
    ):
        raise DatosInconsistentesError(
            f"El campo '{nombre}' debe ser un número mayor que cero."
        )
    return float(valor)


def validar_fecha(valor, nombre):
    """Exige un objeto date (no datetime, no texto)."""
    if isinstance(valor, datetime) or not isinstance(valor, date):
        raise DatosInconsistentesError(
            f"El campo '{nombre}' debe ser una fecha (datetime.date)."
        )
    return valor


def validar_codigo(valor, nombre):
    """Exige un código de letras, números o guiones; lo devuelve en mayúsculas.

    Normalizar a mayúsculas evita que 'al101' y 'AL101' se tomen por vuelos distintos.
    """
    texto = validar_texto_no_vacio(valor, nombre).upper()
    if not re.fullmatch(r"[A-Z0-9-]+", texto):
        raise DatosInconsistentesError(
            f"El campo '{nombre}' solo admite letras, números y guiones, sin espacios."
        )
    return texto


def validar_instancia(valor, clase, nombre):
    """Exige que el valor sea un objeto de la clase indicada."""
    if not isinstance(valor, clase):
        raise DatosInconsistentesError(
            f"El campo '{nombre}' debe ser un objeto de tipo {clase.__name__}."
        )
    return valor
