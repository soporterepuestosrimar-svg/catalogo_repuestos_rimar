import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Repuestos Rimar | Catálogo Digital", page_icon="🚗", layout="wide")

# Estilos personalizados con los colores de Repuestos Rimar
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    h1 {
        color: #0A1628;
    }
    .stButton>button {
        background-color: #E31E24;
        color: white;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado principal
st.title("🚗 Repuestos Rimar - Catálogo Digital")
st.markdown("**Confianza que mueve tu motor** | Explora nuestros repuestos y haz tu pedido directamente con un asesor.")
st.divider()

# Base de datos de productos (puedes editarla o agregar más adelante)
productos = [
    {
        "nombre": "Amortiguador Delantero Ford / Toyota",
        "categoria": "Suspensión",
        "precio": "$180.000",
        "imagen": "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
    },
    {
        "nombre": "Bomba de Agua Jeep / Ram",
        "categoria": "Refrigeración",
        "precio": "$120.000",
        "imagen": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=400"
    },
    {
        "nombre": "Sensor MAP Nissan / Dodge",
        "categoria": "Sensores",
        "precio": "$95.000",
        "imagen": "https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=400"
    },
    {
        "nombre": "Kit de Empaquetadura de Motor",
        "categoria": "Motor",
        "precio": "$210.000",
        "imagen": "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=400"
    }
]

# Barra lateral para filtros
st.sidebar.header("🔍 Filtros de Búsqueda")
busqueda = st.sidebar.text_input("Buscar por repuesto o marca...")

# Filtrar productos según la búsqueda
productos_filtrados = [
    p for p in productos 
    if busqueda.lower() in p["nombre"].lower() or busqueda.lower() in p["categoria"].lower()
]

if not productos_filtrados:
    st.warning("No se encontraron repuestos con ese criterio de búsqueda.")

# Mostrar productos en una cuadrícula de 3 columnas
cols = st.columns(3)
for i, prod in enumerate(productos_filtrados):
    with cols[i % 3]:
        st.image(prod["imagen"], use_container_width=True)
        st.subheader(prod["nombre"])
        st.write(f"**Categoría:** {prod['categoria']}")
        st.write(f"**Precio:** {prod['precio']}")
        
        # Enlace directo a WhatsApp corporativo con mensaje prellenado
        telefono = "573508258778"
        mensaje = f"Hola, me interesa adquirir el producto: {prod['nombre']} ({prod['precio']}) visto en el catálogo digital de Repuestos Rimar. ¿Me confirman disponibilidad?"
        url_whatsapp = f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20')}"
        
        # Botón estilizado de WhatsApp
        st.markdown(
            f'<a href="{url_whatsapp}" target="_blank" style="display:block;text-align:center;padding:10px 15px;background-color:#25D366;color:white;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:10px;">💬 Pedir por WhatsApp</a>',
            unsafe_allow_html=True
        )
        st.divider()

# Pie de página
st.markdown("---")
st.markdown("© 2026 **Repuestos Rimar** - Repuestos que rinden. Contáctanos al **+57 350 8258778**.")
