from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any


# Log function to display responses in a readable format
def log_response(context: str, data: Any):
    print(f"=== {context} ===")
    if isinstance(data, list):
        for item in data:
            print(item)
    else:
        print(data)

class Address(BaseModel):
    street: Optional[str] = Field(..., description="Street address of the customer")
    city: Optional[str] = Field(..., description="City of the customer")
    zip: Optional[str] = Field(..., description="Zip code of the customer")
    country: Optional[str] = Field(..., description="Country name")

    model_config = ConfigDict(
        extra='allow',
    )

class Location(BaseModel):
    name: str = Field(..., description="Location name")
    address: Address = Field(..., description="Address of the location")

class CustomerCreateRequest(BaseModel):
    name: str = Field(default="John Tester", description="Name of the customer")
    type: Optional[str] = "Residential"
    locations: List[Location] = Field(..., description="Locations for the customer")
    address: Optional[Address] = None

""" class JobCreateRequest(BaseModel):
    customer: CustomerCreateRequest
    # customerId: int
    # locationId: int
    # jobTypeId: int = Field(default=1, description="ID of the job type")
    jobStartTime: str = Field(
        default=(datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
        description="Scheduled date in YYYY-MM-DD format",
    )
    jobEndTime: str = Field(
        default=(datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
        description="Scheduled date in YYYY-MM-DD format",
    )
    # scheduledDate: str = Field(
    #     default=datetime.now().strftime("%Y-%m-%d"), description="Scheduled date in YYYY-MM-DD format"
    # )
    # scheduledTime: str = Field(default=datetime.now().strftime("%H:%M"), description="Scheduled time in HH:MM format")
    # summary: str = Field(..., description="Summary of the job")
    # description: str = Field(..., description="Detailed description of the job")
 """

class JobCreateRequest(BaseModel):
    customer: CustomerCreateRequest  # Cliente a crear
    jobTypeId: int  # ✅ Tipo de trabajo (obligatorio)
    priority: str  # ✅ Prioridad (Normal, Alta, etc.)
    businessUnitId: int  # ✅ ID de la unidad de negocio
    campaignId: int  # ✅ ID de la campaña de marketing

    jobStartTime: str = Field(
        default=(datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
        description="Scheduled date in YYYY-MM-DD format",
    )
    jobEndTime: str = Field(
        default=(datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
        description="Scheduled date in YYYY-MM-DD format",
    )

class ToolRequest(BaseModel):
    event: Optional[str] = None
    data: Optional[Any] = None
    args: Any
class jobCreateToolRequest(ToolRequest):
    args: JobCreateRequest

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

class ScheduleData(BaseModel):
    possible_times: list[str]
    start: list[str]
    end: list[str]



""" class Address(BaseModel):
    street: Optional[str] = "1003 W Clark St"
    city: Optional[str] = "Urbana"
    zip: Optional[str] = "61801"
    country: str = Field(..., description="Country name")

    model_config = ConfigDict(
        extra='allow',
    )

class Location(BaseModel):
    name: str
    address: Address """