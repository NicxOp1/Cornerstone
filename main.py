from typing import Union
from datetime import datetime, date
from fastapi import FastAPI, Request, Response
import json

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/filter_data")
async def filter_data(request: Request):
    body = await request.body()
    if not body:
        return []
    data = json.loads(body.decode('utf-8'))
    filtered_data = []
    for item in data:
        start_date = datetime.strptime(item["start"], "%Y-%m-%dT%H:%M:%SZ").date()
        if start_date == date.today():
            filtered_data.append(item)
    return filtered_data

#dowload fastapi: pip install "fastapi[standard]"
#start the server: fastapi dev main.py