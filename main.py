from datetime import datetime, date, timedelta, time, timezone
from typing import Tuple, Dict
from fastapi import FastAPI, Request, Response, HTTPException
import requests
import utils as utils
import logging
from dotenv import load_dotenv
import os
import json
import pytz
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
EASTERN_TIME = pytz.timezone("America/New_York")
MAPS_AUTH= os.getenv("MAPS_AUTH")

app = FastAPI()

CITIES = {
    "agawam", "amesbury", "attleboro", "barnstable", "beverly", "boston", "braintree",
    "brockton", "cambridge", "chelsea", "chicopee", "easthampton", "everett", "fall river",
    "fitchburg", "framingham", "franklin", "gardner", "gloucester", "greenfield",
    "haverhill", "holyoke", "lawrence", "leominster", "lowell", "lynn", "malden",
    "marlborough", "medford", "melrose", "methuen", "new bedford", "newburyport",
    "newton", "north adams", "northampton", "palmer", "peabody", "pittsfield", "quincy",
    "randolph", "revere", "salem", "somerville", "southbridge", "springfield", "taunton",
    "waltham", "watertown", "west springfield", "westfield", "weymouth", "winthrop",
    "woburn", "worcester", "bridgewater", "amherst",
    "berlin", "claremont", "concord", "dover", "franklin", "keene", "laconia",
    "lebanon", "manchester", "nashua", "portsmouth", "rochester", "somersworth", "acton", "arlington", "atkinson", "derry", "hudson", "windham"
}

VALID_STATES = {"MA", "NH", "New Hampshire", "Massachusetts"}

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

def massachusetts_to_utc(dt_str: str) -> str:
    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
    eastern_tz = pytz.timezone("America/New_York")
    dt_eastern = eastern_tz.localize(dt)
    dt_utc = dt_eastern.astimezone(pytz.utc)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

async def get_customer(name):
    print("Getting customer by name...")
    try:
        url_customers = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers?name={name}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        response_customers = requests.get(url_customers, headers=headers)

        if response_customers.status_code == 200:
            customers_data_json = response_customers.json()
            
            if not customers_data_json.get("data"):
                print("Error: No customers found by name.")
                return {"error": "Customer not found by name."}

            for customer in customers_data_json["data"]:
                if customer.get("name") == name:
                    print("Customer found by name✅")
                    return customer.get("id")
            
            print("Error: No exact match for customer name.")
            return {"error": "Customer not found by name."}

        print(f"Error: Unexpected response {response_customers.status_code} - {response_customers.text}")
        return {"error": f"Unexpected response status: {response_customers.status_code}"}
    
    except requests.exceptions.RequestException as e:
        print(f"Error getting client: {e}")
        return {"error": "Error when making external request."}

async def get_customer_by_phone(phone):
    print("Getting customer by phone...")
    try:
        url_customers = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers?phone={phone}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        response_customers = requests.get(url_customers, headers=headers)

        if response_customers.status_code == 200:
            customers_data_json = response_customers.json()
            
            if not customers_data_json.get("data"):
                print("Error: No customers found by phone.")
                return {"error": "Customer not found by phone."}

            customer = customers_data_json["data"][0]
            print("Customer found by phone✅")
            return customer.get("id")

        print(f"Error: Unexpected response {response_customers.status_code} - {response_customers.text}")
        return {"error": f"Unexpected response status: {response_customers.status_code}"}
    
    except requests.exceptions.RequestException as e:
        print(f"Error getting client: {e}")
        return {"error": "Error when making external request."}

