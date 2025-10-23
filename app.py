# -----------------------------------------------------------------------------
# 1. IMPORTACIÓN DE LIBRERÍAS
# -----------------------------------------------------------------------------
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# (Librerías de WordCloud eliminadas)

# -----------------------------------------------------------------------------
# 2. CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="PIF | Insights Fans Basquet",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INYECCIÓN DE CSS PARA REDUCIR EL SIDEBAR ---
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        width: 250px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# --- FIN DE LA INYECCIÓN DE CSS ---


# --- Constantes de Estilo ---
PRIMARY_COLOR = "#0068C9"
COLOR_DISCRETE_MAP = {'M': '#0068C9', 'F': '#D62728', 'Other': '#FF7F0E'}

# -----------------------------------------------------------------------------
# 3. FUNCIONES DE CARGA Y PROCESAMIENTO DE DATOS
# -----------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_data(excel_path):
    """
    Carga todos los datos desde el archivo Excel.
    """
    try:
        xls = pd.ExcelFile(excel_path)
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo de datos en '{excel_path}'.")
        st.stop()
    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        st.stop()

    all_sheets = xls.sheet_names
    df_list = []

    for sheet_name in all_sheets:
        if sheet_name.upper() == "LUF":
            continue
        try:
            df_sheet = pd.read_excel(xls, sheet_name=sheet_name, header=1)
            df_sheet['Club'] = sheet_name.upper()
            df_list.append(df_sheet)
        except Exception as e:
            st.warning(f"No se pudo leer la hoja '{sheet_name}': {e}")

    if not df_list:
        st.error("No se pudo cargar ningún dato de las hojas del Excel.")
        st.stop()

    df_combined = pd.concat(df_list, ignore_index=True)

    df_combined['Edad'] = pd.to_numeric(df_combined['Edad'], errors='coerce')
    df_combined.loc[df_combined['Edad'] > 100, 'Edad'] = pd.NA
    df_combined.dropna(subset=['Nombre completo', 'Email'], inplace=True)
    df_combined['Club'] = df_combined['Club'].astype('category')
    df_combined['Sexo'] = df_combined['Sexo'].astype('category')
    df_combined['Nacionalidad'] = df_combined['Nacionalidad'].astype('category')

    return df_combined

@st.cache_data
def get_users(csv_path):
    """Carga los usuarios desde el archivo users.csv."""
    try:
        users_df = pd.read_csv(csv_path)
        return users_df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo 'users.csv' en la raíz.")
        return None
    except Exception as e:
        st.error(f"Error al leer 'users.csv': {e}")
        return None

def check_login(username, password, users_df):
    """Verifica las credenciales contra el DataFrame de usuarios."""
    if users_df is None:
        return False
    user_record = users_df[users_df['username'] == username]
    if not user_record.empty:
        if str(user_record.iloc[0]['password']) == str(password):
            return True
    return False


# -----------------------------------------------------------------------------
# 4. FUNCIONES DE RENDERIZADO DE PÁGINAS (VISTAS)
# -----------------------------------------------------------------------------

