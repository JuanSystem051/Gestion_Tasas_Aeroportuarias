"""Pruebas de la fase 2: Aeropuerto, Vuelo, Aerolinea y Declaracion.

Se ejecutan con:  python -m unittest discover -s tests -t . -v
"""

import unittest
from datetime import date, datetime

from aerolinea import Aerolinea
from aeropuerto import Aeropuerto
from declaracion import Declaracion, PLAZO_MAXIMO_DIAS
from excepciones import DatosInconsistentesError, DeclaracionExtemporaneaError, ErrorConciliacion
from validaciones import validar_codigo
from vuelo import Vuelo

F = date(2026, 3, 10)


def aeropuerto():
    return Aeropuerto("apd", "Aeropuerto Demo", 20000)


class TestValidarCodigo(unittest.TestCase):
    def test_normaliza_a_mayusculas_y_limpia(self):
        self.assertEqual(validar_codigo("  al-101 ", "x"), "AL-101")

    def test_rechaza_invalidos(self):
        for v in ("", "  ", "AL 101", "AL_101", "AL*1", None, 101):
            with self.assertRaises(DatosInconsistentesError):
                validar_codigo(v, "x")


class TestAeropuerto(unittest.TestCase):
    def test_datos_y_normalizacion(self):
        a = aeropuerto()
        self.assertEqual((a.codigo, a.nombre, a.tarifa_por_pasajero), ("APD", "Aeropuerto Demo", 20000.0))

    def test_cobro_estimado(self):
        self.assertEqual(aeropuerto().cobro_estimado(100), 2000000.0)
        self.assertEqual(aeropuerto().cobro_estimado(0), 0.0)

    def test_cobro_estimado_invalido(self):
        for p in (-1, 2.5, "10", None, True):
            with self.assertRaises(DatosInconsistentesError):
                aeropuerto().cobro_estimado(p)

    def test_constructor_invalido(self):
        for args in (("", "N", 1), ("A", "", 1), ("A", "N", 0), ("A", "N", -1), ("A", "N", "5"), ("A B", "N", 1)):
            with self.assertRaises(DatosInconsistentesError):
                Aeropuerto(*args)

    def test_solo_lectura(self):
        with self.assertRaises(AttributeError):
            aeropuerto().tarifa_por_pasajero = 1


class TestVuelo(unittest.TestCase):
    def test_creacion_y_clave(self):
        v = Vuelo("al101", F, aeropuerto(), 100)
        self.assertEqual(v.clave, ("AL101", F))
        self.assertEqual(v.pasajeros_operados, 100)

    def test_asociacion_con_aeropuerto(self):
        ap = aeropuerto()
        self.assertIs(Vuelo("AL101", F, ap, 10).aeropuerto, ap)

    def test_cobro_esperado_usa_la_tarifa_del_aeropuerto(self):
        self.assertEqual(Vuelo("AL101", F, aeropuerto(), 100).cobro_esperado(), 2000000.0)

    def test_invalidos(self):
        ap = aeropuerto()
        casos = [("", F, ap, 1), ("AL1", "2026-03-10", ap, 1), ("AL1", datetime(2026, 3, 10), ap, 1),
                 ("AL1", F, "APD", 1), ("AL1", F, None, 1), ("AL1", F, ap, 0), ("AL1", F, ap, -4),
                 ("AL1", F, ap, 2.5), ("AL1", F, ap, True)]
        for c in casos:
            with self.assertRaises(DatosInconsistentesError, msg=str(c)):
                Vuelo(*c)

    def test_solo_lectura(self):
        with self.assertRaises(AttributeError):
            Vuelo("AL1", F, aeropuerto(), 1).pasajeros_operados = 9


