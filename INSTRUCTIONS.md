# Investigación y diseño de un nuevo algoritmo de persistent homology

## Objetivo

Quiero investigar cómo construir un algoritmo de Topological Data Analysis (TDA) que calcule persistent homology con menos tiempo y memoria, preservando tanta información topológica como sea posible.

La meta no es simplemente reescribir Ripser en otro lenguaje ni optimizar kernels CUDA. Quiero investigar si podemos encontrar nuevas representaciones, reducciones o combinaciones de técnicas que disminuyan el trabajo que necesita realizar el algoritmo.

Como referencia metodológica, estudia este repositorio:

https://github.com/CrocSwap/integer-mult-bounds

La comunidad ha utilizado ese proyecto para explorar mejoras a una construcción matemática, probar variaciones, comparar cotas, documentar propuestas y verificar resultados. Quiero aprovechar ese enfoque de investigación asistida por LLM, adaptándolo a persistent homology.

**No asumas que la metodología matemática de integer multiplication puede trasladarse directamente a TDA.** Identifica qué partes del proceso de investigación sí podemos reutilizar y cuáles requieren otro enfoque.

La primera etapa consiste en investigar, comparar y elegir una base de trabajo. No implementes todavía un algoritmo nuevo sin justificar antes las decisiones.

## 1. Estudia primero la metodología de integer-mult-bounds

Inspecciona el README, el historial de investigación, los documentos de reproducibilidad, los scripts, los patches, los certificados y las pruebas.

Determina cómo organizan y automatizan estos aspectos:

* Propuestas y variaciones del algoritmo original.
* Búsqueda de parámetros y optimización de cotas.
* Comparación de resultados.
* Comprobación de restricciones y corrección.
* Diferencia entre una conjetura, un resultado empírico y una demostración.
* Registro de experimentos fallidos y exitosos.
* Reproducibilidad y conservación de resultados anteriores.

Después, propón una metodología equivalente para nuestra investigación. Cuando sea posible, quiero que el LLM explore hipótesis y candidatos de forma sistemática, pero que no acepte mejoras sin evidencia.

En TDA tendremos que distinguir al menos tres clases de resultados:

1. Mejoras de implementación, como SIMD, paralelismo o CUDA.
2. Mejoras estructurales, como reducir el número de simplices, columnas o dependencias.
3. Mejoras teóricas, como una cota asintótica mejor o una transformación que permita demostrar que se necesita menos trabajo.

No confundas una mejora de tiempo observado con una mejora de complejidad asintótica.

## 2. Investiga qué complejo simplicial conviene utilizar

Esta es una de las decisiones centrales del proyecto.

Quiero encontrar un buen equilibrio entre información topológica, costo computacional y escalabilidad. No asumas que existe un complejo ganador para todas las clases de datos.

Investiga y compara, como mínimo:

### Vietoris-Rips

Es nuestra referencia principal por su generalidad y por el ecosistema de algoritmos existentes. Analiza su crecimiento combinatorio, representación, reducción y limitaciones.

### Alpha complex

Me interesa especialmente por su eficiencia en datos euclidianos de baja dimensión. Investiga en qué condiciones conserva la información topológica de interés, cómo utiliza la triangulación de Delaunay y cómo cambia su costo con la dimensión ambiente.

### Edge-Collapsed Vietoris-Rips

Investiga las implementaciones existentes y las condiciones bajo las que se conserva exactamente la persistencia. Quiero saber cuánto se puede reducir el complejo antes de realizar la reducción algebraica.

### Sparse Rips

Investiga sus garantías de aproximación, complejidad y utilidad frente a Rips convencional.

### Witness complexes y variantes basadas en landmarks

Estudia cuánto podemos reducir el número de vértices mediante selección de landmarks, cuál es el costo de construcción y qué información se puede perder.

### Cubical complexes

Investiga cuándo son superiores para imágenes, volúmenes, grids y otros datos con estructura regular. No los fuerces como solución general para point clouds.

### Discrete Morse theory y distilled Vietoris-Rips

