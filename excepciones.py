"""Excepciones personalizadas del sistema.

Trabajo académico con datos ficticios. No representa ningún sistema real.

Todas heredan de ErrorConciliacion, así el programa principal puede
capturar cada error por separado o todos juntos con una sola clase base.
"""


class ErrorConciliacion(Exception):
    """Clase base de los errores propios del sistema."""


class DeclaracionExtemporaneaError(ErrorConciliacion):
    """Una declaración se presentó después del plazo máximo permitido."""


class InformeCerradoError(ErrorConciliacion):
    """Se intentó modificar un informe que ya fue cerrado."""


class DatosInconsistentesError(ErrorConciliacion):
    """Un dato es inválido: vacío, negativo, de tipo incorrecto o contradictorio."""
