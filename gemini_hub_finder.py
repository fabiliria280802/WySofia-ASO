import requests
import numpy as np
from google import genai

GOOGLE_PLACES_API_KEY = ""
GENAI_API_KEY = ""

# COORDENADAS DE LOS EXTREMOS DE QUITO (puede ser cualquier ciudad) (cuadrícula de 5 km)
lat_min, lat_max = -0.35, -0.10  # Latitud
lon_min, lon_max = -78.60, -78.35  # Longitud

# Dividimos Quito en una cuadrícula de 5x5 km
num_cuadrantes = 5
latitudes = np.linspace(lat_min, lat_max, num_cuadrantes)
longitudes = np.linspace(lon_min, lon_max, num_cuadrantes)

# Google Places
def obtener_empresas_logisticas(latitud, longitud):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{latitud},{longitud}",
        "radius": 5000,  # Radio de búsqueda en metros (5 km)
        "keyword": "logística transporte distribución",
        "key": GOOGLE_PLACES_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    if "results" in data:
        return len(data["results"])
    return 0

# ⿢ Función para obtener huella de carbono (simulada)
def obtener_huella_carbono(latitud, longitud):
    emisiones_simuladas = np.random.randint(40000, 70000)  # t/año
    return emisiones_simuladas

# API de NASA POWER
def obtener_datos_meteorologicos(latitud, longitud):
    url = (
        f"https://power.larc.nasa.gov/api/temporal/daily/point?"
        f"parameters=T2M,RH2M,WS10M&community=AG&longitude={longitud}&latitude={latitud}"
        f"&format=JSON&start=20250101&end=20250110"
    )
    response = requests.get(url)
    data = response.json()
    try:
        parametros = data["properties"]["parameter"]
        avg_T2M = np.mean(list(parametros["T2M"].values()))
        avg_RH2M = np.mean(list(parametros["RH2M"].values()))
        avg_WS10M = np.mean(list(parametros["WS10M"].values()))
    except (KeyError, ValueError):
        avg_T2M = avg_RH2M = avg_WS10M = None
    return {"avg_T2M": avg_T2M, "avg_RH2M": avg_RH2M, "avg_WS10M": avg_WS10M}

# Función para recolectar todos los datos en cada cuadrante
def encontrar_datos_cuadrantes():
    resultados = []
    for lat in latitudes:
        for lon in longitudes:
            num_empresas = obtener_empresas_logisticas(lat, lon)
            emisiones = obtener_huella_carbono(lat, lon)
            meteorologia = obtener_datos_meteorologicos(lat, lon)
            resultados.append({
                "latitud": lat,
                "longitud": lon,
                "num_empresas": num_empresas,
                "emisiones": emisiones,
                "meteorologia": meteorologia
            })
    return resultados

def decidir_top3_zonas(datos, ciudad="Quito"):

    prompt = "Dada la siguiente información de cuadrantes en {ciudad}, selecciona las 3 mejores ubicaciones para establecer una nueva estación de drones. Considera que se busca maximizar el número de empresas logísticas, la huella de carbono y condiciones meteorológicas favorables. La información de cada cuadrante es:\n\n"
    for d in datos:
        prompt += (
            f"Coordenadas: ({d['latitud']}, {d['longitud']}); "
            f"Empresas: {d['num_empresas']}; "
            f"CO₂: {d['emisiones']} t/año; "
            f"Temperatura promedio: {d['meteorologia']['avg_T2M']:.2f}°C, "
            f"Humedad promedio: {d['meteorologia']['avg_RH2M']:.2f}%, "
            f"Viento promedio: {d['meteorologia']['avg_WS10M']:.2f} m/s.\n"
        )
    prompt += (
        "\nDevuelve solo el top 3 en el siguiente formato exacto:\n"
        "[\n"
        "  {\"latitud\": valor, \"longitud\": valor, \"num_empresas\": valor, \"emisiones\": valor, \"meteorologia\": {\"avg_T2M\": valor, \"avg_RH2M\": valor, \"avg_WS10M\": valor}},\n"
        "  {\"latitud\": valor, \"longitud\": valor, \"num_empresas\": valor, \"emisiones\": valor, \"meteorologia\": {\"avg_T2M\": valor, \"avg_RH2M\": valor, \"avg_WS10M\": valor}},\n"
        "  {\"latitud\": valor, \"longitud\": valor, \"num_empresas\": valor, \"emisiones\": valor, \"meteorologia\": {\"avg_T2M\": valor, \"avg_RH2M\": valor, \"avg_WS10M\": valor}}\n"
        "]\n"
        "No agregues ningún otro texto o explicación."
    )
    
    client = genai.Client(api_key=GENAI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text

def main():
    datos_cuadrantes = encontrar_datos_cuadrantes()
    top3 = decidir_top3_zonas(datos_cuadrantes, ciudad="Quito")
    print(top3)

if __name__ == "__main__":
    main()
