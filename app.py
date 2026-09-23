import streamlit as st
import pandas as pd
import os
import zipfile
import re
import shutil
import cloudinary
import cloudinary.uploader
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# CONFIGURACIÓN OFICIAL DE CLOUDINARY (Nube Permanente)
# ==========================================
cloudinary.config(
  cloud_name = "r9vobuds",
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

# Estilos CSS avanzados para alinear tarjetas de manera prolija
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
    .iva-badge {
        background-color: #FFC107;
        color: #0A1628;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: bold;
        margin-left: 6px;
    }
    .product-card {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .product-title {
        font-size: 1.05rem;
        font-weight: bold;
        color: #0A1628;
        height: 50px;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

DATA_FILE = "inventario_rimar.csv"
LOGO_FILE = "logo_rimar.png"
TEMP_ZIP_DIR = "temp_zip_images"
os.makedirs(TEMP_ZIP_DIR, exist_ok=True)

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
        palabras = desc.split()
        return palabras[0] if palabras else "General"

# --- GENERADOR DE PDF ---
def generar_pdf(dataframe_filtrado, nombre_asesor, telefono_asesor):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elementos = []
    
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#0A1628'), alignment=1)
    estilo_sub = ParagraphStyle('SubTituloPDF', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#555555'), alignment=1)
    estilo_celda = ParagraphStyle('CeldaPDF', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#333333'))
    
    elementos.append(Paragraph("REPUESTOS RIMAR - CATÁLOGO DIGITAL", estilo_titulo))
    elementos.append(Paragraph("Confianza que mueve tu motor | Contacto Asesor: " + nombre_asesor + " (" + telefono_asesor + ")", estilo_sub))
    elementos.append(Spacer(1, 15))
    
    datos_tabla = [["Artículo", "Descripción", "Marca", "Categoría", "Precio (+IVA)"]]
    
    for _, row in dataframe_filtrado.iterrows():
        art = str(row.get('ARTICULO', ''))
        desc = str(row.get('DESCRIPSION', ''))
        marca = str(row.get('MARCA', ''))
        cat = str(row.get('CATEGORIA', ''))
        precio_val = f"${int(row.get('PRECIO', 0)):,}" if pd.notna(row.get('PRECIO', 0)) else "$0"
        
        datos_tabla.append([
            Paragraph(art, estilo_celda),
            Paragraph(desc, estilo_celda),
            Paragraph(marca, estilo_celda),
            Paragraph(cat, estilo_celda),
            Paragraph(precio_val + " +IVA", estilo_celda)
        ])
        
    tabla = Table(datos_tabla, colWidths=[65, 230, 80, 90, 75])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0A1628')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f9f9f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    elementos.append(tabla)
    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()

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

# --- PREPARAR DATOS Y FILTROS ---
df = st.session_state.df_productos
df.columns = [c.strip().upper() for c in df.columns]

if 'CATEGORIA' not in df.columns:
    df['CATEGORIA'] = df['DESCRIPSION'].apply(clasificar_repuesto)

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("🔍 Filtros de Búsqueda")
busqueda = st.sidebar.text_input("Buscar por artículo o descripción...")

categorias_disponibles = ["Todas"] + sorted(df['CATEGORIA'].dropna().unique().tolist())
filtro_categoria = st.sidebar.selectbox("📂 Filtrar por Tipo de Repuesto", categorias_disponibles)

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
modo_admin = False

if password == "admin123":
    modo_admin = True
    st.sidebar.success("✅ Acceso concedido")
    pestana_admin = st.sidebar.radio("Opciones de Admin", [
        "Cargar Masivo (Excel/CSV)", 
        "Subida Masiva de Fotos (ZIP a la Nube)",
        "Cambiar Logo de Empresa"
    ])
    
    if pestana_admin == "Cargar Masivo (Excel/CSV)":
        st.sidebar.subheader("Carga Masiva (Acumulativa)")
        archivo_subido = st.sidebar.file_uploader("Sube tu archivo (Excel/CSV)", type=["csv", "xlsx"])
        
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
                    
                    df_subido['CATEGORIA'] = df_subido['DESCRIPSION'].apply(clasificar_repuesto)
                    
                    df_actual = st.session_state.df_productos
                    df_actual.columns = [c.strip().upper() for c in df_actual.columns]
                    
                    df_subido['ARTICULO'] = df_subido['ARTICULO'].astype(str)
                    df_actual['ARTICULO'] = df_actual['ARTICULO'].astype(str)
                    
                    df_combinado = pd.concat([df_actual, df_subido]).drop_duplicates(subset=['ARTICULO'], keep='last').reset_index(drop=True)
                        
                    st.session_state.df_productos = df_combinado
                    df_combinado.to_csv(DATA_FILE, index=False)
                    st.sidebar.success("¡Artículos agregados exitosamente!")
                    st.rerun()
                else:
                    st.sidebar.error("El archivo debe contener: ARTICULO, DESCRIPSION, PRECIO")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

    elif pestana_admin == "Subida Masiva de Fotos (ZIP a la Nube)":
        st.sidebar.subheader("Subir Fotos a Cloudinary (ZIP Automático)")
        st.sidebar.markdown("Sube tu `.zip`. El sistema leerá el número de cada foto, la subirá a Cloudinary de forma permanente y actualizará el catálogo automáticamente.")
        archivo_zip = st.sidebar.file_uploader("Sube tu archivo ZIP con fotos", type=["zip"])
        
        if archivo_zip is not None:
            if os.path.exists(TEMP_ZIP_DIR):
                shutil.rmtree(TEMP_ZIP_DIR)
            os.makedirs(TEMP_ZIP_DIR, exist_ok=True)
                
            with zipfile.ZipFile(archivo_zip, 'r') as z:
                z.extractall(TEMP_ZIP_DIR)
            
            mapa_fotos = {}
            for root, dirs, files in os.walk(TEMP_ZIP_DIR):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        nombre_base = os.path.splitext(file)[0].strip()
                        limpio = re.sub(r'\D', '', nombre_base)
                        if limpio:
                            mapa_fotos[limpio] = os.path.join(root, file)

            df_actual = st.session_state.df_productos
            df_actual.columns = [c.strip().upper() for c in df_actual.columns]
            
            barra_progreso = st.sidebar.progress(0)
            total_articulos = len(df_actual)
            actualizados = 0

            for idx, row in df_actual.iterrows():
                art_num = str(row['ARTICULO']).strip()
                art_limpio = re.sub(r'\D', '', art_num)
                
                if art_limpio in mapa_fotos:
                    foto_path = mapa_fotos[art_limpio]
                    try:
                        # Subir permanentemente a Cloudinary y capturar URL segura
                        res = cloudinary.uploader.upload(foto_path)
                        secure_url = res.get("secure_url")
                        df_actual.loc[idx, 'IMAGEN'] = secure_url
                        actualizados += 1
                    except Exception as ex:
                        pass
                
                barra_progreso.progress(int((idx + 1) / total_articulos * 100))

            st.session_state.df_productos = df_actual
            df_actual.to_csv(DATA_FILE, index=False)
            st.sidebar.success(f"¡Se asociaron, subieron y guardaron {actualizados} fotos permanentemente en la nube!")
            st.rerun()

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

if busqueda:
    df_filtrado = df_filtrado[
        df_filtrado.get('ARTICULO', pd.Series(['']*len(df_filtrado))).astype(str).str.lower().str.contains(busqueda.lower()) |
        df_filtrado.get('DESCRIPSION', pd.Series(['']*len(df_filtrado))).astype(str).str.lower().str.contains(busqueda.lower())
    ]

if filtro_categoria != "Todas":
    df_filtrado = df_filtrado[df_filtrado['CATEGORIA'] == filtro_categoria]

if filtro_marca != "Todas" and 'MARCA' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['MARCA'].astype(str) == filtro_marca]

# --- BOTÓN DE DESCARGA PDF ---
st.markdown("### 📥 Descargar Catálogo")
pdf_bytes = generar_pdf(df_filtrado, nombre_asesor, telefono_activo)
st.download_button(
    label="📄 Descargar Catálogo Filtrado en PDF",
    data=pdf_bytes,
    file_name="catalogo_repuestos_rimar.pdf",
    mime="application/pdf"
)
st.divider()

if df_filtrado.empty:
    st.warning("No se encontraron repuestos con los filtros seleccionados.")

# --- MOSTRAR PRODUCTOS EN CUADRÍCULA ---
cols = st.columns(3)
for i, row in df_filtrado.iterrows():
    with cols[i % 3]:
        original_idx = row.name
        art_val = row.get('ARTICULO', 'S/N')
        
        if modo_admin:
            with st.expander(f"✏️ Editar Artículo: {art_val}"):
                with st.form(f"form_edit_{original_idx}"):
                    nuevo_desc = st.text_input("Descripción", value=str(row.get('DESCRIPSION', '')))
                    nueva_marca = st.text_input("Marca", value=str(row.get('MARCA', '')))
                    nuevo_precio = st.number_input("Precio ($)", value=int(row.get('PRECIO', 0)), step=1000)
                    nueva_foto = st.file_uploader("Cambiar Foto (Opcional)", type=["jpg", "png", "jpeg"], key=f"img_{original_idx}")
                    
                    guardar_btn = st.form_submit_button("Guardar Cambios")
                    if guardar_btn:
                        df.loc[original_idx, 'DESCRIPSION'] = nuevo_desc
                        df.loc[original_idx, 'MARCA'] = nueva_marca
                        df.loc[original_idx, 'PRECIO'] = nuevo_precio
                        df.loc[original_idx, 'CATEGORIA'] = clasificar_repuesto(nuevo_desc)
                        
                        if nueva_foto is not None:
                            res_up = cloudinary.uploader.upload(nueva_foto)
                            df.loc[original_idx, 'IMAGEN'] = res_up.get("secure_url")
                            
                        st.session_state.df_productos = df
                        df.to_csv(DATA_FILE, index=False)
                        st.success("¡Actualizado con éxito!")
                        st.rerun()

        img_url = row.get('IMAGEN', "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400")
        if pd.isna(img_url) or not str(img_url).startswith("http"):
            img_url = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
            
        marca_val = row.get('MARCA', 'GENERICA')
        desc_val = str(row.get('DESCRIPSION', 'Sin descripción'))
        cat_val = row.get('CATEGORIA', 'General')
        precio_num = row.get('PRECIO', 0)
        precio_val = f"${int(precio_num):,}" if pd.notna(precio_num) else "$0"
        
        # --- TARJETA VISUAL PROLIJA ---
        with st.container():
            st.markdown(f"""
                <div class="product-card">
                    <div>
                        <div style="font-size: 0.8em; color: #666; margin-bottom: 4px;">
                            🆔 <b>Art:</b> {art_val} | 🏷️ <b>Marca:</b> {marca_val} | 📂 {cat_val}
                        </div>
                        <div class="product-title">{desc_val}</div>
                        <div style="font-size: 1.1rem; font-weight: bold; color: #0A1628; margin-bottom: 8px;">
                            Precio: {precio_val} <span class="iva-badge">+IVA</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Carga garantizada desde la URL permanente de Cloudinary
            st.image(img_url, use_container_width=True)
            
            mensaje = f"Hola {nombre_asesor}, me interesa adquirir el repuesto *{desc_val}* (Artículo: {art_val}) por un valor de {precio_val} + IVA visto en Repuestos Rimar. ¿Me confirman disponibilidad?"
            url_whatsapp = f"https://wa.me/{telefono_activo}?text={mensaje.replace(' ', '%20')}"

            st.markdown(f"""
                <div style="margin-top: 10px; margin-bottom: 20px;">
                    <a href="{url_whatsapp}" target="_blank" style="display:block;text-align:center;padding:10px 15px;background-color:#25D366;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">💬 Pedir con {nombre_asesor.split()[0]}</a>
                </div>
            """, unsafe_allow_html=True)
            st.divider()

st.markdown("---")
st.markdown("© 2026 **Repuestos Rimar** - Todos los derechos reservados. Contacto General: **+57 350 8258778**")
