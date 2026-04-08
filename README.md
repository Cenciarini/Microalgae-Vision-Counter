# Diseño, desarrollo y validación de un software de visión artificial para cuantificación automatizada de microalgas en imágenes de microscopio

**Autor:** Ing. Gabriel Cenciarini

**Institución:** Universidad Nacional de Entre Ríos

**Fecha:** Abril 2026

**Proyecto:** Trabajo Final de Grado en Ingeniería Mecatrónica

---

## 🔬 Resumen del Proyecto

Este repositorio contiene el desarrollo, implementación y validación estadística de un sistema basado en Inteligencia Artificial para el conteo automático de microalgas en imágenes de microscopía. El objetivo es sustituir el conteo manual tradicional, eliminando la subjetividad del analista y reduciendo los tiempos de procesamiento en laboratorio mediante modelos de detección de objetos optimizados.

---

## 📁 Estructura del Repositorio

La arquitectura del proyecto separa la lógica de producción, los activos de investigación y la documentación oficial:

```text
├── data/
│   ├── README.md           # Incluye el link y descripción del dataset.
│   └── hyp.yaml            # Hiperparametros del modelo entrenado
├── docs/
│   ├── Tesis_Cenciarini.pdf
│   └── Manual_Usuario.pdf
├── evaluation/
│   ├── scripts/            # Scripts de validación (ICC, CCC, Bland Altman, etc.)
│   ├── results/            # Gráficos generados
│   └── requirements.txt    # REQ 1: Solo librerías estadísticas
├── src/
│   ├── models/             # El modelo .onnx
│   ├── main.py             # Punto de entrada de la aplicación
│   └── requirements.txt    # REQ 2: Solo librerías para que el programa funcione
├── .gitignore
├── LICENSE
└── README.md               # Este documento
```

---

## 🛡️ Integridad y Trazabilidad (Auditoría)

Para garantizar que los archivos utilizados en la defensa de la tesis y en las pruebas estadísticas no han sido alterados, se proporcionan los hashes SHA-256:

| Archivo | Ubicación | Hash SHA-256 |
| :--- | :--- | :--- |
| `best.onnx` | `sc/models/` | `58556DD2B756777F2FDADC969DCC33788F93BA3B1398A1522889499A12D09D40` |
| `dataset.zip` | [Kraggle](https://www.kaggle.com/datasets/cenciarinigabriel/microalgae-microscope-20x-fov18/) | `8FD622A04341958EBA1EFC3D677DFE79DF44AC3BFB5865D8188F174F49424E77` |

*Puedes verificar esto en Windows (PowerShell) con `Get-FileHash <archivo>`.*

---

## 🚀 Instalación y Uso

Este repositorio utiliza entornos de dependencias segmentados para evitar conflictos de librerías. Todos los Scripts están programados para funcionar con **Python 3.12**

### 1. Ejecución de la Aplicación (Producción)

Ideal para usuarios que deseen probar la herramienta de conteo:

```bash
cd src
pip install -r requirements.txt
python main.py
```

### 2. Auditoría Estadística (Investigación)

Para replicar los resultados presentados en la tesis (análisis de concordancia y error):

```bash
cd evaluation
pip install -r requirements.txt
# Ejecutar scripts en /scripts para generar gráficos de resultados
```

---

## 📦 Distribución (Versión Portable)

Para usuarios finales o evaluadores que requieran una prueba rápida sin configurar un entorno de Python, se encuentra disponible una versión **portable (.exe)** en la sección de [Releases](https://github.com/Cenciarini/Microalgae-Vision-Counter/releases/tag/v1.0.0) de este repositorio.

- **Incluye:** Pesos del modelo, librerías de inferencia y manual de usuario embebido.

- **Compatibilidad:** Windows 10/11 x64.

---

## 📊 Validación Científica

La solución fue sometida a rigurosas pruebas de concordancia frente al "Gold Standard" (conteo manual experto), los resultados demostraron una **intercambiabilidad total** entre el método manual y la solución creada, en **escala logaritmica**:

- **Coeficiente de Correlación Intraclase (ICC):** 0.9762.

- **Coeficiente de Correlación de Concordancia (CCC) de Lin:** 0.9757.

- **Análisis de Bland-Altman:** Se decubrió heteroscedasticidad, los LoA dependen de la magnitud medida.

Los resultados detallados y los gráficos correspondientes se encuentran en la carpeta evaluation/results/.

---

# ⚖️ Licencia

**Código Fuente:** [Apache License 2.0](https://github.com/Cenciarini/Microalgae-Vision-Counter/blob/main/LICENSE).

**Documentación y Tesis:** [Creative Commons BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) - Atribución, No Comercial, Sin Obra Derivada.

---

**Contacto:** [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/cenciarinigabriel/)[![Gmail](https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:cenciariniag@gmail.com)

**Ingeniería Mecatrónica - 2026**

---
