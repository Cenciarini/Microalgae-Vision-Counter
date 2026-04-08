import sys
import os
import numpy as np
import json
import pandas as pd
from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtCore import Qt
import cv2
import onnxruntime as ort
import pathlib
from datetime import datetime

temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

if not os.path.exists('databases'):
    os.makedirs('databases')

def get_base_path():
    """ Devuelve la ruta absoluta correcta, ya sea en desarrollo o como ejecutable congelado. """
    if getattr(sys, 'frozen', False):
        # Si es un ejecutable compilado, usa la ruta del .exe
        return os.path.dirname(sys.executable)
    else:
        # Si es el script de Python, usa la ruta del script
        return os.path.dirname(os.path.abspath(__file__))

# Uso de la función para definir tus directorios
BASE_DIR = get_base_path()
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DATABASES_DIR = os.path.join(BASE_DIR, 'databases')

# Cargar el modelo usando la ruta absoluta segura
modelo_onnx_path = os.path.join(MODELS_DIR, 'best.onnx')
session = ort.InferenceSession(modelo_onnx_path, providers=['CPUExecutionProvider'])
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

REQUIRED_COLUMNS = [
    "id", "fecha_hora_creacion", "fecha_hora", "recuento_celular", "concentracion_celular", "concentracion_celular_corregido", "umbral_confianza",
    "factor_dilucion", "dia_recuento", "hora_recuento",
    "medio_cultivo", "tipo_agitacion", "unidad_agitado", "ph_inicial", "ph_corregido", "ph_flag", "temperatura", "humedad",
    "luz_oscuridad", "lim_inf", "lim_sup", "info_extra"
]

class NuevaBaseDatosDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear nueva base de datos")

        self.layout = QFormLayout(self)

        self.nombre_db = QLineEdit()
        self.medio = QLineEdit()
        self.tipo_agitado = QComboBox()
        self.valor_agitado = QLineEdit()
        self.temperatura = QLineEdit()
        self.humedad = QLineEdit()
        self.ciclo = QLineEdit()
        self.ph = QCheckBox()
        self.extra = QLineEdit()

        self.tipo_agitado.addItem("Orbital")
        self.tipo_agitado.addItem("Aireación")
        self.tipo_agitado.addItem("Sin agitado")

        self.layout.addRow("Nombre de la base (sin .csv):", self.nombre_db)
        self.layout.addRow("Medio de cultivo:", self.medio)
        self.layout.addRow("Tipo de agitación:", self.tipo_agitado)
        self.layout.addRow("Unidad de agitado:", self.valor_agitado)
        self.layout.addRow("Temperatura (°C):", self.temperatura)
        self.layout.addRow("Humedad (%):", self.humedad)
        self.layout.addRow("Luz/Oscuridad [h]:", self.ciclo)
        self.layout.addRow("Corrección de pH:", self.ph)
        self.layout.addRow("Información extra:", self.extra)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

    def get_data(self):
        return {
            "nombre": self.nombre_db.text().strip(),
            "medio": self.medio.text(),
            "tipo_agitacion": self.tipo_agitado.currentText(),
            "unidad_agitado": self.valor_agitado.text(),
            "temperatura": self.temperatura.text(),
            "humedad": self.humedad.text(),
            "luz_oscuridad": self.ciclo.text(),
            "ph_flag": self.ph.isChecked(),
            "extra": self.extra.text()
        }

