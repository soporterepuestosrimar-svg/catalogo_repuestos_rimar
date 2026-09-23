import streamlit as st
import pandas as pd
import os
import cloudinary
import cloudinary.uploader

# ==========================================
# CONFIGURACIÓN DE CLOUDINARY (Tus datos de la nube)
# ==========================================
cloudinary.config(
  cloud_name = "Root",
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

@st.cache_data
def cargar_datos():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        data = {
            "codigo": ["RIM-001", "RIM-002", "RIM-003", "RIM-004"],
            "nombre": [
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
    st.markdown("**Somos La Mejor Parte** | Repuestos de Calidad.")

st.divider()

# --- BARRA LATERAL ---
st.sidebar.header("🔍 Filtros de Búsqueda")
busqueda = st.sidebar.text_input("Buscar por código, repuesto o marca...")

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
    pestana_admin = st.sidebar.radio("Opciones de Admin", ["Añadir Producto", "Editar / Cambiar Foto", "Cargar Masivo (Excel/CSV)"])
    
    if pestana_admin == "Añadir Producto":
        st.sidebar.subheader("Nuevo Artículo")
        with st.sidebar.form("form_nuevo"):
            n_codigo = st.text_input("Código único (ej: RIM-005)")
            n_nombre = st.text_input("Nombre del repuesto")
            n_cat = st.text_input("Categoría")
            n_precio = st.number_input("Precio ($)", min_value=0, step=1000)
            n_img_file = st.file_uploader("Subir foto desde dispositivo", type=["jpg", "png", "jpeg"])
            
            submit_add = st.form_submit_button("Guardar Producto")
            
            if submit_add and n_codigo and n_nombre:
                img_url = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
                if n_img_file is not None:
                    upload_result = cloudinary.uploader.upload(n_img_file)
                    img_url = upload_result.get("secure_url")
                
                nuevo_reg = pd.DataFrame([{
                    "codigo": n_codigo,
                    "nombre": n_nombre,
                    "categoria": n_cat,
                    "precio": n_precio,
                    "imagen": img_url
                }])
                st.session_state.df_productos = pd.concat([st.session_state.df_productos, nuevo_reg], ignore_index=True)
                st.session_state.df_productos.to_csv(DATA_FILE, index=False)
                st.sidebar.success("¡Producto agregado correctamente!")
                st.rerun()

    elif pestana_admin == "Editar / Cambiar Foto":
        st.sidebar.subheader("Modificar Artículo Existente")
        df_actual = st.session_state.df_productos
        
        if not df_actual.empty:
            codigo_a_editar = st.sidebar.selectbox("Selecciona el Código del Artículo", df_actual['codigo'].tolist())
            prod_idx = df_actual[df_actual['codigo'] == codigo_a_editar].index[0]
            prod_actual = df_actual.loc[prod_idx]
            
            with st.sidebar.form("form_editar"):
                e_nombre = st.text_input("Nombre", value=str(prod_actual['nombre']))
                e_cat = st.text_input("Categoría", value=str(prod_actual['categoria']))
                e_precio = st.number_input("Precio ($)", value=int(prod_actual['precio']), step=1000)
                e_img_file = st.file_uploader("Actualizar foto desde dispositivo (Opcional)", type=["jpg", "png", "jpeg"])
                
                submit_edit = st.form_submit_button("Actualizar Artículo")
                
                if submit_edit:
                    img_url_final = prod_actual['imagen']
                    if e_img_file is not None:
                        upload_result = cloudinary.uploader.upload(e_img_file)
                        img_url_final = upload_result.get("secure_url")
                    
                    st.session_state.df_productos.at[prod_idx, 'nombre'] = e_nombre
                    st.session_state.df_productos.at[prod_idx, 'categoria'] = e_cat
                    st.session_state.df_productos.at[prod_idx, 'precio'] = e_precio
                    st.session_state.df_productos.at[prod_idx, 'imagen'] = img_url_final
                    
                    st.session_state.df_productos.to_csv(DATA_FILE, index=False)
                    st.sidebar.success("¡Artículo actualizado con éxito!")
                    st.rerun()
            
            if st.sidebar.button("🗑️ Eliminar este artículo"):
                st.session_state.df_productos = df_actual.drop(prod_idx).reset_index(drop=True)
                st.session_state.df_productos.to_csv(DATA_FILE, index=False)
                st.sidebar.success("Artículo eliminado.")
                st.rerun()

    elif pestana_admin == "Cargar Masivo (Excel/CSV)":
        st.sidebar.subheader("Subir Inventario Masivo")
        st.sidebar.markdown("Tu archivo debe contener las columnas: `codigo`, `nombre`, `categoria`, `precio`, `imagen`")
        archivo_subido = st.sidebar.file_uploader("Sube tu archivo CSV o Excel", type=["csv", "xlsx"])
        
        if archivo_subido is not None:
            try:
                if archivo_subido.name.endswith('.csv'):
                    # Intenta leer con coma o con punto y coma de forma automática
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
                
                st.session_state.df_productos = df_subido
                df_subido.to_csv(DATA_FILE, index=False)
                st.sidebar.success("¡Inventario cargado y actualizado con éxito!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error al leer el archivo: Revisa que las columnas coincidan.")

elif password != "":
    st.sidebar.error("❌ Contraseña incorrecta")

# --- VISUALIZACIÓN ---
df = st.session_state.df_productos
if busqueda:
    df_filtrado = df[
        df['codigo'].astype(str).str.lower().str.contains(busqueda.lower()) |
        df['nombre'].astype(str).str.lower().str.contains(busqueda.lower()) |
        df['categoria'].astype(str).str.lower().str.contains(busqueda.lower())
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
        
        st.caption(f"🆔 **Código:** {row['codigo']}")
        st.subheader(row['nombre'])
        st.write(f"**Categoría:** {row['categoria']}")
        
        precio_val = f"${int(row['precio']):,}" if pd.notna(row['precio']) else "$0"
        st.write(f"**Precio:** {precio_val}")
        
        mensaje = f"Hola {nombre_asesor}, me interesa adquirir el producto *{row['nombre']}* (Código: {row['codigo']}) por un valor de {precio_val} visto en Repuestos Rimar. ¿Me confirman disponibilidad?"
        url_whatsapp = f"https://wa.me/{telefono_activo}?text={mensaje.replace(' ', '%20')}"
        
        st.markdown(
            f'<a href="{url_whatsapp}" target="_blank" style="display:block;text-align:center;padding:10px 15px;background-color:#25D366;color:white;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:10px;">💬 Pedir con {nombre_asesor.split()[0]}</a>',
            unsafe_allow_html=True
        )
        st.divider()

st.markdown("---")
st.markdown("© 2026 **Repuestos Rimar** - Todos los derechos reservados. Contacto General: **+57 350 8258778**")
