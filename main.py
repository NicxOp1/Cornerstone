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
        "Assist Other Service", "Bucket Truck", "Call Back", "Cleaning Sales Opportunity", "Cleaning Services",
        "Drain Cleaning", "Dryer Vent Cleaning", "Electrical Troubleshoot", "Emergency Call", "Fixture Install",
        "Follow Up Phone Call", "Generator Install", "Generator Maintenance", "Handyman Services", "Heating System Maintenance",
        "LED Retrofit", "Miscellaneous", "No Heat", "No Hot Water", "Panel Upgrade", "PERMIT", "Sales Opportunity",
        "Service Upgrade", "Visual Inspection", "Water Treatment Quote"
    ],
    "Job Code": [
        42076309, 48838652, 7182465, 7522441, 5879699,
        48841042, 41950467, 4931845, 39203718, 46387202,
        10750638, 3241224, 395, 3676033, 3576199,
        48339970, 29707780, 4356, 393, 396,
        41106945, 399, 10749604, 3719556, 48837239,
        2199172, 391, 39164700, 39164743, 397, 3297029,
        394, 3077, 38049409, 48988302
    ],
    "Business Units": [
        "MA - Electrical, NH - Electrical", "HVAC Repair/Service", "HVAC Install", "NE - Cleaning Services", "NE - Plumbing",
        "HVAC Install", "HVAC Repair/Service", "HVAC Install", "HVAC Install", "NE - Plumbing",
        "Other", "Other", "Other", "NE - Cleaning Services", "NE - Cleaning Services",
        "NE - Plumbing", "NE - Cleaning Services", "MA - Electrical, NH - Electrical", "Other", "NE - Handyman Services",
        "Other", "Other", "Other", "NE - Handyman Services", "HVAC Repair/Service",
        "MA - Electrical, NH - Electrical", "Other", "HVAC Repair/Service", "HVAC Repair/Service", "MA - Electrical, NH - Electrical", "Other",
        "Other", "Other", "Other", "NE - Plumbing"
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

def check_availability(request):
    PO_BOX_SALEM = (42.775, -71.217)
    R = 3958.8
    # Acceso a los atributos del objeto request usando la notación de punto
    address = f"{request.locations.address.street}, {request.locations.address.city}, {request.locations.address.country}"
    
    if not address:
        return {"error": "La dirección no es válida."}
    
    # URL de la API geocode.xyz con la autenticación
    url = f"https://geocode.xyz/{address}?json=1&auth=459731876914636430370x45609"

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

    print(distance)

    if distance > 50:
        return {"error": "No hay disponibilidad de servicios en la zona."}
    
    # Obtener los servicios disponibles en la zona
    distance_category = get_distance_category(distance)
    print (distance_category)

    # Obtener los servicios disponibles en la dirección
    direction = get_direction(PO_BOX_SALEM, (lat, lon))
    print(direction)

    return distance

async def validate_available_slots(start_time: str, end_time: str):
    """
    Validates if there are available slots on the day of the given start time (from 7:00 AM to 4:00 PM in the Salem, New Hampshire timezone).
    :param start_time: Start date and time in ISO format (Example: '2025-01-29T08:00:00Z')
    :param end_time: End date and time in ISO format (Example: '2025-01-29T08:30:00Z')
    """
    try:
        print(f"Validating available slots for the day of {start_time}...")

        # The API doesn't filter correctly, so we will filter manually after receiving the data
        url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/appointments?status=Scheduled&status=Dispatched&status=Working&pageSize=2000"

        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers)
        print(f"Available slots response status: {response.status_code}")

        if response.status_code == 200:
            bookings = response.json()

            # Convert `start_time` to a UTC datetime object
            start_dt_utc = datetime.fromisoformat(start_time.replace("Z", "+00:00")).replace(tzinfo=pytz.utc)

            # Convert the start time from UTC to Salem's Eastern Time timezone
            start_dt_local = start_dt_utc.astimezone(EASTERN_TIME)

            # Manually filter the appointments that occur within the requested range (00:00 to 23:59 of the day in the local Salem timezone)
            slots = [
                {"start": appt["start"], "end": appt["end"]}
                for appt in bookings.get("data", [])
                if start_dt_local.date() == datetime.fromisoformat(appt["start"].replace("Z", "+00:00")).astimezone(EASTERN_TIME).date()
            ]

            # Convert the `start` and `end` dates to "YYYY-MM-DD HH:MM" format
            formatted_slots = {
                "start": [
                    datetime.fromisoformat(slot["start"].replace("Z", "+00:00")).astimezone(EASTERN_TIME).strftime("%Y-%m-%d %H:%M")
                    for slot in slots
                ],
                "end": [
                    datetime.fromisoformat(slot["end"].replace("Z", "+00:00")).astimezone(EASTERN_TIME).strftime("%Y-%m-%d %H:%M")
                    for slot in slots
                ]
            }

            # Filter the slots between 7:00 AM and 4:00 PM
            filtered_slots = [
                {"start": start, "end": end}
                for start, end in zip(formatted_slots["start"], formatted_slots["end"])
                if START_HOUR <= datetime.strptime(start, "%Y-%m-%d %H:%M").time() <= END_HOUR
            ]

            # Sort the slots by start date (ascending)
            sorted_slots = sorted(filtered_slots, key=lambda x: x["start"])

            # Display the sorted result
            sorted_start = [slot["start"] for slot in sorted_slots]
            sorted_end = [slot["end"] for slot in sorted_slots]

