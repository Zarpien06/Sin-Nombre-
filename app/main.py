import os,re,hashlib,hmac,secrets,shutil
import requests
from pathlib import Path
from datetime import datetime,timedelta
from fastapi import FastAPI,Depends,Form,Header,HTTPException,Request,UploadFile,File
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select,delete
from sqlalchemy.orm import Session
from PIL import Image
from .db import Base,engine,get_db
from .models import Thread,Reply
Base.metadata.create_all(engine)
# Migracion liviana para bases SQLite creadas por versiones anteriores.
if engine.dialect.name == "sqlite":
 from sqlalchemy import text
 with engine.begin() as conn:
  for table in ("threads", "replies"):
   columns = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
   if "image" not in columns:
    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN image VARCHAR(200)"))
app=FastAPI(title="Sin Nombre Chat")
base=Path(__file__).parent; uploads=Path("uploads"); uploads.mkdir(exist_ok=True)
SUPABASE_URL=os.getenv("SUPABASE_URL","").rstrip("/"); SUPABASE_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY",""); BUCKET=os.getenv("SUPABASE_STORAGE_BUCKET","sin-nombre-media")
def cloud_storage(): return bool(SUPABASE_URL and SUPABASE_KEY)
app.mount("/static",StaticFiles(directory=base/"static"),name="static"); app.mount("/media",StaticFiles(directory=uploads),name="media")
tpl=Jinja2Templates(directory=base/"templates"); MAX=int(os.getenv("MAX_IMAGE_MB","5"))*1024*1024
def now():return datetime.utcnow()
def token_hash(v):return hashlib.sha256(v.encode()).hexdigest()
def clean(v):
 v=(v or "").strip()
 for p in [r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",r"(?<!\d)(?:\+?57)?[ -]?(?:3\d{2})[ -]?\d{3}[ -]?\d{4}(?!\d)"]:
  if re.search(p,v,re.I):raise HTTPException(400,"No publiques teléfonos ni correos.")
 return v
def alias(code,tid):
 d=hmac.new(os.getenv("APP_SECRET","dev").encode(),f"{code}:{tid}".encode(),hashlib.sha256).hexdigest(); a=["Zorro","Marea","Cuervo","Lince","Bruma","Faro","Nube","Búho"]; c=["Azul","Ámbar","Violeta","Verde","Gris","Rojo","Índigo","Dorado"]
 return f"{a[int(d[:2],16)%8]} {c[int(d[2:4],16)%8]} {int(d[4:8],16)%100}"
async def image_save(f):
 if not f or not f.filename:return None
 if f.content_type not in {"image/jpeg","image/png","image/webp"}:raise HTTPException(400,"Solo JPG, PNG o WEBP.")
 data=await f.read(MAX+1)
 if len(data)>MAX:raise HTTPException(400,"La imagen supera el límite de 5 MB.")
 ext={"image/jpeg":"jpg","image/png":"png","image/webp":"webp"}[f.content_type]; name=f"{secrets.token_hex(16)}.{ext}"
 from io import BytesIO
 try:
  with Image.open(BytesIO(data)) as im: im.verify()
 except Exception: raise HTTPException(400,"La imagen no es válida.")
 if cloud_storage():
  url=f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{name}"
  headers={"Authorization":f"Bearer {SUPABASE_KEY}","apikey":SUPABASE_KEY,"Content-Type":f.content_type,"x-upsert":"false"}
  response=requests.post(url,headers=headers,data=data,timeout=30)
  if response.status_code not in (200,201): raise HTTPException(502,"No se pudo guardar la imagen en Supabase Storage.")
  return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{name}"
 p=uploads/name;p.write_bytes(data);return name
def image_url(name):
 if not name:return None
 return name if name.startswith("http") else f"/media/{name}"
def image_delete(name):
 if not name:return
 if name.startswith("http") and cloud_storage():
  filename=name.rsplit("/",1)[-1]
  requests.delete(f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filename}",headers={"Authorization":f"Bearer {SUPABASE_KEY}","apikey":SUPABASE_KEY},timeout=30)
 else:(uploads/name).unlink(missing_ok=True)

def purge(db):
 old=db.scalars(select(Thread).where(Thread.expires_at<=now())).all()
 for t in old:
  for name in [t.image]+[x.image for x in t.replies]:
   if name:image_delete(name)
  db.delete(t)
 db.commit()
@app.get("/health")
def health():return {"status":"ok"}
@app.get("/",response_class=HTMLResponse)
def home(request:Request,db:Session=Depends(get_db)):
 purge(db); items=db.scalars(select(Thread).order_by(Thread.created_at.desc()).limit(50)).all();return tpl.TemplateResponse(request,"index.html",{"threads":items})
@app.post("/threads")
async def create(title:str=Form(...),body:str=Form(""),duration:int=Form(...),photo:UploadFile|None=File(None),x_author_token:str|None=Header(None),db:Session=Depends(get_db)):
 if not x_author_token:raise HTTPException(400,"Falta llave local.")
 if duration<20 or duration>1440:raise HTTPException(400,"El tiempo debe estar entre 20 minutos y 24 horas.")
 title=clean(title)[:120];body=clean(body)[:5000]; image=await image_save(photo)
 if not body and not image:raise HTTPException(400,"Escribe un mensaje o agrega una foto.")
 t=Thread(title=title,body=body,image=image,author_hash=token_hash(x_author_token),expires_at=now()+timedelta(minutes=duration));db.add(t);db.commit();db.refresh(t);return {"id":t.id,"url":f"/h/{t.id}"}
@app.get("/h/{tid}",response_class=HTMLResponse)
def room(tid:str,request:Request,db:Session=Depends(get_db)):
 purge(db);t=db.get(Thread,tid)
 if not t:raise HTTPException(404,"Esta conversación desapareció.")
 rs=[{"body":x.body,"image":image_url(x.image),"alias":alias(x.alias_code,tid),"created_at":x.created_at} for x in t.replies]
 return tpl.TemplateResponse(request,"room.html",{"thread":t,"thread_image":image_url(t.image),"replies":rs})
@app.post("/h/{tid}/reply")
async def respond(tid:str,body:str=Form(""),photo:UploadFile|None=File(None),x_alias_code:str|None=Header(None),db:Session=Depends(get_db)):
 t=db.get(Thread,tid)
 if not t or t.expires_at<=now():raise HTTPException(404,"La conversación expiró.")
 body=clean(body)[:3000];image=await image_save(photo)
 if not body and not image:raise HTTPException(400,"Escribe un mensaje o agrega una foto.")
 db.add(Reply(thread_id=tid,body=body,image=image,alias_code=token_hash(x_alias_code or secrets.token_hex(8))));db.commit();return {"ok":True}
@app.delete("/h/{tid}")
def remove(tid:str,x_author_token:str|None=Header(None),db:Session=Depends(get_db)):
 t=db.get(Thread,tid)
 if not t:raise HTTPException(404)
 if not x_author_token or token_hash(x_author_token)!=t.author_hash:raise HTTPException(403,"Este dispositivo no tiene la llave.")
 for name in [t.image]+[x.image for x in t.replies]:
  if name:image_delete(name)
 db.delete(t);db.commit();return {"ok":True}
@app.exception_handler(HTTPException)
def errors(req,exc):return JSONResponse({"detail":exc.detail},status_code=exc.status_code)
