import streamlit as st
import pandas as pd
import os
import cloudinary
import cloudinary.uploader
import zipfile
import re

# ==========================================
# CONFIGURACIÓN DE CLOUDINARY (Tus datos oficiales)
# ==========================================
cloudinary.config(
  cloud_name = "Rimar",
  api_key = "973711151787113",
  api_secret = "l38OxV1brV1BxfmQkSTKjQEMYYU",
  secure = True
)

# Configuración de la página
st.set_page_config(
    page_title="Repuestos Rimar | Catálogo Digital", 
    page_icon="🚗", 
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    h1, h2, h3 {
        color: #0A1628;
    }
    .stButton>button {
        background-color: #E31E24;
        color: white;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "inventario_rimar.csv"
LOGO_FILE = "logo_rimar.png"
TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

@st.cache_data
def cargar_datos():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    else:
        data = {
            "ARTICULO": [10652, 10656],
            "DESCRIPSION": [
                "TIJERA INFERIOR F ESCAPE 13/19 LH", 
                "SENSOR MONITOREO PRESION AIRE LLANTAS F EXPLORER 16/19"
            ],
            "MARCA": ["KUNYUAN", "HERKO"],
            "PRECIO": [200000, 80000],
            "IMAGEN": [
                "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400",
                "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=400"
            ]
        }
        return pd.DataFrame(data)

if "df_productos" not in st.session_state:
    st.session_state.df_productos = cargar_datos()

# --- FUNCIÓN PARA DETECTAR TIPO DE REPUESTO AUTOMÁTICAMENTE ---
def clasificar_repuesto(descripcion):
    desc = str(descripcion).upper()
    if any(k in desc for k in ["TIJERA", "BRAZO AXIAL", "MUÑECO", "BUJE", "TERMINAL"]):
        return "Suspensión"
    elif any(k in desc for k in ["SENSOR", "VALVULA", "CUERPO ACELERACION"]):
        return "Sensores / Eléctrico"
    elif any(k in desc for k in ["AMORTIGUADOR"]):
        return "Amortiguadores"
    elif any(k in desc for k in ["BUJIA", "BUJIAS", "BOBINA"]):
        return "Bujías / Encendido"
    elif any(k in desc for k in ["SOPORTE"]):
        return "Soportes"
    elif any(k in desc for k in ["BOMBA", "ENFRIADOR", "TERMOSTATO", "MOTOVENTILADOR"]):
        return "Refrigeración"
    elif any(k in desc for k in ["EMPAQUE", "EMPAQUETADURA", "KIT", "PISTON", "ANILLO", "CASQUETE", "VALVULAS", "CORREA", "TENSOR"]):
        return "Motor"
    elif any(k in desc for k in ["FILTRO"]):
        return "Filtros"
    else:
        # Si no encaja exactamente, devuelve una categoría general basada en la primera palabra
        palabras = desc.split()
        return palabras[0] if palabras else "General"

# --- ENCABEZADO Y LOGO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    logo_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200"
    if os.path.exists(LOGO_FILE):
        logo_url = LOGO_FILE
    st.image(logo_url, width=130)

with col_titulo:
    st.title("Repuestos Rimar - Catálogo Digital")
    st.markdown("**Confianza que mueve tu motor** | Repuestos que rinden.")

st.divider()

# --- PREPARAR DATOS Y FILTROS INTELIGENTES ---
df = st.session_state.df_productos
df.columns = [c.strip().upper() for c in df.columns]

if 'CATEGORIA' not in df.columns:
    df['CATEGORIA'] = df['DESCRIPSION'].apply(clasificar_repuesto)

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("🔍 Filtros de Búsqueda")
busqueda = st.sidebar.text_input("Buscar por artículo o descripción...")

# Filtro por Tipo de Repuesto (Categoría)
categorias_disponibles = ["Todas"] + sorted(df['CATEGORIA'].dropna().unique().tolist())
filtro_categoria = st.sidebar.selectbox("📂 Filtrar por Tipo de Repuesto", categorias_disponibles)

# Filtro por Marca (Kunyuan, Herko, Mopar, Arco, etc.)
if 'MARCA' in df.columns:
    marcas_disponibles = ["Todas"] + sorted(df['MARCA'].dropna().astype(str).unique().tolist())
    filtro_marca = st.sidebar.selectbox("🏷️ Filtrar por Marca", marcas_disponibles)
else:
    filtro_marca = "Todas"

st.sidebar.header("💬 Contactar Asesor")
asesor_elegido = st.sidebar.selectbox(
    "Elige con quién hablar:",
    ("Duban Pérez (+57 316 0181283)", "Maritza Moreno (+57 310 6804713)")
)

if "Duban" in asesor_elegido:
    telefono_activo = "573160181283"
    nombre_asesor = "Duban Pérez"
else:
    telefono_activo = "573106804713"
    nombre_asesor = "Maritza Moreno"

st.sidebar.divider()

# --- PANEL DE ADMINISTRACIÓN ---
st.sidebar.header("⚙️ Panel de Administración")
password = st.sidebar.text_input("Contraseña de Administrador", type="password")

if password == "admin123":
    st.sidebar.success("✅ Acceso concedido")
    pestana_admin = st.sidebar.radio("Opciones de Admin", [
        "Cargar Masivo (Excel/CSV)", 
        "Subida Masiva de Fotos (ZIP)",
        "Cambiar Logo de Empresa"
    ])
    
    # 1. CARGA MASIVA DE EXCEL/CSV
    if pestana_admin == "Cargar Masivo (Excel/CSV)":
        st.sidebar.subheader("Carga Masiva de Inventario")
        st.sidebar.markdown("Sube tu archivo con columnas: **ARTICULO**, **DESCRIPSION**, **MARCA**, **PRECIO**")
        archivo_subido = st.sidebar.file_uploader("Sube tu archivo", type=["csv", "xlsx"])
        
        if archivo_subido is not None:
            try:
                if archivo_subido.name.endswith('.csv'):
                    try:
                        df_subido = pd.read_csv(archivo_subido, sep=',')
                        if len(df_subido.columns) <= 1:
                            archivo_subido.seek(0)
                            df_subido = pd.read_csv(archivo_subido, sep=';')
                    except:
                        archivo_subido.seek(0)
                        df_subido = pd.read_csv(archivo_subido, sep=';', encoding='latin-1')
                else:
                    df_subido = pd.read_excel(archivo_subido)
                
                df_subido.columns = [c.strip().upper() for c in df_subido.columns]
                
                if 'ARTICULO' in df_subido.columns and 'DESCRIPSION' in df_subido.columns and 'PRECIO' in df_subido.columns:
                    if 'IMAGEN' not in df_subido.columns:
                        df_subido['IMAGEN'] = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
                    if 'MARCA' not in df_subido.columns:
                        df_subido['MARCA'] = "GENERICA"
                    
                    # Asignar categorías automáticamente según la descripción
                    df_subido['CATEGORIA'] = df_subido['DESCRIPSION'].apply(clasificar_repuesto)
                        
                    st.session_state.df_productos = df_subido
                    df_subido.to_csv(DATA_FILE, index=False)
                    st.sidebar.success("¡Inventario y descripciones cargadas con éxito!")
                    st.rerun()
                else:
                    st.sidebar.error("El archivo debe contener obligatoriamente las columnas: ARTICULO, DESCRIPSION, PRECIO")
            except Exception as e:
                st.sidebar.error(f"Error al procesar el archivo: {e}")

    # 2. SUBIDA MASIVA DE FOTOS MEJORADA (LEE CUALQUIER NOMBRE/EXTENSIÓN)
    elif pestana_admin == "Subida Masiva de Fotos (ZIP)":
        st.sidebar.subheader("Subir Fotos en Lote (ZIP)")
        st.sidebar.markdown("Sube un archivo **.zip** con tus fotos nombradas con el número de artículo (ej: `10652.jpg`).")
        archivo_zip = st.sidebar.file_uploader("Sube tu archivo ZIP con fotos", type=["zip"])
        
        if archivo_zip is not None:
            # Limpiar directorio temporal previo
            for f in os.listdir(TEMP_IMAGE_DIR):
                os.remove(os.path.join(TEMP_IMAGE_DIR, f))
                
            with zipfile.ZipFile(archivo_zip, 'r') as z:
                z.extractall(TEMP_IMAGE_DIR)
            
            # Recorrer de forma recursiva por si vienen dentro de una carpeta en el ZIP
            mapa_fotos = {}
            for root, dirs, files in os.walk(TEMP_IMAGE_DIR):
                for file in files:
                    # Extraer solo los números del nombre del archivo (ej: "10652.jpg" -> "10652")
                    nombre_base = os.path.splitext(file)[0].strip()
                    limpio = re.sub(r'\D', '', nombre_base) # quita caracteres raros
                    if limpio:
                        mapa_fotos[limpio] = os.path.join(root, file)

            df_actual = st.session_state.df_productos
            df_actual.columns = [c.strip().upper() for c in df_actual.columns]
            
            actualizados = 0
            for idx, row in df_actual.iterrows():
                art_num = str(row['ARTICULO']).strip()
                art_limpio = re.sub(r'\D', '', art_num)
                
                if art_limpio in mapa_fotos:
                    foto_path = mapa_fotos[art_limpio]
                    try:
                        res = cloudinary.uploader.upload(foto_path)
                        secure_url = res.get("secure_url")
                        df_actual.loc[idx, 'IMAGEN'] = secure_url
                        actualizados += 1
                    except Exception as ex:
                        pass

            st.session_state.df_productos = df_actual
            df_actual.to_csv(DATA_FILE, index=False)
            st.sidebar.success(f"¡Se asociaron y subieron {actualizados} fotos a la nube con éxito!")
            st.rerun()

    # 3. CAMBIAR LOGO
    elif pestana_admin == "Cambiar Logo de Empresa":
        st.sidebar.subheader("Actualizar Logo")
        logo_subido = st.sidebar.file_uploader("Sube la imagen de tu logo", type=["png", "jpg", "jpeg"])
        if logo_subido is not None:
            with open(LOGO_FILE, "wb") as f:
                f.write(logo_subido.getbuffer())
            st.sidebar.success("¡Logo actualizado con éxito!")
            st.rerun()

elif password != "":
    st.sidebar.error("❌ Contraseña incorrecta")

# --- APLICAR FILTROS EN PANTALLA ---
df_filtrado = df.copy()

# Filtro de búsqueda por texto
if busqueda:
    df_filtrado = df_filtrado[
        df_filtrado.get('ARTICULO', pd.Series(['']*len(df_filtrado))).astype(str).str.lower().str.contains(busqueda.lower()) |
        df_filtrado.get('DESCRIPSION', pd.Series(['']*len(df_filtrado))).astype(str).str.lower().str.contains(busqueda.lower())
    ]

# Filtro por Categoría / Tipo de Repuesto
if filtro_categoria != "Todas":
    df_filtrado = df_filtrado[df_filtrado['CATEGORIA'] == filtro_categoria]

# Filtro por Marca
if filtro_marca != "Todas" and 'MARCA' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['MARCA'].astype(str) == filtro_marca]

if df_filtrado.empty:
    st.warning("No se encontraron repuestos con los filtros seleccionados.")

# --- MOSTRAR PRODUCTOS EN CUADRÍCULA ---
cols = st.columns(3)
for i, row in df_filtrado.iterrows():
    with cols[i % 3]:
        img_url = row.get('IMAGEN', "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400")
        if pd.isna(img_url) or not str(img_url).startswith("http"):
            img_url = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
            
        st.image(img_url, use_container_width=True)
        
        art_val = row.get('ARTICULO', 'S/N')
        marca_val = row.get('MARCA', 'GENERICA')
        desc_val = row.get('DESCRIPSION', 'Sin descripción')
        cat_val = row.get('CATEGORIA', 'General')
        precio_num = row.get('PRECIO', 0)
        
        st.caption(f"🆔 **Art:** {art_val} | 🏷️ **Marca:** {marca_val} | 📂 {cat_val}")
        st.subheader(str(desc_val))
        
        precio_val = f"${int(precio_num):,}" if pd.notna(precio_num) else "$0"
        st.write(f"**Precio:** {precio_val}")
        
        mensaje = f"Hola {nombre_asesor}, me interesa adquirir el repuesto *{desc_val}* (Artículo: {art_val}) por un valor de {precio_val} visto en Repuestos Rimar. ¿Me confirman disponibilidad?"
        url_whatsapp = f"https://wa.me/{telefono_activo}?text={mensaje.replace(' ', '%20')}"
        
        st.markdown(
            f'<a href="{url_whatsapp}" target="_blank" style="display:block;text-align:center;padding:10px 15px;background-color:#25D366;color:white;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:10px;">💬 Pedir con {nombre_asesor.split()[0]}</a>',
            unsafe_allow_html=True
        )
        st.divider()

st.markdown("---")
st.markdown("© 2026 **Repuestos Rimar** - Todos los derechos reservados. Contacto General: **+57 350 8258778**")
