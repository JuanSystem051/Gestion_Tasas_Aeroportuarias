"""Pruebas de la fase 4: CargadorCSV y los datos ficticios.

Se ejecutan con:  python -m unittest discover -s tests -t . -v
"""

import pathlib
import shutil
import tempfile
import unittest

from aeropuerto import Aeropuerto
from cargador_csv import COLUMNAS_DECLARACIONES, COLUMNAS_VUELOS, CargadorCSV
from conciliador import Conciliador
from declaracion_sin_vuelo import DeclaracionSinVuelo
from diferencia_pasajeros import DiferenciaPasajeros
from excepciones import DatosInconsistentesError, DeclaracionExtemporaneaError
from hallazgo import IMPACTO_EXCESO, IMPACTO_FALTANTE
from informe_conciliacion import InformeConciliacion
from vuelo_sin_declaracion import VueloSinDeclaracion

DATOS = pathlib.Path(__file__).resolve().parent.parent / "datos"
VUELOS_OK = DATOS / "vuelos_operados.csv"
DECLARACIONES_OK = DATOS / "declaraciones.csv"
DECLARACIONES_MALA = DATOS / "declaraciones_con_error.csv"

CAB_V = ",".join(COLUMNAS_VUELOS)
CAB_D = ",".join(COLUMNAS_DECLARACIONES)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.ap = Aeropuerto("APD", "Aeropuerto Demo", 20000)
        self.cargador = CargadorCSV(self.ap)

    def escribir(self, nombre, texto, codificacion="utf-8", binario=None):
        ruta = self.tmp / nombre
        if binario is not None:
            ruta.write_bytes(binario)
        else:
            ruta.write_text(texto, encoding=codificacion, newline="")
        return ruta

    def vuelos(self, *filas, nombre="v.csv"):
        return self.escribir(nombre, CAB_V + "\n" + "\n".join(filas) + "\n")

    def declaraciones(self, *filas, nombre="d.csv"):
        return self.escribir(nombre, CAB_D + "\n" + "\n".join(filas) + "\n")

    def assertRechaza(self, accion, *fragmentos):
        with self.assertRaises(DatosInconsistentesError) as cm:
            accion()
        for fragmento in fragmentos:
            self.assertIn(fragmento, str(cm.exception))
        return str(cm.exception)

    def assertNadaCargado(self):
        self.assertEqual(self.cargador.aerolineas, ())
        self.assertEqual(self.cargador.declaraciones, ())


V1 = "ALF,Aerolínea Alfa,ALF101,2026-03-10,100"
D1 = "ALF,Aerolínea Alfa,ALF101,2026-03-10,2026-03-10,100"


