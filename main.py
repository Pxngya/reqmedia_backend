from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId
from typing import List, Optional

app = FastAPI()

# ตั้งค่า CORS ให้ React เข้าถึงได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- เชื่อมต่อ MongoDB ---
client = AsyncIOMotorClient("mongodb+srv://yos_db_user:00kJUBG53vLFZIqH@cluster0.jivkpdj.mongodb.net/?appName=Cluster0 ",
    tlsAllowInvalidCertificates=True)
db = client.req_media_db
user_collection = db.users
task_collection = db.tasks

# --- Models (โครงสร้างข้อมูล) ---
class CheckUser(BaseModel):
    employee_id: str

class RegisterUser(BaseModel):
    employee_id: str
    fullname: str
    password: str
    department: str

class LoginUser(BaseModel):
    employee_id: str
    password: str

class TaskModel(BaseModel):
    title: str
    department: str
    date: str
    start_time: str
    end_time: str
    color: str

class TaskModel(BaseModel):
    title: str
    title_other: Optional[str] = None  # เพิ่มช่องกรอก "อื่นๆ"
    # department: str  <-- เอาออกตามที่สั่ง
    date: str
    start_time: str
    end_time: str
    color: str
    file_data: Optional[str] = None  # เก็บไฟล์แบบ Base64
    file_name: Optional[str] = None

# --- API สำหรับระบบ User ---

@app.post("/check-user")
async def check_user(user: CheckUser):
    found = await user_collection.find_one({"employee_id": user.employee_id})
    return {"exists": True if found else False}

@app.post("/register")
async def register(user: RegisterUser):
    existing = await user_collection.find_one({"employee_id": user.employee_id})
    if existing:
        raise HTTPException(status_code=400, detail="รหัสพนักงานนี้มีในระบบแล้ว")
    result = await user_collection.insert_one(user.dict())
    return {"status": "success"}

@app.post("/login")
async def login(user: LoginUser):
    found = await user_collection.find_one({"employee_id": user.employee_id, "password": user.password})
    if found:
        return {"status": "success", "user": found["fullname"], "dept": found["department"]}
    raise HTTPException(status_code=401, detail="รหัสผ่านไม่ถูกต้อง")

# --- API สำหรับจัดการ Task (งานในปฏิทิน) ---

@app.get("/tasks")
async def get_tasks():
    tasks = []
    async for task in task_collection.find():
        task["id"] = str(task["_id"])
        del task["_id"]
        tasks.append(task)
    return tasks

@app.post("/tasks")
async def create_task(task: TaskModel):
    result = await task_collection.insert_one(task.dict())
    return {"id": str(result.inserted_id)}

@app.put("/tasks/{task_id}")
async def update_task(task_id: str, task: TaskModel):
    try:
        result = await task_collection.replace_one({"_id": ObjectId(task_id)}, task.dict())
        if result.modified_count == 1:
            return {"status": "success"}
        raise HTTPException(status_code=404, detail="ไม่พบงานที่ต้องการแก้ไข")
    except:
        raise HTTPException(status_code=400, detail="รูปแบบ ID ไม่ถูกต้อง")

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    try:
        await task_collection.delete_one({"_id": ObjectId(task_id)})
        return {"status": "success"}
    except:
        raise HTTPException(status_code=400)
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)