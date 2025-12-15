Sistema Inteligente de Conteo de Personas - Campus La Nubia (UNAL)
Este proyecto implementa un sistema de monitoreo de movilidad peatonal para el Campus La Nubia de la Universidad Nacional de Colombia - Sede Manizales. Utiliza Inteligencia Artificial (YOLOv8) y Reconocimiento Facial para contar ingresos y salidas de forma precisa, evitando duplicados.

🚀 Características Principales
Detección en Tiempo Real: Procesamiento de video de alta velocidad con YOLOv8.

Conteo por Perspectiva: Identifica entradas y salidas basándose en el cambio de área (tamaño) de las personas, siendo más robusto que las líneas de cruce tradicionales.

Filtro Anti-Duplicados (FaceID): Reconoce rostros y evita contar a la misma persona más de una vez en un rango de 5 minutos.

Cero Latencia: Implementación de multithreading para eliminar el lag de las cámaras IP (IP Webcam).

Dashboard Interactivo: Panel web para visualizar aforo, horas pico y descargar reportes en CSV.

Base de Datos Local: Registro persistente de eventos mediante SQLite.

🛠️ Tecnologías Utilizadas
Lenguaje: Python 3.12

IA/Visión: YOLOv8 (Ultralytics), OpenCV.

Biometría: Face_recognition (dlib).

Dashboard: Streamlit, Pandas, Plotly.

Base de Datos: SQLite3.

📋 Requisitos de Instalación
1. Dependencias del Sistema (Ubuntu/Linux)
Es necesario instalar herramientas de compilación para la librería de reconocimiento facial:

Bash

sudo apt update
sudo apt install python3-venv cmake libopenblas-dev liblapack-dev libjpeg-dev build-essential
2. Configuración del Entorno
Bash

# Clonar el repositorio
git clone https://github.com/tu-usuario/nombre-del-repo.git
cd nombre-del-repo

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar librerías
pip install --upgrade pip
pip install -r requirements.txt
💻 Ejecución
El sistema se divide en dos módulos que deben correr simultáneamente:

Motor de Conteo (Backend): Asegúrate de configurar tu fuente de video (IP o USB) en el archivo main.py.

Bash

python main.py
Dashboard de Visualización: Abre una nueva terminal con el entorno activado.

Bash

streamlit run dashboard.py
📈 Visualización y Resultados
El sistema genera un panel web donde se pueden analizar las métricas de movilidad:

KPIs: Aforo actual, entradas y salidas totales.

Gráficas: Flujo por hora y tendencias diarias.

Evidencia: Carpeta Evidencia_Final con capturas de cada ingreso detectado.

📁 Estructura del Proyecto
Plaintext

├── main.py              # Código principal (Procesamiento IA)
├── dashboard.py         # Interfaz web (Streamlit)
├── registro_personas.db # Base de datos SQLite
├── requirements.txt     # Dependencias del proyecto
├── sort.py              # Algoritmo de tracking (opcional)
└── Evidencia_Final/     # Capturas de imágenes de los conteos
✒️ Autor
Vanessa Restrepo Obando - Desarrollo y Experimentación - Universidad Nacional de Colombia.