async def create_customer(customer: utils.CustomerCreateRequest):
    url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers"
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    print("Creating customer ...")
    try:
        if not customer.name or not customer.number or not customer.email:
            return {"error": "Customer name, number, and email are required."}

        # Definir la dirección si no está completa
        if customer.locations and isinstance(customer.locations, list) and len(customer.locations) > 0:
            location = customer.locations[0]
        else:
            return {"error": "Customer location is missing."}

        if hasattr(location, 'address') and location.address:
            location.address.country = location.address.country or "USA"
            location.address.state = location.address.state or "SC"

        # Construcción del payload
        payload = {
            "name": customer.name,
            "type": customer.type,
            "address": {
                "street": location.address.street or "",
                "city": location.address.city or "",
                "state": location.address.state or "",
                "zip": location.address.zip or "",
                "country": location.address.country or "",
            },
            "locations": [
                {
                    "name": location.name,
                    "address": {
                        "street": location.address.street or "",
                        "city": location.address.city or "",
                        "zip": location.address.zip or "",
                        "country": location.address.country,
                        "state": location.address.state,
                    },
                }
            ]
        }

        response = requests.post(url, headers=headers, json=payload)
        print("Response Status Code:", response.status_code)
        
        if response.status_code != 200:
            print(f"Error creating customer: {response.text}")
            return {"error": f"Failed to create customer: {response.text}"}

        data = response.json()
        customer_id = data.get("id")
        location_id = data.get("locations", [{}])[0].get("id")

        if not customer_id or not location_id:
            return {"error": "Customer or Location ID missing in API response."}
        
        if response.status_code == 200:
            print("Created customer successfully ✅")
            data = response.json()
            customer_id = data.get("id")
            location_id = data.get("locations")[0].get("id")
            print({"customer_id": customer_id, "location_id": location_id})

            # Ahora, agregar los datos de contacto
            print("Adding contact data to customer")

            contact_url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers/{customer_id}/contacts"

            # Primero, crea el contacto con el número móvil si está disponible
            if customer.number:
                contact_url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers/{customer_id}/contacts"
                mobile_payload = {
                    "type": "MobilePhone",  # Tipo: móvil
                    "value": customer.number,  # El número móvil
                    "memo": "Customer phone number"  # (Opcional) Nota descriptiva
                }

                response_mobile = requests.post(contact_url, headers=headers, json=mobile_payload)
                if response_mobile.status_code == 200:
                    print("Mobile contact data added successfully ✅")
                else:
                    print(f"Error adding mobile contact data: {response_mobile.text}")
                    raise HTTPException(
                        status_code=response_mobile.status_code,
                        detail=f"Failed to add mobile contact data: {response_mobile.text}",
                    )

            # Luego, crea el contacto con el correo electrónico si está disponible
            if customer.email:
                contact_url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers/{customer_id}/contacts"
                email_payload = {
                    "type": "Email",  # Tipo: correo electrónico
                    "value": customer.email,  # El valor del correo electrónico
                    "memo": "Customer email"  # (Opcional) Nota descriptiva
                }

                response_email = requests.post(contact_url, headers=headers, json=email_payload)
                if response_email.status_code == 200:
                    print("Email contact data added successfully ✅")
                else:
                    print(f"Error adding email contact data: {response_email.text}")
                    raise HTTPException(
                        status_code=response_email.status_code,
                        detail=f"Failed to add email contact data: {response_email.text}",
                    )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create customer: {response.text}",
                )
            
            return {"customer_id": customer_id, "location_id": location_id}
    except ValueError:
        print({"error": "Failed to create customer."})