def render_dashboard_global(df):
    """Muestra la vista 1: Dashboard Global (Revisado y Pulido)"""

    _col_left, col_main, _col_right = st.columns([0.05, 0.9, 0.05])
    with col_main:
        st.title("🏠 Dashboard Global")
        st.markdown("Visión macro de todo el universo de fans registrados en la plataforma.")

        # KPIs Principales
        total_fans = len(df)
        edad_promedio = int(df['Edad'].mean())
        total_clubes = df['Club'].nunique()

        cols_kpi = st.columns(3)
        cols_kpi[0].metric(label="Total de Fans Registrados", value=f"{total_fans}")
        cols_kpi[1].metric(label="Edad Promedio", value=f"{edad_promedio} años")
        cols_kpi[2].metric(label="Total de Clubes", value=f"{total_clubes}")

        st.divider()

        # Gráficos Principales
        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            # Gráfico de Clubes (apilado por sexo)
            club_order = df['Club'].value_counts().index
            fig_clubes = px.bar(
                df,
                x='Club',
                color='Sexo',
                title="Fans por Club (Segmentado por Sexo)",
                labels={'x': 'Club', 'y': 'Cantidad de Fans'},
                color_discrete_map=COLOR_DISCRETE_MAP,
                category_orders={"Club": club_order}
            )
            st.plotly_chart(fig_clubes, use_container_width=True)

        with col_graf2:
            # Gráfico por Sexo (General)
            sex_counts = df['Sexo'].value_counts()
            fig_sexo = px.pie(
                values=sex_counts.values,
                names=sex_counts.index,
                title="Distribución por Sexo (General)",
                color=sex_counts.index,
                color_discrete_map=COLOR_DISCRETE_MAP
            )
            st.plotly_chart(fig_sexo, use_container_width=True)

        # Gráfico Distribución de Edades
        fig_edades = px.histogram(
            df.dropna(subset=['Edad']),
            x='Edad',
            nbins=20,
            title="Distribución de Edades (General)",
            color_discrete_sequence=[PRIMARY_COLOR]
        )
        fig_edades.update_layout(bargap=0.1, xaxis_title="Edad", yaxis_title="Cantidad de Fans")
        st.plotly_chart(fig_edades, use_container_width=True)

        st.divider()

        # ---  Radar Internacional  ---
        df_internacional = df[df['Nacionalidad'] != 'AR']
        if not df_internacional.empty:
            with st.container(border=True):
                st.subheader(f"💡 Oportunidad: Radar de Fans Internacionales ({len(df_internacional)} Fans)")
                st.markdown("Se detectaron fans de alto valor fuera de Argentina. Ideal para campañas de 'Bienvenida'.")

                if len(df_internacional) < 20:
                    st.dataframe(df_internacional[['Nombre completo', 'Club', 'Nacionalidad', 'Email']])
                else:
                    st.dataframe(df_internacional[['Club', 'Nacionalidad']].value_counts().reset_index(name='Cantidad'))
        # --- FIN  ---


def render_analisis_club(df):
    """Muestra la vista 2: Análisis por Club (con deltas)"""

    # Contenedor principal para compactar el diseño
    _col_left, col_main, _col_right = st.columns([0.05, 0.9, 0.05])
    with col_main:
        st.title("📊 Análisis por Club")
        st.markdown("Análisis comparativo de la demografía de los fans por cada club.")

        # Calcular métricas generales PARA COMPARAR
        edad_promedio_general = int(df['Edad'].mean())
        sexo_f_general_pct = (df['Sexo'].value_counts(normalize=True).get('F', 0) * 100)

        # Filtro de Club
        lista_clubes = sorted(df['Club'].unique().tolist())
        club_seleccionado = st.selectbox(
            "Selecciona un Club para analizar:",
            options=lista_clubes,
            index=0
        )

        df_filtrado = df[df['Club'] == club_seleccionado]
        st.divider()

        if df_filtrado.empty:
            st.warning(f"No hay datos para el club '{club_seleccionado}'.")
            st.stop()

        # KPIs del Club (con 'delta' de contexto)
        total_fans_club = len(df_filtrado)

        try:
            edad_promedio_club = int(df_filtrado['Edad'].mean())
            delta_edad = f"{edad_promedio_club - edad_promedio_general:.1f} vs Gral ({edad_promedio_general})"
        except ValueError:
            edad_promedio_club = 0
            delta_edad = "N/D"

        try:
            sexo_f_club_pct = (df_filtrado['Sexo'].value_counts(normalize=True).get('F', 0) * 100)
            delta_sexo = f"{sexo_f_club_pct - sexo_f_general_pct:.1f}% vs Gral ({sexo_f_general_pct:.1f}%)"
        except Exception:
            sexo_f_club_pct = 0
            delta_sexo = "N/D"

        cols_kpi_club = st.columns(3)
        cols_kpi_club[0].metric(label=f"Fans de {club_seleccionado}", value=f"{total_fans_club}")
        cols_kpi_club[1].metric(
            label="Edad Promedio (Club)",
            value=f"{edad_promedio_club} años",
            delta=delta_edad
        )
        cols_kpi_club[2].metric(
            label="% Público Femenino",
            value=f"{sexo_f_club_pct:.1f}%",
            delta=delta_sexo
        )

        # Gráficos del Club
        col_graf_club1, col_graf_club2 = st.columns(2)
        with col_graf_club1:
            fig_edades_club = px.histogram(
                df_filtrado.dropna(subset=['Edad']),
                x='Edad',
                nbins=15,
                title=f"Edades en {club_seleccionado}",
                color_discrete_sequence=[PRIMARY_COLOR]
            )
            st.plotly_chart(fig_edades_club, use_container_width=True)

        with col_graf_club2:
            sex_counts_club = df_filtrado['Sexo'].value_counts()
            fig_sexo_club = px.pie(
                values=sex_counts_club.values,
                names=sex_counts_club.index,
                title=f"Sexo en {club_seleccionado}",
                color=sex_counts_club.index,
                color_discrete_map=COLOR_DISCRETE_MAP
            )
            st.plotly_chart(fig_sexo_club, use_container_width=True)


