"""Pruebas de la fase 3: InformeConciliacion (composición) y Conciliador.

Se ejecutan con:  python -m unittest discover -s tests -t . -v
"""

import gc
import pathlib
import unittest
import weakref
from datetime import date

from aerolinea import Aerolinea
from aeropuerto import Aeropuerto
from conciliador import Conciliador
from declaracion import Declaracion
from declaracion_sin_vuelo import DeclaracionSinVuelo
from diferencia_pasajeros import DiferenciaPasajeros
from excepciones import DatosInconsistentesError, DeclaracionExtemporaneaError, InformeCerradoError
from hallazgo import Hallazgo, IMPACTO_EXCESO, IMPACTO_FALTANTE
from informe_conciliacion import InformeConciliacion
from vuelo import Vuelo
from vuelo_sin_declaracion import VueloSinDeclaracion

F = date(2026, 3, 10)
TARIFA = 20000


def declarar(aerolinea, codigo, pasajeros, fecha=F, retraso=0):
    return Declaracion(aerolinea, codigo, fecha, date(fecha.year, fecha.month, fecha.day + retraso), pasajeros)


class TestInforme(unittest.TestCase):
    def setUp(self):
        self.inf = InformeConciliacion("Informe de prueba")

    def test_inicial(self):
        self.assertEqual(self.inf.titulo, "Informe de prueba")
        self.assertFalse(self.inf.esta_cerrado)
        self.assertEqual(self.inf.cantidad_hallazgos, 0)
        self.assertEqual(self.inf.hallazgos, ())

    def test_titulo_invalido(self):
        for t in ("", "  ", None, 5):
            with self.assertRaises(DatosInconsistentesError):
                InformeConciliacion(t)

    def test_composicion_crea_hallazgos_de_los_tres_tipos(self):
        self.inf.registrar_vuelo_sin_declaracion("AL1", F, TARIFA, 10)
        self.inf.registrar_declaracion_sin_vuelo("AL2", F, TARIFA, 5)
        self.inf.registrar_diferencia_pasajeros("AL3", F, TARIFA, 8, 9)
        tipos = [type(h) for h in self.inf.hallazgos]
        self.assertEqual(tipos, [VueloSinDeclaracion, DeclaracionSinVuelo, DiferenciaPasajeros])
        for h in self.inf.hallazgos:
            self.assertIsInstance(h, Hallazgo)

    def test_no_existe_forma_de_entregarle_un_hallazgo_ya_construido(self):
        publicos = [n for n in dir(self.inf) if not n.startswith("_")]
        self.assertEqual(
            sorted(n for n in publicos if n.startswith("registrar_")),
            ["registrar_declaracion_sin_vuelo", "registrar_diferencia_pasajeros",
             "registrar_vuelo_sin_declaracion"])
        # y registrar_* recibe datos simples: un Hallazgo ya hecho es rechazado
        ajeno = VueloSinDeclaracion("AL1", F, TARIFA, 10)
        with self.assertRaises(DatosInconsistentesError):
            self.inf.registrar_vuelo_sin_declaracion(ajeno, F, TARIFA, 10)

    def test_el_hallazgo_vive_y_muere_con_el_informe(self):
        self.inf.registrar_vuelo_sin_declaracion("AL1", F, TARIFA, 10)
        referencia = weakref.ref(self.inf.hallazgos[0])
        self.assertIsNotNone(referencia())
        del self.inf
        gc.collect()
        self.assertIsNone(referencia())          # sin informe, el hallazgo ya no existe

    def test_hallazgos_devuelve_copia_inmutable(self):
        self.inf.registrar_vuelo_sin_declaracion("AL1", F, TARIFA, 10)
        self.assertIsInstance(self.inf.hallazgos, tuple)
        list(self.inf.hallazgos).clear()
        self.assertEqual(self.inf.cantidad_hallazgos, 1)

    def test_registro_invalido_no_deja_basura(self):
        with self.assertRaises(DatosInconsistentesError):
            self.inf.registrar_vuelo_sin_declaracion("AL1", F, TARIFA, -5)
        with self.assertRaises(DatosInconsistentesError):
            self.inf.registrar_diferencia_pasajeros("AL1", F, TARIFA, 7, 7)
        self.assertEqual(self.inf.cantidad_hallazgos, 0)

    # ---- Cierre e InformeCerradoError ----
    def test_cerrar(self):
        self.inf.cerrar()
        self.assertTrue(self.inf.esta_cerrado)

    def test_cerrado_rechaza_cada_tipo_de_registro_y_conserva_lo_anterior(self):
        self.inf.registrar_vuelo_sin_declaracion("AL1", F, TARIFA, 10)
        self.inf.cerrar()
        acciones = [
            lambda: self.inf.registrar_vuelo_sin_declaracion("AL2", F, TARIFA, 1),
            lambda: self.inf.registrar_declaracion_sin_vuelo("AL2", F, TARIFA, 1),
            lambda: self.inf.registrar_diferencia_pasajeros("AL2", F, TARIFA, 1, 2),
            self.inf.cerrar,
        ]
        for accion in acciones:
            with self.assertRaises(InformeCerradoError):
                accion()
        self.assertEqual(self.inf.cantidad_hallazgos, 1)       # nada cambió
        self.assertEqual(len(self.inf.hallazgos_priorizados()), 1)   # y se puede consultar

    def test_mensaje_de_cerrado_es_claro(self):
        self.inf.cerrar()
        with self.assertRaises(InformeCerradoError) as cm:
            self.inf.verificar_abierto()
        self.assertIn("Informe de prueba", str(cm.exception))
        self.assertIn("cerrado", str(cm.exception))

    # ---- Priorización y totales (polimorfismo) ----
    def test_priorizacion_por_valor_en_riesgo_descendente(self):
        self.inf.registrar_diferencia_pasajeros("PEQ", F, TARIFA, 8, 9)        # 20.000
        self.inf.registrar_vuelo_sin_declaracion("GRA", F, TARIFA, 100)        # 2.000.000
        self.inf.registrar_declaracion_sin_vuelo("MED", F, TARIFA, 10)         # 200.000
        orden = [h.codigo_vuelo for h in self.inf.hallazgos_priorizados()]
        self.assertEqual(orden, ["GRA", "MED", "PEQ"])
        valores = [h.calcular_valor_en_riesgo() for h in self.inf.hallazgos_priorizados()]
        self.assertEqual(valores, sorted(valores, reverse=True))

    def test_empate_se_resuelve_por_codigo_y_es_estable(self):
        self.inf.registrar_vuelo_sin_declaracion("ZZ9", F, TARIFA, 5)
        self.inf.registrar_vuelo_sin_declaracion("AA1", F, TARIFA, 5)
        self.assertEqual([h.codigo_vuelo for h in self.inf.hallazgos_priorizados()], ["AA1", "ZZ9"])

    def test_priorizar_no_altera_el_orden_de_registro(self):
        self.inf.registrar_diferencia_pasajeros("PEQ", F, TARIFA, 8, 9)
        self.inf.registrar_vuelo_sin_declaracion("GRA", F, TARIFA, 100)
        self.inf.hallazgos_priorizados()
        self.assertEqual([h.codigo_vuelo for h in self.inf.hallazgos], ["PEQ", "GRA"])

    def test_totales_por_impacto(self):
        self.inf.registrar_vuelo_sin_declaracion("A", F, TARIFA, 100)          # faltante 2.000.000
        self.inf.registrar_diferencia_pasajeros("B", F, TARIFA, 90, 95)        # faltante 100.000
        self.inf.registrar_declaracion_sin_vuelo("C", F, TARIFA, 50)           # exceso 1.000.000
        self.inf.registrar_diferencia_pasajeros("D", F, TARIFA, 95, 90)        # exceso 100.000
        self.assertEqual(self.inf.total_por_impacto(),
                         {IMPACTO_FALTANTE: 2100000.0, IMPACTO_EXCESO: 1100000.0})

    def test_totales_de_informe_vacio(self):
        self.assertEqual(self.inf.total_por_impacto(), {IMPACTO_FALTANTE: 0.0, IMPACTO_EXCESO: 0.0})

    def test_informe_no_usa_isinstance_ni_type_para_decidir(self):
        codigo = pathlib.Path(__file__).resolve().parent.parent.joinpath("informe_conciliacion.py")
        fuente = codigo.read_text(encoding="utf-8")
        self.assertNotIn("isinstance", fuente)
        self.assertNotIn("type(", fuente)


