
from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pathlib import Path as FilePath
from typing import Annotated, Optional, Literal
from pydantic import BaseModel, Field
import json

app = FastAPI()

# Always use patients.json from the same directory as this Python file
DATA_FILE = FilePath(__file__).resolve().parent / "patients.json"


# Load patient data
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


# Save patient data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


@app.get("/")
def hello():
    return {"message": "Patient Management System API"}


@app.get("/about")
def about():
    return {
        "message": "A fully functional API to manage your patient record"
    }


@app.get("/view")
def view():
    return load_data()


@app.get("/patient/{patient_id}")
def view_patient(
    patient_id: str = Path(
        ...,
        description="Required ID of the patient",
        example="P001"
    )
):
    data = load_data()

    if patient_id in data:
        return data[patient_id]

    raise HTTPException(
        status_code=404,
        detail="Patient not found"
    )


@app.get("/sort")
def sort_patients(
    sort_by: str = Query(
        ...,
        description="Sort on the basis of height, weight, or BMI"
    ),
    order: str = Query(
        "asc",
        description="Ascending or descending order"
    )
):
    valid_fields = ["height", "weight", "bmi"]

    if sort_by not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field. Sort from {valid_fields}"
        )

    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid order. Select between asc or desc"
        )

    data = load_data()

    reverse_order = order == "desc"

    sorted_data = sorted(
        data.values(),
        key=lambda patient: patient.get(sort_by, 0),
        reverse=reverse_order
    )

    return sorted_data


# Patient model for creating a patient
class Patient(BaseModel):

    id: Annotated[
        str,
        Field(
            ...,
            description="ID of the patient",
            examples=["P001", "P004"]
        )
    ]

    name: Annotated[
        str,
        Field(
            ...,
            description="Name of the patient",
            min_length=1
        )
    ]

    city: Annotated[
        str,
        Field(..., description="City where the patient is living")
    ]

    age: Annotated[
        int,
        Field(..., ge=1, description="Age of the patient")
    ]

    gender: Annotated[
        Literal["male", "female", "others"],
        Field(..., description="Gender of the patient")
    ]

    height: Annotated[
        float,
        Field(..., gt=0, description="Height in meters")
    ]

    weight: Annotated[
        float,
        Field(..., gt=0, description="Weight in kg")
    ]

    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"


# Patient model for updating existing records
class PatientUpdate(BaseModel):

    name: Annotated[
        Optional[str],
        Field(default=None, min_length=1)
    ]

    city: Annotated[
        Optional[str],
        Field(
            default=None,
            description="City where the patient is living"
        )
    ]

    age: Annotated[
        Optional[int],
        Field(default=None, ge=1, description="Age of the patient")
    ]

    gender: Annotated[
        Optional[Literal["male", "female", "others"]],
        Field(default=None, description="Gender of the patient")
    ]

    height: Annotated[
        Optional[float],
        Field(default=None, gt=0, description="Height in meters")
    ]

    weight: Annotated[
        Optional[float],
        Field(default=None, gt=0, description="Weight in kg")
    ]


# Create a new patient
@app.post("/create", status_code=201)
def create_patient(patient: Patient):
    data = load_data()

    if patient.id in data:
        raise HTTPException(
            status_code=400,
            detail="Patient already exists"
        )

    patient_data = patient.model_dump()
    patient_data.pop("id")

    # Save calculated BMI and verdict along with other fields
    patient_data["bmi"] = patient.bmi
    patient_data["verdict"] = patient.verdict

    data[patient.id] = patient_data
    save_data(data)

    return JSONResponse(
        status_code=201,
        content={"message": "Patient created successfully"}
    )


# Update an existing patient
@app.put("/edit/{patient_id}")
def update_patient(
    patient_id: str,
    patient_update: PatientUpdate
):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(
            status_code=404,
            detail="Patient ID not found in database"
        )

    # Get existing patient information
    existing_patient_info = data[patient_id].copy()

    # Update only fields explicitly provided by the user
    updated_patient_info = patient_update.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    existing_patient_info.update(updated_patient_info)

    # Recalculate BMI and verdict after updating height or weight
    height = existing_patient_info["height"]
    weight = existing_patient_info["weight"]

    bmi = round(weight / (height ** 2), 2)

    if bmi < 18.5:
        verdict = "Underweight"
    elif bmi < 25:
        verdict = "Normal"
    elif bmi < 30:
        verdict = "Overweight"
    else:
        verdict = "Obese"

    existing_patient_info["bmi"] = bmi
    existing_patient_info["verdict"] = verdict

    # Save updated record in JSON
    data[patient_id] = existing_patient_info
    save_data(data)

    return {
        "message": "Patient updated successfully",
        "patient": {
            "id": patient_id,
            **existing_patient_info
        }
    }
    
@app.delete('/delete/patient_id')  
def delete_patient(patient_id:str):
    data = load_data();
    if patient_id not in data:
        raise HTTPException(status_code=404,detail = 'Patient not found') 
    del data[patient_id]
    save_data(data)
    return JSONResponse(status_code=200,content={'message':'deleted'})
