from datetime import datetime
from typing import List, Optional, Any, Dict, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# BASE TOOL REQUEST WRAPPER
# =============================================================================

T = TypeVar("T")

class ToolRequestWrapper(BaseModel, Generic[T]):
    args: T
    event: Optional[str] = None
    data: Optional[Any] = None

    model_config = {
        "extra": "allow"
    }


# =============================================================================
# ADDRESS
# =============================================================================

class Address(BaseModel):
    street: Optional[str] = Field(..., description="Street address of the customer")
    city: Optional[str] = Field(..., description="City of the customer")
    zip: Optional[str] = Field(..., description="Zip code of the customer")
    country: Optional[str] = Field(..., description="Country name")
    state: Optional[str] = Field(..., description="State name")

    model_config = ConfigDict(extra='allow')

class AddressCheckToolRequest(ToolRequestWrapper[Address]):
    pass


# =============================================================================
# LOCATION
# =============================================================================

class Location(BaseModel):
    name: str = Field(..., description="Location name")
    address: Address = Field(..., description="Address of the location")

class CreateLocationRequest(BaseModel):
    customerId: int = Field(..., description="ID of the existing customer")
    location: Location = Field(..., description="Location to be added for the customer")

class CreateLocationToolRequest(ToolRequestWrapper[CreateLocationRequest]):
    pass


# =============================================================================
# CUSTOMER
# =============================================================================

class CustomerCreateRequest(BaseModel):
    name: str = Field(default="John Tester", description="Name of the customer")
    type: Optional[str] = "Residential"
    locations: List[Location] = Field(..., description="Locations for the customer")
    address: Optional[Address] = None
    number: str = Field(..., description="Phone number of the customer")
    email: str = Field(..., description="Email address of the customer")

class CustomerFindRequest(BaseModel):
    number: Optional[str] = Field(None, description="Phone number of the customer")

class CreateCustomerToolRequest(ToolRequestWrapper[CustomerCreateRequest]):
    pass

class FindCustomerToolRequest(ToolRequestWrapper[CustomerFindRequest]):
    pass


# =============================================================================
# JOB
# =============================================================================

class JobCreateRequest(BaseModel):
    customerId: int = Field(..., description="ID of the customer")
    locationId: int = Field(..., description="ID of the location")
    jobTypeId: int = Field(..., description="ID of the job type")
    priority: str = Field(..., description="Priority of the job request")
    businessUnitId: int = Field(..., description="ID of the business unit")
    campaignId: int = Field(..., description="ID of the campaign")
    jobStartTime: str = Field(..., description="Start time in ISO 8601 format")
    jobEndTime: str = Field(..., description="End time in ISO 8601 format")
    summary: str = Field(..., description="Brief summary of the job request")

class JobCreateToolRequest(ToolRequestWrapper[JobCreateRequest]):
    pass

class CancelJobAppointment(BaseModel):
    jobId: int = Field(..., description="ID of the job to cancel")
    reasonId: int = Field(..., description="ID of the cancellation reason")
    memo: str = Field(..., description="Notes or memo for the cancellation")

class CancelJobAppointmentToolRequest(ToolRequestWrapper[CancelJobAppointment]):
    pass

class UpdateJobSummary(BaseModel):
    jobId: int = Field(..., description="ID of the job")
    info: str = Field(..., description="Summary")

class UpdateJobSummaryToolRequest(ToolRequestWrapper[UpdateJobSummary]):
    pass


# =============================================================================
# APPOINTMENTS
# =============================================================================

class FindAppointmentData(BaseModel):
    customerId: int = Field(..., description="ID of the customer")

class FindAppointmentToolRequest(ToolRequestWrapper[FindAppointmentData]):
    pass


# =============================================================================
# RESCHEDULE
# =============================================================================

class ReScheduleData(BaseModel):
    newSchedule: str = Field(..., description="Requested time for the job in ISO 8601 format")
    jobTypeId: int = Field(..., description="ID of the job type to check availability for")
    businessUnitId: int = Field(..., description="ID of the business unit to check availability for")
    appointmentId: Optional[int] = Field(None, description="ID of the appointment to be rescheduled")
    employeeId: Optional[int] = Field(None, description="ID of the employee (technician) associated with the appointment")

class ReScheduleToolRequest(ToolRequestWrapper[ReScheduleData]):
    pass


# =============================================================================
# BOOKING (INBOUND)
# =============================================================================

class RequestArgs(BaseModel):
    time: str = Field(..., description="Requested time for the job in ISO 8601 format")
    jobTypeId: int = Field(..., description="ID of the job type")

class BookingRequest(BaseModel):
    args: RequestArgs

    model_config = {
        "extra": "allow"
    }


# =============================================================================
# BOOKING (OUTBOUND)
# =============================================================================

class RequestArgsOutbound(BaseModel):
    time: str = Field(..., description="Requested time for the job in ISO 8601 format")

    model_config = {
        "extra": "allow"
    }

class BookingRequestOutbound(BaseModel):
    args: RequestArgsOutbound

    model_config = {
        "extra": "allow"
    }

class JobCreateRequestOutbound(BaseModel):
    name: str = Field(default="John Tester", description="Name of the customer")
    priority: str
    jobStartTime: str = Field(..., description="Scheduled date in YYYY-MM-DD format")
    jobEndTime: str = Field(..., description="Scheduled date in YYYY-MM-DD format")
    summary: str = Field(..., description="Brief summary of the job request")

class JobCreateToolRequestOutbound(ToolRequestWrapper[JobCreateRequestOutbound]):
    pass


# =============================================================================
# LOGGING HELPER
# =============================================================================

def log_response(context: str, data: Any):
    print(f"=== {context} ===")
    if isinstance(data, list):
        for item in data:
            print(item)
    else:
        print(data)
