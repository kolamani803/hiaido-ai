import os,json
from datetime import datetime,timezone,timedelta
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4
import jwt,requests,re
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError,InvalidHash
from fastapi import FastAPI,Depends,Header,HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
from jwt import PyJWKClient
from kubernetes import client,config
from kubernetes.client.rest import ApiException
from pydantic import BaseModel,Field,field_validator
from sqlalchemy import create_engine,text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

VERSION="0.3.0"
SESSION_SECRET=os.getenv("SESSION_SECRET","").strip()
SESSION_ISSUER="hiaido.ai"
TOKEN_TTL_HOURS=int(os.getenv("TOKEN_TTL_HOURS","8"))
BOOTSTRAP_EMAIL=os.getenv("BOOTSTRAP_ADMIN_EMAIL","").strip().lower()
BOOTSTRAP_PASSWORD=os.getenv("BOOTSTRAP_ADMIN_PASSWORD","")
BOOTSTRAP_NAME=os.getenv("BOOTSTRAP_ADMIN_NAME","HiAIDo Administrator")
DEFAULT_TENANT=os.getenv("DEFAULT_TENANT_ID","default").strip()
password_hasher=PasswordHasher()
URL=os.getenv("DATABASE_URL","").strip()
engine=create_engine(URL,pool_pre_ping=True,pool_recycle=300) if URL else None
Session=sessionmaker(bind=engine,autoflush=False,autocommit=False) if engine else None
app=FastAPI(title="HiAIDo.ai API",version=VERSION)
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.getenv("CORS_ORIGINS","").split(",") if x.strip()],allow_credentials=True,allow_methods=["GET","POST","PATCH"],allow_headers=["Authorization","Content-Type"])

class User(BaseModel):
    subject:str
    tenant_id:str
    name:str|None=None
    roles:list[str]=[]
class LoginRequest(BaseModel):
    email:str=Field(min_length=3,max_length=254)
    password:str=Field(min_length=1,max_length=200)
class CreateUserRequest(BaseModel):
    email:str=Field(min_length=3,max_length=254)
    name:str=Field(min_length=2,max_length=100)
    password:str=Field(min_length=12,max_length=200)
    role:str=Field(default="operator",pattern="^(admin|operator|viewer)$")
class Integration(BaseModel):
    name:str=Field(min_length=2,max_length=100)
    provider:str=Field(min_length=2,max_length=60)
    transport:str=Field(pattern="^(stdio|streamable_http)$")
    endpoint:str|None=Field(default=None,max_length=500)
    secret_ref:str|None=Field(default=None,max_length=200)
    allowed_tools:list[str]=Field(default_factory=list,max_length=100)
    access_mode:str=Field(default="read_only",pattern="^(read_only|approval_required)$")
    @field_validator("endpoint")
    @classmethod
    def https_only(cls,v):
        if not v:return v
        p=urlparse(v)
        if p.scheme!="https" or not p.hostname or p.username or p.password: raise ValueError("Remote MCP endpoints require HTTPS and cannot contain credentials")
        return v

def db_session():
    if not Session: raise HTTPException(503,"DATABASE_URL is not configured")
    db=Session()
    try: yield db
    finally: db.close()

def issue_token(row):
    now=datetime.now(timezone.utc)
    return jwt.encode({"sub":row["id"],"tid":row["tenant_id"],"name":row["name"],"role":row["role"],"iat":now,"exp":now+timedelta(hours=TOKEN_TTL_HOURS),"iss":SESSION_ISSUER},SESSION_SECRET,algorithm="HS256")

