# Dataset: Microalgae Population Microscopy for Automated Counting

## 1. Overview

Este dataset fue desarrollado como parte de la tesis de grado en Ingeniería Mecatrónica: "Diseño, desarrollo y validación de un software de visión artificial para cuantificación automatizada de microalgas en imágenes de microscopio". Contiene imágenes de microscopía de alta resolución diseñadas para el entrenamiento y validación de modelos de inteligencia artificial (CNNs) orientados al conteo automatizado de poblaciones de microalgas.

## 2. Data Acquisition & Specifications

- **Instrumentación:** Microscopio óptico tipo lupa y cámaras celulares de 18 y 50 MP.

- **Ocular:** Ocular con FOV 18.

- **Magnificación:** 20x.

- **Resolución Original:** 1280x960 y 1440x1080 píxeles en formato .png.

- **Iluminación:** Campo claro de manera constante.

- **Enfoque:** Dos niveles de enfoque manejados con tornillo micrométrico el microscopio.

- **Preparación de muestra:** Diversos factores de dilución para asegurar una amplia representatividad de las microalgas.

## 3. Ground Truth & Annotation

- **Metodología de etiquetado:** Las imágenes fueron etiquetadas manualmente por mi mismo utilizando la herramienta LabelStudio con la guía de investigadores especializados en microalgas.

- **Clases:** Existe una sola clase denominada 'microalga'.

- **Formato de etiquetas:** YOLOv5 p/ PyTorch.

## 4. Dataset Structure

/
├── images/
│   ├── train/          # 70% de los datos
│   ├── val/            # 20% de los datos
│   └── test/           # 10% de los datos
└── labels/
    ├── train/          # Archivos de anotación correspondientes
    ├── val/
    └── test/

## 5. Statistical Representative & Bias

Las imágenes fueron capturadas utilizando dos celulares diferentes y dos niveles de enfoque distintos. Aún así, este es el dataset original. Se aplicaron técnicas de aumento de datos propias de la red neuronal seleccionada para el entrenamiento del modelo, con el objetivo de mejorar la robustez del mismo. Para obtener más información sobre las técnicas de aumento de datos empleadas, dirigirse al archivo 'hyp.yaml' que se encuentra en el repositorio de GitHub del proyecto.

## 6. Download

La descarga del dataset completo se puede realizar a través de [Kraggle](https://www.kaggle.com/datasets/cenciarinigabriel/microalgae-microscope-20x-fov18/).

## 7. License & Citation

- **Licencia:** [CC BY-NC-ND 4.0]

- **Cita sugerida:** Cenciarini Angel Gabriel. (2026). Microalgae_Microscope_20x_FOV18 [Data set]. Kaggle. https://doi.org/10.34740/KAGGLE/DSV/15568191