async def check_availability_time(time, business_units, job_type):
    print("Checking availability time...")
    
    available_slots = []

    if isinstance(business_units, int):
        business_units = [business_units]
    elif isinstance(business_units, list):
        business_units = [int(bu) for bu in business_units]

    try:
        
        if "Z" in time:
            time = time.replace("Z", "+00:00")

        starts_on_or_after = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Corregir el formato del día si es necesario (eliminando ceros innecesarios en el día)
        time_parts = time.split('T')
        date_parts = time_parts[0].split('-')
        
        # Asegurar que el día tenga siempre dos dígitos
        date_parts[2] = date_parts[2].zfill(2)  

        corrected_time = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}T{time_parts[1]}"
        
        try:
            start_time = datetime.fromisoformat(corrected_time)
        except ValueError:
            print(f"Invalid time format: {corrected_time}")
            return (f"Invalid time format: {corrected_time}")

        # Debug: Verifica las fechas generadas
        print(f"Start Time: {start_time}, Start DateTime: {starts_on_or_after}")

        end_time = start_time + timedelta(days=7)
        end_time = end_time.replace(hour=23, minute=59, second=0, microsecond=0)
        end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Debug: Verifica la fecha final
        print(f"End Time: {end_time}, End DateTime: {end_time_str}")

        url_capacity = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity"
        
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        payload = {
            "startsOnOrAfter": starts_on_or_after,
            "endsOnOrBefore": end_time_str,
            "businessUnitIds": business_units,
            "jobTypeId": job_type,
            "skillBasedAvailability": True
        }

        response_capacity = requests.post(url_capacity, headers=headers, json=payload)

        if response_capacity.status_code == 200:
            print("Availability Time Checked ✅")
            response_capacity_json = response_capacity.json()

            available_slots = [
                {"start": slot["start"], "end": slot["end"]}
                for slot in response_capacity_json.get("availabilities", []) if slot.get("isAvailable")
            ]
        else:
            print(f"Error in response: {response_capacity.status_code}, {response_capacity.text}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print({"error": "Checking availability time failed."})
    
    return available_slots

async def get_technicians_by_businessUnitId(businessUnitId):
    print(f"Getting technicians for Business Unit ID: {businessUnitId}...")
    technicians = []

    try:
        url_technicians = f"https://api.servicetitan.io/settings/v2/tenant/{TENANT_ID}/technicians"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        response_technicians = requests.get(url_technicians, headers=headers)

        if response_technicians.status_code == 200:
            print("Technicians fetched successfully.")
            response_data = response_technicians.json()
            
            # Filtrar los técnicos según el businessUnitId
            technicians = [
                tech for tech in response_data.get("data", []) if tech.get("businessUnitId") == businessUnitId
            ]

            if technicians:
                print(f"Found {len(technicians)} technicians for Business Unit ID {businessUnitId}.")
            else:
                print(f"No technicians found for Business Unit ID {businessUnitId}.")
            
            return technicians

        else:
            print(f"Error fetching technicians. Status Code: {response_technicians.status_code}")
            return {"error": "Failed to retrieve technicians."}

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {"error": "Checking technicians by business unit failed."}


# Endpoints
@app.get("/")
def read_root():
    print("Root endpoint accessed.")
    return {"status": "Service is up"}

@app.post("/checkAvailability")
async def check_availability(data: utils.BookingRequest):
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
 
    available_slots = []

    try:
        available_slots = await check_availability_time(request.time, business_units, request.jobType)

        if not available_slots:
            print("No available slots found.")
    except Exception as e:
        print(f"Error checking availability: {e}")

    print("Checking availability ✅")
    return {
        'businessUnitId': business_units[0],
        'available_slots': available_slots
    }

@app.post("/createJob")
async def create_job(job_request: utils.jobCreateToolRequest):
    print("Creating job...")
    job_request = job_request.args

    url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        # Primero buscar el cliente por número de teléfono
        customer_response = await get_customer_by_phone(job_request.customer.number)

        # Si no lo encuentra por teléfono, buscar por nombre
        if isinstance(customer_response, dict) and "error" in customer_response:
            print(f"{customer_response['error']}. Trying by name...")
            customer_response = await get_customer(job_request.customer.name)

        if isinstance(customer_response, dict) and "error" in customer_response:
            print(f"{customer_response['error']}. Creating new customer...")

            customer_response = await create_customer(job_request.customer)

            if "error" in customer_response:
                print(f"Failed to create customer: {customer_response['error']}")
                return {"error": customer_response['error']}

            customer_id = customer_response.get("customer_id")
            location_id = customer_response.get("location_id")

            if not customer_id or not location_id:
                return {"error": "Customer created but missing customer_id or location_id."}

            print(f"New customer created with ID: {customer_id} and Location ID: {location_id}")
        else:
            customer_id = customer_response
            print(f"Customer found with ID: {customer_id}. Fetching location...")

            url_location = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/locations?customerId={customer_id}"
            location_response = requests.get(url_location, headers=headers)

            if location_response.status_code == 200 and location_response.json().get("data"):
                location_id = location_response.json().get("data")[0].get("id")
                print(f"Location ID found: {location_id}")
            else:
                print("Error: Unable to fetch location ID.")
                return {"error": "Failed to retrieve location ID for existing customer."}

        # Asegurar que las fechas tengan la "Z" al final si no la tienen
        if not job_request.jobStartTime.endswith("Z"):
            job_request.jobStartTime += "Z"
        if not job_request.jobEndTime.endswith("Z"):
            job_request.jobEndTime += "Z"

        # Convertir a UTC desde hora de Massachusetts
        job_request.jobStartTime = massachusetts_to_utc(job_request.jobStartTime)
        job_request.jobEndTime = massachusetts_to_utc(job_request.jobEndTime)

        # ✅ Construir el payload correctamente
        payload = {
            "customerId": customer_id,
            "locationId": location_id,
            "businessUnitId": job_request.businessUnitId,
            "jobTypeId": job_request.jobTypeId,
            "priority": job_request.priority,
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
            "summary": job_request.summary
        }

        # ✅ ENVIAR SOLICITUD A SERVICE TITAN
        
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"Error in response: {response.status_code}, {response.text}")
            return {"error": f"Failed to create job: {response.text}"}

        job_data = response.json()
        print("Job request created successfully ✅")
        return {"status": "Job request booked", "job_id": job_data.get("id")}

    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return {"error": "Unexpected request error"}

