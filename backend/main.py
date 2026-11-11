import os,json
from datetime import datetime,timezone
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4
import jwt,requests
from fastapi import FastAPI,Depends,Header,HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
from jwt import PyJWKClient
from kubernetes import client,config
from kubernetes.client.rest import ApiException
from pydantic import BaseModel,Field,field_validator
from sqlalchemy import create_engine,text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

VERSION="0.2.0"
TENANT=os.getenv("ENTRA_TENANT_ID","").strip()
AUDIENCE=os.getenv("ENTRA_API_AUDIENCE","").strip()
ISSUER=f"https://login.microsoftonline.com/{TENANT}/v2.0" if TENANT else ""
JWKS=PyJWKClient(f"https://login.microsoftonline.com/{TENANT}/discovery/v2.0/keys") if TENANT else None
ROLE=os.getenv("ENTRA_REQUIRED_APP_ROLE","HiAIDo.Access")
URL=os.getenv("DATABASE_URL","").strip()
engine=create_engine(URL,pool_pre_ping=True,pool_recycle=300) if URL else None
Session=sessionmaker(bind=engine,autoflush=False,autocommit=False) if engine else None
app=FastAPI(title="HiAIDo.ai API",version=VERSION)
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.getenv("CORS_ORIGINS","").split(",") if x.strip()],allow_credentials=True,allow_methods=["GET","POST"],allow_headers=["Authorization","Content-Type"])

class User(BaseModel):
    subject:str
    tenant_id:str
    name:str|None=None
    roles:list[str]=[]
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

def current_user(authorization:str|None=Header(default=None))->User:
    # Protected routes fail closed until Entra app registration is configured.
    if not TENANT or not AUDIENCE or not JWKS: raise HTTPException(503,"Entra authentication is not configured")
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401,"Bearer access token required")
    try:
        key=JWKS.get_signing_key_from_jwt(authorization[7:].strip()).key
        claims=jwt.decode(authorization[7:].strip(),key,algorithms=["RS256"],audience=AUDIENCE,issuer=ISSUER,options={"require":["exp","iat","iss","aud","tid","oid"]})
    except Exception: raise HTTPException(401,"Invalid or expired access token")
    if claims.get("tid")!=TENANT: raise HTTPException(403,"Tenant is not permitted")
    roles=claims.get("roles",[])
    if ROLE and ROLE not in roles: raise HTTPException(403,"Required application role is missing")
    return User(subject=str(claims["oid"]),tenant_id=str(claims["tid"]),name=claims.get("name"),roles=roles)

def db_session():
    if not Session: raise HTTPException(503,"DATABASE_URL is not configured")
    db=Session()
    try: yield db
    finally: db.close()

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
def register(payload:Integration,user:User=Depends(current_user),db=Depends(db_session)):
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
