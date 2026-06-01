from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import httpx
import asyncio
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import utils as utils
import logging
from dotenv import load_dotenv
import os
import json
import pytz
import math
import re
import requests

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
MAPS_AUTH = os.getenv("MAPS_AUTH")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
OFFICE_EMAIL = "info@cornerstoneservicesne.com"

DIRECT_LINES = {
    "john": "6033274334",
    "josh": "6033275618",
}

# =============================================================================
# CALL SESSION STORE (in-memory, TTL 2 hours)
# =============================================================================

CALL_SESSION_TTL = 7200  # 2 hours in seconds

# { callId: { "_ts": timestamp, "field": "value", ... } }
call_sessions: dict = {}

# Human-readable labels for each field Harmony collects
FIELD_LABELS = {
    "customerName":   "Name",
    "customerPhone":  "Phone number",
    "street":         "Street address",
    "city":           "City",
    "state":          "State",
    "zip":            "ZIP code",
    "serviceType":    "Service type",
    "preferredDate":  "Appointment date",
    "preferredTime":  "Appointment time",
    "summary":        "Additional notes",
    "customerId":     "Customer ID",
    "locationId":     "Location ID",
    "businessUnitId": "Business unit",
    "jobTypeId":      "Job type",
    "campaignId":     "Campaign",
}

def _cleanup_sessions():
    """Remove sessions older than CALL_SESSION_TTL."""
    now = time.time()
    expired = [k for k, v in call_sessions.items()
               if now - v.get("_ts", 0) > CALL_SESSION_TTL]
    for k in expired:
        del call_sessions[k]

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    missing = [e["loc"][-1] for e in errors]
    logger.error(f"[ValidationError] Missing/invalid fields: {missing} — body: {await request.body()}")
    return JSONResponse(
        status_code=400,
        content={"error": f"Missing or invalid required fields: {missing}"}
    )

CITIES = {
    "agawam", "amesbury", "attleboro", "barnstable", "beverly", "boston", "braintree", "brockton", "cambridge", "chelsea",
    "chicopee", "easthampton", "everett", "fall river", "fitchburg", "framingham", "franklin", "gardner", "gloucester", "greenfield",
    "haverhill", "holyoke", "lawrence", "leominster", "lowell", "lynn", "malden", "marlborough", "medford", "melrose",
    "methuen", "new bedford", "newburyport", "newton", "north adams", "northampton", "palmer", "peabody", "pittsfield", "quincy",
    "randolph", "revere", "salem", "somerville", "southbridge", "springfield", "taunton", "waltham", "watertown", "west springfield",
    "westfield", "weymouth", "winthrop", "woburn", "worcester", "bridgewater", "amherst", "berlin", "claremont", "concord",
    "dover", "franklin", "keene", "laconia", "lebanon", "manchester", "nashua", "portsmouth", "rochester", "somersworth",
    "acton", "arlington", "atkinson", "derry", "hudson", "windham", "hampton"
}

VALID_STATES = {
    "ma", "nh", "new hampshire", "massachusetts"
}

# Auxiliary functions


async def get_access_token():
    try:
        print("Fetching access token...")
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                AUTH_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type": "client_credentials",
                      "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
            )
        if response.status_code == 200:
            token_data = response.json()
            print("Access token fetched successfully. ✅")
            return token_data.get("access_token")
        else:
            print(f"Error fetching token: {response.text}")
            raise HTTPException(status_code=response.status_code,
                                detail=f"Authentication failed: {response.text}")
    except httpx.RequestError as e:
        print(f"Exception while fetching token: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get access token: {str(e)}")


