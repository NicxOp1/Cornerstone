""" from datetime import datetime, timedelta
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

class BookingRequest(BaseModel):
    name: str = Field(..., description="Name of the customer")
    address: str = Field(..., description="Address of the customer")
    locName: str = Field(description="Location name")
    time: str = Field(..., description="Time of the job")
    jobType: int = Field(...,description="ID of the job type")
    locations: Location = Field(..., description="Locations for the customer") """



from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any


# Log function to display responses in a readable format
def log_response(context: str, data: Any):
    print(f"=== {context} ===")
    if isinstance(data, list):
        for item in data:
            print(item)
    else:
        print(data)


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
    street: Optional[str] = Field(..., description="Street address of the customer")
    city: Optional[str] = Field(..., description="City of the customer")
    zip: Optional[str] = Field(..., description="Zip code of the customer")


class Location(BaseModel):
    name: str = Field(..., description="Location name")
    address: Address = Field(..., description="Address of the location")


class BookingRequest(BaseModel):
    name: str = Field(..., description="Name of the customer")
    address: str = Field(..., description="Full address of the customer, e.g., '123 Main St, City, Zip'")
    locName: str = Field(..., description="Location name where the job will be performed")
    time: str = Field(..., description="Requested time for the job in ISO 8601 format")
    jobType: int = Field(..., description="ID of the job type")
    locations: Location = Field(..., description="Details about the location")


class TechnicianAvailabilityRequest(BaseModel):
    startsOnOrAfter: str = Field(..., description="Start time for checking technician availability")
    endsOnOrBefore: str = Field(..., description="End time for checking technician availability")
    skillBasedAvailability: bool = Field(..., description="Whether to filter technicians by required skills")


class BookingAvailabilityRequest(BaseModel):
    fromDate: str = Field(..., description="Start date for checking booking availability")
    toDate: str = Field(..., description="End date for checking booking availability")