Busca técnicas que permitan eliminar trabajo o construir una filtración reducida sin calcular explícitamente todo el complejo original.

Incluye también otras representaciones relevantes que encuentres durante la investigación.

Para cada opción, documenta:

* Datos y métricas compatibles.
* Hipótesis y restricciones geométricas.
* Si la preservación de la persistencia es exacta o aproximada.
* Complejidad temporal y de memoria conocida.
* Sensibilidad a la dimensión y al número de puntos.
* Compatibilidad con paralelismo, GPU y distribución.
* Calidad de la información topológica obtenida.
* Implementaciones disponibles y su estado de mantenimiento.

No compares directamente los diagramas de complejos diferentes suponiendo que deben ser idénticos. Define qué equivalencia o garantía es válida en cada caso.

Al final, recomienda qué familias de complejos deberíamos conservar para la primera ronda de benchmarks y por qué.

## 3. Compara los frameworks existentes

Investiga al menos estos proyectos:

* Ripser: https://github.com/Ripser/ripser
* Ripser++: https://github.com/simonzhang00/ripser-plusplus
* giotto-ph: https://github.com/giotto-ai/giotto-ph
* GUDHI: https://github.com/GUDHI/gudhi-devel
* Oineus: https://github.com/anigmetov/oineus
* Ripserer: https://github.com/mtsch/Ripserer.jl

Añade otros frameworks relevantes si aportan algoritmos o técnicas que no estén cubiertos por estos proyectos.

No quiero una descripción superficial de cada librería. Analiza las diferencias algorítmicas y de implementación.

Por ejemplo:

* Qué emplean para reducir columnas y calcular pares de persistencia.
* Cómo aprovechan apparent pairs, emergent pairs y clearing.
* Si utilizan persistent homology o persistent cohomology y qué consecuencias tiene.
* Cómo representan los simplices y sus relaciones sin almacenar el complejo entero.
* Qué algoritmos de edge collapse, Morse o sparsification incluyen.
* Cómo utilizan CPU, SIMD, múltiples hilos y GPU.
* Qué partes se paralelizan y cuáles siguen siendo secuenciales.
* Qué limitaciones de memoria y comunicación existen.
* Qué garantías de exactitud tienen.
* Qué técnicas parecen combinables y cuáles tienen incompatibilidades.
* Estado de mantenimiento, licencia, dependencias y facilidad de compilación.

Identifica las ideas que aportan valor aunque el framework completo no sea adecuado como base.

### Decisión sobre Ripser++

Quiero mantener Ripser++ desde el principio como implementación de referencia GPU.

Prepara un fork propio si tienes permisos para crearlo en GitHub. En caso contrario, clónalo en el entorno de trabajo, conserva el repositorio upstream y deja claro que se trata de un clon local, no de un fork remoto.

Registra el commit exacto, licencia, dependencias, instrucciones de compilación y cualquier modificación local.

Comprueba si puede compilarse y ejecutarse en el entorno disponible. Si no hay GPU compatible, registra esa limitación sin inventar resultados.

No modifiques inicialmente el código upstream. Queremos mantener una referencia reproducible y poder experimentar con CUDA más adelante.

**No decidas todavía que Ripser++ debe ser el núcleo definitivo del algoritmo nuevo.** La elección debe depender de la comparación algorítmica, los benchmarks y la facilidad de incorporar reducciones nuevas.

Conserva los otros proyectos como referencias independientes. No hagas forks de todos indiscriminadamente ni mezcles código antes de revisar sus licencias y dependencias.

## 4. Diseña y ejecuta una primera ronda de benchmarks

Construye un benchmark pequeño y reproducible para conocer el comportamiento de las implementaciones antes de cambiar algoritmos.

Empieza con unos cuantos datasets sintéticos y al menos uno real que sea fácil de obtener y tenga una licencia apropiada.

Considera, por ejemplo:

