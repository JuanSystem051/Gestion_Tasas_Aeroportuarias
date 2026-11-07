# Gestión de Tasas Aeroportuarias Aeropuertos

> **Aviso:** este es un proyecto académico inspirado en la Aviación Civil (proyecto final de Programación I, Universidad de Manizales).
> Todos los datos —aerolíneas, aeropuerto, vuelos, tarifas, plazos y valores— son **ficticios**.
> El proyecto no representa ni reemplaza ningún sistema real y no tiene relación con ninguna entidad.

## Problema que resuelve

Muchas organizaciones cobran un servicio según lo que otros **declaran**. Si lo declarado no coincide con
lo que realmente ocurrió, hay pérdidas, cobros en exceso y reprocesos, y nadie sabe qué atender primero.

En el contexto de un aeropuerto: las aerolíneas **declaran** los pasajeros de cada vuelo, y el aeropuerto
conoce los vuelos que **realmente operaron**. El sistema:

1. carga ambos registros desde archivos CSV,
2. los compara y detecta cada diferencia,
3. la clasifica en uno de tres tipos,
4. estima el valor en riesgo, y
5. entrega un informe priorizado con la acción recomendada.

| Tipo de diferencia | Qué significa | Impacto |
|---|---|---|
| `VueloSinDeclaracion` | El vuelo operó, pero nadie lo declaró | Faltante de recaudo |
| `DeclaracionSinVuelo` | Se declaró un vuelo que no consta como operado | Posible cobro en exceso |
| `DiferenciaPasajeros` | El vuelo existe en ambos lados, pero los pasajeros no coinciden | Faltante o cobro en exceso, según el sentido |

## Requisitos

- Python 3.10 o superior (desarrollado y probado con Python 3.12).
- **Sin dependencias externas:** solo usa la biblioteca estándar.

## Cómo ejecutarlo

Desde la carpeta del proyecto:

```bash
python main.py
```

El programa **no es interactivo** (no pide datos por teclado): se ejecuta de principio a fin y muestra siempre
el mismo resultado. Tiene seis secciones:

1. Carga de datos desde los CSV.
2. La clase abstracta `Hallazgo` no se puede instanciar.
3. Conciliación y **polimorfismo**: un único ciclo recorre hallazgos de tres clases distintas.
4. Encapsulamiento y validación de datos.
5. Las **tres excepciones personalizadas**, capturadas con el sistema funcionando después de cada una.
6. Resumen final.

## Cómo ejecutar las pruebas

```bash
python -m unittest discover -s tests -t . -v
```

Son 169 pruebas automáticas. Para un resultado más estricto (las advertencias se convierten en errores):

```bash
python -X dev -W error -m unittest discover -s tests -t .
```

## Estructura del proyecto

```
.
├── main.py                       # Programa principal (casos normales y excepcionales)
├── hallazgo.py                   # Clase abstracta Hallazgo
├── vuelo_sin_declaracion.py      # Hija de Hallazgo
├── declaracion_sin_vuelo.py      # Hija de Hallazgo
├── diferencia_pasajeros.py       # Hija de Hallazgo
├── aeropuerto.py                 # Aeropuerto y su tarifa ficticia
├── vuelo.py                      # Vuelo realmente operado
├── aerolinea.py                  # Aerolínea (agrega sus vuelos)
├── declaracion.py                # Declaración presentada por una aerolínea
├── informe_conciliacion.py       # Informe (crea y contiene los hallazgos)
├── conciliador.py                # Compara declaraciones contra vuelos operados
├── cargador_csv.py               # Lee los CSV y construye los objetos
├── excepciones.py                # Excepciones personalizadas
├── validaciones.py               # Funciones de apoyo para validar datos
├── datos/                        # Archivos CSV ficticios
├── tests/                        # Pruebas automáticas
└── docs/                         # UML y documento de decisiones de diseño
```

## Clases y responsabilidades

