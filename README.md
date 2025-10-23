
# PIF: Plataforma de Insights de Fans (Basquet)

Esta es una aplicación analítica en Streamlit diseñada para cargar, analizar y accionar sobre la base de fans demográficos provenientes de un archivo Excel (`BID.BaseDeDatos.xlsx`).

La plataforma transforma un Excel con múltiples hojas (una por club) en un dashboard de inteligencia de negocios interactivo y seguro, enfocado en la segmentación para marketing.

## Características Principales

* **Autenticación Segura:** Un portal de login que verifica las credenciales de los usuarios contra un archivo `users.csv` antes de dar acceso a los datos.
* **Dashboard Global:** Muestra los KPIs principales de toda la base (Total Fans, Edad Promedio), gráficos de composición (Fans por Club segmentado por Sexo, Distribución de Edades) y resalta nichos de oportunidad.
* **Radar de Oportunidades:** Una sección proactiva en el dashboard que detecta y resalta el nicho de "Fans Internacionales" (aquellos con Nacionalidad distinta a 'AR').
* **Análisis por Club:** Una vista dedicada a perfilar cada club individualmente. Incluye **métricas comparativas (delta)** que muestran el rendimiento demográfico del club (ej. edad, % femenino) contra el promedio general de la liga.
* **Módulo de Segmentación:** Herramienta avanzada para filtrar la base de fans combinando múltiples criterios (Club, Rango de Edad, Sexo, Nacionalidad) y exportar las listas de emails resultantes en formato `.csv`.
* **Buscador de Fans:** Una vista de "CRM" simple que permite la búsqueda de perfiles individuales por nombre, email o DNI.

## Estructura de Archivos

El proyecto está contenido en una única carpeta con la siguiente estructura:

/Proyecto-PIF/
├── app.py
├── BID.BaseDeDatos.xlsx
├── users.csv
├── cab-logo.png
└── requirements.txt

## Requisitos y Configuración

### 1. Archivos de Datos

Asegúrate de que los siguientes archivos estén en la misma carpeta que `app.py`:

* **`BID.BaseDeDatos.xlsx`** : El Excel fuente. La app está diseñada para leer todas las hojas (asumiendo que cada hoja es un club) y espera que los datos comiencen en la segunda fila (`header=1`). El script ya maneja la limpieza de la columna `Edad` (ignora valores > 100).
* **`users.csv`** : Un archivo CSV con las columnas `username` y `password`.
* **`cab-logo.png`** : El logo. Si el archivo no se encuentra, la app funcionará igualmente sin mostrarlo.

### 2. Librerías de Python

El proyecto requiere las siguientes librerías de Python:

* `streamlit`
* `pandas`
* `plotly` (usado vía `plotly.express`)
* `openpyxl` (necesario para que `pandas` lea archivos `.xlsx`)
* `Pillow` (importado como `PIL`, para manejar el logo)

Puedes instalarlas creando un archivo `requirements.txt` con el contenido de arriba y ejecutando:

`pip install -r requirements.txt`

O instalarlas manualmente:

`pip install streamlit pandas plotly openpyxl Pillow`

## Ejecución

Para iniciar la aplicación, navega a la carpeta del proyecto en tu terminal y ejecuta:

`streamlit run app.py`
