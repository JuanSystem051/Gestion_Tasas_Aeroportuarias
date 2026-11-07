"""Programa principal: Gestión de Tasas Aeroportuarias Aeropuertos.

Trabajo académico con datos ficticios. No representa ningún sistema real.

Es un programa NO interactivo (no pide datos por teclado): se ejecuta de
principio a fin y muestra siempre el mismo resultado. Se ejecuta con:

    python main.py

Secciones:
  1. Carga de datos desde archivos CSV.
  2. La clase abstracta Hallazgo no se puede instanciar.
  3. Conciliación y polimorfismo (un solo ciclo sobre hallazgos de tres tipos).
  4. Encapsulamiento y validación de datos.
  5. Las tres excepciones personalizadas, capturadas con el sistema funcionando.
  6. Resumen final.

Nota: el texto que se imprime usa solo letras, tildes y signos comunes (sin
símbolos gráficos), para que se vea bien en cualquier consola.
"""

import sys
from datetime import date
from pathlib import Path

from aeropuerto import Aeropuerto
from cargador_csv import CargadorCSV
from conciliador import Conciliador
from excepciones import (DatosInconsistentesError, DeclaracionExtemporaneaError,
                         InformeCerradoError)
from hallazgo import Hallazgo
from informe_conciliacion import InformeConciliacion
from vuelo import Vuelo

CARPETA_DATOS = Path(__file__).resolve().parent / "datos"
FECHA_DEMO = date(2026, 3, 13)


def titulo(numero, texto):
    print()
    print("=" * 72)
    print(f"{numero}. {texto}")
    print("=" * 72)


def dinero(valor):
    return f"${valor:,.2f}"


# ----------------------------------------------------------------------
# 1. Carga de datos
# ----------------------------------------------------------------------
def cargar_datos(aeropuerto):
    titulo(1, "CARGA DE DATOS DESDE ARCHIVOS CSV")
    cargador = CargadorCSV(aeropuerto)
    vuelos = cargador.cargar_vuelos(CARPETA_DATOS / "vuelos_operados.csv")
    declaraciones = cargador.cargar_declaraciones(CARPETA_DATOS / "declaraciones.csv")
    print(f"Aeropuerto: {aeropuerto} | tarifa ficticia: {dinero(aeropuerto.tarifa_por_pasajero)} por pasajero")
    print(f"Vuelos operados cargados: {vuelos}")
    print(f"Declaraciones cargadas:   {declaraciones}")
    print(f"Aerolíneas creadas:      {len(cargador.aerolineas)}")
    for aerolinea in cargador.aerolineas:
        print(f"  - {aerolinea}: {len(aerolinea.vuelos)} vuelos operados")
    return cargador


# ----------------------------------------------------------------------
# 2. Clase abstracta
# ----------------------------------------------------------------------
def demostrar_clase_abstracta(aeropuerto):
    titulo(2, "CLASE ABSTRACTA: HALLAZGO NO SE PUEDE INSTANCIAR")
    try:
        Hallazgo("ALF101", FECHA_DEMO, aeropuerto.tarifa_por_pasajero)
    except TypeError:
        print("Capturado TypeError: Hallazgo es una clase abstracta y no se puede instanciar.")
        print("Solo se pueden crear sus tres clases hijas.")


# ----------------------------------------------------------------------
# 3. Conciliación y polimorfismo
# ----------------------------------------------------------------------
def conciliar_y_listar(aeropuerto, cargador):
    titulo(3, "CONCILIACIÓN Y POLIMORFISMO")
    informe = InformeConciliacion("Conciliación Aeropuerto Demo - marzo 2026")
    registrados = Conciliador(aeropuerto).conciliar(
        cargador.aerolineas, cargador.declaraciones, informe)
    print(f"{informe}")
    print(f"Diferencias detectadas: {registrados}")
    print()
    print("Hallazgos de tres tipos distintos, en UNA sola lista, ordenados por valor en riesgo.")
    print("Un único ciclo los recorre y llama a los mismos metodos, sin preguntar el tipo:")
    print("-" * 72)
    for posicion, hallazgo in enumerate(informe.hallazgos_priorizados(), start=1):
        print(f"{posicion}. [{hallazgo.__class__.__name__}] {hallazgo.describir()}")
        print(f"   Valor en riesgo: {dinero(hallazgo.calcular_valor_en_riesgo())} | Impacto: {hallazgo.impacto()}")
        print(f"   Acción recomendada: {hallazgo.recomendar_accion()}")
    print("-" * 72)
    return informe