#           print(f"Sorted available slots for {start_dt_local.date()}:")
#           print(f"Start: {sorted_start}")
#           print(f"End: {sorted_end}") 
            print("Available slots validated successfully.")
            return [{"possible_times":possible_times,"start":sorted_start,"end":sorted_end}]  # Return the sorted slots

        else:
            print(f"Error fetching bookings: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching bookings")
    except Exception as e:
        print(f"Exception while validating available slots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def check_slot_availability(response_data, data_time: str) -> str:
    """
    Verifica si el horario en 'data_time' está en los slots disponibles.

    :param response_data: Diccionario con la respuesta de los slots disponibles o un JSON en string.
    :param data_time: Fecha y hora en formato ISO con UTC (Ejemplo: "2025-01-29T10:00:00Z").
    :return: Mensaje indicando si hay un conflicto o si se puede reservar.
    """
    try:
        # 🛑 Si response_data es un string JSON, convertirlo a diccionario
        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)  # Convertir string JSON a dict
            except json.JSONDecodeError:
                return "Error: Invalid JSON response format."

        # 🛑 Validar que response_data sea un diccionario
        if not isinstance(response_data, dict):
            return "Error: response_data is not a valid dictionary."

        # 🛑 Verificar si "message" es un string en lugar de un diccionario con "slots"
        if isinstance(response_data.get("message"), str):
            return response_data["message"]  # Si es un string, lo devolvemos directamente

        # 📌 Convertir data_time a un objeto datetime en UTC
        data_dt_utc = datetime.fromisoformat(data_time.replace("Z", "+00:00")).replace(tzinfo=pytz.utc)

        # 📌 Convertir data.time a Eastern Time
        data_dt_et = data_dt_utc.astimezone(EASTERN_TIME)

        # 📌 Extraer la hora en formato HH:MM
        data_hour = data_dt_et.strftime("%H:%M")

        # 📌 Obtener la lista de slots disponibles de forma segura
        available_slots = response_data.get("message", {}).get("slots", [])

        # 📌 Verificar si la hora convertida está en los slots disponibles
        if data_hour in available_slots:
            return "No conflict, you can book."
        else:
            return response_data["message"]["response"]

    except Exception as e:
        return f"Error processing availability check: {str(e)}"

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

""" url:  """
""" {
  "name": "John Tester",
  "type": "Residential",
  "locations": {
    "name": "Home",
    "address": {
      "street": "1003 W Clark St",
      "city": "Urbana",
      "zip": "61801"
    }
  }
}
 """


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

        # Obtener las coordenadas y validar disponibilidad
        availability_info = await check_availability(data)
        if "error" in availability_info:
            print(availability_info["error"])
            print("check 1")
            return availability_info  # Si hay un error, devolverlo directamente
        # Validate technician availability
        start_time = datetime.fromisoformat(data.time.replace("Z", "+00:00")).isoformat()
        end_time = (datetime.fromisoformat(data.time.replace("Z", "+00:00")) + timedelta(hours=3)).isoformat()

        # Validate available slots
        info = await validate_available_slots(start_time, end_time)
        # Check availability
        res = check_availability(info)
        print(f"data of res: {res}")
        print("check 2")
        return check_slot_availability(res,data.time)

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