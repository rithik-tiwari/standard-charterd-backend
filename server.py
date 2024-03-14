from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from Main2 import process_image
import os
import json
import base64
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://example.com",
    "https://sub.example.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

class UserDetails(BaseModel):
    name: str
    age: str
    unique_id: str
    adharcard_number: str
    income_proof: str
    photo_url: str
    signature_url: str
    adhar_url : str
    dob:str
class User(UserDetails):
    pass
upload_folder = "uploads"

os.makedirs(upload_folder, exist_ok=True)
json_file_path = 'users.json'
def read_user_login_info():
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
            return data.get("users", [])
    except FileNotFoundError:
        return []
def write_user_login_info(users):
    data = {"users": users}
    with open(json_file_path, "w") as file:
        json.dump(data, file, indent=2)

@app.post("/user-info/")
async def create_user_info(user_info: UserDetails):
    user_login_info = read_user_login_info()
    user_login_info.append(user_info.model_dump())
    write_user_login_info(user_login_info)
    return user_info

@app.post("/user-photo/{unique_id}")
async def upload_user_photo(unique_id: str, photo: str):
    photo_path = f"userPic/{unique_id}.jpg"
    photo_path.write(base64.b64decode(photo))
    with open(photo_path, "wb") as buffer:
        buffer.write(await photo.read())
    
    # Update user info with photo URL
    users = read_user_login_info()
    for user in users:
        if user["unique_id"] == unique_id:
            user["photo_url"] = photo_path
            break
    
    return {"photo_url": photo_path}

@app.post("/signature/{unique_id}")
async def upload_signature(unique_id: str, photo: UploadFile = File(...)):
    sig_path = f"signature/{unique_id}.jpg"
    with open(sig_path, "wb") as buffer:
        buffer.write(await photo.read())
    
    # Update user info with photo URL
    users = read_user_login_info()
    for user in users:
        if user["unique_id"] == unique_id:
            user["signature_url"] = sig_path
            break
    
    
    return {"photo_url": sig_path}

@app.post("/uploadAdhaar/{unique_id}")
async def upload_image(unique_id: str, photo: UploadFile = File(...)):
    try:
        file_path = f"uploads/{unique_id}.jpg"
        with open(file_path, "wb") as f:
            f.write(await photo.read())
        
        response =  process_image(file_path)
        response = response.replace(" ", "")
        users = read_user_login_info()
        current_user = {}
        for user in users:
            if user["unique_id"] == unique_id:
                user["adhar_url"] = file_path
                current_user = user
                break
        
        if (current_user and response == current_user['adharcard_number']):
            return JSONResponse(response)
        else:
            return JSONResponse({"error": "please provide a valid photo"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))