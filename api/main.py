# api/main.py

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
import bcrypt
from database import get_db, redis_client, engine
import models
import datetime

# Tabloları veritabanında otomatik oluştur
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="S3M NAC Policy Engine", version="1.0")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_TIME_SECONDS = 300 

def get_radius_attr(data, attr_name):
    """FreeRADIUS rlm_rest JSON formatından gerçek değeri güvenle çıkarır"""
    val = data.get(attr_name)
    if val is None:
        return None
    if isinstance(val, dict):
        v = val.get("value")
        if isinstance(v, list) and len(v) > 0:
            return v[0]
        return v
    if isinstance(val, list) and len(val) > 0:
        return val[0]
    return val

@app.post("/auth")
async def authenticate(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    print(f"DEBUG AUTH DATA: {data}")
    username = get_radius_attr(data, "User-Name")
    password = get_radius_attr(data, "User-Password")

    # Eksik bilgi varsa Reject
    if not username or not password:
        return Response(status_code=401)

    # Redis ile Brute-Force Koruması
    redis_key = f"failed_auth:{username}"
    failed_attempts = redis_client.get(redis_key)
    
    if failed_attempts and int(failed_attempts) >= MAX_FAILED_ATTEMPTS:
        return Response(status_code=401)

    user_record = db.query(models.RadCheck).filter(models.RadCheck.username == username).first()
    if not user_record:
        return Response(status_code=401)

    # Native bcrypt ile şifre kontrolü
    if bcrypt.checkpw(password.encode('utf-8'), user_record.value.encode('utf-8')):
        redis_client.delete(redis_key)
        return Response(status_code=204)
    else:
        redis_client.incr(redis_key)
        redis_client.expire(redis_key, LOCKOUT_TIME_SECONDS)
        return Response(status_code=401)

@app.post("/authorize")
async def authorize(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    print(f"DEBUG AUTH DATA: {data}")
    username = get_radius_attr(data, "User-Name")
    password = get_radius_attr(data, "User-Password")
    mac_address = get_radius_attr(data, "Calling-Station-Id")

    # 1. MAB KONTROLÜ (Şifre yok, MAC var)
    if not password and username:
        mac_record = db.query(models.RadCheck).filter(models.RadCheck.username == username).first()
        if mac_record:
            # FreeRADIUS'un okuyabildiği doğru format!
            return {"control:Auth-Type": "Accept"}
        else:
            return Response(status_code=401)

    # 2. NORMAL KULLANICI KONTROLÜ
    response_data = {"control:Auth-Type": "rest"}

    if not username:
        return response_data

    user_group = db.query(models.RadUserGroup).filter(models.RadUserGroup.username == username).first()
    if not user_group:
        return response_data

    group_replies = db.query(models.RadGroupReply).filter(models.RadGroupReply.groupname == user_group.groupname).all()
    
    if group_replies:
        # Reply parametrelerini de FreeRADIUS formatına uygun düz (flat) hale getiriyoruz
        for reply in group_replies:
            key = f"reply:{reply.attribute}"
            response_data[key] = [{"op": ":=", "value": reply.value}]
        
    return response_data

@app.post("/accounting")
async def accounting(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    print(f"DEBUG AUTH DATA: {data}")
    status_type = get_radius_attr(data, "Acct-Status-Type")
    session_id = get_radius_attr(data, "Acct-Session-Id")
    username = get_radius_attr(data, "User-Name")
    nas_ip = get_radius_attr(data, "NAS-IP-Address")

    if status_type == "Start":
        new_acct = models.RadAcct(acctsessionid=session_id, username=username, nasipaddress=nas_ip or "")
        db.add(new_acct)
        db.commit()
        redis_client.set(f"session:{session_id}", username or "unknown")
        
    elif status_type == "Interim-Update":
        acct = db.query(models.RadAcct).filter(models.RadAcct.acctsessionid == session_id).first()
        if acct:
            acct.acctinputoctets = get_radius_attr(data, "Acct-Input-Octets") or 0
            acct.acctoutputoctets = get_radius_attr(data, "Acct-Output-Octets") or 0
            acct.acctupdatetime = datetime.datetime.utcnow()
            db.commit()

    elif status_type == "Stop":
        acct = db.query(models.RadAcct).filter(models.RadAcct.acctsessionid == session_id).first()
        if acct:
            acct.acctsessiontime = get_radius_attr(data, "Acct-Session-Time") or 0
            acct.acctinputoctets = get_radius_attr(data, "Acct-Input-Octets") or 0
            acct.acctoutputoctets = get_radius_attr(data, "Acct-Output-Octets") or 0
            acct.acctstoptime = datetime.datetime.utcnow()
            acct.acctterminatecause = get_radius_attr(data, "Acct-Terminate-Cause") or ""
            db.commit()
        redis_client.delete(f"session:{session_id}")

    return {"status": "ok"}

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.RadCheck.username).all()
    return {"users": [u[0] for u in users]}

@app.get("/sessions/active")
def get_active_sessions():
    keys = redis_client.keys("session:*")
    sessions = [{"session_id": key.split(":")[1], "username": redis_client.get(key)} for key in keys]
    return {"active_sessions": sessions}
    