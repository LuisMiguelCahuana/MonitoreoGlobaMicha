import streamlit as st
import gspread
import pandas as pd
import time

from google.oauth2.service_account import Credentials


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="MONITOR KM_PERDIDAS",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CONFIGURACIÓN GOOGLE SHEETS
# ============================================================

NOMBRE_HOJA = "KM_PERDIDAS"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# ============================================================
# CONEXIÓN GOOGLE SHEETS
# ============================================================

@st.cache_resource
def conectar_google():

    credenciales = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    cliente = gspread.authorize(credenciales)

    return cliente


@st.cache_resource
def obtener_hoja():

    cliente = conectar_google()

    spreadsheet = cliente.open_by_key(
        st.secrets["SPREADSHEET_ID"]
    )

    hoja = spreadsheet.worksheet(NOMBRE_HOJA)

    return hoja


# ============================================================
# LEER DATOS
# ============================================================

def cargar_datos():

    hoja = obtener_hoja()

    valores = hoja.get(
        "A:Q",
        value_render_option="FORMATTED_VALUE"
    )

    if not valores:
        return pd.DataFrame()

    encabezados = [
        "Fecha",
        "Placa",
        "Km Inicial",
        "Km Final",
        "Tot Recorrido",
        "Nom Personal",
        "Celular",
        "Cuadrilla",
        "Item",
        "Unidad Negocio",
        "Servicio Electrico",
        "CECO",
        "Foto KM Inicial",
        "Foto KM Final",
        "Ubicacion Inicial",
        "Ubicacion Final",
        "Observacion"
    ]

    filas = []

    for fila in valores[1:]:

        fila = list(fila)

        if len(fila) < 17:
            fila += [""] * (17 - len(fila))

        filas.append(fila[:17])

    df = pd.DataFrame(
        filas,
        columns=encabezados
    )

    # Eliminar filas completamente vacías
    df = df[
        df.astype(str)
        .apply(lambda x: x.str.strip().ne("").any(), axis=1)
    ].copy()

    return df


# ============================================================
# NORMALIZAR DATOS
# ============================================================

def normalizar_texto(valor):

    if pd.isna(valor):
        return ""

    return str(valor).strip()


def preparar_datos(df):

    if df.empty:
        return df

    columnas_texto = [
        "Fecha",
        "Placa",
        "Km Inicial",
        "Km Final",
        "Tot Recorrido",
        "Nom Personal",
        "Celular",
        "Cuadrilla",
        "Item",
        "Unidad Negocio",
        "Servicio Electrico",
        "CECO",
        "Foto KM Inicial",
        "Foto KM Final",
        "Ubicacion Inicial",
        "Ubicacion Final",
        "Observacion"
    ]

    for columna in columnas_texto:
        df[columna] = df[columna].apply(normalizar_texto)

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    df["Estado"] = df.apply(
        lambda fila:
        "🟢 COMPLETADO"
        if fila["Km Final"] != ""
        else "🟠 PENDIENTE KM FINAL",
        axis=1
    )

    return df


# ============================================================
# FUNCIÓN PARA MOSTRAR ENLACES
# ============================================================

def convertir_enlace(valor, texto):

    valor = normalizar_texto(valor)

    if valor == "":
        return "—"

    # Si Google Sheets devuelve una fórmula HYPERLINK,
    # intentamos extraer la URL.
    if "HYPERLINK" in valor.upper():

        import re

        encontrado = re.search(
            r'"(https?://[^"]+)"',
            valor
        )

        if encontrado:
            url = encontrado.group(1)

            return f'<a href="{url}" target="_blank">{texto}</a>'

    # Si ya es una URL directa
    if valor.startswith("http://") or valor.startswith("https://"):

        return f'<a href="{valor}" target="_blank">{texto}</a>'

    return valor


# ============================================================
# TÍTULO
# ============================================================