def current_user(authorization:str|None=Header(default=None),db=Depends(db_session))->User:
    if len(SESSION_SECRET)<32: raise HTTPException(503,"SESSION_SECRET must be configured with at least 32 characters")
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401,"Bearer session token required")
    try:
        claims=jwt.decode(authorization[7:].strip(),SESSION_SECRET,algorithms=["HS256"],issuer=SESSION_ISSUER,options={"require":["exp","iat","iss","sub","tid","role"]})
    except Exception: raise HTTPException(401,"Invalid or expired session")
    active=db.execute(text("SELECT active FROM user_accounts WHERE id=:id AND tenant_id=:tenant"),{"id":claims["sub"],"tenant":claims["tid"]}).scalar_one_or_none()
    if active is not True: raise HTTPException(401,"Account is disabled or no longer exists")
    return User(subject=str(claims["sub"]),tenant_id=str(claims["tid"]),name=claims.get("name"),roles=[str(claims["role"])])

def require_admin(user:User=Depends(current_user))->User:
    if "admin" not in user.roles: raise HTTPException(403,"Administrator role required")
    return user

def require_operator(user:User=Depends(current_user))->User:
    if not any(role in user.roles for role in ("admin","operator")): raise HTTPException(403,"Operator role required")
    return user

def normalize_email(value):
    value=value.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",value): raise HTTPException(422,"A valid email address is required")
    return value

@app.on_event("startup")
def bootstrap_admin():
    if not engine or not BOOTSTRAP_EMAIL or not BOOTSTRAP_PASSWORD: return
    if len(SESSION_SECRET)<32: raise RuntimeError("SESSION_SECRET must be configured with at least 32 characters")
    if len(BOOTSTRAP_PASSWORD)<16: raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD must be at least 16 characters")
    with engine.begin() as db:
        count=db.execute(text("SELECT count(*) FROM user_accounts WHERE tenant_id=:tenant AND role='admin'"),{"tenant":DEFAULT_TENANT}).scalar_one()
        if count==0:
            db.execute(text("""INSERT INTO user_accounts(id,tenant_id,email,name,password_hash,role,created_by)
            VALUES(:id,:tenant,:email,:name,:hash,'admin','bootstrap') ON CONFLICT (tenant_id,email) DO NOTHING"""),
            {"id":str(uuid4()),"tenant":DEFAULT_TENANT,"email":normalize_email(BOOTSTRAP_EMAIL),"name":BOOTSTRAP_NAME,"hash":password_hasher.hash(BOOTSTRAP_PASSWORD)})

@app.post("/api/v1/auth/login")
def login(payload:LoginRequest,db=Depends(db_session)):
    if len(SESSION_SECRET)<32: raise HTTPException(503,"Local account authentication is not configured")
    email=normalize_email(payload.email)
    row=db.execute(text("""SELECT id,tenant_id,email,name,password_hash,role,active FROM user_accounts WHERE tenant_id=:tenant AND email=:email"""),{"tenant":DEFAULT_TENANT,"email":email}).mappings().first()
    if not row or not row["active"]:
        raise HTTPException(401,"Invalid email or password")
    try: password_hasher.verify(row["password_hash"],payload.password)
    except (VerifyMismatchError,InvalidHash): raise HTTPException(401,"Invalid email or password")
    if password_hasher.check_needs_rehash(row["password_hash"]):
        db.execute(text("UPDATE user_accounts SET password_hash=:hash WHERE id=:id"),{"hash":password_hasher.hash(payload.password),"id":row["id"]});db.commit()
    db.execute(text("""INSERT INTO audit_events(id,tenant_id,actor_id,action,resource_type,resource_id,outcome)
    VALUES(:id,:tenant,:actor,'auth.login','user',:actor,'success')"""),{"id":str(uuid4()),"tenant":row["tenant_id"],"actor":row["id"]});db.commit()
    return {"access_token":issue_token(row),"token_type":"bearer","expires_in":TOKEN_TTL_HOURS*3600,"user":{"id":row["id"],"email":row["email"],"name":row["name"],"role":row["role"]}}

@app.get("/api/v1/users")
def list_users(admin:User=Depends(require_admin),db=Depends(db_session)):
    rows=db.execute(text("""SELECT id,email,name,role,active,created_at FROM user_accounts WHERE tenant_id=:tenant ORDER BY created_at DESC"""),{"tenant":admin.tenant_id}).mappings().all()
    return {"items":[dict(x) for x in rows]}

