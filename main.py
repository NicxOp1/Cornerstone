""" from datetime import datetime, date, timedelta
from fastapi import FastAPI, Request, Response, HTTPException
import requests
import utils as utils
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

AUTH_URL_INT = os.getenv("AUTH_URL_INT")
AUTH_URL = os.getenv("AUTH_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
APP_ID = os.getenv("APP_ID")

async def get_access_token():
    try:
        print("Fetching access token...")
        response = requests.post(
            AUTH_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
        )
        print(f"Token response status: {response.status_code}")
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

async def validate_technician_availability(start_time: str, end_time: str, skill_based: bool):
    try:
        print("Validating technician availability...")
        url = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity"
        access_token = await get_access_token()
        headers = {
            "Authorization": access_token,
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        payload = {
            "startsOnOrAfter": start_time,
            "endsOnOrBefore": end_time,
            "skillBasedAvailability": skill_based
        }
        response = requests.post(url, headers=headers, json=payload)
        print(f"Technician availability response status: {response.status_code}")
        if response.status_code == 200:
            availability = response.json()
            utils.log_response("Technician Availability", availability)
            is_available = availability.get('available', False)
            print(f"Technician availability result: {is_available}")
            return is_available
        else:
            print(f"Error fetching technician availability: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching technician availability")
    except Exception as e:
        print(f"Exception while validating technician availability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def validate_available_slots(start_date: str, end_date: str):
    try:
        print("Validating available slots...")
        url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/export/bookings?from={start_date}&to={end_date}"
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
            utils.log_response("Bookings", bookings)
            print("Available slots validated successfully.")
            return True  # Implement additional logic if necessary
        else:
            print(f"Error fetching bookings: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching bookings")
    except Exception as e:
        print(f"Exception while validating available slots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

app = FastAPI()

@app.get("/")
def read_root():
    print("Root endpoint accessed.")
    return {"status": "Service is up"}

@app.post("/bookSlot")
async def booking_request(data: utils.BookingRequest):

    try:
        print("Processing booking request...")
        print(f"Request data: {data}")

        # Validate job type
        if not await validate_job_type(data.jobType):
            print("Job type validation failed.")
            return {"error": "Invalid job type"}

        # Validate work area
        if not await validate_work_area(data.address):
            print("Work area validation failed.")
            return {"error": "Service not available in the given area"}

        # Validate technician availability
        start_time = datetime.fromisoformat(data.time.replace("Z", "+00:00"))
        end_time = (start_time + timedelta(hours=3)).isoformat()

        if not await validate_technician_availability(start_time, end_time, True):
            print("Technician availability validation failed.")
            return {"error": "No technicians available for the requested time"}

        # Validate available slots
        if not await validate_available_slots(start_time, end_time):
            print("Available slots validation failed.")
            return {"error": "No available slots for the requested time"}

        print("Booking request validated successfully.")
        return {"status": "Booking request validated successfully"}

    except Exception as e:
        print(f"Exception while processing booking request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

#dowload fastapi: pip install "fastapi[standard]"
#dowload dotenv: pip install python-dotenv (may come pre-installed in newer Python versions)
#start the server: fastapi dev main.py

 """





from datetime import datetime, date, timedelta
from fastapi import FastAPI, Request, Response, HTTPException
import requests
import utils as utils
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

AUTH_URL_INT = os.getenv("AUTH_URL_INT")
AUTH_URL = os.getenv("AUTH_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
APP_ID = os.getenv("APP_ID")

async def get_access_token():
    try:
        print("Fetching access token...")
        response = requests.post(
            AUTH_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
        )
        print(f"Token response status: {response.status_code}")
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

""" async def validate_technician_availability(start_time: str, end_time: str, skill_based: bool):
    try:
        print("Validating technician availability...")
        url = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity"
        access_token = await get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "ST-App-Key": APP_ID,
            "Content-Type": "application/json",
        }
        payload = {
            "startsOnOrAfter": start_time,
            "endsOnOrBefore": end_time,
            "skillBasedAvailability": skill_based
        }
        # Serialize datetime to ISO format string
        serialized_payload = json.dumps(payload)
        response = requests.post(url, headers=headers, data=serialized_payload)
        print(f"Technician availability response status: {response.status_code}")
        if response.status_code == 200:
            availability = response.json()
            utils.log_response("Technician Availability", availability)
            is_available = availability.get('available', False)
            print(f"Technician availability result: {is_available}")
            return is_available
        else:
            print(f"Error fetching technician availability: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching technician availability")
    except Exception as e:
        print(f"Exception while validating technician availability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) """

async def validate_available_slots(start_date: str, end_date: str):
    try:
        print("Validating available slots...")
        url = f"https://api.servicetitan.io/crm/v2/tenant/{TENANT_ID}/export/bookings?from={start_date}&to={end_date}"
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
            utils.log_response("Bookings", bookings)
            print("Available slots validated successfully.")
            return True  # Implement additional logic if necessary
        else:
            print(f"Error fetching bookings: {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching bookings")
    except Exception as e:
        print(f"Exception while validating available slots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

app = FastAPI()

@app.get("/")
def read_root():
    print("Root endpoint accessed.")
    return {"status": "Service is up"}

@app.post("/bookSlot")
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
        """ 
        if not await validate_technician_availability(start_time, end_time, True):
            print("Technician availability validation failed.")
            return {"error": "No technicians available for the requested time"} """

        # Validate available slots
        if not await validate_available_slots(start_time, end_time):
            print("Available slots validation failed.")
            return {"error": "No available slots for the requested time"}

        print("Booking request validated successfully.")
        return {"status": "Booking request validated successfully"}

    except Exception as e:
        print(f"Exception while processing booking request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

#dowload fastapi: pip install "fastapi[standard]"
#dowload dotenv: pip install python-dotenv (may come pre-installed in newer Python versions)
#start the server: fastapi dev main.py