* Círculo con ruido.
* Esfera.
* Toro.
* Mezclas de clusters gaussianos.
* Puntos uniformes aleatorios.
* Datos aleatorios de dimensión alta.
* Un subconjunto de MNIST u otro dataset real apropiado.

Usa tamaños iniciales manejables, por ejemplo 500, 1.000, 5.000 y 10.000 puntos. Ajusta los tamaños a las capacidades reales de cada implementación y amplíalos únicamente cuando las pruebas sean viables.

Incluye varias dimensiones ambiente y estudia H0, H1 y H2 cuando los algoritmos y los recursos lo permitan. Documenta los parámetros, la métrica, el umbral de filtración, el tratamiento de empates y cualquier límite de dimensión.

Compara, cuando corresponda:

* Ripser.
* Ripser++.
* giotto-ph.
* GUDHI.
* Oineus.
* Ripserer.

Añade Alpha, Edge-Collapsed Rips, Sparse Rips, Witness y Cubical a los experimentos donde sean aplicables. No fuerces todas las combinaciones.

Mide como mínimo:

* Tiempo total.
* Tiempo de cada etapa cuando pueda instrumentarse.
* Pico de memoria RAM.
* Memoria GPU y utilización cuando estén disponibles.
* Número de vértices, aristas y simplices generados o procesados, cuando pueda medirse.
* Reducción lograda por edge collapse o Morse.
* Número de columnas o reducciones efectuadas cuando pueda obtenerse.
* Condiciones de terminación, errores y límites alcanzados.

Repite las mediciones necesarias para distinguir resultados estables de variaciones normales.

### Fidelidad topológica

Para los algoritmos que deban calcular la misma filtración, compara los diagramas de persistencia y verifica su coincidencia dentro de las tolerancias numéricas justificadas.

Para métodos aproximados o complejos distintos, utiliza las garantías matemáticas correspondientes y métricas como bottleneck distance, Wasserstein distance o curvas de Betti, cuando sean adecuadas.

Mantén separadas estas categorías:

1. Exactamente equivalente.
2. Aproximación con garantía teórica.
3. Resultado empírico con similitud observada.
4. Resultado todavía no verificado.

No declares que un método es mejor solo porque es más rápido. Queremos conocer el equilibrio entre costo, memoria e información topológica.

Usa los resultados para detectar qué etapa representa el principal cuello de botella y qué reducción ofrece el mayor beneficio.

## 5. Investiga las posibilidades de paralelización y distribución

No des por hecho que dividir el point cloud en fragmentos y calcular cada uno de manera independiente produce la persistencia global correcta.

Investiga cómo distribuir, si resulta viable:

* Cálculo de distancias.
* Generación de simplices y cofaces.
* Detección de pares aparentes.
* Edge collapse y reducciones geométricas.
* Reducciones algebraicas.
* Gestión de memoria y almacenamiento.
* Fusión de resultados entre particiones.

Compara paralelismo en una máquina, GPU, procesamiento distribuido por particiones y métodos basados en landmarks o complejos reducidos.

Para cada estrategia, estudia las dependencias entre particiones, la comunicación necesaria, la memoria, el balance de carga y las garantías de corrección.

Distingue entre distribuir el cálculo de una filtración global y calcular filtraciones distintas sobre subconjuntos de los datos.

Mi preferencia inicial es investigar si podemos reducir el complejo de forma global o distribuida antes de repartir el trabajo de reducción algebraica. Sin embargo, evalúa alternativas y no lo trates como una conclusión anticipada.

No implementes un sistema distribuido todavía. Primero identifica las estrategias más prometedoras y sus restricciones matemáticas.

## 6. Encuentra y conserva los papers adecuados

Busca los artículos originales y las publicaciones relevantes sobre:

* Ripser y persistent cohomology.
* Ripser++ y su estrategia GPU.
* giotto-ph y paralelización.
* GUDHI y sus complejos.
* Alpha complexes.
* Edge collapse para Vietoris-Rips.
* Sparse Rips y sus garantías.
* Witness complexes.
* Discrete Morse theory.
* Distilled Vietoris-Rips.
* Reducción de matrices para persistent homology.
* Oineus y métodos paralelos.
* Persistent homology distribuida.
* OpenAI integer multiplication below n log n y la metodología de investigación de CrocSwap.

