from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status
import uuid
from app.models import Message # Assuming Message model is used for responses
from app import models
from app.api import deps
from app.core.config import settings

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("/", response_model=models.PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(
    *,
    db: Session = Depends(deps.get_db),
    property_in: models.PropertyCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new property.
    """
    property = models.Property.model_validate(property_in)
    db.add(property)
    db.commit()
    db.refresh(property)
    return property

@router.post("/url/", response_model=models.PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property_from_url(
    *,
    db: Session = Depends(deps.get_db),
    url: str,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new property from a Zillow URL.
    """
    from app.parsers import ZillowListingParserSelenium

    parser = ZillowListingParserSelenium(url)
    property_data = parser.parse()


    if not property_data:
        raise HTTPException(status_code=400, detail="Failed to parse property data from URL")

    property_in = models.PropertyCreate(** property_data)
    
    return create_property(db=db, property_in=property_in, current_user=current_user)



@router.get("/", response_model=list[models.PropertyRead])
def read_properties(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve properties.
    """
    properties = db.exec(select(models.Property).offset(skip).limit(limit)).all()
    return properties


@router.get("/{property_id}", response_model=models.PropertyRead)
def read_property(
    *,
    db: Session = Depends(deps.get_db),
    property_id: str,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get property by ID.
    """
    property = db.get(models.Property, property_id)
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    return property


# Add these imports at the top if they are not already there


# ... (keep existing imports and router definition)
# router = APIRouter(prefix="/properties", tags=["properties"])

# ... (keep existing routes like create_property, read_properties, etc.)


@router.delete("/{property_id}", response_model=Message)
def delete_property(
    *,
    db: Session = Depends(deps.get_db),
    property_id: uuid.UUID, # Use uuid.UUID since your model uses it
    current_user: models.User = Depends(deps.get_current_user), # Require superuser like create
) -> Message:
    """
    Delete a property by ID.
    """
    # Fetch the property object from the database
    property_to_delete = db.get(models.Property, property_id)

    # Check if the property exists
    if not property_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    # Delete the property from the session
    db.delete(property_to_delete)

    # Commit the transaction to the database
    db.commit()

    # Return a success message
    return Message(message="Property deleted successfully")


@router.delete("/properties/all", response_model=Message)
def delete_all_properties(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Message:
    """
    Delete all properties.
    """
    # Fetch all properties from the database
    properties = db.exec(select(models.Property)).all()

    # Delete all properties from the session
    for property in properties:
        db.delete(property)

    # Commit the transaction to the database
    db.commit()
    return Message(message="All properties deleted successfully")