def massachusetts_to_utc(dt_str: str) -> str:
    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ")
    eastern_tz = pytz.timezone("America/New_York")
    dt_eastern = eastern_tz.localize(dt)
    dt_utc = dt_eastern.astimezone(pytz.utc)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_to_eastern(dt_str: str) -> str:
    """Convierte una fecha UTC de ServiceTitan a hora Eastern (Massachusetts).
    Maneja DST automáticamente a través de pytz."""
    if dt_str.endswith("Z"):
        dt_str = dt_str.replace("Z", "+00:00")
    dt_utc = datetime.fromisoformat(dt_str)
    eastern_tz = pytz.timezone("America/New_York")
    dt_eastern = dt_utc.astimezone(eastern_tz)
    return dt_eastern.strftime("%Y-%m-%dT%H:%M:%SZ")


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
        async with httpx.AsyncClient(timeout=15.0) as client:
            response_customers = await client.get(url_customers, headers=headers)

        if response_customers.status_code == 200:
            customers_data_json = response_customers.json()

            if not customers_data_json.get("data"):
                print("Error: No customers found by phone.")
                return {"error": "Customer not found by phone."}

            customer_data = customers_data_json["data"][0]
            customer = {
                "id": customer_data.get("id"),
                "name": customer_data.get("name")
            }
            print("Customer found by phone ✅")
            return customer

        print(f"Error: Unexpected response {response_customers.status_code} - {response_customers.text}")
        return {"error": f"Unexpected response status: {response_customers.status_code}"}

    except httpx.RequestError as e:
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
        if not customer.name or not customer.number:
            print("Error: Customer name and number are required.")
            return {"error": "Customer name and number are required."}

        if customer.locations and isinstance(customer.locations, list) and len(customer.locations) > 0:
            location = customer.locations[0]
        else:
            print("Error: Customer location is missing.")
            return {"error": "Customer location is missing."}

        if hasattr(location, 'address') and location.address:
            location.address.country = location.address.country or "USA"
            location.address.state = location.address.state or "MA"

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

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            print("Response Status Code:", response.status_code)

            if response.status_code != 200:
                print(f"Error creating customer: {response.text}")
                return {"error": f"Failed to create customer: {response.text}"}

            data = response.json()
            customer_id = data.get("id")
            location_id = data.get("locations", [{}])[0].get("id")

            if not customer_id or not location_id:
                print("Error: Customer or Location ID missing in API response.")
                return {"error": "Customer or Location ID missing in API response."}

            print("Created customer successfully ✅")
            print({"customer_id": customer_id, "location_id": location_id})

            contact_url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers/{customer_id}/contacts"

            if customer.number:
                clean_number = re.sub(r"\D", "", customer.number)
                mobile_payload = {
                    "type": "MobilePhone",
                    "value": clean_number,
                    "memo": "Customer phone number"
                }
                response_mobile = await client.post(contact_url, headers=headers, json=mobile_payload)
                if response_mobile.status_code == 200:
                    print("Mobile contact data added successfully ✅")
                else:
                    print(f"Error adding mobile contact data: {response_mobile.text}")
                    raise HTTPException(
                        status_code=response_mobile.status_code,
                        detail=f"Failed to add mobile contact data: {response_mobile.text}",
                    )

            if customer.email:
                email_payload = {
                    "type": "Email",
                    "value": customer.email,
                    "memo": "Customer email"
                }
                response_email = await client.post(contact_url, headers=headers, json=email_payload)
                if response_email.status_code == 200:
                    print("Email contact data added successfully ✅")
                else:
                    print(f"Error adding email contact data: {response_email.text}")
                    raise HTTPException(
                        status_code=response_email.status_code,
                        detail=f"Failed to add email contact data: {response_email.text}",
                    )

        print("Customer created successfully with contact data added ✅")
        return {"customerId": customer_id, "locationId": location_id}
    except ValueError as e:
        print(f"[create_customer] ValueError: {e}")
        return {"error": "Failed to create customer due to invalid data."}


