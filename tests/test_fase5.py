"""Pruebas de la fase 5: el programa principal (main.py).

Se ejecutan con:  python -m unittest discover -s tests -t . -v
"""

import ast
import contextlib
import importlib
import io
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MAIN = RAIZ / "main.py"


def ejecutar(cwd, codificacion="utf-8"):
    """Ejecuta main.py como lo haría el usuario, en modo estricto de Python."""
    entorno = dict(os.environ, PYTHONIOENCODING=codificacion)
    # stdin cerrado: si el programa pidiera datos por teclado, fallaría de inmediato.
    return subprocess.run([sys.executable, "-X", "dev", "-W", "error", str(MAIN)],
                          cwd=cwd, capture_output=True, env=entorno, timeout=30,
                          stdin=subprocess.DEVNULL)


class EjecucionBase(unittest.TestCase):
    """Ejecuta main.py UNA vez por clase de pruebas. No contiene pruebas propias."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.resultado = ejecutar(cls.tmp.name)           # desde OTRA carpeta, a propósito
        cls.salida = cls.resultado.stdout.decode("utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class TestEjecucion(EjecucionBase):
    def test_termina_bien_y_sin_errores(self):
        self.assertEqual(self.resultado.returncode, 0, self.resultado.stderr.decode("utf-8", "replace"))
        self.assertEqual(self.resultado.stderr, b"")
        self.assertNotIn("Traceback", self.salida)

    def test_funciona_desde_cualquier_carpeta(self):
        # setUpClass ya lo ejecutó desde una carpeta temporal distinta a la del proyecto
        self.assertNotEqual(pathlib.Path(self.tmp.name).resolve(), RAIZ)
        self.assertIn("Vuelos operados cargados: 12", self.salida)

    def test_es_deterministico(self):
        with tempfile.TemporaryDirectory() as otra:
            self.assertEqual(ejecutar(otra).stdout, self.resultado.stdout)

    def test_funciona_con_la_codificacion_de_una_consola_de_windows(self):
        with tempfile.TemporaryDirectory() as otra:
            r = ejecutar(otra, codificacion="cp1252")
        self.assertEqual(r.returncode, 0, r.stderr.decode("cp1252", "replace"))
        self.assertEqual(r.stdout.decode("cp1252"), self.salida)

    def test_secciones_en_orden(self):
        # Los títulos de sección son los números que aparecen justo debajo de una línea de "=".
        numeros = re.findall(r"={72}\r?\n(\d)\. ", self.salida)
        self.assertEqual(numeros, ["1", "2", "3", "4", "5", "6"])

    def test_todas_las_fechas_mostradas_son_las_ficticias(self):
        fechas = re.findall(r"\d{4}-\d{2}-\d{2}", self.salida)
        self.assertGreater(len(fechas), 0)
        for fecha in fechas:
            self.assertTrue(fecha.startswith("2026-03-"), f"fecha inesperada: {fecha}")

    def test_declara_que_los_datos_son_ficticios(self):
        self.assertIn("datos ficticios", self.salida)

    def test_solo_aparecen_nombres_ficticios(self):
        aerolineas = set(re.findall(r"Aerolínea (\w+)", self.salida))
        self.assertEqual(aerolineas, {"Alfa", "Bravo", "Charlie"})
        self.assertEqual(set(re.findall(r"Aeropuerto (\w+)", self.salida)), {"Demo"})


class TestContenido(EjecucionBase):
    """Verifica lo que muestra el programa."""

    def test_carga(self):
        self.assertIn("Vuelos operados cargados: 12", self.salida)
        self.assertIn("Declaraciones cargadas:   11", self.salida)
        self.assertIn("Aerolíneas creadas:      3", self.salida)

    def test_clase_abstracta(self):
        self.assertIn("Capturado TypeError", self.salida)

    def test_los_tres_tipos_de_hallazgo_en_el_mismo_listado(self):
        listado = self.salida.split("-" * 72)[1]
        for clase in ("VueloSinDeclaracion", "DeclaracionSinVuelo", "DiferenciaPasajeros"):
            self.assertIn(f"[{clase}]", listado)

    def test_orden_y_valores_de_los_hallazgos(self):
        listado = self.salida.split("-" * 72)[1]
        esperado = [("ALF102", "$2,400,000.00"), ("CHR303", "$900,000.00"), ("BRV299", "$800,000.00"),
                    ("BRV201", "$100,000.00"), ("BRV202", "$100,000.00"), ("CHR302", "$40,000.00")]
        posiciones = []
        for n, (codigo, valor) in enumerate(esperado, start=1):
            linea = [l for l in listado.splitlines() if l.startswith(f"{n}. ")][0]
            self.assertIn(codigo, linea)
            self.assertIn(f"Valor en riesgo: {valor}", listado.split(linea)[1].split("\n")[1])
            posiciones.append(listado.index(linea))
        self.assertEqual(posiciones, sorted(posiciones))

    def test_totales_por_impacto(self):
        self.assertIn("Faltante de recaudo: $3,440,000.00", self.salida)
        self.assertIn("Posible cobro en exceso: $900,000.00", self.salida)

    def test_encapsulamiento(self):
        self.assertEqual(self.salida.count("Capturado AttributeError"), 2)
        self.assertIn("El valor no cambió: 100 pasajeros.", self.salida)
        self.assertIn("La aerolínea sigue teniendo 4 vuelos.", self.salida)
        self.assertIn("Capturado DatosInconsistentesError al crear un vuelo inválido", self.salida)

    def test_excepcion_declaracion_extemporanea_capturada(self):
        self.assertIn("Capturada: La declaración del vuelo CHR304 de la aerolínea CHR se presentó "
                      "8 días después del vuelo; el plazo máximo es de 3 días.", self.salida)
        self.assertIn("fuera de plazo: 1.", self.salida)
        self.assertIn("El sistema continúa con las demás.", self.salida)

    def test_excepcion_informe_cerrado_capturada(self):
        self.assertIn("está cerrado y no admite cambios.", self.salida)
        self.assertIn("El informe conserva sus 6 hallazgos y se puede consultar:", self.salida)

    def test_excepcion_datos_inconsistentes_capturada_y_el_sistema_sigue(self):
        self.assertIn("declaraciones_con_error.csv, línea 4", self.salida)
        self.assertIn("El archivo se rechazó completo: 0 declaraciones cargadas.", self.salida)
        self.assertIn("el archivo correcto sí se carga (11 declaraciones).", self.salida)

    def test_las_tres_excepciones_aparecen_en_la_salida(self):
        for nombre in ("DeclaracionExtemporaneaError", "InformeCerradoError", "DatosInconsistentesError"):
            self.assertIn(nombre, self.salida)

    def test_resumen_final(self):
        resumen = self.salida.split("6. RESUMEN FINAL")[1]
        self.assertIn("Hallazgos del informe:     6", resumen)
        self.assertIn("Estado del informe: cerrado", resumen)
        self.assertTrue(self.salida.rstrip().endswith("Todos los datos son ficticios."))


class TestCodigoDeMain(unittest.TestCase):
    """Revisa el código fuente de main.py, no solo lo que imprime."""

    @classmethod
    def setUpClass(cls):
        cls.fuente = MAIN.read_text(encoding="utf-8")
        cls.arbol = ast.parse(cls.fuente)

    def ciclo_polimorfico(self):
        """El ciclo for que llama a calcular_valor_en_riesgo()."""
        encontrados = []
        for nodo in ast.walk(self.arbol):
            if isinstance(nodo, ast.For):
                llamadas = {n.func.attr for n in ast.walk(nodo)
                            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
                if "calcular_valor_en_riesgo" in llamadas:
                    encontrados.append(nodo)
        return encontrados

    def test_hay_un_unico_ciclo_polimorfico(self):
        self.assertEqual(len(self.ciclo_polimorfico()), 1)

    def test_el_ciclo_polimorfico_llama_a_los_cuatro_metodos(self):
        ciclo = self.ciclo_polimorfico()[0]
        llamadas = {n.func.attr for n in ast.walk(ciclo)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertTrue({"describir", "calcular_valor_en_riesgo", "impacto", "recomendar_accion"} <= llamadas)

    def test_el_ciclo_polimorfico_no_tiene_condicionales_ni_comprobacion_de_tipo(self):
        ciclo = self.ciclo_polimorfico()[0]
        prohibidos = (ast.If, ast.IfExp, ast.Try, ast.Match, ast.Compare, ast.BoolOp, ast.While, ast.Assert)
        for nodo in ast.walk(ciclo):
            self.assertNotIsInstance(nodo, prohibidos, f"El ciclo usa {type(nodo).__name__}")
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                self.assertNotIn(nodo.func.id, {"isinstance", "type", "issubclass", "hasattr", "getattr"})

    def test_el_ciclo_recorre_una_sola_coleccion_de_hallazgos(self):
        ciclo = self.ciclo_polimorfico()[0]
        llamadas = [n for n in ast.walk(ciclo.iter) if isinstance(n, ast.Call)]
        nombres = {n.func.attr for n in llamadas if isinstance(n.func, ast.Attribute)}
        self.assertIn("hallazgos_priorizados", nombres)

    def test_no_pregunta_el_tipo_en_ninguna_parte(self):
        for palabra in ("isinstance", "issubclass", "type("):
            self.assertNotIn(palabra, self.fuente)

    def test_no_es_interactivo(self):
        self.assertNotIn("input(", self.fuente)

    def test_no_depende_de_la_fecha_actual_ni_del_azar(self):
        for palabra in ("today(", "now(", "random", "time."):
            self.assertNotIn(palabra, self.fuente)

    def test_las_tres_excepciones_se_capturan_en_main(self):
        capturadas = {n.type.id for n in ast.walk(self.arbol)
                      if isinstance(n, ast.ExceptHandler) and isinstance(n.type, ast.Name)}
        self.assertTrue({"DeclaracionExtemporaneaError", "InformeCerradoError",
                         "DatosInconsistentesError", "TypeError", "AttributeError"} <= capturadas)

    def test_nunca_se_captura_todo_a_ciegas(self):
        for n in ast.walk(self.arbol):
            if isinstance(n, ast.ExceptHandler):
                self.assertIsNotNone(n.type, "except sin tipo")
                self.assertNotIn(getattr(n.type, "id", ""), {"Exception", "BaseException"})

    def test_ninguna_excepcion_se_traga_en_silencio(self):
        for n in ast.walk(self.arbol):
            if isinstance(n, ast.ExceptHandler):
                self.assertFalse(len(n.body) == 1 and isinstance(n.body[0], ast.Pass))


class TestImportacion(unittest.TestCase):
    def test_importar_no_ejecuta_nada(self):
        buffer = io.StringIO()
        sys.modules.pop("main", None)
        with contextlib.redirect_stdout(buffer), mock.patch("sys.stdin", io.StringIO("")):
            importlib.import_module("main")
        self.assertEqual(buffer.getvalue(), "")

    def test_main_se_puede_llamar_dos_veces_con_la_misma_salida(self):
        import main
        salidas = []
        for _ in range(2):
            buffer = io.StringIO()
            # stdin vacío: si main pidiera datos por teclado, fallaría de inmediato (EOFError)
            with contextlib.redirect_stdout(buffer), mock.patch("sys.stdin", io.StringIO("")):
                main.main()
            salidas.append(buffer.getvalue())
        self.assertEqual(salidas[0], salidas[1])
        self.assertIn("RESUMEN FINAL", salidas[0])


if __name__ == "__main__":
    unittest.main()
