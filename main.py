from datetime import datetime, date, timedelta, time
from typing import Tuple, Dict
from fastapi import FastAPI, Request, Response, HTTPException
import requests
import utils as utils
import logging
from dotenv import load_dotenv
import os
import json
import pytz
from pydantic import BaseModel
import pandas as pd
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

AUTH_URL_INT = os.getenv("AUTH_URL_INT")
AUTH_URL = os.getenv("AUTH_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
APP_ID = os.getenv("APP_ID")
START_HOUR = time(7, 0)  # 7:00 AM
END_HOUR = time(16, 0)   # 4:00 PM
EASTERN_TIME = pytz.timezone("America/New_York")
MAPS_AUTH= os.getenv("MAPS_AUTH")

possible_times = [
    "07:00",
    "10:00",
    "13:00"
]

app = FastAPI()

# Datos harcodeados

jobs_data = {
    "Job Type": [
        "Outlet Install", "AC Maintanence", "Boiler Install", "Duct Cleaning", "Plumbing Service",
        "HVAC Install", "HVAC Troubleshoot", "Furnace Install", "MiniSplit Install", "Water Treatment",
        "Cleaning Sales Opportunity", "Cleaning Services",
        "Drain Cleaning", "Dryer Vent Cleaning", "Electrical Troubleshoot", "Fixture Install",
        "Handyman Services", "Heating System Maintenance",
        "LED Retrofit", "No Heat", "No Hot Water", "Panel Upgrade", "Water Treatment Quote"
    ],
    "Job Code": [
        42076309, 48838652, 7182465, 7522441, 5879699,
        48841042, 41950467, 4931845, 39203718, 46387202,
        3676033, 3576199,
        48339970, 29707780, 4356, 396,
        3719556, 48837239,
        2199172, 39164700, 39164743, 397, 48988302
    ],
    "Business Units": [
        "MA - Electrical, NH - Electrical", "HVAC Repair/Service", "HVAC Install", "NE - Cleaning Services", "NE - Plumbing",
        "HVAC Install", "HVAC Repair/Service", "HVAC Install", "HVAC Install", "NE - Plumbing",
        "NE - Cleaning Services", "NE - Cleaning Services",
        "NE - Plumbing", "NE - Cleaning Services", "MA - Electrical, NH - Electrical", "NE - Handyman Services",
        "NE - Handyman Services", "HVAC Repair/Service",
        "MA - Electrical, NH - Electrical", "HVAC Repair/Service", "HVAC Repair/Service", "MA - Electrical, NH - Electrical",
        "NE - Plumbing"
    ]
}
jobs_df = pd.DataFrame(jobs_data)

services_by_zone = {
    "Location": [
        "Methuen, MA", "Andover, MA", "North Andover, MA", "Amesbury, MA", "Pelham, MA",
        "Plaistow, MA", "Haverhill, MA", "Newburyport, MA", "Derry, NH", "Londonderry, NH",
        "Hudson, NH", "Windham, NH", "Salem, NH", "Atkinson, NH", "Arlington, MA",
        "Manchester, NH", "Acton, MA", "Concord, NH"
    ],
    "Available Services": [
        ["AC Repair", "AC Installation", "Furnace Repair", "Deep Cleaning", "Electrician", "Handyman Services", "Heat Pumps"],
        ["AC Repair", "AC Installation", "Furnace Repair", "Deep Cleaning", "Electrician", "Handyman Services", "Heat Pumps"],
        ["AC Repair", "AC Installation", "Deep Cleaning", "Electrician", "Handyman Services", "Heat Pumps"],
        ["AC Repair", "AC Installation", "Furnace Repair", "Deep Cleaning", "Electrician", "Handyman Services", "Heat Pumps"],
        ["AC Repair", "AC Installation", "Furnace Repair", "Deep Cleaning", "Electrician", "Handyman Services", "Heat Pumps", "Plumbing"],
        ["AC Repair", "AC Installation", "Furnace Repair", "Deep Cleaning", "Electrician", "Handyman Services", "Heat Pumps", "Plumbing"],
        ["AC Repair", "AC Installation", "Furnace Repair", "Deep Cleaning", "Electrician", "Handyman Services", "Heat Pumps"],
        ["AC Repair", "AC Installation", "Electrician", "Handyman Services", "Heat Pumps"],
        ["AC Repair", "AC Installation", "Electrician", "Handyman Services", "Heat Pumps"],
        ["HVAC Repair", "Plumbing Repair", "Electrical Services", "Home Modifications for Seniors", "Other Services"],
        ["HVAC Repair", "Plumbing Repair", "Electrical Services", "Home Modifications for Seniors", "Other Services"],
        ["HVAC Repair", "Plumbing Repair", "Electrician", "Home Modifications for Seniors", "Other Services"],
        ["HVAC Repair", "Plumbing Repair", "Electrician", "Home Modifications for Seniors", "Other Services"],
        ["Plumbing Services", "HVAC Repair", "Electrician", "Home Modifications for Seniors", "Other Services"],
        ["Electrician"],
        ["Electrician"],
        ["Electrician"],
        ["Electrician"]
    ]
}
services_df = pd.DataFrame(services_by_zone)

# Funciones auxiliares

def get_job_info(job_id):
    # Buscar el índice del Job Code que coincida con el job_id
    if job_id in jobs_data["Job Code"]:
        index = jobs_data["Job Code"].index(job_id)
        
        # Crear un diccionario con la información solicitada
        job_info = {
            "Job Type": jobs_data["Job Type"][index],
            "Job Code": jobs_data["Job Code"][index],
            "Business Units": jobs_data["Business Units"][index]
        }

        return job_info
    else:
        return None

def get_distance_category(distance):
    if 0 <= distance <= 25:
        return "0-25 miles"
    elif 25 < distance <= 50:
        return "25-50 miles"
    else:
        return "Out of range"

def get_direction(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    
    if lat2 > lat1 and lon2 > lon1:
        return "NE"
    elif lat2 > lat1 and lon2 < lon1:
        return "NW"
    elif lat2 < lat1 and lon2 > lon1:
        return "SE"
    elif lat2 < lat1 and lon2 < lon1:
        return "SW"
    else:
        return "Unknown"
    

async def get_access_token():
    try:
        print("Fetching access token...")
        response = requests.post(
            AUTH_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
        )
#        print(f"Token response status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            print("Access token fetched successfully.")
            return token_data.get("access_token")
        else:
            print(f"Error fetching token: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"Authentication failed: {response.text}")
    except Exception as e:
        print(f"Exception while fetching token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get access token: {str(e)}")

async def check_availability(request):
    PO_BOX_SALEM = (42.775, -71.217)
    R = 3958.8
    print("Checking availability...")
    # Comprobar si hay disponibilidad laboral
    job_info = get_job_info(request.jobType)
    print(job_info)
    if job_info is None:
        print("No job found")
        return False
    
    url = f"https://api.servicetitan.io/settings/v2/tenant/{TENANT_ID}/business-units"
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    print(f"Business units response status: {response.status_code}")
    if response.status_code == 200:
        business_units_json = response.json()
        business_units = {unit["name"].strip().lower(): unit["id"] for unit in business_units_json["data"]}

        job_units = job_info["Business Units"].split(",")

        job_units = [unit.strip().lower() for unit in job_units]

        matching_units = [business_units[unit] for unit in job_units if unit in business_units]


    # Acceso a los atributos del objeto request usando la notación de punto
    address = f"{request.locations.address.street}, {request.locations.address.city}, {request.locations.address.country}"
    
    if not address:
        return {"error": "La dirección no es válida."}
    
    # URL de la API geocode.xyz con la autenticación
    url = f"https://geocode.xyz/{address}?json=1&auth={MAPS_AUTH}"

    # Hacer la solicitud GET
    resp = requests.get(url)
        
    # Comprobar si la respuesta es exitosa (200 OK)
    if resp.status_code == 200:
            json_data = resp.json()
    
    # Extraer latitud y longitud
    lat = json_data.get("latt")
    lon = json_data.get("longt")

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return {"error": "Las coordenadas proporcionadas no son válidas."}

    print(lat, lon)

    if lat is None or lon is None:
        return {"error": "No se pudieron obtener las coordenadas de la dirección."}
    
    # Convertir las coordenadas a radianes
    lat1, lon1 = math.radians(PO_BOX_SALEM[0]), math.radians(PO_BOX_SALEM[1])
    lat2, lon2 = math.radians(lat), math.radians(lon)

    # Diferencia entre las coordenadas
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    # Fórmula de Haversine
    a = math.sin(delta_lat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distancia en millas
    distance = round(R * c, 2)

    if distance > 50:
        return {"error": "No hay disponibilidad de servicios en la zona."}
    
    # Obtener los servicios disponibles en la zona
    distance_category = get_distance_category(distance)

    # Obtener los servicios disponibles en la dirección
    direction = get_direction(PO_BOX_SALEM, (lat, lon))

    result = {
        "JobCode": job_info["Job Code"],
        "MatchingUnits": matching_units
    }

    return result

async def create_customer(customer: utils.CustomerCreateRequest) -> Tuple[str, str]:
    print(f"{customer},datos de cliente")
    url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers"

    # Replace these placeholders with actual token and app key
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        customer.locations.address.country = "USA"
        customer.locations.address.state = "SC"
        payload = customer.model_dump(by_alias=True)
        payload["locations"] = [payload["locations"]]
        payload["address"] = customer.locations.address.model_dump()
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            customer_id = data.get("id")
            location_id = data.get("locations")[0].get("id")
            return (customer_id, location_id)
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to create customer: {response.text}",
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

def filter_availabilities(availabilities):
    """Filters the time slots where at least one technician is available."""
    available_slots = []

    for slot in availabilities:
        if slot["isAvailable"]:
            available_technicians = [
                {"id": tech["id"], "name": tech["name"]}
                for tech in slot["technicians"]
                if tech["status"] == "Available"
            ]

            if available_technicians:
                available_slots.append({
                    "slot": f"{slot['startUtc']} - {slot['endUtc']}",
                    "available_technicians": available_technicians
                })
    return available_slots

def transform_availabilities(available_slots):
    """Transforms the available slots to return only the first technician and the slot time."""
    transformed_slots = []

    for slot in available_slots:
        # Get the start time of the slot (in the desired format) and the first technician
        start_time = slot["slot"].split("T")[1].split("Z")[0] + "Z"  # Extracts the time portion
        technician = slot["available_technicians"][0]  # Get the first technician

        # Append the transformed slot
        transformed_slots.append({
            "slot": start_time,
            "id": technician["id"]
        })

    return transformed_slots

async def check_technician_availability(request, time):
    print("Checking technician availability...")
    
    # Convertir la fecha del path a formato ISO (YYYY-MM-DD)
    try:
        start_date = datetime.strptime(time[:10], "%Y-%m-%d")
    except ValueError:
        return json.dumps({"error": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD."}, indent=4)


    # Mantener la hora constante
    starts = start_date.strftime("%Y-%m-%dT06:08:31Z")
    ends = (start_date + timedelta(days=1)).strftime("%Y-%m-%dT06:08:31Z")

    url = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity"
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    body = {
        "startsOnOrAfter": starts,
        "endsOnOrBefore": ends,
        "businessUnitIds": [request["MatchingUnits"][0]],
        "jobTypeId": request["JobCode"],
        "skillBasedAvailability": True,
        "args": []
    }

    # Realizar la solicitud POST
    response = requests.post(url, headers=headers, json=body)
    
    print(f"API response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        available_slots = filter_availabilities(data.get("availabilities", []))
        response = transform_availabilities(available_slots)
        return json.dumps(response, indent=4)  # Retorna la disponibilidad formateada
    else:
        print("Error en la solicitud:", response.status_code, response.text)
        return json.dumps({"error": "Failed to fetch availability"}, indent=4)

@app.get("/")
def read_root():
    print("Root endpoint accessed.")
    return {"status": "Service is up"}

@app.post("/create_customer")
async def create_customer(customer: utils.CustomerCreateRequest):
    """
    Endpoint para crear un cliente en ServiceTitan.
    """
    try:
        logger.info("Recibida solicitud para crear un cliente.")

        # ✅ Convertir el objeto `customer` a diccionario
        customer_data = customer.model_dump()
        logger.info(f"Datos recibidos para el cliente: {customer_data}")

        # ✅ `locations` ya es una lista, no hace falta procesar como objeto único
        locations = customer_data.get("locations", [])

        if not locations:
            raise HTTPException(status_code=400, detail="Missing 'locations' data in request.")

        # ✅ Obtener PRIMERA ubicación (ServiceTitan parece requerir una sola)
        location_data = locations[0]

        # ✅ Construir el payload correctamente
        payload = {
            "name": customer_data["name"],
            "type": customer_data.get("type", "Residential"),
            "locations": locations,  # ✅ Ya es una lista válida
            "address": customer_data.get("address", {})  # ✅ Agregar address separado
        }

        # ✅ Hacer la petición a ServiceTitan para crear el cliente
        url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=payload)
        logger.info(f"Response de ServiceTitan: {response.status_code} - {response.text}")

        if response.status_code == 200:
            data = response.json()
            return {
                "message": "Customer created successfully.",
                "customer_id": data.get("id"),
                "location_id": data["locations"][0]["id"] if "locations" in data else None
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ServiceTitan error: {response.text}"
            )

    except Exception as e:
        logger.error(f"Error al procesar la solicitud: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-job/")
async def create_job(job_request: utils.jobCreateToolRequest):
    job_request = job_request.args  # Extraer argumentos correctamente

    url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
    access_token = await get_access_token()

    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        # ✅ CREAR EL CLIENTE Y OBTENER SU ID
        customer_response = await create_customer(job_request.customer)

        # ✅ Extraer los IDs correctamente de la respuesta
        customer_id = customer_response["customer_id"]
        location_id = customer_response["location_id"]

        # ✅ Construir el payload correctamente
        payload = {
            "customerId": customer_id,
            "locationId": location_id,
            "jobTypeId": job_request.jobTypeId,  # ID del tipo de trabajo
            "priority": job_request.priority,  # Prioridad
            "businessUnitId": job_request.businessUnitId,  # Unidad de negocio
            "campaignId": job_request.campaignId,  # Campaña
            "appointments": [
                {
                    "start": job_request.jobStartTime,
                    "end": job_request.jobEndTime,
                    "arrivalWindowStart": job_request.jobStartTime,
                    "arrivalWindowEnd": job_request.jobEndTime,
                }
            ],
            "scheduledDate": datetime.now().strftime("%Y-%m-%d"),
            "scheduledTime": datetime.now().strftime("%H:%M"),
            "summary": "Plumbing Inspection",
        }

        # ✅ ENVIAR LA PETICIÓN A SERVICE TITAN
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return {"status": "Job request booked", "job_id": response.json().get("id")}
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"External API call failed with status code {response.status_code}: {response.text}",
            )
    
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"HTTP error occurred: {http_err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {err}",
        )

@app.post("/checkAvilability")
async def booking_request(data: utils.BookingRequest):

    try:
        print("Processing booking request...")
        print(f"Request data: {data}")

        job_info = await check_availability(data)
        if "error" in job_info:
            print(job_info["error"])
            return job_info
    
        print(job_info)

        tech_info = await check_technician_availability(job_info, data.time)
        print(tech_info)
        return tech_info
    
    except Exception as e:
        print(f"Exception while processing booking request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_time")
async def get_current_utc_time():
    utc_now = datetime.now(pytz.utc)
    return utc_now.strftime("%Y-%m-%dT%H:%M:%SZ")



#dowload fastapi: pip install "fastapi[standard]"
#dowload dotenv: pip install python-dotenv (may come pre-installed in newer Python versions)
#dowload pytz: pip install pytz
#start the server: fastapi dev main.py