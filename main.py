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

async def get_customer(name):
    print("Getting customer...")
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
            if "data" in customers_data_json and len(customers_data_json["data"]) > 0:
                for customer in customers_data_json["data"]:
                    if customer.get("name") == name:
                        customer_id = customer.get("id")
                        print("Customer achieved ✅")
                        break
                    else:
                        return {"error": "Client ID not found."}
            else:
                return {"error": "Client ID not found."}
        return customer_id
    except requests.exceptions.RequestException as e:
        print(f"Error getting client: {e}")
        return {"error": "Error when making external request."}

async def create_customer(customer: utils.CustomerCreateRequest):
    print("Creating customer ...")
    url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers"

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        if customer.locations and isinstance(customer.locations, list) and len(customer.locations) > 0:
            location = customer.locations[0]

        if hasattr(location, 'address') and location.address:
            if not getattr(location.address, 'country', None):
                location.address.country = "USA"
            if not getattr(location.address, 'state', None):
                location.address.state = "SC"

        payload = {
            "name": customer.name,
            "type": customer.type,
            "locations": [
                {
                    "name": location.name,
                    "address": {
                        "street": location.address.street or "",
                        "city": location.address.city or "",
                        "zip": location.address.zip or "",
                        "country": location.address.country or "USA",
                        "state": location.address.state or "SC",
                    },
                }
            ],
            "address": {
                "street": (customer.address.street if customer.address else location.address.street) or "",
                "city": (customer.address.city if customer.address else location.address.city) or "",
                "zip": (customer.address.zip if customer.address else location.address.zip) or "",
                "country": (customer.address.country if customer.address else location.address.country) or "USA",
                "state": (customer.address.state if customer.address else location.address.state) or "SC",
            },
        }

        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("Created customer successfully ✅")
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

async def check_availability_time(time, business_units, job_type):
    print("Checking availability time...")
    if isinstance(business_units, int):
        business_units = [business_units]
    elif isinstance(business_units, list):
        business_units = [int(bu) for bu in business_units]
    try:
        starts_on_or_after = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
        start_time = datetime.fromisoformat(time.replace("Z", "+00:00"))

        end_time = start_time + timedelta(days=7)
        end_time = end_time.replace(hour=23, minute=59, second=0, microsecond=0)
        end_time_str = end_time.isoformat().replace("+00:00", "Z")

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
    except ValueError:
        print({"error": "Checking availability time failed."})
    
    return available_slots

# Endpoints
@app.get("/")
def read_root():
    print("Root endpoint accessed.")
    return {"status": "Service is up"}

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
            if "data" in customer_info_json and customer_info_json["data"]:
                first_data = customer_info_json["data"][0]

                if "address" in first_data and "latitude" in first_data["address"] and "longitude" in first_data["address"]:
                    lat, lon = first_data["address"]["latitude"], first_data["address"]["longitude"]
                    print(lat, lon)
                else:
                    print("Error: La dirección del cliente no tiene latitud o longitud.")
            else:
                print("Error: No se encontraron datos de cliente.")
            
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
    
    available_slots = []

    try:
        available_slots = await check_availability_time(request.time, business_units, request.jobType)

        if not available_slots:
            print("No available slots found.")
        if not available_slots:
            print("No available slots found.")
    except Exception as e:
        print(f"Error checking availability: {e}")


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
        # ✅ CREAR CLIENTE Y OBTENER SU ID
        customer_response = await create_customer(job_request.customer)
        customer_id = customer_response["customer_id"]
        location_id = customer_response["location_id"]

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