@app.post("/api/v1/users",status_code=status.HTTP_201_CREATED)
def create_user(payload:CreateUserRequest,admin:User=Depends(require_admin),db=Depends(db_session)):
    email=normalize_email(payload.email)
    uid=str(uuid4())
    try:
        db.execute(text("""INSERT INTO user_accounts(id,tenant_id,email,name,password_hash,role,created_by)
        VALUES(:id,:tenant,:email,:name,:hash,:role,:actor)"""),{"id":uid,"tenant":admin.tenant_id,"email":email,"name":payload.name.strip(),"hash":password_hasher.hash(payload.password),"role":payload.role,"actor":admin.subject})
        db.execute(text("""INSERT INTO audit_events(id,tenant_id,actor_id,action,resource_type,resource_id,outcome)
        VALUES(:id,:tenant,:actor,'user.create','user',:rid,'success')"""),{"id":str(uuid4()),"tenant":admin.tenant_id,"actor":admin.subject,"rid":uid})
        db.commit()
    except Exception as e:
        db.rollback()
        if "uq_user_accounts_tenant_email" in str(e) or "unique" in str(e).lower(): raise HTTPException(409,"An account with this email already exists")
        raise HTTPException(503,"User account could not be created")
    return {"id":uid,"email":email,"name":payload.name.strip(),"role":payload.role,"status":"created"}

@app.patch("/api/v1/users/{user_id}/status")
def update_user_status(user_id:str,active:bool,admin:User=Depends(require_admin),db=Depends(db_session)):
    if user_id==admin.subject and not active: raise HTTPException(400,"You cannot deactivate your own account")
    result=db.execute(text("UPDATE user_accounts SET active=:active WHERE id=:id AND tenant_id=:tenant"),{"active":active,"id":user_id,"tenant":admin.tenant_id})
    if result.rowcount==0: raise HTTPException(404,"User not found")
    db.execute(text("""INSERT INTO audit_events(id,tenant_id,actor_id,action,resource_type,resource_id,outcome)
    VALUES(:id,:tenant,:actor,'user.status_change','user',:rid,:outcome)"""),{"id":str(uuid4()),"tenant":admin.tenant_id,"actor":admin.subject,"rid":user_id,"outcome":"active" if active else "disabled"});db.commit()
    return {"id":user_id,"active":active}

def kube():
    try: config.load_incluster_config()
    except config.ConfigException:
        try: config.load_kube_config()
        except Exception as e: raise RuntimeError("Kubernetes credentials unavailable") from e
    return client.CoreV1Api()
def ready(p): return any(c.type=="Ready" and c.status=="True" for c in (p.status.conditions or []))

@app.get("/health")
def health(): return {"status":"ok","service":"hiaido-api","version":VERSION}
@app.get("/ready")
def readiness():
    if not engine: raise HTTPException(503,"Database is not configured")
    try:
        with engine.connect() as c:c.execute(text("SELECT 1"))
    except SQLAlchemyError: raise HTTPException(503,"Database is not ready")
    return {"status":"ready"}
@app.get("/api/v1/me")
def me(user:User=Depends(current_user)):
    return {"subject":user.subject,"tenant_id":user.tenant_id,"name":user.name,"roles":user.roles}
@app.get("/api/v1/integrations")
def integrations(user:User=Depends(current_user),db=Depends(db_session)):
    rows=db.execute(text("SELECT id,name,provider,transport,endpoint,secret_ref,allowed_tools,access_mode,status,created_at FROM integrations WHERE tenant_id=:t ORDER BY created_at DESC"),{"t":user.tenant_id}).mappings().all()
    return {"items":[dict(x) for x in rows]}