def render_segmentacion_email(df):
    """Muestra la vista 3: Módulo de Segmentación"""

    # Contenedor principal para compactar el diseño
    _col_left, col_main, _col_right = st.columns([0.05, 0.9, 0.05])
    with col_main:
        st.title("📧 Módulo de Segmentación (Email Marketing)")
        st.markdown("Construye un segmento de audiencia, obtén la lista de correos y descárgala en CSV.")

        st.subheader("1. Definir Segmento (Cluster)")

        col1, col2 = st.columns(2)

        with col1:
            # Filtro 1: Clubes
            clubes_opciones = sorted(df['Club'].unique().tolist())
            clubes_seleccionados = st.multiselect(
                "Filtrar por Club/es:",
                options=clubes_opciones,
                placeholder="Selecciona uno o varios clubes (deja vacío para 'Todos')"
            )

            # Filtro 2: Sexo
            sexo_opciones = sorted(df['Sexo'].dropna().unique().tolist())
            sexo_seleccionados = st.multiselect(
                "Filtrar por Sexo:",
                options=sexo_opciones,
                placeholder="Selecciona uno o varios sexos (deja vacío para 'Todos')"
            )

        with col2:
            # Filtro 3: Edad
            edad_min_val = int(df['Edad'].min())
            edad_max_val = int(df['Edad'].max())

            rango_edad_seleccionado = st.slider(
                "Filtrar por Rango de Edad:",
                min_value=edad_min_val,
                max_value=edad_max_val,
                value=(edad_min_val, edad_max_val)
            )

            # Filtro 4: Nacionalidad
            nacionalidad_opciones = sorted(df['Nacionalidad'].dropna().unique().tolist())
            nacionalidad_seleccionados = st.multiselect(
                "Filtrar por Nacionalidad:",
                options=nacionalidad_opciones,
                placeholder="Selecciona nacionalidades (deja vacío para 'Todos')"
            )

        # --- Aplicar Filtros ---
        df_segmentado = df.copy()

        if clubes_seleccionados:
            df_segmentado = df_segmentado[df_segmentado['Club'].isin(clubes_seleccionados)]
        if sexo_seleccionados:
            df_segmentado = df_segmentado[df_segmentado['Sexo'].isin(sexo_seleccionados)]
        if nacionalidad_seleccionados:
            df_segmentado = df_segmentado[df_segmentado['Nacionalidad'].isin(nacionalidad_seleccionados)]

        df_segmentado = df_segmentado[
            (df_segmentado['Edad'] >= rango_edad_seleccionado[0]) &
            (df_segmentado['Edad'] <= rango_edad_seleccionado[1])
        ]

        st.divider()
        st.subheader("2. Audiencia Resultante")

        total_segmento = len(df_segmentado)
        st.metric(label="Total de Fans en el Segmento", value=f"{total_segmento} Fans")

        if total_segmento > 0:
            emails_list = df_segmentado['Email'].dropna().unique()
            st.text_area(
                "Lista de Emails (copiar y pegar):",
                value=", ".join(emails_list),
                height=150
            )

            @st.cache_data
            def convert_df_to_csv(df_in):
                cols_descarga = ['Nombre completo', 'Email', 'Club', 'Edad', 'Sexo', 'Nacionalidad']
                return df_in[cols_descarga].to_csv(index=False).encode('utf-8')

            csv = convert_df_to_csv(df_segmentado)

            st.download_button(
                label="📥 Descargar Segmento Completo (CSV)",
                data=csv,
                file_name=f"segmento_fans_{total_segmento}.csv",
                mime="text/csv",
            )

            st.dataframe(df_segmentado.head(20))
        else:
            st.warning("El segmento definido no arrojó resultados. Prueba con filtros más amplios.")