@app.post("/findAppointment")
async def find_appointment(data: utils.FindAppointmentDataToolRequest):
    print("Processing findAppointment request...")
    data = data.args
    access_token = await get_access_token()

    # Step 1: Buscar cliente por teléfono, si no existe, por nombre
    customer_response = await get_customer_by_phone(data.number)
    if isinstance(customer_response, dict) and "error" in customer_response:
        print(f"Not found by phone: {customer_response['error']}. Searching by name...")
        customer_response = await get_customer(data.name)
    if isinstance(customer_response, dict) and "error" in customer_response:
        return {"error": customer_response["error"]}
    customer_id = customer_response

    # Step 2: Obtener todos los jobs agendados para ese cliente
    print("Fetching scheduled jobs for customer...")
    url_jobs = (
        f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
        f"?customerId={customer_id}&jobStatus=Scheduled"
    )
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }
    resp_jobs = requests.get(url_jobs, headers=headers)
    if resp_jobs.status_code != 200:
        return {"error": "Failed to fetch jobs."}
    jobs = resp_jobs.json().get("data", [])

    # Step 3 & 4: Por cada job, buscar sus appointments agendados y combinar datos
    combined = []
    for job in jobs:
        job_id = job.get("id")
        business_unit_id = job.get("businessUnitId")
        job_type_id = job.get("jobTypeId")
        summary = job.get("summary", "")
        job_id = job.get("id")
        employeeId = job.get("jobGeneratedLeadSource", {}).get("employeeId")

        print(f"Fetching appointments for job {job_id}...")
        url_apps = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/appointments"
            f"?jobId={job_id}&status=Scheduled"
        )
        resp_apps = requests.get(url_apps, headers=headers)
        if resp_apps.status_code != 200:
            continue

        apps = resp_apps.json().get("data", [])
        for a in apps:
            # Convertir UTC -> hora local de Massachusetts
            def to_eastern(ts: str) -> str:
                if ts.endswith("Z"):
                    ts = ts.replace("Z", "+00:00")
                dt_utc = datetime.fromisoformat(ts)
                return dt_utc.astimezone(pytz.timezone("America/New_York")).isoformat()

            start_local = to_eastern(a.get("start"))
            end_local   = to_eastern(a.get("end"))

            combined.append({
                "jobId": job_id,
                "businessUnitId": business_unit_id,
                "jobTypeId": job_type_id,
                "summary": summary,
                "employeeId": employeeId,
                "appointmentId": a.get("id"),
                "start": start_local,
                "end": end_local,
            })
    
    print("Appointment found ✅")
    return {"appointments": combined}

