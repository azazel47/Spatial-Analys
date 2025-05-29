import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(layout="wide")
st.title("📌 Aplikasi Overlay Tata Ruang")

# === Load Shapefile Tata Ruang (dari folder repository) ===
SHAPEFILE_DIR = "shapefile_tataruang"  # folder di dalam repo

if not os.path.exists(SHAPEFILE_DIR):
    st.error("Folder shapefile_tataruang tidak ditemukan. Pastikan shapefile sudah disediakan di repository.")
else:
    try:
        gdf_tataruang = gpd.read_file(SHAPEFILE_DIR)
        atribut_list = list(gdf_tataruang.columns)
        atribut_overlay = st.sidebar.selectbox("Pilih atribut untuk overlay:", atribut_list)
        st.success("Shapefile tata ruang berhasil dimuat dari repository.")
    except Exception as e:
        st.error(f"Gagal memuat shapefile dari folder: {e}")
        gdf_tataruang = None
        atribut_overlay = None

# === Upload Excel Koordinat ===
st.sidebar.header("Upload Excel Koordinat")
excel_file = st.sidebar.file_uploader("Upload Excel berisi id, bujur, lintang", type=["xlsx"])

if excel_file and gdf_tataruang is not None:
    try:
        df_excel = pd.read_excel(excel_file)
        if not set(["id", "bujur", "lintang"]).issubset(df_excel.columns):
            st.error("Kolom wajib: id, bujur, lintang tidak ditemukan.")
        else:
            # Buat GeoDataFrame dari titik koordinat
            geometry = [Point(xy) for xy in zip(df_excel.bujur, df_excel.lintang)]
            gdf_excel = gpd.GeoDataFrame(df_excel, geometry=geometry, crs="EPSG:4326")

            # Pastikan CRS sama
            gdf_tataruang = gdf_tataruang.to_crs("EPSG:4326")

            # Lakukan spatial join
            join_result = gpd.sjoin(gdf_excel, gdf_tataruang, how="left", predicate="within")
            hasil = join_result[["id", "bujur", "lintang", atribut_overlay]]

            st.subheader("🗺️ Peta Overlay")
            m = folium.Map(location=[df_excel.lintang.mean(), df_excel.bujur.mean()], zoom_start=10)
            folium.GeoJson(gdf_tataruang).add_to(m)
            for _, row in hasil.iterrows():
                popup = f"ID: {row['id']}<br>{atribut_overlay}: {row[atribut_overlay]}"
                folium.Marker([row["lintang"], row["bujur"]], popup=popup).add_to(m)

            st_data = st_folium(m, width=900, height=500)

            st.subheader("📄 Hasil Overlay")
            st.dataframe(hasil)

            # Unduh hasil
            csv = hasil.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh Hasil CSV", csv, "hasil_overlay.csv", "text/csv")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses: {e}")

elif excel_file:
    st.warning("Shapefile tata ruang belum berhasil dimuat.")