class TestDatosFicticios(Base):
    """Los archivos que se entregan con el proyecto."""

    def test_carga_normal(self):
        self.assertEqual(self.cargador.cargar_vuelos(VUELOS_OK), 12)
        self.assertEqual(self.cargador.cargar_declaraciones(DECLARACIONES_OK), 11)
        self.assertEqual([a.codigo for a in self.cargador.aerolineas], ["ALF", "BRV", "CHR"])
        self.assertEqual([len(a.vuelos) for a in self.cargador.aerolineas], [4, 4, 4])
        self.assertEqual(len(self.cargador.declaraciones), 11)

    def test_se_superan_los_ocho_objetos_que_exige_la_actividad(self):
        self.cargador.cargar_vuelos(VUELOS_OK)
        self.cargador.cargar_declaraciones(DECLARACIONES_OK)
        total = 1 + len(self.cargador.aerolineas) + sum(len(a.vuelos) for a in self.cargador.aerolineas) \
            + len(self.cargador.declaraciones)
        self.assertGreaterEqual(total, 8)

    def test_conciliacion_con_los_datos_entregados(self):
        self.cargador.cargar_vuelos(VUELOS_OK)
        self.cargador.cargar_declaraciones(DECLARACIONES_OK)
        informe = InformeConciliacion("Datos ficticios")
        self.assertEqual(Conciliador(self.ap).conciliar(
            self.cargador.aerolineas, self.cargador.declaraciones, informe), 6)
        resultado = []
        for h in informe.hallazgos_priorizados():        # único ciclo, sin condicionales por tipo
            resultado.append((h.codigo_vuelo, type(h), h.calcular_valor_en_riesgo(), h.impacto()))
        self.assertEqual(resultado, [
            ("ALF102", VueloSinDeclaracion, 2400000.0, IMPACTO_FALTANTE),
            ("CHR303", VueloSinDeclaracion, 900000.0, IMPACTO_FALTANTE),
            ("BRV299", DeclaracionSinVuelo, 800000.0, IMPACTO_EXCESO),
            ("BRV201", DiferenciaPasajeros, 100000.0, IMPACTO_FALTANTE),
            ("BRV202", DiferenciaPasajeros, 100000.0, IMPACTO_EXCESO),
            ("CHR302", DiferenciaPasajeros, 40000.0, IMPACTO_FALTANTE)])
        self.assertEqual(informe.total_por_impacto(),
                         {IMPACTO_FALTANTE: 3440000.0, IMPACTO_EXCESO: 900000.0})

    def test_los_datos_cubren_los_tres_tipos_de_hallazgo(self):
        self.cargador.cargar_vuelos(VUELOS_OK)
        self.cargador.cargar_declaraciones(DECLARACIONES_OK)
        informe = InformeConciliacion("x")
        Conciliador(self.ap).conciliar(self.cargador.aerolineas, self.cargador.declaraciones, informe)
        self.assertEqual({type(h) for h in informe.hallazgos},
                         {VueloSinDeclaracion, DeclaracionSinVuelo, DiferenciaPasajeros})

    def test_los_datos_incluyen_exactamente_una_declaracion_tardia(self):
        self.cargador.cargar_vuelos(VUELOS_OK)
        self.cargador.cargar_declaraciones(DECLARACIONES_OK)
        tardias = []
        for d in self.cargador.declaraciones:
            try:
                d.verificar_plazo()
            except DeclaracionExtemporaneaError:
                tardias.append(d.codigo_vuelo)
        self.assertEqual(tardias, ["CHR304"])

    def test_el_orden_de_carga_no_cambia_el_resultado(self):
        otro = CargadorCSV(self.ap)
        otro.cargar_declaraciones(DECLARACIONES_OK)       # al revés: declaraciones primero
        otro.cargar_vuelos(VUELOS_OK)
        self.cargador.cargar_vuelos(VUELOS_OK)
        self.cargador.cargar_declaraciones(DECLARACIONES_OK)

        def resumen(cargador):
            inf = InformeConciliacion("x")
            Conciliador(self.ap).conciliar(cargador.aerolineas, cargador.declaraciones, inf)
            return [(h.codigo_vuelo, h.calcular_valor_en_riesgo()) for h in inf.hallazgos_priorizados()]
        self.assertEqual(resumen(otro), resumen(self.cargador))

    def test_el_archivo_con_error_se_rechaza_indicando_la_linea(self):
        self.assertRechaza(lambda: self.cargador.cargar_declaraciones(DECLARACIONES_MALA),
                           "declaraciones_con_error.csv", "línea 4", "pasajeros_declarados", "-90")
        self.assertNadaCargado()

    def test_el_sistema_sigue_funcionando_tras_el_rechazo(self):
        self.cargador.cargar_vuelos(VUELOS_OK)
        with self.assertRaises(DatosInconsistentesError):
            self.cargador.cargar_declaraciones(DECLARACIONES_MALA)
        self.assertEqual(len(self.cargador.aerolineas), 3)            # lo anterior sigue intacto
        self.assertEqual(self.cargador.cargar_declaraciones(DECLARACIONES_OK), 11)   # y se puede seguir