@app.post("/rescheduleAppointmentTimeAvailability")
async def reschedule_appointment_time_availability(data: utils.ReSchedulaDataToolRequest):
    print("Processing re-scheduling availability request...")
    # extraer args directos del agente de voz
    data = data.args

    # usar directamente los datos enviados por el agente
    job_type_id = data.jobTypeId
    business_unit_id = data.businessUnitId
    desired_time = data.newSchedule

    # validar que vengan ambos IDs
    if not job_type_id or not business_unit_id:
        return {"error": "Missing jobTypeId or businessUnitId in request."}

    print(f"Checking availability for businessUnitId={business_unit_id}, jobTypeId={job_type_id}, around {desired_time}...")
    try:
        slots_available = await check_availability_time(desired_time, business_unit_id, job_type_id)
        if slots_available:
            return {"availableSlots": slots_available}
        else:
            print("No slots available.")
            return {"availableSlots": []}
    except requests.exceptions.RequestException as e:
        print(f"Error getting slots: {e}")
        return {"error": "Error when requesting availability."}

@app.post("/rescheduleAppointment")
async def reschedule_appointment(data: utils.ReSchedulaDataToolRequest):
    print("Processing re-scheduling request...")
    data = data.args
    access_token = await get_access_token()

    appointment_id = data.appointmentId
    technician_id = data.employeeId
    new_schedule = data.newSchedule

    # 1. Unassign technician if provided
    if technician_id:
        tech_ids = technician_id if isinstance(technician_id, list) else [technician_id]
        print(f"Unassigning technician(s) {tech_ids} from appointment {appointment_id}...")
        url_unassign = (
            f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}"
            "/appointment-assignments/unassign-technicians"
        )
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        unassign_payload = {
            "jobAppointmentId": appointment_id,
            "technicianIds": tech_ids
        }
        resp_unassign = requests.patch(url_unassign, json=unassign_payload, headers=headers)
        if resp_unassign.status_code == 200:
            print("Technician unassigned successfully ✅")
        else:
            print(f"Failed to unassign technician: {resp_unassign.text}")

    # 2. Ensure the new_schedule string ends with "Z"
    if not new_schedule.endswith("Z"):
        new_schedule += "Z"

    # 3. Convert from Massachusetts local time to UTC
    start_utc = massachusetts_to_utc(new_schedule)

    # 4. Calculate end_utc = start_utc + 3 hours
    start_dt = datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(hours=3)
    end_utc = end_dt.isoformat().replace("+00:00", "Z")

    # 5. Send the reschedule PATCH
    print(f"Rescheduling appointment {appointment_id} to start {start_utc} and end {end_utc}...")
    url_resch = (
        f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}"
        f"/appointments/{appointment_id}/reschedule"
    )
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }
    resch_payload = {
        "start": start_utc,
        "end": end_utc,
        "arrivalWindowStart": start_utc,
        "arrivalWindowEnd": end_utc
    }
    resp = requests.patch(url_resch, json=resch_payload, headers=headers)

    if resp.status_code == 200:
        print("Reschedule request processed successfully ✅")
        return {"status": "Reschedule request processed successfully"}
    else:
        return {
            "error": f"Request error: {resp.status_code}",
            "details": resp.text
        }

@app.post("/cancelAppointment")
async def cancel_appointment(data: utils.cancelJobAppointmentToolRequest):
    print("Processing cancellation request...")
    data = data.args

    # extraer directamente los datos necesarios
    job_id   = data.jobId
    reason_id = data.reasonId
    memo     = data.memo

    if not job_id:
        return {"error": "Missing jobId in request."}

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    # llamar al endpoint de cancelación
    url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs/{job_id}/cancel"
    payload = {
        "reasonId": reason_id,
        "memo": memo
    }

    print(f"Cancelling job {job_id} with reason {reason_id}...")
    resp = requests.put(url, headers=headers, json=payload)
    print(f"External API responded: {resp.status_code}")

    if resp.status_code == 200:
        # a veces el body viene vacío
        if not resp.text.strip():
            print("Job canceled successfully ✅")
            return {"message": "Job canceled successfully"}
        return resp.json()
    elif resp.status_code == 404:
        return {"error": "Job ID not found", "details": resp.json()}
    else:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

