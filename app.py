import streamlit as st
import pandas as pd
import os
import zipfile
import re
import shutil
import cloudinary
import cloudinary.uploader
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# CONFIGURACIÓN OFICIAL DE CLOUDINARY
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

# Estilos CSS avanzados
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
h1, h2, h3 { color: #0A1628; }
.stButton>button { background-color: #E31E24; color: white; font-weight: bold; width: 100%; border-radius: 6px; }
.btn-volver>button { background-color: #6c757d !important; color: white !important; }
.iva-badge { background-color: #FFC107; color: #0A1628; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 6px; }
.product-card { background-color: white; border: 1px solid #e0e0e0; border-radius: 10px; padding: 16px; margin-bottom: 20px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 6px rgba(0,0,0,0.04); height: 100%; }
.product-title { font-size: 0.95rem; font-weight: bold; color: #0A1628; height: 44px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# Lógica del estado del Carrito de Compras
if "carrito" not in st.session_state:
    st.session_state.carrito = []

DATA_FILE = "inventario_rimar.csv"
LOGO_FILE = "logo_rimar.png"
TEMP_ZIP_DIR = "temp_zip_images"
os.makedirs(TEMP_ZIP_DIR, exist_ok=True)

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

df = cargar_datos()

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
    estilo_titulo = ParagraphStyle('TituloPDF', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0A1628'), alignment=1)
    estilo_sub = ParagraphStyle('SubTituloPDF', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#555555'), alignment=1)
    estilo_celda = ParagraphStyle('CeldaPDF', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#333333'))
    
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
        
    tabla = Table(datos_tabla, colWidths=[60, 235, 75, 90, 80])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0A1628')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
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
    st.image(logo_url, width=120)

with col_titulo:
    st.title("Repuestos Rimar - Catálogo Digital")
    st.markdown("**Confianza que mueve tu motor** | Repuestos que rinden.")

st.divider()

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

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False

if not st.session_state.admin_logged:
    password = st.sidebar.text_input("Contraseña de Administrador", type="password")
    if password == "admin123":
        st.session_state.admin_logged = True
        st.rerun()
    elif password != "":
        st.sidebar.error("❌ Contraseña incorrecta")

modo_admin = st.session_state.admin_logged

if modo_admin:
    st.sidebar.success("✅ Acceso concedido como Administrador")
    
    if st.sidebar.button("🔒 Cerrar Sesión Admin"):
        st.session_state.admin_logged = False
        st.rerun()

    pestana_admin = st.sidebar.radio("Opciones de Admin", [
        "Cargar Masivo (Excel/CSV)", 
        "Subida Masiva de Fotos (ZIP Permanente)",
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
                    
                    df_subido['ARTICULO'] = df_subido['ARTICULO'].astype(str)
                    df['ARTICULO'] = df['ARTICULO'].astype(str)
                    
                    df_combinado = pd.concat([df, df_subido]).drop_duplicates(subset=['ARTICULO'], keep='last').reset_index(drop=True)
                        
                    df_combinado.to_csv(DATA_FILE, index=False)
                    st.sidebar.success("¡Artículos guardados en la base de datos!")
                    st.rerun()
                else:
                    st.sidebar.error("El archivo debe contener: ARTICULO, DESCRIPSION, PRECIO")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

    elif pestana_admin == "Subida Masiva de Fotos (ZIP Permanente)":
        st.sidebar.subheader("Subida Masiva a la Nube")
        st.sidebar.markdown("Sube tu `.zip`. Las fotos se subirán a Cloudinary y se guardarán permanentemente.")
        archivo_zip = st.sidebar.file_uploader("Sube tu archivo ZIP", type=["zip"])
        
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

            actualizados = 0
            for idx, row in df.iterrows():
                art_num = str(row['ARTICULO']).strip()
                art_limpio = re.sub(r'\D', '', art_num)
                
                if art_limpio in mapa_fotos:
                    foto_path = mapa_fotos[art_limpio]
                    try:
                        res = cloudinary.uploader.upload(foto_path, folder="catalogo_rimar")
                        secure_url = res.get("secure_url")
                        df.loc[idx, 'IMAGEN'] = secure_url
                        actualizados += 1
                    except Exception as ex:
                        pass

            df.to_csv(DATA_FILE, index=False)
            st.sidebar.success(f"¡{actualizados} fotos subidas y guardadas en la nube!")
            st.rerun()

    elif pestana_admin == "Cambiar Logo de Empresa":
        st.sidebar.subheader("Actualizar Logo")
        logo_subido = st.sidebar.file_uploader("Sube la imagen de tu logo", type=["png", "jpg", "jpeg"])
        if logo_subido is not None:
            with open(LOGO_FILE, "wb") as f:
                f.write(logo_subido.getbuffer())
            st.sidebar.success("¡Logo actualizado con éxito!")
            st.rerun()

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


# =======================================================
# LÓGICA DE VISTA AMPLIADA (MODAL) Y SUMADOR DE CANTIDADES
# =======================================================
if "detalle_articulo" not in st.session_state:
    st.session_state.detalle_articulo = None

if st.session_state.detalle_articulo is not None:
    art_sel = st.session_state.detalle_articulo
    fila_match = df[df['ARTICULO'].astype(str) == str(art_sel)]
    
    if not fila_match.empty:
        prod = fila_match.iloc[0]
        
        # Botón superior con "X" para cerrar y volver
        st.markdown('<div class="btn-volver">', unsafe_allow_html=True)
        if st.button("❌ CERRAR VISTA Y VOLVER AL CATÁLOGO"):
            st.session_state.detalle_articulo = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
                
        st.markdown("---")
        
        c1, c2 = st.columns([1, 1], gap="large")
        with c1:
            img_detalle = prod.get('IMAGEN', "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400")
            if pd.isna(img_detalle) or not str(img_detalle).startswith("http"):
                img_detalle = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
            
            # HTML COMPACTADO PARA EVITAR CONFLICTOS DE MARKDOWN
            html_img_detalle = f"""<div style="height: 400px; border: 1px solid #ddd; border-radius: 8px; display: flex; justify-content: center; align-items: center; background-color: #fff; overflow: hidden;"><img src="{img_detalle}" style="max-width: 100%; max-height: 100%; object-fit: contain;"></div>"""
            st.markdown(html_img_detalle, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"## 🆔 Artículo: {prod.get('ARTICULO')}")
            st.markdown(f"### 🏷️ Marca: {prod.get('MARCA', 'GENERICA')}")
            st.markdown(f"### 📂 Categoría: {prod.get('CATEGORIA', 'General')}")
            st.markdown(f"**Descripción detallada:**\n\n {prod.get('DESCRIPSION')}")
            
            precio_unit = prod.get('PRECIO', 0)
            precio_fmt = f"${int(precio_unit):,}" if pd.notna(precio_unit) else "$0"
            st.markdown(f"### Precio Unitario: {precio_fmt} <span class='iva-badge'>+IVA</span>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### 🔢 Selecciona la cantidad:")
            
            cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1, label_visibility="collapsed")
            
            precio_total = int(precio_unit) * cantidad if pd.notna(precio_unit) else 0
            precio_total_fmt = f"${precio_total:,}"
            
            st.markdown(f"**Subtotal ({cantidad} unidad/es):** `{precio_total_fmt} +IVA`")
            
            desc_text = str(prod.get('DESCRIPSION'))
            art_code = str(prod.get('ARTICULO'))

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button(f"🛒 Agregar {cantidad} unidad(es) al Carrito", type="primary", use_container_width=True):
                st.session_state.carrito.append({
                    'articulo': art_code,
                    'descripcion': desc_text,
                    'cantidad': cantidad,
                    'precio_unitario': int(precio_unit) if pd.notna(precio_unit) else 0,
                    'precio_total': precio_total
                })
                st.session_state.detalle_articulo = None
                st.rerun()

            mensaje_directo = f"Hola {nombre_asesor}, me interesa adquirir {cantidad} unidad(es) del repuesto *{desc_text}* (Artículo: {art_code}) por un valor total de {precio_total_fmt} + IVA visto en Repuestos Rimar. ¿Me confirman disponibilidad?"
            url_wa_directo = f"https://wa.me/{telefono_activo}?text={urllib.parse.quote(mensaje_directo)}"

            html_btn_wa_solo = f"""<div style="margin-top: 10px;"><a href="{url_wa_directo}" target="_blank" style="display:block;text-align:center;padding:10px 20px;background-color:#fff;color:#25D366;border: 2px solid #25D366;text-decoration:none;border-radius:6px;font-weight:bold;font-size:1rem;">💬 O Comprar solo este por WhatsApp</a></div>"""
            st.markdown(html_btn_wa_solo, unsafe_allow_html=True)
            
        st.stop()


# =======================================================
# BARRA SUPERIOR: DESCARGAR PDF Y CARRITO DE COMPRAS
# =======================================================
col_pdf, col_cart = st.columns([1, 1])

with col_pdf:
    st.markdown("### 📥 Descargar Catálogo")
    pdf_bytes = generar_pdf(df_filtrado, nombre_asesor, telefono_activo)
    st.download_button(
        label="📄 Descargar Catálogo Filtrado en PDF",
        data=pdf_bytes,
        file_name="catalogo_repuestos_rimar.pdf",
        mime="application/pdf"
    )

with col_cart:
    st.markdown("### 🛒 Mi Carrito de Compras")
    if len(st.session_state.carrito) == 0:
        st.info("Tu carrito está vacío. ¡Agrega repuestos desde el catálogo!")
    else:
        total_items = sum(item['cantidad'] for item in st.session_state.carrito)
        total_pedido = sum(item['precio_total'] for item in st.session_state.carrito)
        
        st.markdown(f"**Has seleccionado:** {total_items} artículos")
        st.markdown(f"**Total Acumulado:** <span style='font-size:1.2rem;font-weight:bold;color:#0A1628;'>${total_pedido:,}</span> <span class='iva-badge'>+IVA</span>", unsafe_allow_html=True)
        st.markdown(f"**Asesor de Venta:** {nombre_asesor}")
        
        c_enviar, c_vaciar = st.columns([2, 1])
        with c_enviar:
            mensaje_pedido = f"Hola {nombre_asesor}, me interesa realizar el siguiente pedido del catálogo:\n\n"
            for item in st.session_state.carrito:
                mensaje_pedido += f"👉 {item['cantidad']}x [Art: {item['articulo']}] {item['descripcion']} - Subtotal: ${item['precio_total']:,}\n"
            mensaje_pedido += f"\n*💰 Total a pagar:* ${total_pedido:,} + IVA\n\n¿Me confirmas disponibilidad?"
            url_wa_carrito = f"https://wa.me/{telefono_activo}?text={urllib.parse.quote(mensaje_pedido)}"
            
            st.markdown(f"""<a href="{url_wa_carrito}" target="_blank" style="display:block;text-align:center;padding:10px;background-color:#25D366;color:white;text-decoration:none;border-radius:6px;font-weight:bold;">✅ Enviar Pedido por WhatsApp</a>""", unsafe_allow_html=True)
        
        with c_vaciar:
            if st.button("🗑️ Vaciar Carrito"):
                st.session_state.carrito = []
                st.rerun()

st.divider()

if df_filtrado.empty:
    st.warning("No se encontraron repuestos con los filtros seleccionados.")

# --- CUADRÍCULA ORDENADA Y ALINEADA ---
lista_productos = df_filtrado.to_dict('records')
num_cols = 3
filas = [lista_productos[i:i + num_cols] for i in range(0, len(lista_productos), num_cols)]

for fila in filas:
    cols = st.columns(num_cols)
    for idx, row in enumerate(fila):
        with cols[idx]:
            art_val = str(row.get('ARTICULO', 'S/N'))
            
            if modo_admin:
                with st.expander(f"✏️ Editar: {art_val}"):
                    with st.form(f"form_edit_{art_val}"):
                        nuevo_desc = st.text_input("Descripción", value=str(row.get('DESCRIPSION', '')))
                        nueva_marca = st.text_input("Marca", value=str(row.get('MARCA', '')))
                        nuevo_precio = st.number_input("Precio ($)", value=int(row.get('PRECIO', 0)), step=1000)
                        nueva_foto = st.file_uploader("Cambiar Foto", type=["jpg", "png", "jpeg"], key=f"img_{art_val}")
                        
                        guardar_btn = st.form_submit_button("Guardar Cambios")
                        if guardar_btn:
                            match_idx = df[df['ARTICULO'].astype(str) == art_val].index
                            if len(match_idx) > 0:
                                i_real = match_idx[0]
                                df.loc[i_real, 'DESCRIPSION'] = nuevo_desc
                                df.loc[i_real, 'MARCA'] = nueva_marca
                                df.loc[i_real, 'PRECIO'] = nuevo_precio
                                df.loc[i_real, 'CATEGORIA'] = clasificar_repuesto(nuevo_desc)
                                
                                if nueva_foto is not None:
                                    res_up = cloudinary.uploader.upload(nueva_foto, folder="catalogo_rimar")
                                    df.loc[i_real, 'IMAGEN'] = res_up.get("secure_url")
                                    
                                df.to_csv(DATA_FILE, index=False)
                                st.success("¡Actualizado en la nube!")
                                st.rerun()

            img_url = row.get('IMAGEN', "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400")
            if pd.isna(img_url) or not str(img_url).startswith("http"):
                img_url = "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
                
            marca_val = row.get('MARCA', 'GENERICA')
            desc_val = str(row.get('DESCRIPSION', 'Sin descripción'))
            cat_val = row.get('CATEGORIA', 'General')
            precio_num = row.get('PRECIO', 0)
            precio_val = f"${int(precio_num):,}" if pd.notna(precio_num) else "$0"
            
            # --- TARJETA COMPACTA HTML PARA EVITAR ERRORES DE MARKDOWN ---
            html_tarjeta_catalogo = f"""<div class="product-card"><div style="font-size: 0.75em; color: #666; margin-bottom: 4px;">🆔 <b>Art:</b> {art_val} | 🏷️ <b>Marca:</b> {marca_val} | 📂 {cat_val}</div><div class="product-title">{desc_val}</div><div style="height: 200px; display: flex; justify-content: center; align-items: center; overflow: hidden; margin-bottom: 15px; border-radius: 8px; background-color: #ffffff;"><img src="{img_url}" style="max-width: 100%; max-height: 100%; object-fit: contain;"></div><div style="font-size: 1.05rem; font-weight: bold; color: #0A1628; margin-bottom: 10px; text-align: center;">{precio_val} <span class="iva-badge">+IVA</span></div></div>"""
            
            st.markdown(html_tarjeta_catalogo, unsafe_allow_html=True)
            
            if st.button("🔍 Ver Detalle y Comprar", key=f"btn_det_cat_{art_val}"):
                st.session_state.detalle_articulo = art_val
                st.rerun()

st.markdown("---")
st.markdown("© 2026 **Repuestos Rimar** - Todos los derechos reservados. Contacto General: **+57 350 8258778**")