class TestRutaYArchivo(Base):
    def test_acepta_str_y_path(self):
        ruta = self.vuelos(V1)
        self.assertEqual(CargadorCSV(self.ap).cargar_vuelos(str(ruta)), 1)
        self.assertEqual(CargadorCSV(self.ap).cargar_vuelos(ruta), 1)

    def test_ruta_invalida(self):
        for ruta in (None, 5, "", "   ", b"datos.csv", ["a.csv"]):
            self.assertRechaza(lambda r=ruta: self.cargador.cargar_vuelos(r), "ruta")

    def test_archivo_inexistente(self):
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(self.tmp / "no_existe.csv"),
                           "No se encontró", "no_existe.csv")

    def test_ruta_que_es_una_carpeta(self):
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(self.tmp), "No se pudo leer")

    def test_archivo_vacio(self):
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(self.escribir("e.csv", "")), "vacío")

    def test_solo_encabezado_se_rechaza(self):
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(self.escribir("h.csv", CAB_V + "\n")),
                           "no contiene filas de datos")

    def test_solo_lineas_en_blanco_se_rechaza(self):
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(self.escribir("b.csv", CAB_V + "\n\n\n")),
                           "no contiene filas de datos")

    def test_codificacion_incorrecta(self):
        contenido = (CAB_V + "\nALF,Aerol\xedn,ALF101,2026-03-10,100\n").encode("latin-1")
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(self.escribir("l.csv", "", binario=contenido)),
                           "UTF-8")
        self.assertNadaCargado()

    def test_acepta_bom_de_excel(self):
        ruta = self.escribir("bom.csv", CAB_V + "\n" + V1 + "\n", codificacion="utf-8-sig")
        self.assertEqual(self.cargador.cargar_vuelos(ruta), 1)

    def test_acepta_finales_de_linea_de_windows_y_lineas_en_blanco(self):
        ruta = self.escribir("crlf.csv", CAB_V + "\r\n" + V1 + "\r\n\r\n" + V1.replace("101", "102") + "\r\n")
        self.assertEqual(self.cargador.cargar_vuelos(ruta), 2)

    def test_campo_entre_comillas_con_coma(self):
        ruta = self.vuelos('ALF,"Aerolínea Alfa, S.A.",ALF101,2026-03-10,100')
        self.cargador.cargar_vuelos(ruta)
        self.assertEqual(self.cargador.aerolineas[0].nombre, "Aerolínea Alfa, S.A.")

    def test_el_archivo_queda_cerrado(self):
        # -W error convierte un archivo sin cerrar en fallo; aquí se comprueba además que se puede borrar
        ruta = self.vuelos(V1)
        self.cargador.cargar_vuelos(ruta)
        ruta.unlink()
        self.assertFalse(ruta.exists())


class TestEncabezado(Base):
    def test_columna_faltante(self):
        ruta = self.escribir("c.csv", "aerolinea,nombre_aerolinea,codigo_vuelo,fecha\nALF,Alfa,A1,2026-03-10\n")
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(ruta), "columnas incorrectas")

    def test_columna_sobrante(self):
        ruta = self.escribir("c.csv", CAB_V + ",extra\n" + V1 + ",x\n")
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(ruta), "columnas incorrectas")

    def test_columna_repetida(self):
        ruta = self.escribir("c.csv", "aerolinea,aerolinea,codigo_vuelo,fecha,pasajeros_operados\nA,A,V,2026-03-10,5\n")
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(ruta), "columnas incorrectas")

    def test_archivo_equivocado(self):
        # cargar el CSV de declaraciones como si fuera de vuelos
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(DECLARACIONES_OK), "columnas incorrectas")
        self.assertRechaza(lambda: self.cargador.cargar_declaraciones(VUELOS_OK), "columnas incorrectas")
        self.assertNadaCargado()

    def test_el_orden_de_las_columnas_no_importa(self):
        ruta = self.escribir("o.csv", "pasajeros_operados,fecha,codigo_vuelo,nombre_aerolinea,aerolinea\n"
                                      "100,2026-03-10,ALF101,Aerolínea Alfa,ALF\n")
        self.assertEqual(self.cargador.cargar_vuelos(ruta), 1)
        self.assertEqual(self.cargador.aerolineas[0].vuelos[0].pasajeros_operados, 100)