@app.post("/api/v1/integrations",status_code=status.HTTP_201_CREATED)
def register(payload:Integration,user:User=Depends(require_operator),db=Depends(db_session)):
    if payload.transport=="streamable_http" and not payload.endpoint: raise HTTPException(422,"HTTPS endpoint is required for Streamable HTTP")
    if payload.transport=="stdio" and payload.endpoint: raise HTTPException(422,"stdio servers are launched by managed workers; endpoint must be empty")
    iid=str(uuid4())
    try:
        db.execute(text("""INSERT INTO integrations(id,tenant_id,name,provider,transport,endpoint,secret_ref,allowed_tools,access_mode,status,created_by)
        VALUES(:id,:t,:n,:p,:tr,:e,:sr,CAST(:tools AS jsonb),:am,'pending_validation',:actor)"""),
        {"id":iid,"t":user.tenant_id,"n":payload.name,"p":payload.provider,"tr":payload.transport,"e":payload.endpoint,"sr":payload.secret_ref,"tools":json.dumps(payload.allowed_tools),"am":payload.access_mode,"actor":user.subject})
        db.execute(text("""INSERT INTO audit_events(id,tenant_id,actor_id,action,resource_type,resource_id,outcome)
        VALUES(:id,:t,:actor,'integration.register','integration',:rid,'accepted')"""),{"id":str(uuid4()),"t":user.tenant_id,"actor":user.subject,"rid":iid})
        db.commit()
    except SQLAlchemyError:
        db.rollback();raise HTTPException(503,"Integration registration could not be persisted")
    return {"id":iid,"status":"pending_validation","message":"Metadata registered; worker validation and approval are required"}
@app.get("/api/v1/overview")
def overview(user:User=Depends(current_user)):
    providers={"openshift":{"connected":False},"ontap":{"connected":False}}
    resources=[];activity=[];count=healthy=active=0
    try:
        core=kube();nodes=core.list_node().items;pods=core.list_pod_for_all_namespaces(limit=500).items
        count=len(nodes)+len(pods)
        healthy=sum(1 for n in nodes if any(c.type=="Ready" and c.status=="True" for c in (n.status.conditions or [])))+sum(1 for p in pods if ready(p))
        providers["openshift"]={"connected":True,"cluster":os.getenv("KUBERNETES_SERVICE_HOST","in-cluster")}
        for n in nodes:
            ok=any(c.type=="Ready" and c.status=="True" for c in (n.status.conditions or []))
            resources.append({"name":n.metadata.name,"type":"Node","environment":"Kubernetes","status":"Healthy" if ok else "NotReady"})
        for p in pods:
            phase=p.status.phase or "Unknown";st="Healthy" if ready(p) else ("Critical" if phase=="Failed" else phase)
            resources.append({"name":f"{p.metadata.namespace}/{p.metadata.name}","type":"Pod","environment":p.metadata.namespace,"status":st})
            if phase in ("Pending","Failed"):
                active+=1;activity.append({"title":f"Pod {p.metadata.name}: {phase}","source":p.metadata.namespace,"time":p.metadata.creation_timestamp.isoformat() if p.metadata.creation_timestamp else "Current"})
    except (RuntimeError,ApiException) as e: providers["openshift"]={"connected":False,"error":str(e)[:240]}
    base=os.getenv("ONTAP_BASE_URL","").rstrip("/");u=os.getenv("ONTAP_USERNAME");pw=os.getenv("ONTAP_PASSWORD")
    if base and u and pw:
        try:
            r=requests.get(base+"/api/cluster",auth=(u,pw),verify=os.getenv("ONTAP_VERIFY_TLS","true").lower()=="true",timeout=8,headers={"Accept":"application/json"});r.raise_for_status()
            providers["ontap"]={"connected":True,"name":r.json().get("name","ONTAP cluster")};count+=1
        except requests.RequestException as e:providers["ontap"]={"connected":False,"error":str(e)[:240]}
    return {"generated_at":datetime.now(timezone.utc).isoformat(),"resource_count":count,"healthy_count":healthy,"active_operations":active,"connected_integrations":sum(1 for p in providers.values() if p.get("connected")),"providers":providers,"resources":resources[:100],"activity":activity[:20]}
