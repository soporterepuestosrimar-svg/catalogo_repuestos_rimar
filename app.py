import streamlit as st
import pandas as pd
import os
import cloudinary
import cloudinary.uploader

# ==========================================
# CONFIGURACIÓN DE CLOUDINARY (Tus datos de la nube)
# ==========================================
cloudinary.config(
  cloud_name = "TU_CLOUD_NAME",
  api_key = "TU_API_KEY",
  api_secret = "TU_API_SECRET",
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

@st.cache_data
def cargar_datos():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        data = {
            "articulo": ["RIM-001", "RIM-002", "RIM-003", "RIM-004"],
            "descripcion": [
                "Amortiguador Delantero Ford / Toyota", 
                "Bomba de Agua Jeep / Ram", 
                "Sensor MAP Nissan / Dodge", 
                "Kit de Empaquetadura de Motor"
            ],
            "categoria": ["Suspensión", "Refrigeración", "Sensores", "Motor"],
            "precio": [180000, 120000, 95000, 210000],
            "imagen": [
                "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400",
                "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=400",
                "https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=400",
                "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
            ]
        }
        return pd.DataFrame(data)

if "df_productos" not in st.session_state:
    st.session_state.df_productos = cargar_datos()

# --- ENCABEZADO Y LOGO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200", width=120)
with col_titulo:
    st.title("Repuestos Rimar - Catálogo Digital")
    st.markdown("**Confianza que mueve tu motor** | Repuestos que rinden.")

st.divider()

# --- BARRA LATERAL ---
st.sidebar.header("🔍 Filtros de Búsqueda")
busqueda = st.sidebar.text_input("Buscar por artículo, descripción...")

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
    pestana_admin = st.sidebar.radio("Opciones de Admin", ["Añadir / Editar Producto", "Cargar Masivo (CSV/Excel)"])
    
    if pestana_admin == "Añadir / Editar Producto":
        st.sidebar.subheader("Gestión de Artículo")
        df_actual = st.session_state.df_productos
        
        # Opción para seleccionar un artículo existente o crear uno nuevo
        lista_articulos = ["-- NUEVO ARTÍCULO --"] + df_actual['articulo'].astype(str).tolist()
        art_seleccionado = st.sidebar.selectbox("Selecciona Artículo (o crea uno nuevo)", lista_articulos)
        
        with st.sidebar.form("form_gestion"):
            if art_seleccionado == "-- NUEVO ARTÍCULO --":
                n_articulo = st.text_input("Número de Artículo (Ej: 12345 o RIM-005)")
                n_desc = st.text_input("Descripción del repuesto")
                n_cat = st.text_input("Categoría")
                n_precio = st.number_input("Precio ($)", min_value=0, step=1000)
            else:
                idx_prod = df_actual[df_actual['articulo'].astype(str) == str(art_seleccionado)].index[0]
                p_info = df_actual.loc[idx_prod]
                
                n_articulo = st.text_input("Número de Artículo", value=str(p_info['articulo']))
                n_desc = st.text_input("Descripción", value=str(p_info['descripcion']))
                n_cat = st.text_input("Categoría", value=str(p_info.get('categoria', 'General')))
                n_precio = st.number_input("Precio ($)", value=int(p_info['precio']), step=1000)
            
            n_img_file = st.file_uploader("Subir foto desde tu dispositivo", type=["jpg", "png", "jpeg"])
            submit_form = st.form_submit_button("Guardar Cambios")
            
            if submit_form and n_articulo:
                # Subir foto a Cloudinary si se seleccionó una nueva
                img_url_final = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
                if art_seleccionado != "-- NUEVO ARTÍCULO --":
                    img_url_final = p_info['imagen']
                
                if n_img_file is not None:
                    upload_result = cloudinary.uploader.upload(n_img_file)
                    img_url_final = upload_result.get("secure_url")
                
                nuevo_reg = {
                    "articulo": n_articulo,
                    "descripcion": n_desc,
                    "categoria": n_cat,
                    "precio": n_precio,
                    "imagen": img_url_final
                }
                
                if art_seleccionado == "-- NUEVO ARTÍCULO --":
                    df_nuevo = pd.DataFrame([nuevo_reg])
                    st.session_state.df_productos = pd.concat([st.session_state.df_productos, df_nuevo], ignore_index=True)
                else:
                    st.session_state.df_productos.loc[idx_prod] = nuevo_reg
                
                st.session_state.df_productos.to_csv(DATA_FILE, index=False)
                st.sidebar.success("¡Guardado correctamente!")
                st.rerun()

    elif pestana_admin == "Cargar Masivo (CSV/Excel)":
        st.sidebar.subheader("Carga Masiva de Inventario")
        st.sidebar.markdown("Tu archivo debe contener las columnas: `articulo`, `descripcion`, `precio` (y opcionalmente `categoria`, `imagen`)")
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
                
                # Normalizar nombres de columnas a minúsculas por si acaso
                df_subido.columns = [c.strip().lower() for c in df_subido.columns]
                
                # Validar que existan las columnas principales
                if 'articulo' in df_subido.columns and 'descripcion' in df_subido.columns and 'precio' in df_subido.columns:
                    if 'imagen' not in df_subido.columns:
                        df_subido['imagen'] = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
                    if 'categoria' not in df_subido.columns:
                        df_subido['categoria'] = "General"
                        
                    st.session_state.df_productos = df_subido
                    df_subido.to_csv(DATA_FILE, index=False)
                    st.sidebar.success("¡Inventario cargado con éxito!")
                    st.rerun()
                else:
                    st.sidebar.error("El archivo debe tener las columnas: articulo, descripcion, precio")
            except Exception as e:
                st.sidebar.error(f"Error al procesar el archivo: {e}")

elif password != "":
    st.sidebar.error("❌ Contraseña incorrecta")

# --- VISUALIZACIÓN DE PRODUCTOS ---
df = st.session_state.df_productos
if busqueda:
    df_filtrado = df[
        df['articulo'].astype(str).str.lower().str.contains(busqueda.lower()) |
        df['descripcion'].astype(str).str.lower().str.contains(busqueda.lower()) |
        df.get('categoria', pd.Series(['']*len(df))).astype(str).str.lower().str.contains(busqueda.lower())
    ]
else:
    df_filtrado = df

if df_filtrado.empty:
    st.warning("No se encontraron repuestos con ese criterio de búsqueda.")

cols = st.columns(3)
for i, row in df_filtrado.iterrows():
    with cols[i % 3]:
        img_url = row['imagen'] if pd.notna(row['imagen']) and str(row['imagen']).startswith("http") else "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
        st.image(img_url, use_container_width=True)
        
        st.caption(f"🆔 **Artículo:** {row['articulo']}")
        st.subheader(row['descripcion'])
        st.write(f"**Categoría:** {row.get('categoria', 'General')}")
        
        precio_val = f"${int(row['precio']):,}" if pd.notna(row['precio']) else "$0"
        st.write(f"**Precio:** {precio_val}")
        
        mensaje = f"Hola {nombre_asesor}, me interesa adquirir el repuesto *{row['descripcion']}* (Artículo: {row['articulo']}) por un valor de {precio_val} visto en Repuestos Rimar. ¿Me confirman disponibilidad?"
        url_whatsapp = f"https://wa.me/{telefono_activo}?text={mensaje.replace(' ', '%20')}"
        
        st.markdown(
            f'<a href="{url_whatsapp}" target="_blank" style="display:block;text-align:center;padding:10px 15px;background-color:#25D366;color:white;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:10px;">💬 Pedir con {nombre_asesor.split()[0]}</a>',
            unsafe_allow_html=True
        )
        st.divider()

st.markdown("---")
st.markdown("© 2026 **Repuestos Rimar** - Todos los derechos reservados. Contacto General: **+57 350 8258778**")