# ----------------------------------------------------------------------
# 4. Encapsulamiento y validación
# ----------------------------------------------------------------------
def demostrar_encapsulamiento(aeropuerto, cargador):
    titulo(4, "ENCAPSULAMIENTO Y VALIDACIÓN DE DATOS")
    aerolinea = cargador.aerolineas[0]
    vuelo = aerolinea.vuelos[0]
    print(f"Vuelo de ejemplo: {vuelo}")

    try:
        vuelo.pasajeros_operados = 9999
    except AttributeError:
        print("Capturado AttributeError: los pasajeros operados son de solo lectura.")
    print(f"El valor no cambió: {vuelo.pasajeros_operados} pasajeros.")

    try:
        aerolinea.vuelos.append(vuelo)
    except AttributeError:
        print("Capturado AttributeError: la lista de vuelos de la aerolínea no se puede alterar desde fuera.")
    print(f"La aerolínea sigue teniendo {len(aerolinea.vuelos)} vuelos.")

    try:
        Vuelo("ALF999", FECHA_DEMO, aeropuerto, -5)
    except DatosInconsistentesError as error:
        print(f"Capturado DatosInconsistentesError al crear un vuelo inválido: {error}")


# ----------------------------------------------------------------------
# 5. Excepciones personalizadas
# ----------------------------------------------------------------------
def demostrar_excepciones(aeropuerto, cargador, informe):
    titulo(5, "EXCEPCIONES PERSONALIZADAS (EL SISTEMA SIGUE FUNCIONANDO)")

    print("5.1 DeclaracionExtemporaneaError: se revisa el plazo de cada declaración.")
    tardias = 0
    for declaracion in cargador.declaraciones:
        try:
            declaracion.verificar_plazo()
        except DeclaracionExtemporaneaError as error:
            tardias += 1
            print(f"    Capturada: {error}")
    print(f"    Revisadas: {len(cargador.declaraciones)} declaraciones; fuera de plazo: {tardias}.")
    print("    El sistema continúa con las demás.")

    print()
    print("5.2 InformeCerradoError: se cierra el informe y se intenta modificar.")
    informe.cerrar()
    print(f"    {informe}")
    try:
        informe.registrar_vuelo_sin_declaracion(
            "ALF999", FECHA_DEMO, aeropuerto.tarifa_por_pasajero, 50)
    except InformeCerradoError as error:
        print(f"    Capturada: {error}")
    print(f"    El informe conserva sus {informe.cantidad_hallazgos} hallazgos y se puede consultar:")
    for impacto, total in informe.total_por_impacto().items():
        print(f"      {impacto}: {dinero(total)}")

    print()
    print("5.3 DatosInconsistentesError: se intenta cargar un archivo con una fila dañada.")
    cargador_prueba = CargadorCSV(aeropuerto)
    try:
        cargador_prueba.cargar_declaraciones(CARPETA_DATOS / "declaraciones_con_error.csv")
    except DatosInconsistentesError as error:
        print(f"    Capturada: {error}")
    print(f"    El archivo se rechazó completo: {len(cargador_prueba.declaraciones)} declaraciones cargadas.")
    cargadas = cargador_prueba.cargar_declaraciones(CARPETA_DATOS / "declaraciones.csv")
    print(f"    El sistema sigue funcionando: el archivo correcto sí se carga ({cargadas} declaraciones).")


# ----------------------------------------------------------------------
# 6. Resumen
# ----------------------------------------------------------------------
def mostrar_resumen(cargador, informe):
    titulo(6, "RESUMEN FINAL")
    vuelos = sum(len(a.vuelos) for a in cargador.aerolineas)
    print(f"Vuelos operados revisados: {vuelos}")
    print(f"Declaraciones revisadas:   {len(cargador.declaraciones)}")
    print(f"Hallazgos del informe:     {informe.cantidad_hallazgos}")
    for impacto, total in informe.total_por_impacto().items():
        print(f"  {impacto}: {dinero(total)}")
    print(f"Estado del informe: {'cerrado' if informe.esta_cerrado else 'abierto'}")
    print()
    print("Fin del programa. Todos los datos son ficticios.")


def configurar_consola():
    """Respeta la codificación de la consola y evita errores con caracteres no soportados.

    En una consola de Windows las tildes se ven bien; si la salida se redirige
    con otra codificación, los caracteres que no existan se reemplazan en lugar
    de detener el programa.
    """
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(errors="replace")


def main():
    configurar_consola()
    print("GESTIÓN DE TASAS AEROPORTUARIAS AEROPUERTOS")
    print("Trabajo académico con datos ficticios.")
    aeropuerto = Aeropuerto("APD", "Aeropuerto Demo", 20000)
    cargador = cargar_datos(aeropuerto)
    demostrar_clase_abstracta(aeropuerto)
    informe = conciliar_y_listar(aeropuerto, cargador)
    demostrar_encapsulamiento(aeropuerto, cargador)
    demostrar_excepciones(aeropuerto, cargador, informe)
    mostrar_resumen(cargador, informe)


if __name__ == "__main__":
    main()