Busca también resultados recientes que puedan haber aparecido después de las publicaciones originales.

Prioriza papers originales, documentación oficial, arXiv y versiones de acceso abierto autorizadas.

Descarga los PDF más importantes que sean legalmente accesibles si el entorno lo permite. Evita incorporar versiones de editor que no estén autorizadas para redistribución.

Para cada paper registra:

* Título y autores.
* Año.
* DOI, arXiv u otra URL oficial.
* PDF o ubicación local si se descargó.
* Técnica principal.
* Qué deberíamos leer.
* Qué idea podría ser aprovechable para el proyecto.

No descargues decenas de documentos sin criterio. Empieza por los fundamentales y amplía la bibliografía según lo que revelen los benchmarks.

## 7. Historial de investigación y reproducibilidad

Crea un archivo raíz llamado `RESEARCH_LOG.md`.

Debe ser muy resumido. Su función es que el agente pueda retomar el trabajo en otra sesión sabiendo qué se investigó, qué se intentó, qué se concluyó y qué falta.

Cada entrada debe incluir:

* Fecha.
* Pregunta investigada.
* Hipótesis o propuesta.
* Experimento o análisis realizado.
* Resultado y evidencia.
* Decisión tomada.
* Siguiente paso.

Distingue explícitamente entre propuestas pendientes, experimentos realizados, resultados reproducidos y conclusiones verificadas.

No guardes razonamientos extensos ni conversaciones completas en este archivo.

Al comienzo de cada sesión, lee `RESEARCH_LOG.md` y los documentos relevantes antes de repetir trabajo. Al terminar cada sesión o experimento significativo, actualiza el historial.

Crea también, si hacen falta, estos documentos:

* `docs/RESEARCH_PLAN.md`: preguntas de investigación, etapas y criterios de decisión.
* `docs/ALGORITHM_COMPARISON.md`: comparación técnica de complejos y frameworks.
* `docs/PAPERS.md`: bibliografía comentada.
* `docs/BENCHMARK_PROTOCOL.md`: procedimiento y criterios de comparación.
* `benchmarks/`: scripts, configuraciones, resultados y metadatos reproducibles.
* Un manifiesto de repositorios externos con URL, licencia, commit utilizado y propósito.

No conviertas esto en una estructura documental innecesariamente grande. Cada archivo debe tener una responsabilidad concreta.

Sigue el ejemplo de CrocSwap en reproducibilidad, pruebas, trazabilidad y conservación de resultados. No necesitamos copiar literalmente su estructura de certificados ni adoptar herramientas formales que no aporten valor a este problema.

## 8. Cómo investigar un algoritmo nuevo

Después de revisar los proyectos y ejecutar los benchmarks, identifica los cuellos de botella y propón varias direcciones algorítmicas.

Para cada propuesta, explica:

* Qué problema concreto intenta resolver.
* Qué técnica existente utiliza como punto de partida.
* Qué trabajo espera eliminar.
* Qué propiedades topológicas debe preservar.
* Qué hipótesis necesita.
* Qué complejidad tendría antes y después, si puede justificarse.
* Qué riesgos o contraejemplos existen.
* Cómo verificar la corrección.
* Qué experimento mínimo permitiría descartar o apoyar la idea.

Inspírate en el proceso iterativo de integer-mult-bounds para explorar alternativas y parámetros de manera sistemática. Utiliza búsqueda automatizada cuando sea útil, pero no confundas una optimización numérica con una demostración.

Prioriza hipótesis que puedan conducir a una representación más pequeña o reducir el número de operaciones necesarias, en lugar de buscar únicamente constantes mejores.

Cuando sea posible, formula invariantes y condiciones verificables. Si una transformación pretende preservar exactamente la persistencia, busca una demostración o una justificación matemática precisa. Los tests y los benchmarks son necesarios, pero no sustituyen la demostración general.

