import requests
import numpy as np
import math

# ------------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE APIS Y PARÁMETROS
# ------------------------------------------------------------------------------
GOOGLE_API_KEY = "AIzaSyClK9xTT6YDIyK0Se8RNHpkzXT1PWWrBds"

# Parámetros de filtrado para clima/altitud
TEMP_MIN = 18       # °C
TEMP_MAX = 28       # °C
VIENTO_MAX = 15     # km/h
PRECIPITACION_MAX = 900   # mm
ALTITUD_MAX = 3000        # m

# Rango de búsqueda máximo para Places (10 km)
MAX_RADIO_PLACES = 10000

# Umbrales de negocio
UMBRAL_TIENDAS_RETAIL = 10  # p.ej. "alto volumen" si > 10 tiendas
UMBRAL_LOGISTICAS = 2       # al menos 2 empresas logísticas
# Hospitales/Farmacéuticas: se verifica que haya al menos 1 en 0–5 km

# COORDENADAS DE LOS EXTREMOS DE QUITO (para dividir en ~5 km cada cuadrante)
lat_min, lat_max = -0.35, -0.10
lon_min, lon_max = -78.60, -78.35
num_cuadrantes = 5
latitudes = np.linspace(lat_min, lat_max, num_cuadrantes)
longitudes = np.linspace(lon_min, lon_max, num_cuadrantes)