class MainWindow(QtWidgets.QMainWindow):

    def closeEvent(self, event):
        """ Intercepta el clic en la 'X' de la ventana """
        if hasattr(self, 'LiveThread') and self.LiveThread.isRunning():
            print("Cerrando flujo de video antes de salir...")
            try:
                self.LiveThread.ImageUpdate.disconnect()
            except Exception:
                pass
                
            self.LiveThread.stop()
            if not self.LiveThread.wait(2000):
                print("Advertencia: OpenCV bloqueó la red. Forzando la destrucción del hilo...")
                self.LiveThread.terminate() # Aniquilación del subproceso
                self.LiveThread.wait()
            
        # Aceptar el evento de cierre y destruir la ventana
        event.accept()

    def __init__(self):
        super(MainWindow, self).__init__()

        # Obtener la ruta absoluta del archivo .ui
        ui_path = os.path.join(os.path.dirname(__file__), 'mainwindow.ui')
        
        # Cargar el archivo .ui
        uic.loadUi(ui_path, self)
        pixmap = QPixmap("Images/Logo.png")
        self.pixmap2 = QPixmap("Images/NoSignal.png")

        # Cambiar el texto del boton de captura a 'Capturar y Analizar'
        self.pushButton.setText("Capturar y Analizar")

        # Asignar el QPixmap al QLabel
        self.FeedLabel.setPixmap(self.pixmap2)
        self.labelLogo.setPixmap(pixmap)

        self.setStyleSheet("""
        QMainWindow { 
            background-color: #D2D0A0; 
        }        
                                      
        QLabel {
            color: black;
        }
                           
        QPushButton {
            padding: 6px 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
            border-radius: 2px;
            border: 0.5px solid black;
            background-color: #537D5D;
            color: white;
        }

        QPushButton:hover {
            background: #9EBC8A;
            color: #DFDEDF;
        }
        """)

        self.cancelBtn.clicked.connect(self.CancelFeed)
        self.pushButtonConectar.clicked.connect(self.Start)
        self.pushButton.clicked.connect(self.captureFrame)
        self.btn_nueva_db.clicked.connect(self.crear_nueva_base_datos)
        self.comboBoxProyect.currentIndexChanged.connect(self.updateUI)

        self.actualizar_bases_datos()

    def updateUI(self):
        archivo = self.comboBoxProyect.currentText()
        if not archivo:
            QMessageBox.warning(self, "Error", "No hay base de datos seleccionada.")
            return

        nombre_base = archivo.replace(".csv", "")
        ruta_meta = os.path.join(DATABASES_DIR, nombre_base + "_meta.json")

        if not os.path.exists(ruta_meta):
            QMessageBox.critical(self, "Error", "No se encontraron los metadatos asociados.")
            return
        
        try:
            with open(ruta_meta, "r", encoding="utf-8") as f:
                metadatos = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo de metadatos:\n{e}")
            return
        
        pf_final = metadatos.get("ph_flag", "")

        if pf_final:
            self.lineEditPhF.show()
            self.labelPhF.show()
        else:
            self.lineEditPhF.hide()
            self.labelPhF.hide()

    def actualizar_bases_datos(self):
        self.comboBoxProyect.clear()
        if not os.path.exists(DATABASES_DIR):
            os.makedirs(DATABASES_DIR)

        archivos = [f for f in os.listdir(DATABASES_DIR) if f.endswith(".csv")]
        self.comboBoxProyect.addItems(archivos)

    def crear_nueva_base_datos(self):
        dialog = NuevaBaseDatosDialog(self)
        if dialog.exec():
            datos = dialog.get_data()
            nombre_archivo = datos["nombre"] + ".csv"
            ruta_csv = os.path.join(DATABASES_DIR, nombre_archivo)
            ruta_meta = os.path.join(DATABASES_DIR, datos["nombre"] + "_meta.json")

            if os.path.exists(ruta_csv):
                QMessageBox.warning(self, "Error", "Ese archivo ya existe.")
                return

            # Guardar CSV vacío
            df = pd.DataFrame(columns=REQUIRED_COLUMNS)
            df.to_csv(ruta_csv, index=False)

            # Guardar metadatos en JSON
            metadatos = {
                "fecha_hora_creacion": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "medio_cultivo": datos["medio"],
                "tipo_agitacion": datos["tipo_agitacion"],
                "unidad_agitado": datos["unidad_agitado"],
                "temperatura": datos["temperatura"],
                "humedad": datos["humedad"],
                "luz_oscuridad": datos["luz_oscuridad"],
                "ph_flag": datos["ph_flag"],
                "info_extra": datos["extra"]
            }

            with open(ruta_meta, "w", encoding="utf-8") as f:
                json.dump(metadatos, f, indent=4)

            QMessageBox.information(self, "Éxito", "Base de datos creada.")
            self.actualizar_bases_datos()

    def captureFrame(self):
        if hasattr(self, 'LiveThread') and self.LiveThread.current_frame is not None:
            # Obtener el frame actual sin escalar
            frame = self.LiveThread.current_frame

            self.pushButton.setEnabled(False)  # Deshabilitar el botón para evitar múltiples clics
            self.pushButton.setText("Analizando...")

            # Iniciar el Worker que analiza el frame actual
            self.DetectionThread = DetectionThread(frame)
            self.DetectionThread.result_signal.connect(self.On_detection_complete)
            self.DetectionThread.start()
    
    def On_detection_complete(self, count):
        msg = QMessageBox(self)
        msg.setWindowTitle("Detección finalizada")
        msg.setText(f"Se detectaron {count} microalgas en la imagen")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

        self.pushButton.setEnabled(True)  # Rehabilitar el botón
        self.pushButton.setText("Capturar y Analizar")

        archivo = self.comboBoxProyect.currentText()
        if not archivo:
            QMessageBox.warning(self, "Error", "No hay base de datos seleccionada.")
            return

        nombre_base = archivo.replace(".csv", "")
        ruta_csv = os.path.join(DATABASES_DIR, archivo)
        ruta_meta = os.path.join(DATABASES_DIR, nombre_base + "_meta.json")

        if not os.path.exists(ruta_meta):
            QMessageBox.critical(self, "Error", "No se encontraron los metadatos asociados.")
            return

        try:
            df = pd.read_csv(ruta_csv)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer la base de datos:\n{e}")
            return

        try:
            with open(ruta_meta, "r", encoding="utf-8") as f:
                metadatos = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo de metadatos:\n{e}")
            return

        # Determinar próximo ID
        if not df.empty and "id" in df.columns:
            ultimo_id = df["id"].max()
            nuevo_id = int(ultimo_id) + 1
        else:
            nuevo_id = 1

        recuento_celular = count  
        umbral_confianza = 0.45
        factor_dilucion = self.lineEdit_FD.text()
        concentracion_celular = (float(count) * float(factor_dilucion) * 40000.0) / (2.54469) # PI * D^2

        concentracion_celular_aux = concentracion_celular / 1000000.0

        if(concentracion_celular_aux <= 0):
            QMessageBox.warning(self, "Error", "La concentración celular es demasiado baja para aplicar la corrección logarítmica.")
            return
        else:
            x_log = np.log(concentracion_celular_aux)
            sesgo_log = 0.229 - 0.076 * x_log
            sd_log = (0.204 - 0.035 * x_log) * np.sqrt(np.pi / 2)

            x_corregido_log = x_log - sesgo_log

            lim_inf_log = x_corregido_log + 1.96 * sd_log
            lim_sup_log = x_corregido_log - 1.96 * sd_log

            #Transformar todo a escala lineal
            concentracion_celular_corregido = np.exp(x_corregido_log) * 1000000.0
            lim_sup = np.exp(lim_sup_log) * 1000000.0
            lim_inf = np.exp(lim_inf_log) * 1000000.0

        fecha_actual = datetime.now()

        if not df.empty:
            try:
                primera_fecha_str = metadatos.get("fecha_hora_creacion", "")
                primera_fecha = datetime.strptime(primera_fecha_str, "%Y-%m-%d %H:%M:%S")
                diferencia = fecha_actual - primera_fecha
                dias_transcurridos = diferencia.days
                horas_transcurridas = diferencia.total_seconds() // 3600  # como número entero
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo calcular la diferencia de tiempo:\n{e}")
                return
        else:
            dias_transcurridos = 0
            horas_transcurridas = 0

        nueva_fila = {
            "id": nuevo_id,
            "fecha_hora_creacion": metadatos.get("fecha_hora_creacion", ""),
            "fecha_hora": fecha_actual.strftime("%Y-%m-%d %H:%M:%S"),
            "recuento_celular": recuento_celular,
            "concentracion_celular": int(concentracion_celular),
            "concentracion_celular_corregido": int(concentracion_celular_corregido),
            "umbral_confianza": umbral_confianza,
            "factor_dilucion": factor_dilucion,
            "dia_recuento": int(dias_transcurridos),
            "hora_recuento": int(horas_transcurridas),
            "medio_cultivo": metadatos.get("medio_cultivo", ""),
            "tipo_agitacion": metadatos.get("tipo_agitacion", ""),
            "unidad_agitado": metadatos.get("unidad_agitado", ""),
            "ph_inicial": self.lineEditPhI.text(),
            "ph_corregido": self.lineEditPhF.text(),
            "ph_flag": metadatos.get("ph_flag", ""),
            "temperatura": metadatos.get("temperatura", ""),
            "humedad": metadatos.get("humedad", ""),
            "luz_oscuridad": metadatos.get("luz_oscuridad", ""),
            "lim_inf": int(lim_inf),
            "lim_sup": int(lim_sup),
            "info_extra": metadatos.get("info_extra", "")
        }

        df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
        df.to_csv(ruta_csv, index=False)

        QMessageBox.information(self, "Guardado", f"Fila {nuevo_id} agregada con éxito.")


    def Start(self):
        video_url = self.lineEdit.text()

        if not video_url:
            QMessageBox.warning(self, "Entrada Inválida", "Por favor, ingrese una URL válida antes de iniciar.")
            return

        self.pushButtonConectar.setEnabled(False) 
        self.pushButtonConectar.setText("Conectando...")
        self.LiveThread = LiveThread(self.FeedLabel, video_url)
        self.LiveThread.ImageUpdate.connect(self.ImageUpdateSlot)
        self.LiveThread.ErrorConexion.connect(self.Error_camara)
        self.LiveThread.start()

    def Error_camara(self, mensaje):
        """ Este slot (función) se ejecuta solo si el hilo reporta una falla """
        # Mostrar el cartel en pantalla
        QMessageBox.critical(self, "Error de Transmisión", mensaje)
        
        # Restaurar la interfaz a su estado original
        self.pushButtonConectar.setEnabled(True)
        self.pushButtonConectar.setText("Conectar")
        
        # Limpiar el hilo muerto
        self.LiveThread.quit()
        self.LiveThread.wait()

    def ImageUpdateSlot(self, Image):
        pixmap = QPixmap.fromImage(Image)
        # Establecer el pixmap en el QLabel con la alineación centrada
        self.FeedLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.FeedLabel.setPixmap(pixmap)
        
    def CancelFeed(self):
        if hasattr(self, 'LiveThread') and self.LiveThread.isRunning():
            try:
                self.LiveThread.ImageUpdate.disconnect()
            except Exception:
                pass
            
            self.LiveThread.stop()
            
        # 2. Restaurar la interfaz a su estado original
        self.pushButtonConectar.setEnabled(True)
        self.pushButtonConectar.setText("Conectar")
        
        # Opcional: Limpiar el QLabel donde se mostraba el video
        self.FeedLabel.clear()
        self.FeedLabel.setPixmap(self.pixmap2)