Conserva también los intentos fallidos que ayuden a descartar una dirección, de forma breve y reproducible.

## 9. Entregables de esta primera etapa

Al terminar, quiero tener:

1. Un mapa comparativo de los complejos simpliciales y sus garantías.
2. Un análisis de las implementaciones existentes y de qué ideas aporta cada una.
3. Ripser++ preservado como referencia GPU, con un fork remoto si los permisos lo permiten.
4. Los papers fundamentales identificados y los PDF de acceso abierto más útiles descargados, cuando sea posible.
5. Una primera ronda de benchmarks ejecutada o, si hay limitaciones del entorno, un informe preciso de qué pudo y qué no pudo ejecutarse.
6. Una recomendación sobre qué complejo o combinación de técnicas merece ser nuestra base.
7. Una propuesta inicial de arquitectura para un algoritmo nuevo y una evaluación de las opciones de paralelización y distribución.
8. `RESEARCH_LOG.md` y la documentación necesaria para continuar sin reconstruir toda la investigación.

Termina con una recomendación concreta, no con una lista indefinida de posibilidades.

Explica qué deberíamos conservar como baseline, qué repositorio conviene modificar primero, qué técnicas vale la pena combinar y cuáles son los siguientes experimentos prioritarios.

No implementes todavía una nueva versión completa del algoritmo. El resultado esperado es una decisión de investigación respaldada por evidencia, código reproducible y una ruta clara para comenzar el desarrollo.

## Estrategia de desarrollo: CPU primero, GPU después

El algoritmo nuevo debe desarrollarse inicialmente para **CPU**. La prioridad es encontrar una mejor representación del complejo simplicial, reducir el trabajo necesario y validar matemáticamente la corrección del algoritmo antes de introducir optimizaciones específicas de hardware.

Sigue estas etapas:

1. **Algoritmo CPU:** desarrollar una implementación correcta, reproducible y eficiente en CPU. Utiliza paralelismo multinúcleo cuando sea conveniente, pero evita optimizaciones prematuras que dificulten experimentar con nuevas ideas algorítmicas.
2. **Validación y benchmarks:** comparar la implementación con Ripser, Ripser++, giotto-ph, GUDHI y los demás baselines pertinentes. Verificar la exactitud de los diagramas de persistencia, medir tiempo y memoria e identificar los cuellos de botella reales.
3. **Optimización de CPU:** estudiar SIMD, distribución del trabajo entre hilos, estructuras de datos y otras optimizaciones. Diferenciar las mejoras de implementación de las reducciones en el número de operaciones.
4. **Extensión a GPU:** una vez que el algoritmo CPU esté validado, identificar qué etapas pueden ejecutarse eficientemente en GPU e implementar kernels CUDA para ellas. Evaluar las dependencias entre operaciones, el costo de transferir datos entre CPU y GPU, la ocupación de memoria y la sincronización.
5. **Validación cruzada:** comparar la versión GPU con la versión CPU usando los mismos datasets y parámetros. Ambas deben respetar las mismas garantías de corrección y equivalencia topológica.

La arquitectura debe permitir reutilizar los componentes independientes del hardware y mantener separadas, cuando sea conveniente, las operaciones del algoritmo y sus implementaciones específicas para CPU y GPU.

**No diseñes el algoritmo alrededor de CUDA desde el principio ni asumas que todas las etapas deben ejecutarse en GPU.** La GPU debe ser una extensión posterior del algoritmo validado, no un requisito que limite la búsqueda de mejores ideas matemáticas.

Conserva Ripser++ como referencia para comparar rendimiento GPU y estudiar sus técnicas de paralelización. Su presencia no implica que debamos usar su código como núcleo del algoritmo nuevo.

En cada benchmark, diferencia las ganancias obtenidas por una reducción del trabajo algorítmico de las obtenidas por optimizaciones de hardware. Queremos saber si descubrimos un algoritmo mejor, además de si conseguimos ejecutarlo más rápido.
