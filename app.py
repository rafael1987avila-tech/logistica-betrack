import streamlit as st
import easyocr
from PIL import Image
import numpy as np

st.set_page_config(page_title="BeTrack Línea a Línea", layout="centered")
st.title("🚚 Extractor de Rutas")

@st.cache_resource
def load_reader():
    return easyocr.Reader(['es'])

reader = load_reader()

archivo = st.file_uploader("Sube la captura de BeTrack", type=["jpg", "png", "jpeg"])

if archivo:
    img = Image.open(archivo)
    ancho, alto = img.size
    
    # Recorte para eliminar la barra superior (hora, batería)
    img_recortada = img.crop((0, int(alto * 0.08), ancho, alto))
    img_np = np.array(img_recortada)
    
    st.image(img_recortada, caption="Captura analizada", use_container_width=True)
    
    with st.spinner("Separando direcciones..."):
        # CAMBIO CLAVE: paragraph=False para que no junte el nombre con la calle
        resultados = reader.readtext(img_np, paragraph=False)
        
        detecciones_sucias = []
        basura_tecnica = ["4G", "LTE", "VOLTE", "%", "VO))", "BAT"]

        for res in resultados:
            texto = res[1].upper().strip()
            
            # Filtros para descartar lo que NO es dirección
            es_pedido = texto.startswith("4000")
            es_telefono = (texto.startswith("9") and len(texto) >= 9)
            es_barra = any(b in texto for b in basura_tecnica)
            
            # Solo nos interesan líneas que tengan algún número (numeración de casa)
            tiene_numero = any(char.isdigit() for char in texto)

            if tiene_numero and not es_pedido and not es_telefono and not es_barra and len(texto) > 4:
                # Limpieza rápida de basura
                limpio = texto.replace(";", "").replace("|", "").strip()
                if limpio not in detecciones_sucias:
                    detecciones_sucias.append(limpio)

    if detecciones_sucias:
        st.subheader("📍 Selecciona solo las direcciones:")
        finales = []
        
        for i, d in enumerate(detecciones_sucias):
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                # Aquí verás el texto tal cual salió, sin recortes raros
                editada = st.text_input(f"Línea detectada {i+1}", value=d, key=f"in_{i}")
            with col2:
                # Solo marcamos por defecto las que tienen nombres de calles probables
                palabras_viales = ["CALLE", "PASAJE", "PSJE", "AV.", "CAMINO", "RINCONADA", "HIPODROMO", "SANTA", "PIRAMIDE", "FONTOVA"]
                es_calle_probable = any(v in d for v in palabras_viales)
                
                ok = st.checkbox("OK", value=es_calle_probable, key=f"ch_{i}")
            
            if ok:
                finales.append(editada)
        
        if finales:
            st.divider()
            comuna = st.text_input("Comuna base:", value="Huechuraba")
            puntos_ruta = "/".join([f"{f}, {comuna}, Chile" for f in finales])
            # Link para abrir la lista de edición de paradas directamente
            url_maps = f"https://www.google.com/maps/dir//{puntos_ruta}"
            
            st.success("¡Listo! Arrastra las paradas en Maps para optimizar.")
            st.link_button("🚀 ABRIR EN MAPS", url_maps)

if st.button("Limpiar Pantalla"):
    st.rerun()