class LiveThread(QThread):
    ImageUpdate = pyqtSignal(QImage)
    ErrorConexion = pyqtSignal(str)

    def __init__(self, feed_label, video_url):
        super().__init__()
        self.FeedLabel = feed_label
        self.ThreadActive = False
        self.Capture = None
        self.video_url = video_url

    def run(self):
        self.ThreadAactive = True
        self.Capture = cv2.VideoCapture(self.video_url)

        if not self.Capture.isOpened():
            self.ErrorConexion.emit(f"No se pudo conectar a la transmisión IP:\n{self.video_url}\nVerifique la red o la dirección.")
            return

        while self.ThreadAactive:
            ret, frame = self.Capture.read()
            if not ret:
                # Si la conexión se cae a la mitad de la transmisión
                self.ErrorConexion.emit("Se perdió la conexión con la cámara IP abruptamente.")
                break

            self.current_frame = frame

            Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ConvertToQtFormat = QImage(Image.data, Image.shape[1], Image.shape[0], QImage.Format.Format_RGB888)
            
            # Calcular las nuevas dimensiones respetando la proporción
            label_width = max(self.FeedLabel.width() - 50, 1)  # Asegurar ancho mínimo de 1 px
            label_height = max(self.FeedLabel.height() - 50, 1)  # Asegurar alto mínimo de 1 px
            
            Pic = ConvertToQtFormat.scaled(label_width, label_height, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
            self.ImageUpdate.emit(Pic)

        self.Capture.release()

    def stop(self):
        """ Este método es llamado desde la interfaz principal """
        self.ThreadActive = False # Rompe el bucle while
        self.quit() # Detiene el ciclo de eventos internos del hilo

class DetectionThread(QThread):
    result_signal = pyqtSignal(int)

    def __init__(self, frame):
        super().__init__()
        self.frame = frame

    def run(self):

        # 1. PREPROCESAMIENTO
        img_bgr = self.frame.copy()
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        img_letterbox, ratio, (pad_w, pad_h) = letterbox(img_rgb)
        
        # Normalizar e intercambiar ejes a CHW
        img_normalized = img_letterbox.astype(np.float32) / 255.0
        img_transposed = np.transpose(img_normalized, (2, 0, 1))
        input_tensor = np.expand_dims(img_transposed, axis=0)

        # 2. INFERENCIA ONNX
        outputs = session.run([output_name], {input_name: input_tensor})
        predictions = outputs[0][0] # Eliminar dimensión de batch: queda shape [N, 6]

        # 3. POSTPROCESAMIENTO
        conf_threshold = 0.45
        iou_threshold = 0.5
        
        # A. Filtrar por confianza
        # Asumiendo que el índice 4 es la confianza del objeto
        conf_mask = predictions[:, 4] > conf_threshold
        filtered_preds = predictions[conf_mask]

        boxes = []
        confidences = []

        # B. Preparar datos para NMS
        for pred in filtered_preds:
            # Extraer variables
            x_c, y_c, w, h, conf = pred[0], pred[1], pred[2], pred[3], pred[4]
            
            # Convertir a formato [x_min, y_min, ancho, alto] para cv2.dnn.NMSBoxes
            x_min = int(x_c - (w / 2))
            y_min = int(y_c - (h / 2))
            
            boxes.append([x_min, y_min, int(w), int(h)])
            confidences.append(float(conf))

        # C. Aplicar NMS
        # indices devuelve las posiciones de las cajas que sobrevivieron al filtro
        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, iou_threshold)
        
        detecciones_finales = []
        
        if len(indices) > 0:
            for i in indices.flatten():
                box = boxes[i]
                x_min, y_min, w, h = box[0], box[1], box[2], box[3]
                x_max = x_min + w
                y_max = y_min + h
                
                # D. Re-escalar coordenadas a la imagen original
                # Restar el padding y dividir por el ratio de escala
                x_min_orig = int((x_min - pad_w) / ratio)
                y_min_orig = int((y_min - pad_h) / ratio)
                x_max_orig = int((x_max - pad_w) / ratio)
                y_max_orig = int((y_max - pad_h) / ratio)
                
                detecciones_finales.append([x_min_orig, y_min_orig, x_max_orig, y_max_orig, confidences[i]])

        total_detections = len(detecciones_finales)
        
        self.result_signal.emit(total_detections)

def letterbox(im, new_shape=(1024, 1024), color=(114, 114, 114)):
        # Forma actual [alto, ancho]
        shape = im.shape[:2] 
        
        # Calcular ratio de redimensionamiento
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

        # Nuevas dimensiones sin padding
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        
        # Calcular padding (ancho, alto)
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  
        
        # Dividir padding para centrar la imagen
        dw /= 2  
        dh /= 2

        # Redimensionar si es necesario
        if shape[::-1] != new_unpad:  
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
        
        # Aplicar bordes (padding)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  
        
        return im, r, (dw, dh)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
