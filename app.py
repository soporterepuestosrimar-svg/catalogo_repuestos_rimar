import streamlit as st
import pandas as pd
import os
import cloudinary
import cloudinary.uploader
import zipfile

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
            "MARCA": ["KUNYUAN", "KUNYUAN"],
            "PRECIO": [200000, 80000],
            "IMAGEN": [
                "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400",
                "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=400"
            ]
        }
        return pd.DataFrame(data)

if "df_productos" not in st.session_state:
    st.session_state.df_productos = cargar_datos()

# --- ENCABEZADO Y LOGO PERSONALIZADO ---
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

# --- BARRA LATERAL ---
st.sidebar.header("🔍 Filtros de Búsqueda")
busqueda = st.sidebar.text_input("Buscar por artículo, descripción o marca...")

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
        "Añadir / Editar Producto", 
        "Cargar Masivo (Excel/CSV)", 
        "Subida Masiva de Fotos (ZIP)",
        "Cambiar Logo de Empresa"
    ])
    
    # 1. GESTIÓN INDIVIDUAL
    if pestana_admin == "Añadir / Editar Producto":
        st.sidebar.subheader("Gestión de Artículo")
        df_actual = st.session_state.df_productos
        df_actual.columns = [c.strip().upper() for c in df_actual.columns]
        
        col_id = 'ARTICULO' if 'ARTICULO' in df_actual.columns else df_actual.columns[0]
        lista_articulos = ["-- NUEVO ARTÍCULO --"] + df_actual[col_id].astype(str).tolist()
        art_seleccionado = st.sidebar.selectbox("Selecciona Artículo (o crea uno nuevo)", lista_articulos)
        
        with st.sidebar.form("form_gestion"):
            if art_seleccionado == "-- NUEVO ARTÍCULO --":
                n_articulo = st.text_input("Número de Artículo (Ej: 10652)")
                n_desc = st.text_input("Descripción del repuesto")
                n_marca = st.text_input("Marca", value="KUNYUAN")
                n_precio = st.number_input("Precio ($)", min_value=0, step=1000)
            else:
                idx_prod = df_actual[df_actual[col_id].astype(str) == str(art_seleccionado)].index[0]
                p_info = df_actual.loc[idx_prod]
                
                n_articulo = st.text_input("Número de Artículo", value=str(p_info.get(col_id, '')))
                n_desc = st.text_input("Descripción", value=str(p_info.get('DESCRIPSION', '')))
                n_marca = st.text_input("Marca", value=str(p_info.get('MARCA', 'KUNYUAN')))
                n_precio = st.number_input("Precio ($)", value=int(p_info.get('PRECIO', 0)), step=1000)
            
            n_img_file = st.file_uploader("Subir foto del repuesto", type=["jpg", "png", "jpeg"])
            submit_form = st.form_submit_button("Guardar Cambios")
            
            if submit_form and n_articulo:
                img_url_final = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
                if art_seleccionado != "-- NUEVO ARTÍCULO --":
                    img_url_final = p_info.get('IMAGEN', img_url_final)
                
                if n_img_file is not None:
                    upload_result = cloudinary.uploader.upload(n_img_file)
                    img_url_final = upload_result.get("secure_url")
                
                nuevo_reg = {
                    "ARTICULO": n_articulo,
                    "DESCRIPSION": n_desc,
                    "MARCA": n_marca,
                    "PRECIO": n_precio,
                    "IMAGEN": img_url_final
                }
                
                if art_seleccionado == "-- NUEVO ARTÍCULO --":
                    df_nuevo = pd.DataFrame([nuevo_reg])
                    st.session_state.df_productos = pd.concat([st.session_state.df_productos, df_nuevo], ignore_index=True)
                else:
                    for k, v in nuevo_reg.items():
                        st.session_state.df_productos.loc[idx_prod, k] = v
                
                st.session_state.df_productos.to_csv(DATA_FILE, index=False)
                st.sidebar.success("¡Guardado correctamente!")
                st.rerun()

    # 2. CARGA MASIVA DE EXCEL/CSV
    elif pestana_admin == "Cargar Masivo (Excel/CSV)":
        st.sidebar.subheader("Carga Masiva de Inventario")
        st.sidebar.markdown("Sube tu archivo con las columnas: **ARTICULO**, **DESCRIPSION**, **MARCA**, **PRECIO**")
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
                        df_subido['MARCA'] = "KUNYUAN"
                        
                    st.session_state.df_productos = df_subido
                    df_subido.to_csv(DATA_FILE, index=False)
                    st.sidebar.success("¡Inventario y descripciones cargadas con éxito!")
                    st.rerun()
                else:
                    st.sidebar.error("Tu archivo debe contener obligatoriamente las columnas: ARTICULO, DESCRIPSION, PRECIO")
            except Exception as e:
                st.sidebar.error(f"Error al procesar el archivo: {e}")

    # 3. SUBIDA MASIVA DE FOTOS MEDIANTE UN ARCHIVO ZIP
    elif pestana_admin == "Subida Masiva de Fotos (ZIP)":
        st.sidebar.subheader("Subir Fotos en Lote")
        st.sidebar.markdown("Sube un archivo **.zip** con tus fotos. Nombra cada foto con el número de artículo exacto (Ej: `10652.jpg` o `10652.png`).")
        archivo_zip = st.sidebar.file_uploader("Sube tu archivo ZIP con fotos", type=["zip"])
        
        if archivo_zip is not None:
            with zipfile.ZipFile(archivo_zip, 'r') as z:
                z.extractall(TEMP_IMAGE_DIR)
            
            # Recorrer productos y buscar si existe una foto con el nombre del artículo
            df_actual = st.session_state.df_productos
            df_actual.columns = [c.strip().upper() for c in df_actual.columns]
            
            actualizados = 0
            for idx, row in df_actual.iterrows():
                art_num = str(row['ARTICULO']).strip()
                for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.PNG']:
                    foto_path = os.path.join(TEMP_IMAGE_DIR, art_num + ext)
                    if os.path.exists(foto_path):
                        # Subir a Cloudinary de manera automática
                        res = cloudinary.uploader.upload(foto_path)
                        secure_url = res.get("secure_url")
                        df_actual.loc[idx, 'IMAGEN'] = secure_url
                        actualizados += 1
                        break
            
            st.session_state.df_productos = df_actual
            df_actual.to_csv(DATA_FILE, index=False)
            st.sidebar.success(f"¡Se asociaron y subieron {actualizados} fotos automáticamente a la nube!")
            st.rerun()

    # 4. CAMBIAR LOGO
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

