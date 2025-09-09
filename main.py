from fastapi import FastAPI,HTTPException      # Supports for type hints
from models import User
from typing import Optional,List  # Most widely used data validation library for python
from pydantic import BaseModel   # Supports for enumerations
from enum import Enum

from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app:FastAPI):
    await startup_db_client(app)
    yield
    await shutdown_db_client(app)

async def startup_db_client(app):
    app.mongo_client=AsyncIOMotorClient(
        "mongodb+srv://jeet:jeet123@cluster0.zjxrylz.mongodb.net/"
    )
    app.mongodb=app.mongo_client.get_database("college")
    print("MongoDB Connected")

#method to close the database connection
async def shutdown_db_client(app):
    app.mongo_client.close()
    print("database disconnected")


#creating a server with python FastApI
app=FastAPI(lifespan=lifespan)


@app.post("/api/v1/create-user",response_model=User)
async def insert_user(user:User):
    result=await app.mongodb["users"].insert_one(user.model_dump())
    inserted_user=await app.mongodb["users"].find_one({"_id":result.inserted_id})
    return inserted_user



@app.get("/")
async def root():
    return {"message": "FastAPI server is running 🚀"}


# Read all users

@app.get("/api/v1/read-all-users",response_model=List[User])
async def read_users():
    users=await app.mongodb["users"].find().to_list(None)
    return users

# Read one user by email_address
@app.get("/api/v1/read-user/{email_address}",response_model=User)
async def read_user_by_email(email_address:str):
    user=await app.mongodb["users"].find_one({"email_address":email_address})
    if user is None:
        raise HTTPException(status_code=404,detail="User Not Found")
    return user


# U <=== Update
# Update user
class UpdateUserDTO(BaseModel):
    other_names:List[str]=None
    age : int = None

@app.put("/api/v1/update-user/{email_address}",response_model=User)
async def update_user(email_address:str,user_update:UpdateUserDTO):
    updated_result=await app.mongodb["users"].update_one(
        {"email_address":email_address},{"$set":user_update.model_dump(exclude_unset=True)}
        )    
    if updated_result.modified_count==0:
        raise HTTPException(status_code=404,detail="User not found or no update needed")
    updated_user=await app.mongodb["users"].find_one({"email_address":email_address})
    return updated_result

#delete
@app.delete("/api/v1/delete-user/{email_address}",response_model=dict)
async def delete_user_by_email(email_address:str):
    delete_result=await app.mongodb["users"].delete_one({"email_address":email_address})
    if delete_result.deleted_count==0:
        raise HTTPException(status_code=404,detail="User Not Found")
    return {"message":"User deleted Successfully"}



