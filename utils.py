from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict


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
    state: Optional[str] = Field(..., description="State name")
    
    model_config = ConfigDict(
        extra='allow',
    )

class Location(BaseModel):
    name: str = Field(..., description="Location name")
    address: Address = Field(..., description="Address of the location")

class RequestArgs(BaseModel):
    name: str = Field(..., description="Name of the customer")
    address: str = Field(description="Full address of the customer, e.g., '123 Main St, City, Zip'")
    locName: str = Field(description="Location name where the job will be performed")
    time: str = Field(..., description="Requested time for the job in ISO 8601 format")
    jobType: int = Field(..., description="ID of the job type")
    locations: Location = Field(description="Details about the location")
    isCustomer: bool = Field(..., description="If the user is a customer")
    number: int = Field(..., description="phone number of the customer")
    email: str = Field(..., description="email address of the customer")

class BookingRequest(BaseModel):
    args: RequestArgs

    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }



class CustomerCreateRequest(BaseModel):
    name: str = Field(default="John Tester", description="Name of the customer")
    type: Optional[str] = "Residential"
    locations: List[Location] = Field(..., description="Locations for the customer")
    address: Optional[Address] = None
    number: str = Field(..., description="Phone number of the customer")
    email: str = Field(..., description="Email address of the customer")

class JobCreateRequest(BaseModel):
    customer: CustomerCreateRequest  # Cliente a crear
    jobTypeId: int  # ✅ Tipo de trabajo (obligatorio)
    priority: str  # ✅ Prioridad (Normal, Alta, etc.)
    businessUnitId: int  # ✅ ID de la unidad de negocio
    campaignId: int  # ✅ ID de la campaña de marketing
    jobStartTime: str = Field(..., description="Scheduled date in YYYY-MM-DD format")
    jobEndTime: str = Field(..., description="Scheduled date in YYYY-MM-DD format")
    summary: str = Field(..., description="Brief summary of the job request")

class ToolRequest(BaseModel):
    event: Optional[str] = None
    data: Optional[Any] = None
    args: Any

    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }

class addressCheckToolRequest(ToolRequest):
    args: Address
    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }

class jobCreateToolRequest(ToolRequest):
    args: JobCreateRequest
    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }



class FindAppointmentData(BaseModel):
    name: str = Field(..., description="Name of the customer")
    number: str = Field(..., description="Phone number of the customer")

class FindAppointmentDataToolRequest(ToolRequest):
    args: FindAppointmentData
    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }

class ReScheduleData(BaseModel):
    newSchedule: str = Field(..., description="Requested time for the job in ISO 8601 format")
    jobTypeId: int = Field(..., description="ID of the job type to check availability for")
    businessUnitId: int = Field(..., description="ID of the business unit to check availability for")
    appointmentId: Optional[int] = Field(None, description="ID of the appointment to be rescheduled")
    employeeId: Optional[int] = Field(None, description="ID of the employee (technician) associated with the appointment")

class ReSchedulaDataToolRequest(ToolRequest):
    args: ReScheduleData
    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }



class cancelJobAppointment(BaseModel):
    jobId: int = Field(..., description="ID of the job to cancel")
    reasonId: int = Field(..., description="ID of the cancellation reason")
    memo: str = Field(..., description="Notes or memo for the cancellation")

class cancelJobAppointmentToolRequest(ToolRequest):
    args: cancelJobAppointment
    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }


class updateJobSummary(BaseModel):
    number: str = Field(..., description="Phone number of the customer")
    name: str = Field(..., description="Name of the customer")
    info: str = Field(description="Summary")

class updateJobSummaryToolRequest(ToolRequest):
    args: updateJobSummary
    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }


#Outbound 

class RequestArgsOutbound(BaseModel):
    time: str = Field(..., description="Requested time for the job in ISO 8601 format")

    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }

class BookingRequestOutbound(BaseModel):
    args: RequestArgsOutbound

    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }


class JobCreateRequestOutbound(BaseModel):
    name: str = Field(default="John Tester", description="Name of the customer")
    priority: str  # ✅ Prioridad (Normal, Alta, etc.)
    jobStartTime: str = Field(..., description="Scheduled date in YYYY-MM-DD format")
    jobEndTime: str = Field(..., description="Scheduled date in YYYY-MM-DD format")
    summary: str = Field(..., description="Brief summary of the job request")

class jobCreateToolRequestOutbound(ToolRequest):
    args: JobCreateRequestOutbound
    model_config = {
        "extra": "allow"  # Permite aceptar datos adicionales sin error
    }