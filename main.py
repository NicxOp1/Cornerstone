from datetime import datetime, date
from fastapi import FastAPI, Request, Response, HTTPException
import requests
import utils as utils
from dotenv import load_dotenv
import json
import os

load_dotenv()

AUTH_URL_INT = os.getenv("AUTH_URL_INT")
AUTH_URL = os.getenv("AUTH_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
APP_ID = os.getenv("APP_ID")

async def get_access_token():
    try:
        response = requests.post(
            AUTH_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET},
        )
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Authentication failed: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get access token: {str(e)}")

app = FastAPI()

@app.get("/")
def read_root():
    return 

# Create new customer in system: https://developer.servicetitan.io/api-details/#api=tenant-crm-v2&operation=Customers_Create&definition=Crm.V2.Customers.CustomerAddress
@app.post("/bookSlot")
async def bookingRequest(data: utils.BookingRequest):

    url = f"https://api.servicetitan.io/jpm/v2/tenant/{TENANT_ID}/jobs"

    # Replace these placeholders with actual token and app key
    access_token = await get_access_token()
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    try:
        payload = data.model_dump(by_alias=True)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(data, "data")
            return True
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to get jobs: {response.text}",
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

#dowload fastapi: pip install "fastapi[standard]"
#dowload dotenv: pip install python-dotenv (puedo venir por defecto en versiones nuevas de python)
#start the server: fastapi dev main.py