st.markdown(
    """
    <h1 style="text-align:center;">
        🚗 MONITOR DE KILOMETRAJES
    </h1>

    <p style="
        text-align:center;
        color:#666;
        font-size:16px;
        margin-top:-10px;
    ">
        Supervisión de registros de KM_PERDIDAS
    </p>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CARGAR DATOS
# ============================================================

try:

    df = cargar_datos()

except Exception as e:

    st.error(
        "❌ No se pudo conectar con Google Sheets."
    )

    st.stop()


if df.empty:

    st.info(
        "ℹ️ No existen registros en la hoja KM_PERDIDAS."
    )

    st.stop()


df = preparar_datos(df)


# ============================================================
# FECHA ACTUAL
# ============================================================

fecha_hoy = time.strftime("%d/%m/%Y")


# ============================================================
# FILTROS
# ============================================================

st.markdown("### 🔎 FILTROS")


col1, col2, col3, col4 = st.columns(4)


# ------------------------------------------------------------
# FECHA
# ------------------------------------------------------------

fechas = sorted(
    df["Fecha"]
    .dropna()
    .astype(str)
    .unique()
    .tolist(),
    reverse=True
)

with col1:

    fecha_filtro = st.selectbox(
        "📅 Fecha",
        ["TODAS"] + fechas
    )


# ------------------------------------------------------------
# PLACA
# ------------------------------------------------------------

placas = sorted(
    [
        x for x in
        df["Placa"].dropna().unique().tolist()
        if str(x).strip() != ""
    ]
)

with col2:

    placa_filtro = st.selectbox(
        "🚗 Placa",
        ["TODAS"] + placas
    )


# ------------------------------------------------------------
# PERSONAL
# ------------------------------------------------------------

personales = sorted(
    [
        x for x in
        df["Nom Personal"].dropna().unique().tolist()
        if str(x).strip() != ""
    ]
)

with col3:

    personal_filtro = st.selectbox(
        "👷 Personal",
        ["TODOS"] + personales
    )


# ------------------------------------------------------------
# ESTADO
# ------------------------------------------------------------

with col4:

    estado_filtro = st.selectbox(
        "📌 Estado",
        [
            "TODOS",
            "🟠 PENDIENTE KM FINAL",
            "🟢 COMPLETADO"
        ]
    )


# ============================================================
# SEGUNDA FILA DE FILTROS
# ============================================================

col5, col6, col7, col8 = st.columns(4)


# ------------------------------------------------------------
# UNIDAD
# ------------------------------------------------------------

unidades = sorted(
    [
        x for x in
        df["Unidad Negocio"].dropna().unique().tolist()
        if str(x).strip() != ""
    ]
)

with col5:

    unidad_filtro = st.selectbox(
        "🏢 Unidad de Negocio",
        ["TODAS"] + unidades
    )


# ------------------------------------------------------------
# SERVICIO
# ------------------------------------------------------------

servicios = sorted(
    [
        x for x in
        df["Servicio Electrico"].dropna().unique().tolist()
        if str(x).strip() != ""
    ]
)

with col6:

    servicio_filtro = st.selectbox(
        "⚡ Servicio Eléctrico",
        ["TODOS"] + servicios
    )


# ------------------------------------------------------------
# ITEM
# ------------------------------------------------------------

items = sorted(
    [
        x for x in
        df["Item"].dropna().unique().tolist()
        if str(x).strip() != ""
    ]
)

with col7:

    item_filtro = st.selectbox(
        "📋 Ítem",
        ["TODOS"] + items
    )


# ------------------------------------------------------------
# CECO
# ------------------------------------------------------------

cecos = sorted(
    [
        x for x in
        df["CECO"].dropna().unique().tolist()
        if str(x).strip() != ""
    ]
)

with col8:

    ceco_filtro = st.selectbox(
        "🏷️ CECO",
        ["TODOS"] + cecos
    )


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()


if fecha_filtro != "TODAS":

    df_filtrado = df_filtrado[
        df_filtrado["Fecha"] == fecha_filtro
    ]


if placa_filtro != "TODAS":

    df_filtrado = df_filtrado[
        df_filtrado["Placa"] == placa_filtro
    ]


if personal_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["Nom Personal"] == personal_filtro
    ]


if estado_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["Estado"] == estado_filtro
    ]


if unidad_filtro != "TODAS":

    df_filtrado = df_filtrado[
        df_filtrado["Unidad Negocio"] == unidad_filtro
    ]


if servicio_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["Servicio Electrico"] == servicio_filtro
    ]


if item_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["Item"] == item_filtro
    ]


if ceco_filtro != "TODOS":

    df_filtrado = df_filtrado[
        df_filtrado["CECO"] == ceco_filtro
    ]


# ============================================================
# INDICADORES
# ============================================================

total_registros = len(df_filtrado)

total_vehiculos = (
    df_filtrado["Placa"]
    .replace("", pd.NA)
    .dropna()
    .nunique()
)

total_personal = (
    df_filtrado["Nom Personal"]
    .replace("", pd.NA)
    .dropna()
    .nunique()
)

total_pendientes = len(
    df_filtrado[
        df_filtrado["Km Final"] == ""
    ]
)

total_completados = len(
    df_filtrado[
        df_filtrado["Km Final"] != ""
    ]
)


st.markdown("### 📊 RESUMEN")


k1, k2, k3, k4, k5 = st.columns(5)


with k1:

    st.metric(
        "📋 Registros",
        total_registros
    )


with k2:

    st.metric(
        "🚗 Vehículos",
        total_vehiculos
    )


with k3:

    st.metric(
        "👷 Personal",
        total_personal
    )


with k4:

    st.metric(
        "🟠 Pendientes",
        total_pendientes
    )


with k5:

    st.metric(
        "🟢 Completados",
        total_completados
    )


# ============================================================
# TABLA PRINCIPAL
# ============================================================

st.markdown("### 📋 REGISTROS")


if df_filtrado.empty:

    st.warning(
        "No existen registros con los filtros seleccionados."
    )

else:

    df_mostrar = df_filtrado.copy()

    # --------------------------------------------------------
    # CONVERTIR FOTOS EN ENLACES
    # --------------------------------------------------------

    df_mostrar["📷 KM Inicial"] = df_mostrar[
        "Foto KM Inicial"
    ].apply(
        lambda x: convertir_enlace(
            x,
            "📷 Ver foto"
        )
    )

    df_mostrar["📷 KM Final"] = df_mostrar[
        "Foto KM Final"
    ].apply(
        lambda x: convertir_enlace(
            x,
            "📷 Ver foto"
        )
    )

    # --------------------------------------------------------
    # UBICACIONES
    # --------------------------------------------------------

    def enlace_ubicacion(valor):

        valor = normalizar_texto(valor)

        if valor == "":
            return "—"

        if valor.startswith("http://") or valor.startswith("https://"):

            return (
                f'<a href="{valor}" target="_blank">'
                '📍 Ver ubicación'
                '</a>'
            )

        return valor


    df_mostrar["📍 Ubicación Inicial"] = (
        df_mostrar["Ubicacion Inicial"]
        .apply(enlace_ubicacion)
    )


    df_mostrar["📍 Ubicación Final"] = (
        df_mostrar["Ubicacion Final"]
        .apply(enlace_ubicacion)
    )


    # --------------------------------------------------------
    # SELECCIONAR COLUMNAS
    # --------------------------------------------------------

    columnas_mostrar = [
        "Fecha",
        "Placa",
        "Nom Personal",
        "Celular",
        "Cuadrilla",
        "Item",
        "Unidad Negocio",
        "Servicio Electrico",
        "CECO",
        "Km Inicial",
        "Km Final",
        "Tot Recorrido",
        "Estado",
        "📷 KM Inicial",
        "📷 KM Final",
        "📍 Ubicación Inicial",
        "📍 Ubicación Final",
        "Observacion"
    ]

    tabla = df_mostrar[columnas_mostrar].copy()


    # --------------------------------------------------------
    # MOSTRAR TABLA
    # --------------------------------------------------------

    st.markdown(
        """
        <style>

        .tabla-supervisor {
            width: 100%;
            overflow-x: auto;
        }

        .tabla-supervisor table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        .tabla-supervisor th {
            background-color: #f0f2f6;
            padding: 8px;
            border: 1px solid #ddd;
            text-align: center;
            white-space: nowrap;
        }

        .tabla-supervisor td {
            padding: 8px;
            border: 1px solid #ddd;
            white-space: nowrap;
        }

        .tabla-supervisor a {
            text-decoration: none;
            font-weight: bold;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # HTML DE TABLA
    # ========================================================

    html = tabla.to_html(
        index=False,
        escape=False,
        classes="tabla-supervisor"
    )

    st.markdown(
        f"""
        <div class="tabla-supervisor">
            {html}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# ACTUALIZACIÓN AUTOMÁTICA
# ============================================================

st.markdown("---")

st.caption(
    "🔄 Esta aplicación consulta Google Sheets y muestra "
    "los registros actuales de KM_PERDIDAS."
)

st.caption(
    "Actualización automática cada 10 segundos."
)


time.sleep(10)

st.rerun()
