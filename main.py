import cv2
import time
import os
import sqlite3
import threading
from datetime import datetime
from collections import defaultdict
from ultralytics import YOLO

# ================= CONFIGURACIÓN =================
VIDEO_SOURCE = "http://192.168.101.39:8080/video"

CONFIDENCE = 0.5 


# UMBRAL_ENTRADA: Alto (12000) para asegurar que realmente entró.
UMBRAL_ENTRADA = 12000 

# UMBRAL_SALIDA: Más bajo (6000). 
# Al bajar este número, el sistema detecta la salida MÁS RÁPIDO (más cerca).
# Si aún esta lejos, bajar esto a 4000 o 5000.
UMBRAL_SALIDA = 6000   

FOLDER_NAME = "Evidencia_Perspectiva"
# =================================================

class CamaraSinLag:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
        self.lock = threading.Lock()

    def start(self):
        t = threading.Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        while True:
            if self.stopped: return
            (grabbed, frame) = self.stream.read()
            with self.lock:
                self.grabbed = grabbed
                self.frame = frame

    def read(self):
        with self.lock: return self.grabbed, self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

def iniciar_db():
    conn = sqlite3.connect('registro_personas.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS conteos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, hora TEXT, track_id INTEGER, tipo TEXT)''')
    conn.commit()
    conn.close()

def guardar_en_db(track_id, tipo):
    try:
        conn = sqlite3.connect('registro_personas.db')
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute("INSERT INTO conteos (fecha, hora, track_id, tipo) VALUES (?, ?, ?, ?)",
                       (now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), track_id, tipo))
        conn.commit()
        conn.close()
        print(f"💾 REGISTRADO: {tipo} - ID {track_id}")
    except: pass

if not os.path.exists(FOLDER_NAME): os.makedirs(FOLDER_NAME)
iniciar_db()

print("[INFO] Cargando IA...")
model = YOLO('yolov8n.pt')

print("[INFO] Iniciando cámara...")
cap = CamaraSinLag(VIDEO_SOURCE).start()
time.sleep(1.0)

historial_areas = defaultdict(list)
ids_procesados = set() 
conteo_in = 0
conteo_out = 0

bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
last_motion_time = time.time()
is_active_mode = False

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        time.sleep(0.1); continue

    frame = cv2.resize(frame, (640, 480))
    display_frame = frame.copy()
    
    # Sensor Movimiento
    mask = bg_subtractor.apply(frame)
    if cv2.countNonZero(mask) > 3000:
        last_motion_time = time.time()
        if not is_active_mode:
            is_active_mode = True
            historial_areas.clear()

    if is_active_mode and (time.time() - last_motion_time > 4.0):
        is_active_mode = False

    if is_active_mode:
        results = model.track(frame, persist=True, classes=0, conf=CONFIDENCE, verbose=False, tracker="bytetrack.yaml")

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = map(int, box)
                
                # Calcular Área
                area_actual = (x2 - x1) * (y2 - y1)
                
                historial_areas[track_id].append(area_actual)
                if len(historial_areas[track_id]) > 40: 
                    historial_areas[track_id].pop(0)

                # --- LÓGICA DE PERSPECTIVA ASIMÉTRICA ---
                if track_id not in ids_procesados:
                    
                    if len(historial_areas[track_id]) > 15:
                        inicio_avg = sum(historial_areas[track_id][:5]) / 5
                        fin_avg = sum(historial_areas[track_id][-5:]) / 5
                        
                        diferencia = fin_avg - inicio_avg

                        # CASO A: CRECIÓ MUCHO (Entrada - Requiere cambio grande)
                        if diferencia > UMBRAL_ENTRADA:
                            conteo_in += 1
                            ids_procesados.add(track_id)
                            guardar_en_db(track_id, "ENTRADA")
                            cv2.imwrite(f"{FOLDER_NAME}/IN_ID{track_id}.jpg", frame)
                            print(f"✅ ENTRADA (Cambio: {int(diferencia)})")
                        
                        # CASO B: SE ACHICÓ UN POCO (Salida - Requiere cambio menor)
                        # Usamos -UMBRAL_SALIDA (negativo porque se reduce)
                        elif diferencia < -UMBRAL_SALIDA:
                            conteo_out += 1
                            ids_procesados.add(track_id) 
                            guardar_en_db(track_id, "SALIDA")
                            cv2.imwrite(f"{FOLDER_NAME}/OUT_ID{track_id}.jpg", frame)
                            print(f"👋 SALIDA RÁPIDA (Cambio: {int(diferencia)})")

                # Visualización
                color = (255, 255, 0)
                texto = f"A:{area_actual}"
                if track_id in ids_procesados:
                    diff_debug = historial_areas[track_id][-1] - historial_areas[track_id][0]
                    if diff_debug > 0:
                        color = (0, 255, 0); texto = "ENTRADA"
                    else:
                        color = (0, 0, 255); texto = "SALIDA"
                
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display_frame, f"{track_id} {texto}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.rectangle(display_frame, (0, 0), (640, 50), (0,0,0), -1)
    cv2.putText(display_frame, f"IN: {conteo_in}", (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(display_frame, f"OUT: {conteo_out}", (350, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    cv2.imshow("Conteo Perspectiva Asimetrica", display_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.stop()
cv2.destroyAllWindows()