class TestAerolinea(unittest.TestCase):
    def setUp(self):
        self.ap = aeropuerto()
        self.al = Aerolinea("al", "Aerolínea Uno")

    def test_creacion(self):
        self.assertEqual((self.al.codigo, self.al.nombre), ("AL", "Aerolínea Uno"))
        self.assertEqual(self.al.vuelos, ())

    def test_agregacion_el_vuelo_existe_por_fuera(self):
        v = Vuelo("AL101", F, self.ap, 10)       # se crea ANTES e independiente
        self.al.agregar_vuelo(v)
        self.assertIs(self.al.vuelos[0], v)
        del self.al                              # la aerolínea desaparece...
        self.assertEqual(v.codigo, "AL101")      # ...y el vuelo sigue existiendo

    def test_vuelos_devuelve_copia_inmutable(self):
        self.al.agregar_vuelo(Vuelo("AL101", F, self.ap, 10))
        self.assertIsInstance(self.al.vuelos, tuple)
        copia = list(self.al.vuelos)
        copia.clear()
        self.assertEqual(len(self.al.vuelos), 1)   # la lista interna no se alteró

    def test_no_admite_repetidos(self):
        self.al.agregar_vuelo(Vuelo("AL101", F, self.ap, 10))
        with self.assertRaises(DatosInconsistentesError):
            self.al.agregar_vuelo(Vuelo("al101", F, self.ap, 20))
        self.assertEqual(len(self.al.vuelos), 1)

    def test_mismo_codigo_otra_fecha_si_se_admite(self):
        self.al.agregar_vuelo(Vuelo("AL101", F, self.ap, 10))
        self.al.agregar_vuelo(Vuelo("AL101", date(2026, 3, 11), self.ap, 10))
        self.assertEqual(len(self.al.vuelos), 2)

    def test_solo_admite_vuelos(self):
        for malo in ("AL101", None, 5, self.ap):
            with self.assertRaises(DatosInconsistentesError):
                self.al.agregar_vuelo(malo)

    def test_buscar_vuelo(self):
        v = Vuelo("AL101", F, self.ap, 10)
        self.al.agregar_vuelo(v)
        self.assertIs(self.al.buscar_vuelo("al101", F), v)
        self.assertIsNone(self.al.buscar_vuelo("AL999", F))
        self.assertIsNone(self.al.buscar_vuelo("AL101", date(2026, 3, 11)))

    def test_buscar_vuelo_con_datos_invalidos(self):
        with self.assertRaises(DatosInconsistentesError):
            self.al.buscar_vuelo("", F)

    def test_constructor_invalido(self):
        for args in (("", "N"), ("AL", ""), ("A L", "N"), (None, "N")):
            with self.assertRaises(DatosInconsistentesError):
                Aerolinea(*args)


class TestDeclaracion(unittest.TestCase):
    def setUp(self):
        self.al = Aerolinea("AL", "Aerolínea Uno")

    def crear(self, retraso_dias=0, pasajeros=100):
        return Declaracion(self.al, "al101", F, date(2026, 3, 10 + retraso_dias), pasajeros)

    def test_creacion_asociacion_y_clave(self):
        d = self.crear()
        self.assertIs(d.aerolinea, self.al)
        self.assertEqual(d.clave, ("AL101", F))
        self.assertEqual(d.pasajeros_declarados, 100)

    def test_dias_de_presentacion(self):
        self.assertEqual(self.crear(0).dias_de_presentacion, 0)
        self.assertEqual(self.crear(2).dias_de_presentacion, 2)

    def test_en_plazo_no_lanza(self):
        for dias in range(0, PLAZO_MAXIMO_DIAS + 1):      # 0, 1, 2 y 3 días son válidos
            self.crear(dias).verificar_plazo()

    def test_fuera_de_plazo_lanza_la_excepcion_correcta(self):
        with self.assertRaises(DeclaracionExtemporaneaError) as cm:
            self.crear(PLAZO_MAXIMO_DIAS + 1).verificar_plazo()
        self.assertIn("AL101", str(cm.exception))
        self.assertIn(str(PLAZO_MAXIMO_DIAS), str(cm.exception))

    def test_la_extemporanea_se_puede_crear(self):
        # Crear una declaración tardía NO falla: el error solo sale al verificar el plazo,
        # para que el sistema pueda seguir funcionando con ella.
        self.assertEqual(self.crear(10).dias_de_presentacion, 10)

    def test_extemporanea_es_un_error_del_sistema(self):
        with self.assertRaises(ErrorConciliacion):
            self.crear(9).verificar_plazo()

    def test_presentacion_anterior_al_vuelo(self):
        with self.assertRaises(DatosInconsistentesError):
            Declaracion(self.al, "AL101", F, date(2026, 3, 9), 10)

    def test_invalidos(self):
        casos = [("AL", "AL1", F, F, 10), (None, "AL1", F, F, 10), (self.al, "", F, F, 10),
                 (self.al, "AL1", "2026-03-10", F, 10), (self.al, "AL1", F, "2026-03-10", 10),
                 (self.al, "AL1", F, F, 0), (self.al, "AL1", F, F, -2), (self.al, "AL1", F, F, 1.5),
                 (self.al, "AL1", F, F, None)]
        for c in casos:
            with self.assertRaises(DatosInconsistentesError, msg=str(c)):
                Declaracion(*c)

    def test_solo_lectura(self):
        with self.assertRaises(AttributeError):
            self.crear().pasajeros_declarados = 1


if __name__ == "__main__":
    unittest.main()