| Clase | Responsabilidad |
|---|---|
| `Hallazgo` (abstracta) | Representa una diferencia y define cómo se valora, qué impacto tiene y qué acción se recomienda |
| `VueloSinDeclaracion`, `DeclaracionSinVuelo`, `DiferenciaPasajeros` | Los tres tipos de diferencia |
| `Aeropuerto` | Identifica el aeropuerto y guarda su tarifa ficticia por pasajero |
| `Vuelo` | Vuelo realmente operado |
| `Aerolinea` | Identifica a la aerolínea y agrupa sus vuelos |
| `Declaracion` | Lo que reportó la aerolínea; sabe si se presentó a tiempo |
| `InformeConciliacion` | Crea y contiene los hallazgos, los prioriza, los totaliza y puede cerrarse |
| `Conciliador` | Compara declaraciones contra vuelos operados |
| `CargadorCSV` | Lee los archivos de datos y construye los objetos |

## Cómo cumple los requerimientos de la actividad

| Requerimiento | Dónde está |
|---|---|
| Seis clases concretas o más | 10 clases concretas y 1 abstracta (tabla anterior) |
| Una clase abstracta | `Hallazgo` (`hallazgo.py`), con 3 métodos abstractos |
| Tres clases que heredan de una común | `VueloSinDeclaracion`, `DeclaracionSinVuelo`, `DiferenciaPasajeros` |
| Constructores y encapsulamiento | Atributos privados (`__x`), propiedades de solo lectura y validación en los constructores |
| Dos métodos sobrescritos por las hijas | `calcular_valor_en_riesgo()`, `impacto()`, `recomendar_accion()` y `describir()` (este con `super()`) |
| Colección heterogénea y polimorfismo | `main.py`, sección 3: un único ciclo `for` sobre `informe.hallazgos_priorizados()`, sin condicionales por tipo |
| Dos relaciones entre objetos | Asociaciones `Vuelo → Aeropuerto` y `Declaracion → Aerolinea`; agregación `Aerolinea ◇ Vuelo` |
| Una composición | `InformeConciliacion ◆ Hallazgo`: el informe crea sus propios hallazgos con los métodos `registrar_*` |
| Tres excepciones personalizadas | Ver tabla siguiente |
| Al menos ocho objetos | 1 aeropuerto, 3 aerolíneas, 12 vuelos, 11 declaraciones y 6 hallazgos, entre otros |
| Programa principal con casos normales y excepcionales | `main.py` |

### Excepciones personalizadas

| Excepción | Se lanza en | Situación |
|---|---|---|
| `DeclaracionExtemporaneaError` | `Declaracion.verificar_plazo()` | La declaración se presentó fuera del plazo (ficticio: 3 días) |
| `InformeCerradoError` | `InformeConciliacion.verificar_abierto()` | Se intenta modificar un informe ya cerrado |
| `DatosInconsistentesError` | Funciones de `validaciones.py` y `CargadorCSV` | Un dato es inválido, vacío o contradictorio |

Las tres heredan de `ErrorConciliacion`, se capturan en `main.py` por su nombre exacto y, tras cada una, el
programa continúa.

## Datos de ejemplo

Están en la carpeta `datos/`:

- `vuelos_operados.csv`: columnas `aerolinea, nombre_aerolinea, codigo_vuelo, fecha, pasajeros_operados`.
- `declaraciones.csv`: columnas `aerolinea, nombre_aerolinea, codigo_vuelo, fecha_vuelo, fecha_presentacion, pasajeros_declarados`.
- `declaraciones_con_error.csv`: el mismo formato, con una fila dañada a propósito (para demostrar `DatosInconsistentesError`).

Las fechas usan el formato `AAAA-MM-DD`. La carga es **estricta y atómica**: si una fila es inválida se rechaza el
archivo completo, indicando archivo y línea, y no se carga nada a medias.

## Documentación

- Diagrama UML de clases: [`docs/uml_clases.png`](docs/uml_clases.png).
- Documento de Decisiones de Diseño: [`Documento de Decisiones de Diseño - Actividad Colaborativa N°3_ Proyecto Final.pdf`](<docs/Documento de Decisiones de Diseño - Actividad Colaborativa N°3_ Proyecto Final.pdf>).

## Autores

Juan David Perdomo Rojas y Legna Liliana Ferreira Rosas  — Programación I, Universidad de Manizales (trabajo colaborativo). Noviembre de 2026.

## Uso de inteligencia artificial

Se utilizó una herramienta de inteligencia artificial como apoyo para verificar el correcto funcionamiento del proyecto, aplicar buenas prácticas en el desarrollo de software y comprender diferentes conceptos de POO.
