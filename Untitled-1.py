# Main API endpoint: https://developer.servicetitan.io/api-details/#api=tenant-dispatch-v2&operation=Capacity_GetList
@router.post("/get-available-slots/")
async def get_available_slots(availabilityRequest: utils.getAvailableSlotsToolRequest):

    start_time = availabilityRequest.args.start_time
    end_datetime = datetime.strptime(availabilityRequest.args.start_time, "%Y-%m-%d %H:%M") + timedelta(minutes=240)
    end_time = end_datetime.strftime("%Y-%m-%d %H:%M")

    access_token = await get_access_token()
    intervals = utils.generate_intervals(start_time, end_time)

    external_api_url = f"https://api.servicetitan.io/dispatch/v2/tenant/{TENANT_ID}/capacity"
    headers = {
        "Authorization": access_token,
        "ST-App-Key": APP_ID,
        "Content-Type": "application/json",
    }

    available_slots = []
    # Iterate over intervals and call the external API
    for interval in intervals:
        payload = {
            "startsOnOrAfter": start_time,  # interval["starttime"],
            "endsOnOrBefore": end_time,  # interval["endtime"],
            "businessUnitIds": [
                1097
            ],  # get business unit list: https://developer.servicetitan.io/api-details/#api=tenant-settings-v2&operation=BusinessUnits_GetList
            "jobTypeId": 1124,
            "skillBasedAvailability": True,
        }
        response = requests.post(external_api_url, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            availabilities = data.get("availabilities")
            print("Len of availabilities: ", len(availabilities))
            for slot in availabilities:
                print("start: ", slot["start"], "end: ", slot["end"])
                print(slot)
                if slot["isAvailable"]:
                    print("slots are available")
                    # if previous_slot and previous_slot["endtime"] == interval["starttime"]:
                    #     # Extend the previous slot's end time
                    #     previous_slot["endtime"] = interval["endtime"]
                    # else:
                    # # Add a new slot
                    #     previous_slot = interval
                    available_slot = {
                        "starttime": slot["start"],
                        "endtime": slot["end"],
                        "starttime_UTC": slot["startUtc"],
                        "endtime_UTC": slot["endUtc"],
                    }
                    available_slots.append(available_slot)
                # Ensure Service Length Fits:
                # Filter out slots that don’t meet the required service duration (e.g., 30 minutes).

        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"External API call failed with status code {response.status_code}: {response.text}",
            )
        break

    # Return available slots in string format
    return {"available_slots": available_slots}













from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any


class ToolRequest(BaseModel):
    event: Optional[str] = None
    data: Optional[Any] = None
    args: Any


# Helper function to generate 15-minute intervals
def generate_intervals(start_time: str, end_time: str):

    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
        intervals = []
        while start_dt < end_dt:
            interval_end = start_dt + timedelta(minutes=15)
            if interval_end > end_dt:
                break
            intervals.append(
                {"starttime": start_dt.strftime("%Y-%m-%d %H:%M"), "endtime": interval_end.strftime("%Y-%m-%d %H:%M")}
            )
            start_dt = interval_end
        return intervals
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format. Use 'YYYY-MM-DD HH:MM'.")


class Address(BaseModel):
    street: Optional[str] = "1003 W Clark St"
    city: Optional[str] = "Urbana"
    zip: Optional[str] = "61801"

    model_config = ConfigDict(
        extra='allow',
    )



class Location(BaseModel):
    name: str
    address: Address


class CustomerCreateRequest(BaseModel):
    name: str = Field(default="Vanshika", description="Name of the customer")
    type: Optional[str] = "Residential"
    locations: Location = Field(..., description="Locations for the customer")
    


class JobCreateRequest(BaseModel):
    customer: CustomerCreateRequest
    # customerId: int
    # locationId: int
    # jobTypeId: int = Field(default=1, description="ID of the job type")
    jobStartTime: str = Field(
        default=(datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
        description="Scheduled date in YYYY-MM-DD format",
    )
    jobEndTime: str = Field(
        default=(datetime.now() + timedelta(hours=5, minutes=15)).strftime("%Y-%m-%d %H:%M"),
        description="Scheduled date in YYYY-MM-DD format",
    )
    # scheduledDate: str = Field(
    #     default=datetime.now().strftime("%Y-%m-%d"), description="Scheduled date in YYYY-MM-DD format"
    # )
    # scheduledTime: str = Field(default=datetime.now().strftime("%H:%M"), description="Scheduled time in HH:MM format")
    # summary: str = Field(..., description="Summary of the job")
    # description: str = Field(..., description="Detailed description of the job")

class jobCreateToolRequest(ToolRequest):
    args: JobCreateRequest

class getAvailableSlotsRequest(BaseModel):
    start_time: str
    # end_time: str

class getAvailableSlotsToolRequest(ToolRequest):
    args: getAvailableSlotsRequest


    # Modelos de entrada y salida
class JobRequest(BaseModel):
    job_id: int
    latitude: float
    longitude: float

class JobResponse(BaseModel):
    job_type: str
    business_units: str
    distance_miles: float
    distance_category: str
    direction: str