class TestFilasInvalidas(Base):
    def malo_v(self, fila, *fragmentos):
        ruta = self.vuelos(V1.replace("101", "100"), fila)       # la fila mala queda en la línea 3
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(ruta), "línea 3", *fragmentos)
        self.assertNadaCargado()                                  # ni la fila buena quedó cargada

    def malo_d(self, fila, *fragmentos):
        ruta = self.declaraciones(D1.replace("101", "100"), fila)
        self.assertRechaza(lambda: self.cargador.cargar_declaraciones(ruta), "línea 3", *fragmentos)
        self.assertNadaCargado()

    def test_campos_de_mas_o_de_menos(self):
        self.malo_v("ALF,Aerolínea Alfa,ALF101,2026-03-10,100,sobra", "más campos")
        self.malo_v("ALF,Aerolínea Alfa,ALF101,2026-03-10", "menos campos")

    def test_pasajeros_invalidos(self):
        for valor in ("-5", "abc", "10.5", "", " ", "1_000", "+10", "1e3", "٣", "1234567890"):
            self.malo_v(f"ALF,Aerolínea Alfa,ALF101,2026-03-10,{valor}", "pasajeros_operados")

    def test_cero_pasajeros(self):
        self.malo_v("ALF,Aerolínea Alfa,ALF101,2026-03-10,0", "pasajeros_operados")

    def test_fechas_invalidas(self):
        for valor in ("10/03/2026", "2026-3-10", "20260310", "2026-02-30", "2026-13-01", "0000-01-01", "", "hoy"):
            self.malo_v(f"ALF,Aerolínea Alfa,ALF101,{valor},100", "fecha")

    def test_codigo_de_vuelo_invalido(self):
        for valor in ("", " ", "ALF 101", "ALF_101", "ALF*1"):
            self.malo_v(f"ALF,Aerolínea Alfa,{valor},2026-03-10,100", "codigo_vuelo")

    def test_codigo_de_vuelo_invalido_en_declaraciones(self):
        for valor in ("", "ALF 101", "ALF_101"):
            self.malo_d(f"ALF,Aerolínea Alfa,{valor},2026-03-10,2026-03-10,100", "codigo_vuelo")

    def test_aerolinea_invalida(self):
        self.malo_v(",Aerolínea Alfa,ALF101,2026-03-10,100", "aerolinea")
        self.malo_v("A L,Aerolínea Alfa,ALF101,2026-03-10,100", "aerolinea")
        self.malo_v("ALF,,ALF101,2026-03-10,100", "nombre_aerolinea")

    def test_vuelo_repetido_en_el_mismo_archivo(self):
        ruta = self.vuelos(V1, V1.replace("100", "55"))
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(ruta), "línea 3", "línea 2")
        self.assertNadaCargado()

    def test_mismo_codigo_en_otra_fecha_no_es_repetido(self):
        self.assertEqual(self.cargador.cargar_vuelos(self.vuelos(V1, V1.replace("03-10", "03-11"))), 2)

    def test_misma_aerolinea_con_dos_nombres_en_un_archivo(self):
        self.malo_v("ALF,Otro Nombre,ALF102,2026-03-10,100", "ALF", "Otro Nombre")

    def test_declaracion_presentada_antes_del_vuelo(self):
        self.malo_d("ALF,Aerolínea Alfa,ALF101,2026-03-10,2026-03-09,100", "fecha de presentación")

    def test_declaracion_repetida_en_el_mismo_archivo(self):
        ruta = self.declaraciones(D1, D1.replace(",100", ",99"))
        self.assertRechaza(lambda: self.cargador.cargar_declaraciones(ruta), "línea 3", "línea 2")
        self.assertNadaCargado()

    def test_fechas_de_declaracion_invalidas(self):
        self.malo_d("ALF,Aerolínea Alfa,ALF101,2026-03-10,31/03/2026,100", "fecha_presentacion")
        self.malo_d("ALF,Aerolínea Alfa,ALF101,xx,2026-03-10,100", "fecha_vuelo")

    def test_la_primera_fila_mala_se_reporta_primero(self):
        ruta = self.vuelos("ALF,Aerolínea Alfa,ALF101,2026-03-10,-1", "ALF,Aerolínea Alfa,ALF102,xx,5")
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(ruta), "línea 2")


