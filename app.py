import streamlit as st
import pandas as pd
import os

# Configuración de la página
st.set_page_config(
    page_title="Repuestos Rimar | Catálogo Digital", 
    page_icon="🚗", 
    layout="wide"
)

# Estilos personalizados (Colores corporativos de Repuestos Rimar)
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

# Directorio para almacenar imágenes subidas
UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Archivo local de persistencia para los productos
DATA_FILE = "inventario_rimar.csv"

# Cargar inventario inicial o guardado
@st.cache_data
def cargar_datos():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        # Datos iniciales por defecto
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
    # Puedes cambiar esta URL por el enlace directo de tu logo alojado en la web o Drive
    st.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200", width=120)
with col_titulo:
    st.title("Repuestos Rimar - Catálogo Digital")
    st.markdown("**Confianza que mueve tu motor** | Repuestos que rinden.")

st.divider()

# --- BARRA LATERAL (FILTROS Y PANEL DE ADMINISTRACIÓN) ---
st.sidebar.header("🔍 Filtros de Búsqueda")
busqueda = st.sidebar.text_input("Buscar por código, repuesto o marca...")

# Selector de Asesor para WhatsApp
st.sidebar.header("💬 Contactar Asesor")
asesor_elegido = st.sidebar.selectbox(
    "Elige con quién hablar:",
    ("Duban Pérez (+57 316 0181283)", "Maritza Moreno (+57 310 6804713)")
)

# Definir número según asesor
if "Duban" in asesor_elegido:
    telefono_activo = "573160181283"
    nombre_asesor = "Duban Pérez"
else:
    telefono_activo = "573106804713"
    nombre_asesor = "Maritza Moreno"

st.sidebar.divider()

# --- PANEL DE ADMINISTRACIÓN / GESTIÓN DE INVENTARIO ---
st.sidebar.header("⚙️ Panel de Administración")
modo_admin = st.sidebar.checkbox("Activar modo administrador")

if modo_admin:
    st.sidebar.subheader("Subir Inventario Masivo")
    archivo_csv = st.sidebar.file_uploader("Sube tu archivo CSV con columnas: codigo, nombre, categoria, precio, imagen", type=["csv"])
    if archivo_csv is not None:
        df_nuevo = pd.read_csv(archivo_csv)
        st.session_state.df_productos = df_nuevo
        df_nuevo.to_csv(DATA_FILE, index=False)
        st.sidebar.success("¡Inventario actualizado con éxito!")
        st.rerun()

    st.sidebar.subheader("Agregar Producto Individual")
    with st.sidebar.form("form_agregar"):
        n_codigo = st.text_input("Código único (ej: RIM-005)")
        n_nombre = st.text_input("Nombre del repuesto")
        n_cat = st.text_input("Categoría")
        n_precio = st.number_input("Precio ($)", min_value=0, step=1000)
        n_img = st.text_input("URL de la imagen")
        submit_btn = st.form_submit_button("Añadir producto")
        
        if submit_btn and n_codigo and n_nombre:
            nuevo_reg = pd.DataFrame([{
                "codigo": n_codigo,
                "nombre": n_nombre,
                "categoria": n_cat,
                "precio": n_precio,
                "imagen": n_img if n_img else "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
            }])
            st.session_state.df_productos = pd.concat([st.session_state.df_productos, nuevo_reg], ignore_index=True)
            st.session_state.df_productos.to_csv(DATA_FILE, index=False)
            st.success("¡Producto agregado!")
            st.rerun()

    if st.sidebar.button("🔄 Restablecer valores originales"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.rerun()

# --- FILTRADO DE PRODUCTOS ---
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

# --- VISUALIZACIÓN EN CUADRÍCULA ---
cols = st.columns(3)
for i, row in df_filtrado.iterrows():
    with cols[i % 3]:
        # Validar imagen
        img_url = row['imagen'] if pd.notna(row['imagen']) and str(row['imagen']).startswith("http") else "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
        st.image(img_url, use_container_width=True)
        
        st.caption(f"🆔 **Código:** {row['codigo']}")
        st.subheader(row['nombre'])
        st.write(f"**Categoría:** {row['categoria']}")
        
        # Formato de precio en pesos
        precio_val = f"${int(row['precio']):,}" if pd.notna(row['precio']) else "$0"
        st.write(f"**Precio:** {precio_val}")
        
        # Enlace directo al WhatsApp del asesor seleccionado
        mensaje = f"Hola {nombre_asesor}, me interesa adquirir el producto *{row['nombre']}* (Código: {row['codigo']}) por un valor de {precio_val} visto en Repuestos Rimar. ¿Me confirman disponibilidad?"
        url_whatsapp = f"https://wa.me/{telefono_activo}?text={mensaje.replace(' ', '%20')}"
        
        st.markdown(
            f'<a href="{url_whatsapp}" target="_blank" style="display:block;text-align:center;padding:10px 15px;background-color:#25D366;color:white;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:10px;">💬 Pedir con {nombre_asesor.split()[0]}</a>',
            unsafe_allow_html=True
        )
        st.divider()

# Pie de página
st.markdown("---")
st.markdown("© 2026 **Repuestos Rimar** - Todos los derechos reservados. Contacto General: **+57 350 8258778**")