async def check_availability_time(time, business_units, job_type, access_token=None):
    print("Checking availability time...")

    if isinstance(business_units, int):
        business_units = [business_units]
    elif isinstance(business_units, list):
        business_units = [int(bu) for bu in business_units]

    # Parsear tiempo inicial
    if "Z" in time:
        time = time.replace("Z", "+00:00")

    time_parts = time.split('T')
    date_parts = time_parts[0].split('-')
    date_parts[2] = date_parts[2].zfill(2)
    corrected_time = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}T{time_parts[1]}"

    try:
        start_time = datetime.fromisoformat(corrected_time)
    except ValueError:
        print(f"Invalid time format: {corrected_time}")
        return []

    if not access_token:
        access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    # Intentos (máx 5), sumando 7 días cada vez
    for attempt in range(5):
        print(f"Attempt {attempt + 1}/5...")

        current_start = start_time + timedelta(days=attempt * 7)
        current_end = current_start + timedelta(days=13)
        current_end = current_end.replace(
            hour=23, minute=59, second=0, microsecond=0)

        starts_on_or_after = current_start.replace(
            tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        ends_on_or_before = current_end.strftime('%Y-%m-%dT%H:%M:%SZ')

        payload = {
            "startsOnOrAfter": starts_on_or_after,
            "endsOnOrBefore": ends_on_or_before,
            "businessUnitIds": business_units,
            "jobTypeId": job_type,
            "skillBasedAvailability": True
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity",
                    headers=headers,
                    json=payload
                )

            if response.status_code == 200:
                data = response.json()
                slots = [
                    {"start": slot["start"], "end": slot["end"]}
                    for slot in data.get("availabilities", []) if slot.get("isAvailable")
                ]

                if slots:
                    print("Checking availability time completed ✅")
                    return slots
                else:
                    print(f"No slots on attempt {attempt + 1}, retrying...")
            else:
                print(f"❌ Error in API response: {response.status_code} {response.text}")

        except httpx.RequestError as e:
            print(f"❌ Exception occurred: {str(e)}")

    print("No available slots found after 5 attempts.")
    return []


async def get_technicians_by_businessUnitId(businessUnitId):
    print(f"Getting technicians for Business Unit ID: {businessUnitId}...")

    try:
        url_technicians = f"https://api.servicetitan.io/settings/v2/tenant/{TENANT_ID}/technicians"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response_technicians = await client.get(url_technicians, headers=headers)

        if response_technicians.status_code == 200:
            print("Technicians fetched successfully.")
            response_data = response_technicians.json()
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

    except httpx.RequestError as e:
        print(f"Error occurred: {str(e)}")
        return {"error": "Checking technicians by business unit failed."}


# Endpoints
@app.get("/")
def read_root():
    print("Root endpoint accessed.")
    return {"status": "Service is up"}


@app.post("/getTime")
async def get_current_boston_time():
    print("Processing getTime request... 🔄")
    eastern = pytz.timezone("America/New_York")
    now_eastern = datetime.now(eastern)

    print(f"Current Boston time: {now_eastern.strftime('%Y-%m-%dT%H:%M:%S')}")
    print("getTime request completed ✅")

    return now_eastern.strftime("%Y-%m-%dT%H:%M:%S")


@app.post("/checkWorkArea")
async def check_work_area(data: utils.AddressCheckToolRequest):
    print("Processing checkWorkArea request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.Address.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    PO_BOX_SALEM = (42.775, -71.217)
    R = 3958.8

    city = data.city.strip().lower()
    state = data.state.strip().lower()

    # Validación rápida: estado permitido y ciudad en lista única
    if state in VALID_STATES and city in CITIES:
        print("Coordinates Checked In List ✅")
        return {"message": "City is in the working area (matched from predefined list)."}

    # Fallback: geocodificación + cálculo de distancia
    address = f"{data.street}, {data.city}, {data.country}"
    if not address:
        print("error: The direction is not valid.")
        return {"error": "The direction is not valid."}

    url_geocode = f"https://geocode.xyz/{address}?json=1&auth={MAPS_AUTH}"
    resp = await asyncio.to_thread(requests.get, url_geocode)
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
        print(
            "error: The provided zip code does not match the address. The zip code should be: {expected_zip_clean}")
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
    a = math.sin(delta_lat/2)**2 + math.cos(lat1) * \
        math.cos(lat2)*math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = round(R * c, 2)

    if distance > 50:
        print("error: There are no services available in the area.")
        return {"error": "There are no services available in the area."}
    print("checkWorkArea request completed ✅")
    return {"message": "Address is in the working area."}


@app.post("/findCustomer")
async def find_customer(data: utils.FindCustomerToolRequest):
    print("Processing findCustomer request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.CustomerFindRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    phone = args_obj.number

    try:
        url_customers = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/customers?phone={phone}"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response_customers = await client.get(url_customers, headers=headers)
        if response_customers.status_code == 200:
            customers_data_json = response_customers.json()
            customers_list = customers_data_json.get("data", [])
            if not customers_list:
                print("No customers found by phone.")
                return {
                    "found": False,
                    "message": "No customers found by phone."
                }
            customers = [
                {"customerId": c.get("id"), "customerName": c.get("name")}
                for c in customers_list
            ]
            print(f"Found {len(customers)} customers by phone ✅")
            return customers
        print(f"Error: Unexpected response {response_customers.status_code} - {response_customers.text}")
        return {"error": f"Unexpected response status: {response_customers.status_code}"}
    except httpx.RequestError as e:
        print(f"Error getting customers: {e}")
        return {"error": "Error when making external request."}


@app.post("/getCustomerLocations")
async def get_customer_locations(data: utils.FindAppointmentToolRequest):

    if isinstance(data.args, dict):
        args_obj = utils.FindAppointmentData.parse_obj(data.args)
    else:
        args_obj = data.args

    customer_id = args_obj.customerId

    print(f"Getting locations for customer ID: {customer_id}... 🔄")

    try:
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        url_location = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/locations?customerId={customer_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response_location = await client.get(url_location, headers=headers)

        if response_location.status_code == 200:
            locations_data = response_location.json().get("data", [])
            if not locations_data:
                return {"error": "No locations found for this customer."}

            locations = []
            for loc in locations_data:
                addr = loc.get("address", {})
                formatted_address = f"{addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state', '')}".strip(
                    ", ")
                locations.append({
                    "locationId": loc.get("id"),
                    "locationAddress": formatted_address
                })

            print(f"Locations found: {len(locations)} ✅")
            return {
                "customerId": customer_id,
                "locations": locations
            }
        else:
            print(
                f"Failed to get locations: {response_location.status_code} - {response_location.text}")
            return {"error": "Failed to retrieve locations."}

    except Exception as e:
        print(f"Error fetching locations: {e}")
        return {"error": str(e)}


@app.post("/createLocation")
async def create_location(data: utils.CreateLocationToolRequest):
    print("Processing createLocation request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.CreateLocationRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json"
    }

    payload = {
        "customerId": data.customerId,
        "name": data.location.name,
        "address": data.location.address.dict()
    }

    url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/locations"
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"Error creating location: {response.text}")
        return {"error": response.text}

    print("createLocation request completed ✅")
    # Suponiendo que response es lo que devuelve el POST al crear la location:
    response_data = response.json()
    location_id = response_data.get("id")

    return {
        "message": "Location created successfully.",
        "locationId": location_id
    }


@app.post("/createCustomer")
async def create_customer_endpoint(data: utils.CreateCustomerToolRequest):
    print("Processing createCustomer request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.CustomerCreateRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    try:
        response = await create_customer(data)

        if "error" in response:
            print(f"{response['error']}.")
            return {"error": response["error"]}

        print("createCustomer request completed ✅")
        return {
            "customerId": response.get("customerId"),
            "locationId": response.get("locationId"),
            "status": "created"
        }

    except Exception as e:
        print(f"Error processing createCustomer request: {e}")
        return {"error": str(e)}


@app.post("/checkAvailability")
@app.post("/checkAvailability/")
async def check_availability(data: utils.BookingRequest):
    print("Processing checkAvailability request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.RequestArgs.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    print("Checking business unit...")
    try:
        url_jobTypes = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/job-types/"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response_jobTypes = await client.get(url_jobTypes, headers=headers)

        if response_jobTypes.status_code == 200:
            job_types_json = response_jobTypes.json()
            job_types = {job_type["id"]: job_type["businessUnitIds"]
                         for job_type in job_types_json["data"]}
            business_units = job_types.get(data.jobTypeId, None)
            if not business_units:
                print(f"Job Type {data.jobTypeId} not found in response.")
                return {"error": f"Job type {data.jobTypeId} not found. Cannot determine business unit."}
        else:
            print(f"❌ Failed to fetch job types: {response_jobTypes.status_code} - {response_jobTypes.text}")
            return {"error": "Could not retrieve job type information. Please try again."}

        print("Business Unit Checked ✅")
    except ValueError:
        return {"error": "Checking business unit failed."}

    available_slots = []

    try:
        available_slots = await check_availability_time(data.time, business_units, data.jobTypeId, access_token)

        if not available_slots:
            print("No available slots found.")
            start_date = datetime.strptime(data.time, "%Y-%m-%dT%H:%M:%SZ")
            end_date = start_date + timedelta(days=42)
            return {"message": f"No availability found when checking up to {end_date.strftime('%Y-%m-%d')}"}
    except Exception as e:
        print(f"Error checking availability: {e}")

    print("Checking availability ✅")
    return {
        'businessUnitId': business_units[0],
        'available_slots': available_slots
    }


@app.post("/createJob")
async def create_job(data: utils.JobCreateToolRequest):
    print("Processing createJob request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.JobCreateRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    try:
        if not data.locationId:
            logger.error(f"[createJob] ❌ locationId is missing. customerId={data.customerId}. Agent must call /getCustomerLocations first.")
            return {"error": "locationId is required. Please call getCustomerLocations first to get the correct locationId for this customer."}

        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }

        # Asegurar formato de fecha con "Z"
        if not data.jobStartTime.endswith("Z"):
            data.jobStartTime += "Z"
        if not data.jobEndTime.endswith("Z"):
            data.jobEndTime += "Z"

        # Convertir fechas a UTC desde hora local de Massachusetts
        data.jobStartTime = massachusetts_to_utc(data.jobStartTime)
        data.jobEndTime = massachusetts_to_utc(data.jobEndTime)

        # Construir el payload para ServiceTitan
        payload = {
            "customerId": data.customerId,
            "locationId": data.locationId,
            "businessUnitId": data.businessUnitId,
            "jobTypeId": data.jobTypeId,
            "priority": data.priority,
            "campaignId": data.campaignId,
            "appointments": [
                {
                    "start": data.jobStartTime,
                    "end": data.jobEndTime,
                    "arrivalWindowStart": data.jobStartTime,
                    "arrivalWindowEnd": data.jobEndTime,
                }
            ],
            "scheduledDate": datetime.now().strftime("%Y-%m-%d"),
            "scheduledTime": datetime.now().strftime("%H:%M"),
            "summary": data.summary
        }

        # Enviar request a ServiceTitan
        url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
        print(f"[createJob] Payload enviado a ServiceTitan: {json.dumps(payload, indent=2)}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        print(f"[createJob] Status code: {response.status_code}")
        print(f"[createJob] Response body: {response.text}")

        if response.status_code != 200:
            print(f"[createJob] ❌ Error creando job: {response.status_code} - {response.text}")
            return {"error": f"Failed to create job: {response.text}"}

        job_data = response.json()
        job_id = job_data.get("id")
        appointment_id = job_data.get("lastAppointmentId")
        print(f"[createJob] ✅ Job creado: jobId={job_id}, appointmentId={appointment_id}")
        return {
            "status": "Job booked",
            "jobId": job_id,
            "appointmentId": appointment_id
        }

    except httpx.RequestError as e:
        print(f"[createJob] ❌ Request error: {str(e)}")
        return {"error": "Unexpected request error"}


@app.post("/findAppointments")
async def find_appointments(data: utils.FindAppointmentToolRequest):
    print("Processing findAppointments request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.FindAppointmentData.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj
    customer_id = data.customerId

    print(f"Using provided customerId: {customer_id}")

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    def to_eastern(ts: str) -> str:
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        dt_utc = datetime.fromisoformat(ts)
        return dt_utc.astimezone(pytz.timezone("America/New_York")).isoformat()

    async def fetch_jobs_by_status(job_status: str):
        url = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
            f"?customerId={customer_id}&jobStatus={job_status}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        print(f"Error fetching jobs with status {job_status}: {resp.text}")
        return []

    async def fetch_appointments_for_job(job: dict, appointment_status: str):
        job_id = job.get("id")
        url = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/appointments"
            f"?jobId={job_id}&status={appointment_status}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching appointments for job {job_id}: {resp.text}")
            return []
        appointments = []
        for a in resp.json().get("data", []):
            appointments.append({
                "jobId": job.get("id"),
                "businessUnitId": job.get("businessUnitId"),
                "jobTypeId": job.get("jobTypeId"),
                "summary": job.get("summary", ""),
                "employeeId": job.get("jobGeneratedLeadSource", {}).get("employeeId"),
                "appointmentId": a.get("id"),
                "start": to_eastern(a.get("start")),
                "end": to_eastern(a.get("end")),
            })
        return appointments

    # Fetch los 3 estados en paralelo
    scheduled_jobs, dispatched_jobs, working_jobs = await asyncio.gather(
        fetch_jobs_by_status("Scheduled"),
        fetch_jobs_by_status("Dispatched"),
        fetch_jobs_by_status("InProgress"),
    )
    print(f"Found {len(scheduled_jobs)} Scheduled, {len(dispatched_jobs)} Dispatched, {len(working_jobs)} Working jobs")

    # Fetch appointments en paralelo para todos los jobs
    all_tasks = (
        [(job, "Scheduled") for job in scheduled_jobs] +
        [(job, "Dispatched") for job in dispatched_jobs] +
        [(job, "Working") for job in working_jobs]
    )
    all_results = await asyncio.gather(*[fetch_appointments_for_job(job, status) for job, status in all_tasks])

    scheduled_appointments = []
    dispatched_appointments = []
    working_appointments = []

    idx = 0
    for job in scheduled_jobs:
        scheduled_appointments.extend(all_results[idx]); idx += 1
    for job in dispatched_jobs:
        dispatched_appointments.extend(all_results[idx]); idx += 1
    for job in working_jobs:
        working_appointments.extend(all_results[idx]); idx += 1

    # Si no hay nada encontrado
    if not any([
        scheduled_appointments,
        dispatched_appointments,
        working_appointments,
    ]):
        print("No appointments found.")
        return {"message": "No scheduled, dispatched or working appointments found for this customer."}

    print("findAppointments request completed ✅")
    return {
        "scheduledAppointments": scheduled_appointments,
        "dispatchedAppointments": dispatched_appointments,
        "workingAppointments": working_appointments
    }


@app.post("/findPastAppointments")
async def find_past_appointments(data: utils.FindAppointmentToolRequest):
    print("Processing findPastAppointments request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.FindAppointmentData.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj
    customer_id = data.customerId

    print(f"Using provided customerId: {customer_id}")

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    def to_eastern_past(ts: str) -> str:
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        dt_utc = datetime.fromisoformat(ts)
        return dt_utc.astimezone(pytz.timezone("America/New_York")).isoformat()

    async def fetch_jobs_by_status_past(job_status: str):
        url = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"
            f"?customerId={customer_id}&jobStatus={job_status}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        print(f"Error fetching jobs with status {job_status}: {resp.text}")
        return []

    async def fetch_appointments_for_job_past(job: dict, appointment_status: str):
        job_id = job.get("id")
        url = (
            f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/appointments"
            f"?jobId={job_id}&status={appointment_status}"
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching appointments for job {job_id}: {resp.text}")
            return []
        appointments = []
        for a in resp.json().get("data", []):
            appointments.append({
                "jobId": job.get("id"),
                "businessUnitId": job.get("businessUnitId"),
                "jobTypeId": job.get("jobTypeId"),
                "summary": job.get("summary", ""),
                "employeeId": job.get("jobGeneratedLeadSource", {}).get("employeeId"),
                "appointmentId": a.get("id"),
                "start": to_eastern_past(a.get("start")),
                "end": to_eastern_past(a.get("end")),
            })
        return appointments

    hold_jobs, done_jobs, canceled_jobs = await asyncio.gather(
        fetch_jobs_by_status_past("Hold"),
        fetch_jobs_by_status_past("Completed"),
        fetch_jobs_by_status_past("Canceled"),
    )
    print(f"Found {len(hold_jobs)} Hold, {len(done_jobs)} Done, {len(canceled_jobs)} Canceled jobs")

    all_past_tasks = (
        [(job, "Hold") for job in hold_jobs] +
        [(job, "Done") for job in done_jobs] +
        [(job, "Canceled") for job in canceled_jobs]
    )
    all_past_results = await asyncio.gather(*[fetch_appointments_for_job_past(job, status) for job, status in all_past_tasks])

    hold_appointments = []
    done_appointments = []
    canceled_appointments = []

    idx = 0
    for job in hold_jobs:
        hold_appointments.extend(all_past_results[idx]); idx += 1
    for job in done_jobs:
        done_appointments.extend(all_past_results[idx]); idx += 1
    for job in canceled_jobs:
        canceled_appointments.extend(all_past_results[idx]); idx += 1

    if not any([hold_appointments, done_appointments, canceled_appointments]):
        print("No past appointments found.")
        return {"message": "No past appointments found for this customer."}

    print("findPastAppointments request completed ✅")
    return {
        "holdAppointments": hold_appointments,
        "doneAppointments": done_appointments,
        "canceledAppointments": canceled_appointments,
    }


@app.post("/rescheduleAppointmentTimeAvailability")
async def reschedule_appointment_time_availability(data: utils.ReScheduleToolRequest):
    print("Processing rescheduleAppointmentTimeAvailability request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.ReScheduleData.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    job_type_id = data.jobTypeId
    business_unit_id = data.businessUnitId
    desired_time = data.newSchedule

    if not job_type_id or not business_unit_id:
        print("Missing jobTypeId or businessUnitId in request.")
        return {"error": "Missing jobTypeId or businessUnitId in request."}

    print(
        f"Checking availability for businessUnitId={business_unit_id}, jobTypeId={job_type_id}, around {desired_time}...")
    try:
        slots_available = await check_availability_time(desired_time, business_unit_id, job_type_id)
        if slots_available:
            slots_eastern = [
                {"start": utc_to_eastern(s["start"]), "end": utc_to_eastern(s["end"])}
                for s in slots_available
            ]
            print("rescheduleAppointmentTimeAvailability request completed ")
            return {"availableSlots": slots_eastern}
        else:
            print("No slots available.")
            start_date = datetime.strptime(
                data.newSchedule, "%Y-%m-%dT%H:%M:%SZ")
            end_date = start_date + timedelta(days=42)
            return {"message": f"No availability found when checking up to {end_date.strftime('%Y-%m-%d')}"}
    except httpx.RequestError as e:
        print(f"Error getting slots: {e}")
        return {"error": "Error when requesting availability."}


@app.post("/rescheduleAppointment")
async def reschedule_appointment(data: utils.ReScheduleToolRequest):
    print("Processing rescheduleAppointment request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.ReScheduleData.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    access_token = await get_access_token()

    appointment_id = data.appointmentId
    technician_id = data.employeeId
    new_schedule = data.newSchedule

    # 1. Unassign technician if provided
    st_headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    if technician_id:
        tech_ids = technician_id if isinstance(technician_id, list) else [technician_id]
        print(f"Unassigning technician(s) {tech_ids} from appointment {appointment_id}...")
        url_unassign = (
            f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}"
            "/appointment-assignments/unassign-technicians"
        )
        unassign_payload = {
            "jobAppointmentId": appointment_id,
            "technicianIds": tech_ids
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp_unassign = await client.patch(url_unassign, json=unassign_payload, headers=st_headers)
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
    resch_payload = {
        "start": start_utc,
        "end": end_utc,
        "arrivalWindowStart": start_utc,
        "arrivalWindowEnd": end_utc
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.patch(url_resch, json=resch_payload, headers=st_headers)

    if resp.status_code == 200:
        print("rescheduleAppointment request completed ✅")
        return {"status": "rescheduleAppointment request processed successfully"}
    else:
        print(f"Failed to reschedule appointment: {resp.text}")
        return {
            "error": f"Request error: {resp.status_code}",
            "details": resp.text
        }


@app.post("/cancelAppointment")
async def cancel_appointment(data: utils.CancelJobAppointmentToolRequest):
    print("Processing cancelAppointment request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.CancelJobAppointment.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    # extraer directamente los datos necesarios
    job_id = data.jobId
    reason_id = data.reasonId
    memo = data.memo

    if not job_id:
        print("Missing jobId in request.")
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
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.put(url, headers=headers, json=payload)
    print(f"External API responded: {resp.status_code}")

    if resp.status_code == 200:
        # a veces el body viene vacío
        if not resp.text.strip():
            print("cancelAppointment request completed ✅")
            return {"message": "Job canceled successfully"}
        print("cancelAppointment request completed ✅")
        return resp.json()
    elif resp.status_code == 404:
        print("Job ID not found.")
        return {"error": "Job ID not found", "details": resp.json()}
    else:
        print(f"Failed to cancel job: {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail=resp.text)


@app.post("/updateJobSummary")
async def update_job_summary(data: utils.UpdateJobSummaryToolRequest):
    print("Processing updateJobSummary request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.UpdateJobSummary.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    job_id = data.jobId
    info = data.info

    if not job_id or not info:
        return {"error": "Missing required fields: jobId and info"}

    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    print(f"Fetching current summary for job ID {job_id}...")

    job_url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs/{job_id}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        job_resp = await client.get(job_url, headers=headers)

    if job_resp.status_code != 200:
        return {
            "error": f"Failed to fetch job data for job ID {job_id}",
            "status_code": job_resp.status_code,
            "details": job_resp.text
        }

    job_data = job_resp.json()
    current_summary = job_data.get("summary", "")

    new_summary = f"<p>{info}</p>"
    updated_summary = f"{current_summary}\n\n{new_summary}".strip() if current_summary else new_summary

    print(f"Updating summary for job ID {job_id}...")
    patch_url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs/{job_id}"
    patch_payload = {"summary": updated_summary}

    async with httpx.AsyncClient(timeout=15.0) as client:
        patch_resp = await client.patch(patch_url, headers=headers, json=patch_payload)

    if patch_resp.status_code == 200:
        print("updateJobSummary completed ✅")
        return {"status": "Job summary updated"}
    else:
        print(f"Failed to update job summary: {patch_resp.text}")
        return {
            "error": "Failed to update job summary.",
            "status_code": patch_resp.status_code,
            "details": patch_resp.text
        }


# Outbound

@app.post("/checkAvailabilityOutbound")
@app.post("/checkAvailabilityOutbound/")
async def check_availability_outbound(data: utils.BookingRequestOutbound):
    print("Processing checkAvailabilityOutbound request... 🔄")
    jobType = 5879699
    business_unit = 5878155

    if isinstance(data.args, dict):
        args_obj = utils.RequestArgsOutbound.parse_obj(data.args)
    else:
        args_obj = data.args

    data = args_obj

    print("Checking availability...")

    available_slots = []

    try:
        available_slots = await check_availability_time(data.time, business_unit, jobType)

        if not available_slots:
            print("No available slots found.")
            return {'message': 'No availability found.'}

    except Exception as e:
        print(f"Error checking availability: {e}")
    print("checkAvailabilityOutbound completed ✅")
    return {
        'available_slots': available_slots
    }


async def _resolve_call_id(request: Request, args_obj):
    """Get the Retell call_id from the request body's 'call' object,
    falling back to whatever the agent passed in args."""
    try:
        body = await request.json()
        call_obj = body.get("call") or {}
        cid = call_obj.get("call_id") or body.get("call_id")
        if cid:
            return cid
    except Exception:
        pass
    return getattr(args_obj, "callId", None)


@app.post("/storeCallData")
async def store_call_data(data: utils.StoreCallDataToolRequest, request: Request):
    print("Processing storeCallData request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.StoreCallDataRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    _cleanup_sessions()

    call_id = await _resolve_call_id(request, args_obj)
    if not call_id:
        print("[storeCallData] ❌ Could not determine call ID.")
        return {"error": "Could not determine the call ID for this session."}

    if call_id not in call_sessions:
        call_sessions[call_id] = {"_ts": time.time()}

    call_sessions[call_id][args_obj.field] = args_obj.value
    call_sessions[call_id]["_ts"] = time.time()

    print(f"[storeCallData] callId={call_id} | {args_obj.field} = {args_obj.value} ✅")
    return {"status": "stored", "field": args_obj.field, "value": args_obj.value}


@app.post("/getCallData")
async def get_call_data(data: utils.GetCallDataToolRequest, request: Request):
    print("Processing getCallData request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.GetCallDataRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    call_id = await _resolve_call_id(request, args_obj)
    session = call_sessions.get(call_id, {})

    # Build ordered field list (skip internal keys starting with _)
    fields = []
    for field, label in FIELD_LABELS.items():
        value = session.get(field)
        if value:
            fields.append({"field": field, "label": label, "value": value})

    if not fields:
        print(f"[getCallData] callId={call_id} — no data found")
        return {"fields": [], "readableScript": "I don't have any stored information for this call yet."}

    # Build readable script Harmony reads aloud
    readable = ". ".join([f"{f['label']}: {f['value']}" for f in fields])

    print(f"[getCallData] callId={call_id} — {len(fields)} fields ✅")
    return {"fields": fields, "readableScript": readable}


@app.post("/updateCallField")
async def update_call_field(data: utils.UpdateCallFieldToolRequest, request: Request):
    print("Processing updateCallField request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.UpdateCallFieldRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    call_id = await _resolve_call_id(request, args_obj)
    if not call_id:
        print("[updateCallField] ❌ Could not determine call ID.")
        return {"error": "Could not determine the call ID for this session."}

    if call_id not in call_sessions:
        print(f"[updateCallField] callId={call_id} not found, creating new session")
        call_sessions[call_id] = {"_ts": time.time()}

    old_value = call_sessions[call_id].get(args_obj.field, "—")
    call_sessions[call_id][args_obj.field] = args_obj.value
    call_sessions[call_id]["_ts"] = time.time()

    print(f"[updateCallField] callId={call_id} | {args_obj.field}: '{old_value}' → '{args_obj.value}' ✅")
    return {"status": "updated", "field": args_obj.field, "oldValue": old_value, "newValue": args_obj.value}


@app.post("/clearCallData")
async def clear_call_data(data: utils.ClearCallDataToolRequest, request: Request):
    print("Processing clearCallData request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.ClearCallDataRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    call_id = await _resolve_call_id(request, args_obj)
    if call_id and call_id in call_sessions:
        del call_sessions[call_id]
        print(f"[clearCallData] callId={call_id} cleared ✅")
        return {"status": "cleared"}

    print(f"[clearCallData] callId={call_id} not found (already cleared or expired)")
    return {"status": "not_found"}


@app.post("/getDirectLine")
async def get_direct_line(data: utils.DirectLineToolRequest):
    print("Processing getDirectLine request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.DirectLineRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    name = args_obj.name.strip().lower()

    for key, phone in DIRECT_LINES.items():
        if key in name:
            print(f"Direct line found for '{key}' ✅")
            return {"name": key.capitalize(), "phone": phone}

    print(f"No direct line found for '{name}'")
    return {"message": "We don't have contact information for that person. Is there anything else I can help you with?"}


def _send_gmail(subject: str, body: str):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("❌ Gmail credentials not configured (GMAIL_USER / GMAIL_APP_PASSWORD missing)")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = OFFICE_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


@app.post("/sendOfficeMessage")
async def send_office_message(data: utils.OfficeMessageToolRequest):
    print("Processing sendOfficeMessage request... 🔄")

    if isinstance(data.args, dict):
        args_obj = utils.OfficeMessageRequest.parse_obj(data.args)
    else:
        args_obj = data.args

    caller_info = ""
    if args_obj.callerName:
        caller_info += f"Caller: {args_obj.callerName}\n"
    if args_obj.callerPhone:
        caller_info += f"Phone: {args_obj.callerPhone}\n"

    subject = "Harmony - Customer Question Unanswered"
    body = (
        f"A caller had a question Harmony could not answer.\n\n"
        f"{caller_info}"
        f"Question: {args_obj.question}\n\n"
        f"Please follow up with the customer."
    )

    success = await asyncio.to_thread(_send_gmail, subject, body)

    if success:
        print("sendOfficeMessage completed ✅")
        return {"status": "Message sent to office successfully"}
    else:
        print("sendOfficeMessage failed ❌")
        return {"error": "Failed to send message. Please try again or call the office directly."}


# start the server: fastapi dev main.py