class TestAtomicidadYEstado(Base):
    def test_rechazo_en_la_ultima_fila_no_deja_nada(self):
        ruta = self.vuelos(V1, V1.replace("101", "102"), "BRV,Aerolínea Bravo,BRV1,2026-03-10,xx")
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(ruta), "línea 4")
        self.assertNadaCargado()

    def test_rechazo_conserva_lo_cargado_antes(self):
        self.cargador.cargar_vuelos(self.vuelos(V1))
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(self.vuelos(
            "BRV,Aerolínea Bravo,BRV1,2026-03-10,5", "BRV,Aerolínea Bravo,BRV2,mal,5", nombre="v2.csv")))
        self.assertEqual([a.codigo for a in self.cargador.aerolineas], ["ALF"])   # BRV no quedó
        self.assertEqual(len(self.cargador.aerolineas[0].vuelos), 1)

    def test_cargar_dos_veces_el_mismo_archivo_de_vuelos_se_rechaza_sin_duplicar(self):
        ruta = self.vuelos(V1)
        self.cargador.cargar_vuelos(ruta)
        self.assertRechaza(lambda: self.cargador.cargar_vuelos(ruta), "ya había sido cargado", "línea 2")
        self.assertEqual(len(self.cargador.aerolineas[0].vuelos), 1)

    def test_cargar_dos_veces_el_mismo_archivo_de_declaraciones_se_rechaza_sin_duplicar(self):
        ruta = self.declaraciones(D1)
        self.cargador.cargar_declaraciones(ruta)
        self.assertRechaza(lambda: self.cargador.cargar_declaraciones(ruta), "carga anterior")
        self.assertEqual(len(self.cargador.declaraciones), 1)

    def test_nombre_de_aerolinea_distinto_al_de_otra_carga(self):
        self.cargador.cargar_vuelos(self.vuelos(V1))
        self.assertRechaza(lambda: self.cargador.cargar_declaraciones(
            self.declaraciones("ALF,Nombre Distinto,ALF101,2026-03-10,2026-03-10,100")),
            "Aerolínea Alfa", "Nombre Distinto")
        self.assertEqual(self.cargador.declaraciones, ())

    def test_aerolinea_solo_declarante_se_crea_sin_vuelos(self):
        self.cargador.cargar_declaraciones(self.declaraciones("ZZZ,Aerolínea Zeta,ZZZ1,2026-03-10,2026-03-10,10"))
        self.assertEqual(self.cargador.aerolineas[0].codigo, "ZZZ")
        self.assertEqual(self.cargador.aerolineas[0].vuelos, ())

    def test_la_declaracion_usa_el_mismo_objeto_aerolinea_que_los_vuelos(self):
        self.cargador.cargar_vuelos(self.vuelos(V1))
        self.cargador.cargar_declaraciones(self.declaraciones(D1))
        self.assertIs(self.cargador.declaraciones[0].aerolinea, self.cargador.aerolineas[0])

    def test_los_vuelos_usan_el_aeropuerto_del_cargador(self):
        self.cargador.cargar_vuelos(self.vuelos(V1))
        self.assertIs(self.cargador.aerolineas[0].vuelos[0].aeropuerto, self.ap)

    def test_codigos_se_normalizan_a_mayusculas(self):
        self.cargador.cargar_vuelos(self.vuelos("alf,Aerolínea Alfa,alf101,2026-03-10,100"))
        self.cargador.cargar_declaraciones(self.declaraciones("ALF,Aerolínea Alfa,ALF101,2026-03-10,2026-03-10,100"))
        informe = InformeConciliacion("x")
        self.assertEqual(Conciliador(self.ap).conciliar(
            self.cargador.aerolineas, self.cargador.declaraciones, informe), 0)

    def test_colecciones_devueltas_son_inmutables(self):
        self.cargador.cargar_vuelos(self.vuelos(V1))
        self.cargador.cargar_declaraciones(self.declaraciones(D1))
        self.assertIsInstance(self.cargador.aerolineas, tuple)
        self.assertIsInstance(self.cargador.declaraciones, tuple)

    def test_aeropuerto_invalido(self):
        for malo in ("APD", None, 5):
            self.assertRechaza(lambda m=malo: CargadorCSV(m), "aeropuerto")

    def test_solo_lectura(self):
        with self.assertRaises(AttributeError):
            self.cargador.aeropuerto = self.ap
        with self.assertRaises(AttributeError):
            self.cargador.aerolineas = ()


if __name__ == "__main__":
    unittest.main()