# --- VISUALIZACIÓN DE PRODUCTOS EN LA PÁGINA ---
df = st.session_state.df_productos
df.columns = [c.strip().upper() for c in df.columns]

if busqueda:
    df_filtrado = df[
        df.get('ARTICULO', pd.Series(['']*len(df))).astype(str).str.lower().str.contains(busqueda.lower()) |
        df.get('DESCRIPSION', pd.Series(['']*len(df))).astype(str).str.lower().str.contains(busqueda.lower()) |
        df.get('MARCA', pd.Series(['']*len(df))).astype(str).str.lower().str.contains(busqueda.lower())
    ]
else:
    df_filtrado = df

if df_filtrado.empty:
    st.warning("No se encontraron repuestos con ese criterio de búsqueda.")

cols = st.columns(3)
for i, row in df_filtrado.iterrows():
    with cols[i % 3]:
        img_url = row.get('IMAGEN', "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400")
        if pd.isna(img_url) or not str(img_url).startswith("http"):
            img_url = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
            
        st.image(img_url, use_container_width=True)
        
        art_val = row.get('ARTICULO', 'S/N')
        marca_val = row.get('MARCA', 'KUNYUAN')
        desc_val = row.get('DESCRIPSION', 'Sin descripción')
        precio_num = row.get('PRECIO', 0)
        
        st.caption(f"🆔 **Artículo:** {art_val} | **Marca:** {marca_val}")
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
