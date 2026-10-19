from pydantic import BaseModel, Field
from typing import Optional


class ServiceInfo(BaseModel):
    name: str = Field(
        description="Name of the service offered by the business."
    )

    price: Optional[float] = Field(
        default=None,
        description="Price of the service."

    )

    duration_minutes: Optional[int] = Field(
        default=None,
        description="Duration of the service in minutes."
    )


class BusinessInfo(BaseModel):
    business_name: Optional[str] = Field(
        default=None,
        description="Business name."
    )

    business_type: Optional[str] = Field(
        default=None,
        description="Type of business."
    )

    services: list[ServiceInfo] = Field(
        default_factory=list,
        description="Services offered by the business."
    )

    booking_deposit: Optional[float] = Field(
        default=None,
        description="Required booking deposit."
    )

    opening_time: Optional[str] = Field(
        default=None,
        description="Opening time in HH:MM format."
    )

    closing_time: Optional[str] = Field(
        default=None,
        description="Closing time in HH:MM format."
    )

    working_days: list[str] = Field(
        default_factory=list,
        description="Days when the business is open."
    )

    location: Optional[str] = Field(
        default=None,
        description="Business location or address."
    )

    contact_phone: Optional[str] = Field(
        default=None,
        description="Business contact phone number."
    )

    contact_email: Optional[str] = Field(
        default=None,
        description="Business contact email."
    )

    booking_length_minutes: Optional[int] = Field(
        default=None,
        description="Standard booking length in minutes."
    )
    number_of_resources: Optional[int] = Field(
        default=None,
        description="""
        Number of independently bookable resources available
        for the business, such as pitches, rooms, chairs,
        doctors, courts, tables, or similar resources.
        """
    )



class BookingRequest(BaseModel):
    business_name: Optional[str] = Field(
        default=None,
        description="Name of the business the customer wants to book."
    )

    booking_date: Optional[str] = Field(
        default=None,
        description="""
        Date requested by the customer.
        Preserve relative expressions exactly, such as:
        today, tomorrow, day after tomorrow,
        Monday, Tuesday, Friday.
        If the customer provides an exact date,
        return it as YYYY-MM-DD.
        """
    )

    booking_time: Optional[str] = Field(
        default=None,
        description="Requested booking start time in HH:MM format."
    )

    duration_minutes: Optional[int] = Field(
        default=None,
        description="Requested booking duration in minutes."
    )

    service_name: Optional[str] = Field(
        default=None,
        description="Name of the service or resource the customer wants to book."
    )

    customer_name: Optional[str] = Field(
        default=None,
        description="Customer's name."
    )

    customer_phone: Optional[str] = Field(
        default=None,
        description="Customer's phone number."
    )