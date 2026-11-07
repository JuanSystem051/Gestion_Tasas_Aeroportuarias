"""Pruebas de la fase 1: excepciones, clase abstracta Hallazgo y sus tres hijas.

Se ejecutan con:  python -m unittest discover -s tests -t . -v
"""

import unittest
from datetime import date, datetime

from excepciones import (DatosInconsistentesError, DeclaracionExtemporaneaError,
                         ErrorConciliacion, InformeCerradoError)
from hallazgo import Hallazgo, IMPACTO_EXCESO, IMPACTO_FALTANTE
from vuelo_sin_declaracion import VueloSinDeclaracion
from declaracion_sin_vuelo import DeclaracionSinVuelo
from diferencia_pasajeros import DiferenciaPasajeros

F = date(2026, 3, 10)
TARIFA = 20000


class TestExcepciones(unittest.TestCase):
    def test_todas_heredan_de_la_base(self):
        for clase in (DeclaracionExtemporaneaError, InformeCerradoError, DatosInconsistentesError):
            self.assertTrue(issubclass(clase, ErrorConciliacion))

    def test_se_pueden_capturar_por_la_base(self):
        with self.assertRaises(ErrorConciliacion):
            raise InformeCerradoError("prueba")


class TestClaseAbstracta(unittest.TestCase):
    def test_hallazgo_no_se_puede_instanciar(self):
        with self.assertRaises(TypeError):
            Hallazgo("V1", F, TARIFA)

    def test_hija_incompleta_tampoco(self):
        class Incompleta(Hallazgo):
            def calcular_valor_en_riesgo(self):
                return 0
        with self.assertRaises(TypeError):
            Incompleta("V1", F, TARIFA)


class TestHijas(unittest.TestCase):
    def test_valores_en_riesgo(self):
        self.assertEqual(VueloSinDeclaracion("AL101", F, TARIFA, 100).calcular_valor_en_riesgo(), 2000000.0)
        self.assertEqual(DeclaracionSinVuelo("AL102", F, TARIFA, 50).calcular_valor_en_riesgo(), 1000000.0)
        self.assertEqual(DiferenciaPasajeros("AL103", F, TARIFA, 90, 95).calcular_valor_en_riesgo(), 100000.0)

    def test_impactos(self):
        self.assertEqual(VueloSinDeclaracion("A", F, TARIFA, 1).impacto(), IMPACTO_FALTANTE)
        self.assertEqual(DeclaracionSinVuelo("A", F, TARIFA, 1).impacto(), IMPACTO_EXCESO)
        self.assertEqual(DiferenciaPasajeros("A", F, TARIFA, 90, 95).impacto(), IMPACTO_FALTANTE)
        self.assertEqual(DiferenciaPasajeros("A", F, TARIFA, 95, 90).impacto(), IMPACTO_EXCESO)

    def test_diferencia_es_valor_absoluto(self):
        self.assertEqual(DiferenciaPasajeros("A", F, TARIFA, 95, 90).diferencia, 5)
        self.assertEqual(DiferenciaPasajeros("A", F, TARIFA, 90, 95).diferencia, 5)

    def test_acciones_distintas(self):
        acciones = {
            VueloSinDeclaracion("A", F, TARIFA, 1).recomendar_accion(),
            DeclaracionSinVuelo("A", F, TARIFA, 1).recomendar_accion(),
            DiferenciaPasajeros("A", F, TARIFA, 1, 2).recomendar_accion(),
            DiferenciaPasajeros("A", F, TARIFA, 2, 1).recomendar_accion(),
        }
        self.assertEqual(len(acciones), 4)

    def test_describir_reutiliza_la_base_con_super(self):
        base = "Vuelo AL101 del 2026-03-10 (tarifa aplicada: $20,000.00 por pasajero)"
        for h in (VueloSinDeclaracion("AL101", F, TARIFA, 100),
                  DeclaracionSinVuelo("AL101", F, TARIFA, 100),
                  DiferenciaPasajeros("AL101", F, TARIFA, 90, 95)):
            self.assertTrue(h.describir().startswith(base))
            self.assertGreater(len(h.describir()), len(base))

    def test_polimorfismo_un_solo_ciclo_sin_condicionales_por_tipo(self):
        hallazgos = [VueloSinDeclaracion("A", F, TARIFA, 10),
                     DeclaracionSinVuelo("B", F, TARIFA, 5),
                     DiferenciaPasajeros("C", F, TARIFA, 8, 9)]
        valores = []
        for h in hallazgos:                      # único ciclo, sin if ni isinstance
            valores.append(h.calcular_valor_en_riesgo())
        self.assertEqual(valores, [200000.0, 100000.0, 20000.0])


class TestEncapsulamiento(unittest.TestCase):
    def test_atributos_de_solo_lectura(self):
        h = VueloSinDeclaracion("AL101", F, TARIFA, 100)
        with self.assertRaises(AttributeError):
            h.codigo_vuelo = "OTRO"
        with self.assertRaises(AttributeError):
            h.pasajeros_operados = 5

    def test_atributo_privado_no_es_accesible_por_su_nombre(self):
        h = VueloSinDeclaracion("AL101", F, TARIFA, 100)
        with self.assertRaises(AttributeError):
            h.__codigo_vuelo


class TestValidaciones(unittest.TestCase):
    def assertInvalido(self, fabrica):
        with self.assertRaises(DatosInconsistentesError):
            fabrica()

    def test_codigo_vacio_o_no_texto(self):
        self.assertInvalido(lambda: VueloSinDeclaracion("  ", F, TARIFA, 1))
        self.assertInvalido(lambda: VueloSinDeclaracion(None, F, TARIFA, 1))
        self.assertInvalido(lambda: VueloSinDeclaracion(123, F, TARIFA, 1))

    def test_fecha_invalida(self):
        self.assertInvalido(lambda: VueloSinDeclaracion("A", "2026-03-10", TARIFA, 1))
        self.assertInvalido(lambda: VueloSinDeclaracion("A", datetime(2026, 3, 10), TARIFA, 1))

    def test_tarifa_invalida(self):
        for t in (0, -5, "20000", None, True, float("nan"), float("inf")):
            self.assertInvalido(lambda t=t: VueloSinDeclaracion("A", F, t, 1))

    def test_pasajeros_invalidos(self):
        for p in (0, -3, 2.5, "10", None, True):
            self.assertInvalido(lambda p=p: VueloSinDeclaracion("A", F, TARIFA, p))
            self.assertInvalido(lambda p=p: DeclaracionSinVuelo("A", F, TARIFA, p))

    def test_diferencia_con_pasajeros_invalidos_o_iguales(self):
        self.assertInvalido(lambda: DiferenciaPasajeros("A", F, TARIFA, -1, 5))
        self.assertInvalido(lambda: DiferenciaPasajeros("A", F, TARIFA, 5, 5))
        self.assertInvalido(lambda: DiferenciaPasajeros("A", F, TARIFA, 5.0, 6))

    def test_diferencia_permite_cero_de_un_lado(self):
        self.assertEqual(DiferenciaPasajeros("A", F, TARIFA, 0, 4).diferencia, 4)

    def test_espacios_se_limpian(self):
        self.assertEqual(VueloSinDeclaracion("  AL101 ", F, TARIFA, 1).codigo_vuelo, "AL101")


if __name__ == "__main__":
    unittest.main()
