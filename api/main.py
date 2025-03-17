from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from typing import Optional, Dict, Any, List
import requests
import json
import random
import time
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KEYCLOAK_URL = "http://keycloak:8080"
KEYCLOAK_REALM = "reports-realm"
KEYCLOAK_CLIENT_ID = "reports-api"
KEYCLOAK_CLIENT_SECRET = "oNwoLQdvJAvRcL89SydqCWCe5ry1jMgq"


def get_keycloak_public_key():
    url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return f"-----BEGIN PUBLIC KEY-----\n{response.json()['public_key']}\n-----END PUBLIC KEY-----"
    except Exception as e:
        print(f"Error fetching public key: {e}")
        return None


class ReportData(BaseModel):
    date: str
    movement_type: str
    duration: float
    success_rate: float
    battery_level: float


class ReportResponse(BaseModel):
    user_id: str
    username: str
    device_id: str
    generation_time: str
    data: List[ReportData]


async def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_type, token = authorization.split()
    if token_type.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            get_keycloak_public_key(),
            algorithms=["RS256"],
            audience="account",
            options={"verify_signature": True}
        )
        roles = payload.get("realm_access", {}).get("roles", [])
        if "prothetic_user" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Role 'prothetic_user' required",
            )

        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_report_data(user_id: str, username: str):
    device_id = f"BP-{random.randint(1000, 9999)}"

    data = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        for movement in ["grab", "release", "rotate", "flex"]:
            data.append(
                ReportData(
                    date=date,
                    movement_type=movement,
                    duration=round(random.uniform(0.05, 0.3), 2),
                    success_rate=round(random.uniform(75, 99), 1),
                    battery_level=round(random.uniform(30, 100), 1)
                )
            )

    return ReportResponse(
        user_id=user_id,
        username=username,
        device_id=device_id,
        generation_time=datetime.now().isoformat(),
        data=data
    )


@app.get("/reports")
async def get_reports(token_payload: Dict = Depends(verify_token)):
    user_id = token_payload.get("sub")
    username = token_payload.get("preferred_username", "unknown")

    report = generate_report_data(user_id, username)

    return report


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)