class TestConciliador(unittest.TestCase):
    def setUp(self):
        self.ap = Aeropuerto("APD", "Aeropuerto Demo", TARIFA)
        self.con = Conciliador(self.ap)
        self.al1 = Aerolinea("AL", "Aerolínea Uno")
        self.al2 = Aerolinea("BR", "Aerolínea Dos")
        self.inf = InformeConciliacion("Conciliación de prueba")

    def vuelo(self, aerolinea, codigo, pasajeros, fecha=F, aeropuerto=None):
        v = Vuelo(codigo, fecha, aeropuerto or self.ap, pasajeros)
        aerolinea.agregar_vuelo(v)
        return v

    def conciliar(self, aerolineas, declaraciones):
        return self.con.conciliar(aerolineas, declaraciones, self.inf)

    # ---- Casos normales ----
    def test_todo_coincide_no_genera_hallazgos(self):
        self.vuelo(self.al1, "AL101", 100)
        self.vuelo(self.al2, "BR201", 80)
        n = self.conciliar([self.al1, self.al2],
                           [declarar(self.al1, "AL101", 100), declarar(self.al2, "BR201", 80)])
        self.assertEqual(n, 0)
        self.assertEqual(self.inf.cantidad_hallazgos, 0)

    def test_vuelo_sin_declaracion(self):
        self.vuelo(self.al1, "AL101", 100)
        self.assertEqual(self.conciliar([self.al1], []), 1)
        h = self.inf.hallazgos[0]
        self.assertIsInstance(h, VueloSinDeclaracion)
        self.assertEqual((h.codigo_vuelo, h.pasajeros_operados, h.calcular_valor_en_riesgo()),
                         ("AL101", 100, 2000000.0))

    def test_declaracion_sin_vuelo(self):
        self.assertEqual(self.conciliar([self.al1], [declarar(self.al1, "AL999", 50)]), 1)
        h = self.inf.hallazgos[0]
        self.assertIsInstance(h, DeclaracionSinVuelo)
        self.assertEqual((h.codigo_vuelo, h.calcular_valor_en_riesgo()), ("AL999", 1000000.0))

    def test_diferencia_de_pasajeros_en_ambos_sentidos(self):
        self.vuelo(self.al1, "AL101", 95)      # declaró 90, operaron 95 -> faltante
        self.vuelo(self.al1, "AL102", 90)      # declaró 95, operaron 90 -> exceso
        self.conciliar([self.al1], [declarar(self.al1, "AL101", 90), declarar(self.al1, "AL102", 95)])
        impactos = {h.codigo_vuelo: h.impacto() for h in self.inf.hallazgos}
        self.assertEqual(impactos, {"AL101": IMPACTO_FALTANTE, "AL102": IMPACTO_EXCESO})

    def test_declaracion_de_aerolinea_desconocida_es_declaracion_sin_vuelo(self):
        # la aerolínea BR no está en la lista a conciliar y no tiene vuelos
        self.assertEqual(self.conciliar([self.al1], [declarar(self.al2, "BR201", 40)]), 1)
        self.assertIsInstance(self.inf.hallazgos[0], DeclaracionSinVuelo)

    def test_mismo_codigo_en_otra_fecha_no_coincide(self):
        self.vuelo(self.al1, "AL101", 100)
        self.conciliar([self.al1], [declarar(self.al1, "AL101", 100, fecha=date(2026, 3, 11))])
        self.assertEqual(sorted(type(h).__name__ for h in self.inf.hallazgos),
                         ["DeclaracionSinVuelo", "VueloSinDeclaracion"])

    def test_misma_clave_pero_otra_aerolinea_no_coincide(self):
        self.vuelo(self.al1, "AL101", 100)
        self.conciliar([self.al1, self.al2], [declarar(self.al2, "AL101", 100)])
        self.assertEqual(self.inf.cantidad_hallazgos, 2)

    def test_vuelos_de_otro_aeropuerto_se_ignoran(self):
        otro = Aeropuerto("OTR", "Otro Aeropuerto Demo", 15000)
        self.vuelo(self.al1, "AL101", 100, aeropuerto=otro)
        self.assertEqual(self.conciliar([self.al1], []), 0)

    def test_codigos_en_minuscula_coinciden(self):
        self.vuelo(self.al1, "al101", 100)
        self.assertEqual(self.conciliar([self.al1], [declarar(self.al1, "AL101", 100)]), 0)

    def test_declaracion_tardia_se_concilia_sin_error(self):
        self.vuelo(self.al1, "AL101", 100)
        tardia = declarar(self.al1, "AL101", 100, retraso=8)
        self.assertEqual(self.conciliar([self.al1], [tardia]), 0)
        with self.assertRaises(DeclaracionExtemporaneaError):    # el plazo se controla aparte
            tardia.verificar_plazo()

    def test_acepta_cualquier_coleccion_iterable(self):
        self.vuelo(self.al1, "AL101", 100)
        self.assertEqual(self.conciliar((a for a in [self.al1]), iter([])), 1)

    def test_resultado_es_determinista(self):
        def ejecutar():
            a1 = Aerolinea("AL", "Uno"); a2 = Aerolinea("BR", "Dos")
            for a, c, p in ((a1, "AL101", 100), (a1, "AL102", 50), (a2, "BR201", 80)):
                a.agregar_vuelo(Vuelo(c, F, self.ap, p))
            inf = InformeConciliacion("x")
            self.con.conciliar([a1, a2], [declarar(a2, "BR999", 10)], inf)
            return [(type(h).__name__, h.codigo_vuelo) for h in inf.hallazgos]
        self.assertEqual(ejecutar(), ejecutar())

    # ---- Escenario completo (el que usará main) ----
    def test_escenario_completo_con_polimorfismo(self):
        self.vuelo(self.al1, "AL101", 100)          # coincide
        self.vuelo(self.al1, "AL102", 120)          # sin declaración
        self.vuelo(self.al2, "BR201", 95)           # declarado 90 -> faltante
        self.vuelo(self.al2, "BR202", 70)           # declarado 75 -> exceso
        decl = [declarar(self.al1, "AL101", 100), declarar(self.al2, "BR201", 90),
                declarar(self.al2, "BR202", 75), declarar(self.al2, "BR299", 40)]   # BR299 sin vuelo
        self.assertEqual(self.conciliar([self.al1, self.al2], decl), 4)
        valores = []
        for h in self.inf.hallazgos_priorizados():          # único ciclo, sin condicionales por tipo
            valores.append((h.codigo_vuelo, h.calcular_valor_en_riesgo(), h.impacto()))
        self.assertEqual(valores, [
            ("AL102", 2400000.0, IMPACTO_FALTANTE),
            ("BR299", 800000.0, IMPACTO_EXCESO),
            ("BR201", 100000.0, IMPACTO_FALTANTE),
            ("BR202", 100000.0, IMPACTO_EXCESO)])
        self.assertEqual(self.inf.total_por_impacto(),
                         {IMPACTO_FALTANTE: 2500000.0, IMPACTO_EXCESO: 900000.0})

    # ---- Errores y atomicidad ----
    def test_informe_cerrado_se_detecta_antes_de_conciliar(self):
        self.vuelo(self.al1, "AL101", 100)
        self.inf.cerrar()
        with self.assertRaises(InformeCerradoError):
            self.conciliar([self.al1], [])
        self.assertEqual(self.inf.cantidad_hallazgos, 0)

    def test_informe_cerrado_se_rechaza_aunque_no_haya_diferencias(self):
        self.vuelo(self.al1, "AL101", 100)
        self.inf.cerrar()
        with self.assertRaises(InformeCerradoError):     # todo coincide: sin hallazgos que registrar
            self.conciliar([self.al1], [declarar(self.al1, "AL101", 100)])

    def test_informe_con_hallazgos_previos_se_rechaza(self):
        self.vuelo(self.al1, "AL101", 100)
        self.conciliar([self.al1], [])
        with self.assertRaises(DatosInconsistentesError):
            self.conciliar([self.al1], [])
        self.assertEqual(self.inf.cantidad_hallazgos, 1)       # no se duplicó

    def test_declaracion_duplicada_no_registra_nada(self):
        self.vuelo(self.al1, "AL101", 100)
        self.vuelo(self.al1, "AL102", 100)                     # esto generaría un hallazgo...
        with self.assertRaises(DatosInconsistentesError):
            self.conciliar([self.al1], [declarar(self.al1, "AL201", 5), declarar(self.al1, "AL201", 6)])
        self.assertEqual(self.inf.cantidad_hallazgos, 0)       # ...pero no se registró nada

    def test_aerolineas_repetidas(self):
        with self.assertRaises(DatosInconsistentesError):
            self.conciliar([self.al1, self.al1], [])
        self.assertEqual(self.inf.cantidad_hallazgos, 0)

    def test_mismo_vuelo_en_dos_aerolineas_es_ambiguo(self):
        self.vuelo(self.al1, "XX100", 10)
        self.vuelo(self.al2, "XX100", 10)
        with self.assertRaises(DatosInconsistentesError):
            self.conciliar([self.al1, self.al2], [])
        self.assertEqual(self.inf.cantidad_hallazgos, 0)

    def test_tipos_incorrectos(self):
        malos = [
            (lambda: Conciliador("APD")),
            (lambda: Conciliador(None)),
            (lambda: self.con.conciliar(5, [], self.inf)),
            (lambda: self.con.conciliar(["AL"], [], self.inf)),
            (lambda: self.con.conciliar([self.al1], 5, self.inf)),
            (lambda: self.con.conciliar([self.al1], ["x"], self.inf)),
            (lambda: self.con.conciliar([self.al1], [], "informe")),
            (lambda: self.con.conciliar([self.al1], [], None)),
            (lambda: self.con.conciliar([None], [], self.inf)),
        ]
        for accion in malos:
            with self.assertRaises(DatosInconsistentesError):
                accion()
        self.assertEqual(self.inf.cantidad_hallazgos, 0)

    def test_el_conciliador_no_guarda_estado_entre_ejecuciones(self):
        self.vuelo(self.al1, "AL101", 100)
        self.conciliar([self.al1], [])
        otro = InformeConciliacion("Otro")
        self.assertEqual(self.con.conciliar([self.al1], [], otro), 1)

    def test_solo_lectura(self):
        with self.assertRaises(AttributeError):
            self.con.aeropuerto = self.ap


if __name__ == "__main__":
    unittest.main()