def render_buscador_fans(df):
    """Muestra la vista 4: Buscador de Fans"""

    # NUEVO: Contenedor principal para compactar el diseño
    _col_left, col_main, _col_right = st.columns([0.05, 0.9, 0.05])
    with col_main:
        st.title("👤 Buscador de Fans (Vista por Cliente)")
        st.markdown("Encuentra un fan específico por su nombre, email o documento.")

        search_query = st.text_input(
            "Buscar fan:",
            placeholder="Escribe un nombre, email o DNI...",
            label_visibility="collapsed"
        )

        st.divider()

        if search_query:
            query_lower = str(search_query).lower()

            df_result = df[
                df['Nombre completo'].astype(str).str.lower().str.contains(query_lower) |
                df['Email'].astype(str).str.lower().str.contains(query_lower) |
                df['Documento'].astype(str).str.lower().str.contains(query_query)
            ]

            total_encontrados = len(df_result)
            st.subheader(f"Resultados de la búsqueda: {total_encontrados} encontrados")

            if total_encontrados > 0:
                if total_encontrados > 50:
                    st.warning("Demasiados resultados. Mostrando los primeros 50. Afina tu búsqueda.")
                    st.dataframe(df_result.head(50))
                else:
                    for _, row in df_result.iterrows():
                        with st.container(border=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader(row['Nombre completo'])
                                st.caption(f"Alias: {row['Alias']}")
                            with col2:
                                st.markdown(f"**Club:** {row['Club']}")
                                st.markdown(f"**Email:** {row['Email']}")

                            st.divider()

                            cols_info = st.columns(4)
                            cols_info[0].metric("Edad", int(row['Edad']) if pd.notna(row['Edad']) else "N/A")
                            cols_info[1].metric("Sexo", row['Sexo'])
                            cols_info[2].metric("Nacionalidad", row['Nacionalidad'])
                            cols_info[3].metric("DNI", row['Documento'])
            else:
                st.info("No se encontraron fans que coincidan con tu búsqueda.")
        else:
            st.info("Ingresa un término de búsqueda para ver los resultados.")


# -----------------------------------------------------------------------------
# 5. LÓGICA PRINCIPAL DE LA APLICACIÓN (MAIN)
# -----------------------------------------------------------------------------

def main():

    # --- A. Carga de Logo y Datos de Usuario ---
    try:
        logo = Image.open("cab-logo.png")
    except FileNotFoundError:
        logo = None

    users_df = get_users('users.csv')
    if users_df is None:
        st.stop()

    # --- B. Manejo de Estado de Login ---
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # --- C. Pantalla de Login ---
    if not st.session_state.logged_in:

        col1, col2, col3 = st.columns([1,2,1]) # Centrar el formulario
        with col2:
            if logo:
                st.image(logo, width=200)
            st.title("Plataforma de Insights de Fans")
            st.caption("Por favor, ingrese sus credenciales")

            with st.form("login_form"):
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Ingresar")

                if submitted:
                    if check_login(username, password, users_df):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("Login exitoso!")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")

        st.stop()

    # --- D. Aplicación Principal (Si está logueado) ---

    df_fans = load_data('BID.BaseDeDatos.xlsx')

    # --- E. Configuración de la Barra Lateral (Sidebar) ---
    if logo:
        st.sidebar.image(logo, width=150)

    st.sidebar.title(f"Bienvenido,")
    st.sidebar.markdown(f"**{st.session_state.username}**")
    st.sidebar.divider()

    menu_options = {
        "Dashboard Global": "🏠",
        "Análisis por Club": "📊",
        "Segmentación Email": "📧",
        "Buscador de Fans": "👤"
    }

    selection_label = st.sidebar.radio(
        "Menú Principal",
        options=menu_options.keys(),
        format_func=lambda x: f"{menu_options[x]} {x}"
    )

    st.sidebar.divider()
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.cache_data.clear()
        st.rerun()

    # --- F. "Router" de Vistas ---

    if selection_label == "Dashboard Global":
        render_dashboard_global(df_fans)

    elif selection_label == "Análisis por Club":
        render_analisis_club(df_fans)

    elif selection_label == "Segmentación Email":
        render_segmentacion_email(df_fans)

    elif selection_label == "Buscador de Fans":
        render_buscador_fans(df_fans)

# -----------------------------------------------------------------------------
# 6. EJECUCIÓN DEL SCRIPT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