app.post("/getTime")
async def get_current_boston_time():
    print("Getting current time...")
    utc_now = datetime.now(timezone.utc)

    # Hora de Boston (Eastern Time - EST/EDT)
    boston_offset = timedelta(hours=-5)  # UTC-5 (EST) por defecto
    boston_time = utc_now + boston_offset

    # Verificar si es horario de verano (DST)
    start_dst = datetime(utc_now.year, 3, 10, 2, tzinfo=timezone.utc)  # Segundo domingo de marzo
    end_dst = datetime(utc_now.year, 11, 3, 2, tzinfo=timezone.utc)  # Primer domingo de noviembre

    if start_dst <= utc_now < end_dst:
        boston_time += timedelta(hours=1)  # UTC-4 en horario de verano (EDT)

    print(f"Current UTC time: {utc_now.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"Current Boston time: {boston_time.strftime('%Y-%m-%dT%H:%M:%S')}")
    print("Getting current time successfully ✅")

    return boston_time.strftime("%Y-%m-%dT%H:%M:%S")

@app.post("/checkWorkArea")
async def check_work_area(data: utils.addressCheckToolRequest):
    data = data.args
    print("Checking coordinates...")
    PO_BOX_SALEM = (42.775, -71.217)
    R = 3958.8

    city = data.city.strip().lower()
    state = data.state

    # Validación rápida: estado permitido y ciudad en lista única
    if state in VALID_STATES and city in CITIES:
        print("Coordinates Checked In List✅")
        return {"message": "City is in the working area (matched from predefined list)."}

    # Fallback: geocodificación + cálculo de distancia
    address = f"{data.street}, {data.city}, {data.country}"
    if not address:
        print("error: The direction is not valid.")
        return {"error": "The direction is not valid."}

    url_geocode = f"https://geocode.xyz/{address}?json=1&auth={MAPS_AUTH}"
    resp = requests.get(url_geocode)
    if resp.status_code != 200:
        print("error: no response from geocode api")
        return {"error": "Failed to fetch geolocation data."}

    json_data = resp.json()
    if json_data.get("error") or json_data.get("longt") == "0.00000" or json_data.get("latt") == "0.00000":
        print("error: Address no found in geocode api")
        return {"error": "The address received does not exist."}

    expected_zip = json_data.get("standard", {}).get("postal")
    client_zip = data.zip
    expected_zip_clean = expected_zip.split('-')[0] if expected_zip else None
    if expected_zip_clean and expected_zip_clean != client_zip:
        print("error: The provided zip code does not match the address. The zip code should be: {expected_zip_clean}")
        return {"error": f"The provided zip code does not match the address. The zip code should be: {expected_zip_clean}"}

    try:
        lat = float(json_data.get("latt"))
        lon = float(json_data.get("longt"))
    except (TypeError, ValueError):
        print("error: The provided coordinates are not valid.")
        return {"error": "The provided coordinates are not valid."}

    lat1, lon1 = math.radians(PO_BOX_SALEM[0]), math.radians(PO_BOX_SALEM[1])
    lat2, lon2 = math.radians(lat), math.radians(lon)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = math.sin(delta_lat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = round(R * c, 2)

    if distance > 50:
        print("error: There are no services available in the area.")
        return {"error": "There are no services available in the area."}
    return {"message": "Address is in the working area."}

@app.post("/updateJobSummary")
async def update_job_summary(data: utils.updateJobSummaryToolRequest):
    data = data.args
    access_token = await get_access_token()
    customer_id = await get_customer(data.name)

    if not customer_id:
        return {"error": "Customer not found."}

    print("Getting job data...")
    url_jobs = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs?customerId={customer_id}"
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }
    response_jobs = requests.get(url_jobs, headers=headers)

    if response_jobs.status_code != 200:
        return {"error": "Failed to fetch job data."}

    jobs_data_json = response_jobs.json()
    if not jobs_data_json.get("data"):
        return {"error": "No jobs found for this customer."}

    job = jobs_data_json["data"][0]
    job_id = job.get("id")
    current_summary = job.get("summary")

    new_summary = f"<p>{data.info}</p>"

    if current_summary:
        updated_summary = f"{current_summary}\n{new_summary}".strip()
    else:
        updated_summary = new_summary

    print(f"Updating summary for job ID {job_id}...")
    url_patch = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs/{job_id}"
    patch_payload = {
        "summary": updated_summary
    }

    patch_response = requests.patch(url_patch, headers=headers, json=patch_payload)

    if patch_response.status_code == 200:
        print("Job summary updated successfully ✅")
        return {"status": "Job summary updated"}
    else:
        return {
            "error": "Failed to update job summary.",
            "status_code": patch_response.status_code,
            "details": patch_response.text
        }


#Outbound

@app.post("/checkAvailabilityOutbound")
async def check_availability_outbound(data: utils.BookingRequestOutbound):
    jobType = 5879699
    business_unit = 5878155
    request = data.args

    await get_technicians_by_businessUnitId(5878155)

    print("Checking availability...")
 
    available_slots = []

    try:
        available_slots = await check_availability_time(request.time, business_unit, jobType)

        if not available_slots:
            print("No available slots found.")
    except Exception as e:
        print(f"Error checking availability: {e}")

    print("Checking availability ✅")
    return {
        'available_slots': available_slots
    }

#@app.post("/createJobOutbound")
async def create_job_outbound(job_request: utils.jobCreateToolRequestOutbound):

    print("Creating job...")
    campaignId = 82014707
    job_request = job_request.args
    jobType = 48838652
    business_unit = 4931462

    url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        # Traer customerId
        customer_response = await get_customer(job_request.name)

        if isinstance(customer_response, dict) and "error" in customer_response:
            print(f"Error fetching customer: {customer_response['error']}")
            return customer_response
    
        customer_id = customer_response

        #Traer locationId
        url_location = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/locations?customerId={customer_id}"
        location_response = requests.get(url_location, headers=headers)
        location_id = location_response.json().get("data")[0].get("id")

        # Convertir jobStartTime y jobEndTime a datetime
        start_time = datetime.fromisoformat(job_request.jobStartTime.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(job_request.jobEndTime.replace("Z", "+00:00"))

        # Sumar 3 horas
        start_time += timedelta(hours=4)
        end_time += timedelta(hours=4)

        # Convertir a formato ISO 8601 con "Z"
        job_request.jobStartTime = start_time.isoformat().replace("+00:00", "Z")
        job_request.jobEndTime = end_time.isoformat().replace("+00:00", "Z")

        # ✅ Construir el payload correctamente 
        payload = {
            "customerId": customer_id,
            "locationId": location_id,
            "businessUnitId": business_unit,
            "jobTypeId": jobType,
            "priority": job_request.priority,
            "campaignId": campaignId,
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
            "summary": job_request.summary
        }

        # ✅ ENVIAR SOLICITUD A SERVICE TITAN
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"Error in response: {response.status_code}, {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create job: {response.text}",
            )

        job_data = response.json()
        print("Job request created successfully ✅")
        return {"status": "Job request booked", "job_id": job_data.get("id")}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")



    print("Processing cancellation request...")
    data = data.args
    try:
        customer_response = await get_customer(data.name)

        if isinstance(customer_response, dict) and "error" in customer_response:
            print(f"Error fetching customer: {customer_response['error']}")
            return customer_response
        
        customer_id = customer_response

        # Obtener el jobId correspondiente al customerId
        url_appointment = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/appointments?&customerId={customer_id}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        print("Getting job id ...")
        response_appointment = requests.get(url_appointment, headers=headers)

        if response_appointment.status_code != 200:
            return {"error": "Error obtaining reservations.", "details": response_appointment.text}

        appointment_data_json = response_appointment.json()
        job_id = appointment_data_json["data"][0]["jobId"]
        print(f"Job ID: {job_id}")

        if not job_id:
            print("Job ID not found")
            return {"error": "A Job ID was not found for the customer."}

        # Cancelar la cita
        print("Processing cancel appointment request...")
        url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs/{job_id}/cancel"

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
                print("Job appointmet canceled successfully ✅")
                return {"message": "Job appointment canceled successfully."}
            return response.json()

        return {"error": f"Error in request: {response.status_code}", "details": response.text}
    except Exception as e:
        print(f"Exception while processing cancel job appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

#download fastapi: pip install "fastapi[standard]"
#download dotenv: pip install python-dotenv (may come pre-installed in newer Python versions)
#download pytz: pip install pytz
#download pandas: pip install pandas
#start the server: fastapi dev main.py