@app.post("/rescheduleAppointmentTimeAvailability")
async def rescheduleAppointmentTimeAvailability (data: utils.ReSchedulaDataToolRequest):
    print("Processing re scheduling time availability request...")
    data = data.args
    access_token = await get_access_token()
    customer_id = await get_customer(data.name)

    print("Getting job data ...")
    try:
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
                job_type_id = jobs_data_json["data"][0].get("jobTypeId")
                business_unit_id = jobs_data_json["data"][0].get("businessUnitId")
                print(f"JOB DATA: {job_type_id, business_unit_id}")
                print("Job achieved ✅")
        else:
            print("Error getting job data.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting appointment id: {e}")
        return {"error": "Error when making external request."}

    print("Getting slots availables...")
    try:
        slots_availables = await check_availability_time(data.newSchedule, business_unit_id, job_type_id)
        if slots_availables:
            return slots_availables
        else:
            print("No slots availables.")
            return "No slots availables."
    except requests.exceptions.RequestException as e:
        print(f"Error getting slots availables: {e}")
        return {"error": "Error when making external request."}

@app.post("/rescheduleAppointment")
async def reschedule_appointment(data: utils.ReSchedulaDataToolRequest): 
    print("Processing re scheduling request...")
    data = data.args
    print(f"Request data: {data}")
    access_token = await get_access_token()
    
    customer_id = await get_customer(data.name)
    
    print("Getting appointment id ...")
    try:
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
                technician_id = jobs_data_json["data"][0]["jobGeneratedLeadSource"].get("employeeId")
        else:
            print("Error getting job data.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting appointment id: {e}")
        return {"error": "Error when making external request."}

    if technician_id is not None:
        print("Unassign technician...")
        if not isinstance(technician_id, list):
            technician_id = [technician_id]
        url_unassign = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/appointment-assignments/unassign-technicians"
        payload = {
            "jobAppointmentId": appointment_id,
            "technicianIds": technician_id
        }
        response_unassign = requests.patch(url_unassign, json=payload, headers=headers)
        if response_unassign.status_code == 200:
            print("Unassign technician request processed successfully ✅")
    else:
        print("No tecnician assingned to this job")

    if not appointment_id:
        return {"error": "No valid calendar was found for the client."}
    
    print("Rescheduling appointment...")
    try:
        url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/appointments/{appointment_id}/reschedule"
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        start_time = datetime.fromisoformat(data.newSchedule)
        end_time = start_time + timedelta(hours=3)
        payload = {
            "start": data.newSchedule,
            "end": end_time.isoformat()     
        }

        # Realizar la solicitud PATCH
        response = requests.patch(url, json=payload, headers=headers)
            
        # Devolver la respuesta de la API externa
        if response.status_code == 200:
            print("Reschedule request processed successfully ✅")
            return response.json()
        else:
            return {"error": f"Request error: {response.status_code}", "details": response.text}
    except requests.exceptions.RequestException as e:
        return {"error": "Error when making external request."}

@app.post("/cancelAppointment")
async def cancel_appointment(data: utils.cancelJobAppointmentToolRequest):
    print("Processing cancellation request...")
    data = data.args
    try:
        customer_id = await get_customer(data.name)
        url_customer = f"https://api.servicetitan.io/crm/v2/tenant/488267682/customers/{customer_id}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        
        response_customer = requests.get(url_customer, headers=headers)
        if response_customer.status_code != 200:
            return {"error": "Error obtaining customer data.", "details": response_customer.text}
        
        customer_data_json = response_customer.json()
        customer_name = customer_data_json.get("name")

        # Obtener el jobId correspondiente al customer
        print("Getting job id ...")
        url_bookings = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/export/bookings"
        response_bookings = requests.get(url_bookings, headers=headers)

        if response_bookings.status_code != 200:
            return {"error": "Error obtaining reservations.", "details": response_bookings.text}

        bookings_data_json = response_bookings.json()
        job_id = None

        for entry in bookings_data_json.get("data", []):
            if entry.get("name") == customer_name:
                job_id = entry.get("jobId")
                break

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

@app.post("/getTime")
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



#dowload fastapi: pip install "fastapi[standard]"
#dowload dotenv: pip install python-dotenv (may come pre-installed in newer Python versions)
#dowload pytz: pip install pytz
#start the server: fastapi dev main.py