# ------------------------------------------------------------------------------
# 2. FUNCIONES AUXILIARES
# ------------------------------------------------------------------------------

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos (lat1, lon1) y (lat2, lon2)
    usando la Fórmula de Haversine. Devuelve la distancia en metros.
    """
    R = 6371000  # Radio de la Tierra en metros
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat/2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def buscar_places_en_10km_rangos(lat, lon, keyword=None, place_type=None):
    """
    Hace una búsqueda en Google Places en un radio de 10 km (MAX_RADIO_PLACES).
    - Se pueden usar 'keyword' o 'type'.
    - Retorna un diccionario con:
        {
          'count_0_5': X,  # número de resultados en 0–5 km
          'count_5_10': Y, # número de resultados en 5–10 km
          'count_total': X+Y
        }
    NOTA: Solo maneja la primera página (máx 20 resultados).
    """
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": MAX_RADIO_PLACES,  # 10 km
        "key": GOOGLE_API_KEY
    }
    # Si se especifica 'keyword' o 'type', lo agregamos
    if keyword:
        params["keyword"] = keyword
    if place_type:
        params["type"] = place_type

    response = requests.get(url, params=params)
    data = response.json()
    
    # Contadores
    count_0_5 = 0
    count_5_10 = 0

    if "results" in data:
        for place in data["results"]:
            # Obtenemos la lat/lon del lugar
            if "geometry" in place and "location" in place["geometry"]:
                lat_p = place["geometry"]["location"]["lat"]
                lon_p = place["geometry"]["location"]["lng"]
                # Calculamos distancia a (lat, lon)
                dist_m = haversine_distance(lat, lon, lat_p, lon_p)
                if dist_m <= 5000:
                    count_0_5 += 1
                elif dist_m <= 10000:
                    count_5_10 += 1

    return {
        "count_0_5": count_0_5,
        "count_5_10": count_5_10,
        "count_total": count_0_5 + count_5_10
    }

def obtener_huella_carbono(lat, lon):
    # Simulación
    return np.random.randint(40000, 70000)

def obtener_altitud(lat, lon):
    # Consulta a Google Elevation
    url = "https://maps.googleapis.com/maps/api/elevation/json"
    params = {
        "locations": f"{lat},{lon}",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if "results" in data and len(data["results"]) > 0:
        return data["results"][0]["elevation"]
    # Si no se obtiene altitud, simulamos
    return np.random.uniform(2800, 2900)

def obtener_datos_climaticos(lat, lon):
    # Simulación de datos climáticos
    temperatura_promedio = np.random.uniform(15, 30)
    velocidad_viento = np.random.uniform(0, 20)
    direccion_viento = np.random.uniform(0, 360)
    precipitacion_anual = np.random.uniform(800, 1200)
    return temperatura_promedio, velocidad_viento, direccion_viento, precipitacion_anual

# ------------------------------------------------------------------------------
# 3. FUNCIÓN PRINCIPAL
# ------------------------------------------------------------------------------
def encontrar_mejores_zonas():
    resultados = []
    
    for lat in latitudes:
        for lon in longitudes:
            print(f"Buscando en cuadrante: latitud {lat}, longitud {lon}...")

            # 1. Criterios de clima y altitud
            emisiones = obtener_huella_carbono(lat, lon)
            altitud = obtener_altitud(lat, lon)
            temperatura, viento, direccion, precipitacion = obtener_datos_climaticos(lat, lon)
            
            cumple_clima = (
                TEMP_MIN <= temperatura <= TEMP_MAX and
                viento < VIENTO_MAX and
                precipitacion < PRECIPITACION_MAX and
                altitud is not None and altitud < ALTITUD_MAX
            )
            
            # 2. Búsqueda de hospitales o centros médicos (0-5 km y 5-10 km)
            #    Usamos 'keyword="hospital centro medico"'
            hospitales_data = buscar_places_en_10km_rangos(
                lat, lon, 
                keyword="hospital centro medico"
            )
            
            # 3. Búsqueda de farmacéuticas o laboratorios (0-5 km y 5-10 km)
            #    Usamos 'keyword="farmacia laboratorio"'
            farm_data = buscar_places_en_10km_rangos(
                lat, lon, 
                keyword="farmacia laboratorio"
            )
            
            # 4. Búsqueda de tiendas (retail/e-commerce) con type=store
            retail_data = buscar_places_en_10km_rangos(
                lat, lon, 
                place_type="store"
            )
            
            # 5. Búsqueda de empresas de logística (keyword)
            log_data = buscar_places_en_10km_rangos(
                lat, lon, 
                keyword="logistica transporte distribucion"
            )
            
            # Criterios de negocio:
            # - Hospitales cercanos: al menos 1 en 0-5 km
            # - Farmacéuticas/laboratorios: al menos 1 en 0-5 km
            # - Retail "alto volumen" => > UMBRAL_TIENDAS_RETAIL en 0-10 km
            # - Logísticas => >= UMBRAL_LOGISTICAS en 0-10 km
            cumple_hospitales = (hospitales_data["count_0_5"] >= 1)
            cumple_farmaceuticas = (farm_data["count_0_5"] >= 1)
            cumple_retail = (retail_data["count_total"] > UMBRAL_TIENDAS_RETAIL)
            cumple_logistica = (log_data["count_total"] >= UMBRAL_LOGISTICAS)
            
            cumple_negocios = (
                cumple_hospitales and
                cumple_farmaceuticas and
                cumple_retail and
                cumple_logistica
            )
            
            cumple_todos_criterios = cumple_clima and cumple_negocios
            
            # Impresión de resultados parciales
            alt_str = f"{altitud:.2f} m" if altitud is not None else "No disponible"
            print(f"  Clima -> Temp: {temperatura:.2f}°C, Viento: {viento:.2f} km/h, Precip: {precipitacion:.2f} mm, Alt: {alt_str}")
            print(f"  Hospitales (0-5km): {hospitales_data['count_0_5']}  (5-10km): {hospitales_data['count_5_10']}")
            print(f"  Farmacéuticas (0-5km): {farm_data['count_0_5']}  (5-10km): {farm_data['count_5_10']}")
            print(f"  Retail total (0-10km): {retail_data['count_total']}")
            print(f"  Logísticas total (0-10km): {log_data['count_total']}")
            print(f"  => Cumple clima/altitud: {cumple_clima}, Cumple negocios: {cumple_negocios}, TOTAL: {cumple_todos_criterios}\n")
            
            # Guardamos en la lista de resultados
            resultados.append({
                "latitud": lat,
                "longitud": lon,
                "emisiones": emisiones,
                "altitud": altitud,
                "temperatura": temperatura,
                "viento": viento,
                "direccion_viento": direccion,
                "precipitacion": precipitacion,
                "hospitales_0_5": hospitales_data["count_0_5"],
                "hospitales_5_10": hospitales_data["count_5_10"],
                "farm_0_5": farm_data["count_0_5"],
                "farm_5_10": farm_data["count_5_10"],
                "retail_total": retail_data["count_total"],
                "log_total": log_data["count_total"],
                "cumple_clima": cumple_clima,
                "cumple_negocios": cumple_negocios,
                "cumple_todos_criterios": cumple_todos_criterios
            })
    
    # Filtramos solo los que cumplen todos los criterios
    resultados_filtrados = [r for r in resultados if r["cumple_todos_criterios"]]
    
    # Ordenamos, por ejemplo, priorizando más logística y luego más retail
    mejores_zonas = sorted(
        resultados_filtrados,
        key=lambda x: (x["log_total"], x["retail_total"]),
        reverse=True
    )
    
    print("📍 Las 3 mejores ubicaciones en Quito para una nueva estación de drones (criterios clima, altitud y negocios):")
    for i, zona in enumerate(mejores_zonas[:3]):
        alt_str = f"{zona['altitud']:.2f} m" if zona['altitud'] is not None else "No disponible"
        print(f"{i+1}. Lat: {zona['latitud']}, Lon: {zona['longitud']}")
        print(f"   - Emisiones CO₂: {zona['emisiones']} t/año")
        print(f"   - Altitud: {alt_str}")
        print(f"   - Clima -> Temp: {zona['temperatura']:.2f}°C, Viento: {zona['viento']:.2f} km/h, Precip: {zona['precipitacion']:.2f} mm")
        print(f"   - Hospitales 0-5km: {zona['hospitales_0_5']}, 5-10km: {zona['hospitales_5_10']}")
        print(f"   - Farmacéuticas 0-5km: {zona['farm_0_5']}, 5-10km: {zona['farm_5_10']}")
        print(f"   - Retail total (0-10km): {zona['retail_total']}")
        print(f"   - Logísticas total (0-10km): {zona['log_total']}\n")

# ------------------------------------------------------------------------------
# 4. EJECUTAR ANÁLISIS
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    encontrar_mejores_zonas()
