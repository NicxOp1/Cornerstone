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

print("funciono")

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

def check_availability(ScheduleData : utils.ScheduleData):
    print("Checking availability...")
    # Hardcoded values
    overlap_threshold = 8
    slot_duration = "03:00"

    # Extract the data from the request body
    print(ScheduleData)
    body = ScheduleData

    # Process the data (you can use the logic from your existing file)
    available_times = body[0]["possible_times"]
    # Initialize lists to store all busy start and end times
    busy_start_times = []
    busy_end_times = []
    # Iterate through each schedule data
    for schedule in body:
        busy_start_times.extend(schedule["start"])
        busy_end_times.extend(schedule["end"])

#    print(f"available_times: {available_times}")
#    print(f"busy_start_times: {busy_start_times}")
#    print(f"busy_end_times: {busy_end_times}")

    # Convert busy times to datetime objects
    busy_start_times = [
        datetime.strptime(time, "%Y-%m-%d %H:%M") for time in busy_start_times
    ]
    busy_end_times = [
        datetime.strptime(time, "%Y-%m-%d %H:%M") for time in busy_end_times
    ]

    # Function to check for overlap
    def count_overlaps(slot_start, slot_end):
        overlap_count = 0
        for busy_start, busy_end in zip(busy_start_times, busy_end_times):
            # Check if the slot overlaps with any busy time
            if slot_start < busy_end and slot_end > busy_start:
                overlap_count += 1
        return overlap_count

    # Get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Convert available times to datetime
    available_times_dt = [
        datetime.strptime(f"{current_date} {t}", "%Y-%m-%d %H:%M")
        for t in available_times
    ]
    # Prioritize times ending in ":00", then ":30", then ":15"
    priority_order = {":00": 1, ":30": 2, ":15": 3, ":45": 4}
    sorted_times = sorted(available_times_dt,
                        key=lambda t: priority_order[t.strftime(":%M")])
    # Calculate overlap for each slot
    slot_overlaps = {}
    for slot_start in sorted_times:
        slot_end = slot_start + timedelta(
            hours=int(slot_duration.split(":")[0]),
            minutes=int(slot_duration.split(":")[1]))
        overlap_count = count_overlaps(slot_start, slot_end)
        slot_overlaps[slot_start.strftime("%H:%M")] = overlap_count

    print(f"slot_overlaps: {slot_overlaps}")

    # Filter out slots with overlap greater than 1
    filtered_slots = [slot for slot, overlap in slot_overlaps.items() if overlap <= overlap_threshold]
    # Sort the filtered slots by time
    sorted_slots = sorted(filtered_slots, key=lambda item: priority_order[f":{item.split(':')[1]}"])
    valid_slots = sorted_slots[:2]

    print(f"sorted_slots: {sorted_slots}")
    print(f"valid_slots: {valid_slots}")

    # Format the response
    if valid_slots:
        response = {
        "response": f"The available time slots for this day are: {sorted_slots}.",
        "slots": sorted_slots  # Guarda los sorted_slots en la clave "slots"
        }
    else:
        response = 'There are no available time slots. Could you please suggest another day?'
    return {"message": response}

async def validate_job_type(job_type_id: int):
    try:
        print("Validating job type...")
        url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/job-types/{job_type_id}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
    }
        response = requests.get(url, headers=headers)
        print(f"Job type response status: {response.status_code}")
        if response.status_code == 200:
            job_type = response.json()
            utils.log_response("Job Types", job_type)
            if job_type.get('id') == job_type_id:
                    print(f"Job type validated successfully. Duration: {job_type.get('duration')} seconds")
                    return job_type.get('duration')  # Return the duration in seconds
            print("Job type validation failed.")
            return None
        else:
            print(f"Error fetching job types: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching job types")
    except Exception as e:
        print(f"Exception while validating job type: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def validate_work_area(client_address: str):
    try:
        print("Validating work area...")
        url = f"https://api.servicetitan.io/settings/v2/tenant/{TENANT_ID}/business-units"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
    }
        response = requests.get(url, headers=headers)
        print(f"Work area response status: {response.status_code}")
        if response.status_code == 200:
            business_units = response.json()
            # Iterate over the 'data' key in the response
            for bu in business_units["data"]:
                if bu["address"]["city"] == client_address.split(", ")[1] and bu["address"]["zip"] == client_address.split(", ")[2]:
                    print("Work area validated successfully.")
                    return True
            print("Work area validation failed.")
            return False
        else:
            print(f"Error fetching business units: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching business units")
    except Exception as e:
        print(f"Exception while validating work area: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
app = FastAPI()

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

        # Validate job type
        duration_seconds = await validate_job_type(data.jobType)
        if duration_seconds is None:
            print("Job type validation failed.")
            return {"error": "Invalid job type"}

        # Validate work area
        if not await validate_work_area(data.address):
            print("Work area validation failed.")
            return {"error": "Service not available in the given area"}

        # Validate technician availability
        start_time = datetime.fromisoformat(data.time.replace("Z", "+00:00")).isoformat()
        end_time = (datetime.fromisoformat(data.time.replace("Z", "+00:00")) + timedelta(seconds=duration_seconds)).isoformat()

        # Validate available slots
        info = await validate_available_slots(start_time, end_time)
        # Check availability
        res = check_availability(info)
        print(f"data of res: {res}")
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