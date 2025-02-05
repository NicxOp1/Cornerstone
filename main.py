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

# Auxiliary functions
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
            print("Access token fetched successfully. ✅")
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

    print("Checking if is customer...")
    try:
        url_customer = f"https://api.servicetitan.io/crm/v2/tenant/488267682/customers?name={request.name}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        response_customer = requests.get(url_customer, headers=headers)
        print(f"Customer response status: {response_customer.status_code}")
        if response_customer.status_code == 200:
            customer_info_json = response_customer.json()

        # Verify "data" contains elements
        if "data" in customer_info_json and len(customer_info_json["data"]) > 0:
            if customer_info_json["data"][0]["name"] == request.name:
                request.isCustomer = True
                print("Is Customer")
            else:
                request.isCustomer = False
                print("Not Customer")
        print("Customer Checked ✅")
    except ValueError:
        return {"error": "Cheking customer failed."}


    print("Checking coordinates...")
    try:
        if request.isCustomer == True:
            lat, lon = customer_info_json["data"][0]["address"]["latitude"], customer_info_json["data"][0]["address"]["longitude"]
            print(lat, lon)
            
        if lat is None or lon is None:
            address = f"{request.locations.address.street}, {request.locations.address.city}, {request.locations.address.country}"
            
            if not address:
                return {"error": "The direction is not valid."}
            
            url_geocode = f"https://geocode.xyz/{address}?json=1&auth={MAPS_AUTH}"
            resp = requests.get(url_geocode)

            if resp.status_code == 200:
                    json_data = resp.json()
            
            lat = json_data.get("latt")
            lon = json_data.get("longt")

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return {"error": "The proporcioned coordinates are no valid."}

        print(lat, lon)

        if lat is None or lon is None:
            return {"error": "Could not get address coordinates."}
        
        lat1, lon1 = math.radians(PO_BOX_SALEM[0]), math.radians(PO_BOX_SALEM[1])
        lat2, lon2 = math.radians(lat), math.radians(lon)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        #Haversine
        a = math.sin(delta_lat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = round(R * c, 2)
        print(f"Distance: {distance} miles")

        if distance > 50:
            return {"error": "There are no services available in the area."}
        
        print("Coordinates Checked ✅")
    except ValueError:
        return {"error": "Checking coordinates failed."}


    print("Checking business unit...")
    try:
        url_jobTypes = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/job-types/"
        response_jobTypes = requests.get(url_jobTypes, headers=headers)

        print(f"Job types response status: {response_jobTypes.status_code}")
        if response_jobTypes.status_code == 200:
            job_types_json = response_jobTypes.json()
            job_types = {job_type["id"]: job_type["businessUnitIds"] for job_type in job_types_json["data"]}

        business_units = job_types.get(request.jobType, None)

        if business_units:
            print(f"Business Units for Job Type {request.jobType}: {business_units}")
        else:
            print(f"Job Type {request.jobType} not found in response.")
        
        print("Business Unit Checked ✅")
    except ValueError:
        return {"error": "Checking business unit failed."}
    
    print("Checking availability time...")
    try:
        start_time = datetime.fromisoformat(request.time.replace("Z", "+00:00"))
        end_time = start_time + timedelta(days=7)
        
        print(f"Start time: {request.time}, End time: {end_time}")

        url_capacity = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity"
        payload = {
            "startsOnOrAfter": request.time,
            "endsOnOrBefore": end_time.isoformat().replace("+00:00", "Z"),
            "businessUnitIds": business_units,
            "jobTypeId": request.jobType,
            "skillBasedAvailability": True
        }

        response_capacity = requests.get(url_capacity, headers=headers, json=payload)

        if response_capacity.status_code == 200:
            response_capacity_json = response_capacity.json()

            available_slots = [
                {"start": slot["start"], "end": slot["end"]}
                for slot in response_capacity_json.get("availabilities", []) if slot.get("isAvailable")
            ]

            print("Available slots:", available_slots)
        else:
            print(f"Error in response: {response_capacity.status_code}, {response_capacity.text}")
        
        print("Availability Time Checked ✅")
    except ValueError:
        print({"error": "Checking availability time failed."})
    
    return available_slots

async def create_customer(customer: utils.CustomerCreateRequest) -> Tuple[str, str]:
    url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers"

    # Replace these placeholders with actual token and app key
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        if customer.locations and isinstance(customer.locations, list) and len(customer.locations) > 0:
            customer.locations[0].address.country = "USA"
            customer.locations[0].address.state = "SC"

        payload = customer.model_dump(by_alias=True)

        # Evita listas anidadas
        if not isinstance(payload["locations"], list):
            payload["locations"] = [payload["locations"]]

        payload["address"] = customer.locations[0].address.model_dump()


        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            customer_id = data.get("id")
            location_id = data.get("locations")[0].get("id")
            return {"customer_id": customer_id, "location_id": location_id}

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

def transform_availabilities(available_slots, business_id):
    """Transforms the available slots to return only the first technician and the slot time."""
    transformed_slots = []

    for slot in available_slots:
        # Get the start time of the slot (in the desired format) and the first technician
        start_time = slot["slot"].split("T")[1].split("Z")[0] + "Z"  # Extracts the time portion
        technician = slot["available_technicians"][0]  # Get the first technician

        # Append the transformed slot
        transformed_slots.append({
            "slot": start_time,
            "id": technician["id"],
            "businessId": business_id
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
        print("Disponibilidad obtenida:", data)
        available_slots = filter_availabilities(data.get("availabilities", []))
        print("Disponibilidad obtenida:", response)

        response = transform_availabilities(available_slots, request["MatchingUnits"][0])
        print("MU :", request["MatchingUnits"][0])
        return json.dumps(response, indent=4)  # Retorna la disponibilidad formateada
    else:
        print("Error en la solicitud:", response.status_code, response.text)
        return json.dumps({"error": "Failed to fetch availability"}, indent=4)

async def check_technician_availability_schedule(request, time):
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
        "businessUnitIds": [request["MatchingUnits"]],
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
        response = transform_availabilities(available_slots, request["MatchingUnits"][0])
        return json.dumps(response, indent=4)  # Retorna la disponibilidad formateada
    else:
        print("Error en la solicitud:", response.status_code, response.text)
        return json.dumps({"error": "Failed to fetch availability"}, indent=4)

@app.get("/")
def read_root():
    print("Root endpoint accessed.")
    return {"status": "Service is up"}

@app.post("/create-job/")
async def create_job(job_request: utils.jobCreateToolRequest):
    job_request = job_request.args

    url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
    access_token = await get_access_token()

    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        # ✅ CREAR CLIENTE Y OBTENER SU ID
        customer_response = await create_customer(job_request.customer)
        print(f"Customer response: {customer_response}")
        customer_id = customer_response["customer_id"]
        location_id = customer_response["location_id"]

        # ✅ Construir el payload correctamente
        payload = {
            "customerId": customer_id,
            "locationId": location_id,
            "jobTypeId": job_request.jobTypeId,
            "priority": job_request.priority,
            "businessUnitId": job_request.businessUnitId,
            "campaignId": job_request.campaignId,
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

        # ✅ ENVIAR SOLICITUD A SERVICE TITAN
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create job: {response.text}",
            )

        job_data = response.json()

        last_appointment_id = job_data.get("lastAppointmentId")

        if not last_appointment_id:
            raise HTTPException(status_code=500, detail="No appointment ID returned from API")

        # ✅ VALIDAR SI EL TÉCNICO ESTÁ PRESENTE
        if not job_request.technician:
            raise HTTPException(status_code=400, detail="Technician ID is missing")

        # ✅ ENVIAR LA SOLICITUD PARA ASIGNAR EL TÉCNICO
        url_tech = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/appointment-assignments/assign-technicians"
        
        payloadTech = {
            "jobAppointmentId": last_appointment_id,
            "technicianIds": [job_request.technician]
        }

        tech_response = requests.post(url_tech, headers=headers, json=payloadTech)

        if tech_response.status_code != 200:
            raise HTTPException(
                status_code=tech_response.status_code,
                detail=f"Failed to assign technician: {tech_response.text}",
            )

        print(f"job data: {job_data}")
        return {"status": "Job request booked", "job_id": job_data.get("id")}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"An error occurred: {err}")

@app.post("/checkAvailability")
async def check_availability(data: utils.BookingRequest):
    PO_BOX_SALEM = (42.775, -71.217)
    R = 3958.8
    request = data.args
    print("Checking availability...")

    print("Checking if is customer...")
    try:
        url_customer = f"https://api.servicetitan.io/crm/v2/tenant/488267682/customers?name={request.name}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        response_customer = requests.get(url_customer, headers=headers)
        print(f"Customer response status: {response_customer.status_code}")
        if response_customer.status_code == 200:
            customer_info_json = response_customer.json()

        # Verify "data" contains elements
        if "data" in customer_info_json and len(customer_info_json["data"]) > 0:
            if customer_info_json["data"][0]["name"] == request.name:
                request.isCustomer = True
                print("Is Customer")
            else:
                request.isCustomer = False
                print("Not Customer")
        print("Customer Checked ✅")
    except ValueError:
        return {"error": "Cheking customer failed."}


    print("Checking coordinates...")
    try:
        lat, lon = None, None

        if request.isCustomer == True:
            lat, lon = customer_info_json["data"][0]["address"]["latitude"], customer_info_json["data"][0]["address"]["longitude"]
            print(lat, lon)
            
        if lat is None or lon is None:
            address = f"{request.locations.address.street}, {request.locations.address.city}, {request.locations.address.country}"
            
            if not address:
                return {"error": "The direction is not valid."}
            
            url_geocode = f"https://geocode.xyz/{address}?json=1&auth={MAPS_AUTH}"
            resp = requests.get(url_geocode)

            if resp.status_code == 200:
                    json_data = resp.json()
            
            lat = json_data.get("latt")
            lon = json_data.get("longt")

        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return {"error": "The proporcioned coordinates are no valid."}

        print(lat, lon)

        if lat is None or lon is None:
            return {"error": "Could not get address coordinates."}
        
        lat1, lon1 = math.radians(PO_BOX_SALEM[0]), math.radians(PO_BOX_SALEM[1])
        lat2, lon2 = math.radians(lat), math.radians(lon)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        #Haversine
        a = math.sin(delta_lat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = round(R * c, 2)
        print(f"Distance: {distance} miles")

        if distance > 50:
            return {"error": "There are no services available in the area."}
        
        print("Coordinates Checked ✅")
    except ValueError:
        return {"error": "Checking coordinates failed."}


    print("Checking business unit...")
    try:
        url_jobTypes = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/job-types/"
        response_jobTypes = requests.get(url_jobTypes, headers=headers)

        print(f"Job types response status: {response_jobTypes.status_code}")
        if response_jobTypes.status_code == 200:
            job_types_json = response_jobTypes.json()
            job_types = {job_type["id"]: job_type["businessUnitIds"] for job_type in job_types_json["data"]}

        business_units = job_types.get(request.jobType, None)

        if business_units:
            print(f"Business Units for Job Type {request.jobType}: {business_units}")
        else:
            print(f"Job Type {request.jobType} not found in response.")
        
        print("Business Unit Checked ✅")
    except ValueError:
        return {"error": "Checking business unit failed."}
    
    print("Checking availability time...")
    try:
        start_time = datetime.fromisoformat(request.time.replace("Z", "+00:00"))
        end_time = start_time + timedelta(days=7)
        end_time_str = end_time.isoformat().replace("+00:00", "Z")
        
        print(f"Start time: {request.time}, End time: {end_time_str}")

        url_capacity = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity"
        payload = {
            "startsOnOrAfter": request.time,
            "endsOnOrBefore": end_time_str,
            "businessUnitIds": business_units,
            "jobTypeId": request.jobType,
            "skillBasedAvailability": True
        }

        response_capacity = requests.post(url_capacity, headers=headers, json=payload)

        if response_capacity.status_code == 200:
            response_capacity_json = response_capacity.json()

            available_slots = [
                {"start": slot["start"], "end": slot["end"]}
                for slot in response_capacity_json.get("availabilities", []) if slot.get("isAvailable")
            ]

            print("Available slots:", available_slots)
        else:
            print(f"Error in response: {response_capacity.status_code}, {response_capacity.text}")
        
    except ValueError:
        print({"error": "Checking availability time failed."})
    
    print("Availability Time Checked ✅")
    return available_slots

@app.post("/reschedule_appointment")
async def reschedule_appointment(data: utils.ReScheduleData): 
    print("Processing re scheduling request...")
    print(f"Request data: {data}")
    access_token = await get_access_token()
    
    try:
        print("Getting customer...")
        url_customers = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers?name={data.name}"
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        response_customers = requests.get(url_customers, headers=headers)

        if response_customers.status_code == 200:
            customers_data_json = response_customers.json()
            if "data" in customers_data_json and len(customers_data_json["data"]) > 0:
                customer_id = customers_data_json["data"][0].get("id")
            else:
                return {"error": "No se encontró el id del cliente."}

    except requests.exceptions.RequestException as e:
        print(f"Error al obtener cliente: {e}")
        return {"error": "Error al realizar la solicitud externa."}
    
    try:
        print("Getting appointment id ...")
        print('Getting jobs ...')

        url_jobs = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs?customerId={customer_id}"
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        response_jobs = requests.get(url_jobs, headers=headers)

        if response_jobs.status_code == 200:
            jobs_data_json = response_jobs.json()
            if jobs_data_json and "data" in jobs_data_json and len(jobs_data_json["data"]) > 0:
                appointment_id = jobs_data_json["data"][0].get("lastAppointmentId")
                print(f"APPOINTMENT ID: {appointment_id}")
        else:
            print("Error en la solicitud de trabajos")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error al obtener appointment id: {e}")
        return {"error": "Error al realizar la solicitud externa."}

    if not appointment_id:
        return {"error": "No se encontró una agenda válida para el cliente."}
    
    try:
        url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/appointments/{appointment_id}/reschedule"
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
    
        # Convertir a objeto datetime
        start_time = datetime.fromisoformat(data.newSchedule)

        # Agregar 3 horas a end
        end_time = start_time + timedelta(hours=3)

        # Convertir de nuevo a formato ISO
        payload = {
            "start": data.newSchedule,  # Mantiene el valor original
            "end": end_time.isoformat()  # Ahora tiene 3 horas más
    }
        
        # Realizar la solicitud PATCH
        response = requests.patch(url, json=payload, headers=headers)
        print(f"Respuesta de la API externa: {response.status_code}")
            
        # Devolver la respuesta de la API externa
        if response.status_code == 200:
            print(response.json())
            return response.json()
        else:
            return {"error": f"Error en la solicitud: {response.status_code}", "details": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": "Error al realizar la solicitud externa."}

@app.post("/cancel_appointment")
async def cancel_appointment(data: utils.cancelJobAppointment):
    try:
        print("Getting customer...")
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        # Obtener el customer_id
        url_customers = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers?name={data.name}"
        response_customers = requests.get(url_customers, headers=headers)

        if response_customers.status_code != 200:
            return {"error": "Error al obtener el cliente.", "details": response_customers.text}

        customers_data_json = response_customers.json()
        if not customers_data_json.get("data"):
            return {"error": "No se encontró el ID del cliente."}

        customer_id = customers_data_json["data"][0].get("id")
        print(f"CUSTOMER ID: {customer_id}")

        # Obtener el jobId correspondiente al customer_id
        print("Getting job id ...")
        url_bookings = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/export/bookings"
        response_bookings = requests.get(url_bookings, headers=headers)

        if response_bookings.status_code != 200:
            return {"error": "Error al obtener las reservas.", "details": response_bookings.text}

        bookings_data_json = response_bookings.json()
        job_id = None

        for entry in bookings_data_json.get("data", []):
            if entry.get("name") == data.name:
                job_id = entry.get("jobId")
                break

        if not job_id:
            return {"error": "No se encontró un Job ID para el cliente."}

        print(f"JOB ID: {job_id}")

        # Cancelar la cita
        print("Processing cancel appointment request...")
        url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs/{job_id}/cancel"
        print(f"Request URL: {url}")

        payload = {
            "reasonId": data.reasonId,
            "memo": data.memo
        }

        response = requests.put(url, headers=headers, json=payload)
        print(f"Response of the API external: {response.status_code}")

        # Manejo de errores específicos
        if response.status_code == 404:
            return {"error": "Job ID not found.", "details": response.json()}

        if response.status_code == 200:
            if not response.text.strip():  # Si la respuesta está vacía
                return {"message": "Job appointment canceled successfully."}
            return response.json()

        return {"error": f"Error in request: {response.status_code}", "details": response.text}

    except Exception as e:
        print(f"Exception while processing cancel job appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_time")
async def get_current_utc_time():
    utc_now = datetime.now(pytz.utc)
    return utc_now.strftime("%Y-%m-%dT%H:%M:%SZ")



#dowload fastapi: pip install "fastapi[standard]"
#dowload dotenv: pip install python-dotenv (may come pre-installed in newer Python versions)
#dowload pytz: pip install pytz
#start the server: fastapi dev main.py