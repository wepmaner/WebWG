from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Request, status, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jwt import PyJWTError, encode as jwt_encode, decode as jwt_decode
import utils
import os
import wg
from dotenv import load_dotenv
from schemas import ServerInfo, User, Login, UserCreate, ErrorResponse, TokenData
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
from logger import get_logger
import json
load_dotenv()
log = get_logger("main")

ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
SECRET_KEY = os.getenv("SECRET_KEY")
HASHED_PASSWORD = os.getenv("PASSWORD_HASHED").encode("utf-8")

def create_access_token(expires_delta: timedelta | None = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"exp": expire, "sub": "123"}
    return jwt_encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing")
    try:
        payload = jwt_decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        data = TokenData(**payload)
        return data.sub
    except (PyJWTError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

app = FastAPI(
    debug=True,
    title="Web-Wireguard",
    version="1.0",
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def openHtmlFile(filename: str) -> str:
    with open("static/html/" + filename, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/")
def read_root(token: str = Depends(get_current_user)):
    html_content = openHtmlFile("index.html")
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/api/server")
async def server(token: str = Depends(get_current_user)):
    """Включить или отключить впн"""
    action = wg.toggle()
    return {"status": "success", "action": action}


@app.get("/api/getInfo")
def getInfo(token: str = Depends(get_current_user)) -> ServerInfo:
    """Получить информацию о впн сервере и о пользователях"""
    return JSONResponse(
        wg.getInfo()
    )

@app.get("/api/sync")
def configSync(token: str = Depends(get_current_user)):
    """Синхронизировать пльзователей c админ панели в конфиг wg"""
    config = wg.load_config()
    wg.save_config(config)
    return JSONResponse({"status":"success"})

@app.get("/api/users/{username}/config")
def getConfig(username, token: str = Depends(get_current_user)):
    """Получить пользовательский конфиг"""
    config_text = wg.createUserConfig(username)
    buffer = BytesIO(config_text.encode('utf-8'))

    return StreamingResponse(buffer,
        media_type='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{username}.conf"'})

@app.get("/api/users/{username}/qrcode")
def qrcode(username:str, token: str = Depends(get_current_user)):
    """Получить qr code"""
    qrcode_path = wg.generate_wg_qr(username)
    return JSONResponse({"status":"success","qrcode":qrcode_path})

@app.get("/404")
def not_found():
    html_content = openHtmlFile("404.html")
    return HTMLResponse(content=html_content, status_code=404)

@app.post("/login")
def login(login: Login):
    if not utils.verify_password(login.password, HASHED_PASSWORD):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    token = create_access_token()
    response = JSONResponse(content={"message": "Logged in"})
    response.set_cookie(
    key="access_token", value=token,
    httponly=True, samesite="Lax", max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response


@app.post("/api/users",
        responses={
        400: {"model": ErrorResponse, "description": "Пользователь уже существует"},
    },)
async def create_user(user: UserCreate, token: str = Depends(get_current_user)):
    """Добавление пользователя"""
    result, allowed_ips = wg.peer_add(user.username)
    if result:
        return JSONResponse({"status": "success", "username": user.username, "allowed_ips":allowed_ips})
    raise HTTPException(
        status_code=400,
        detail="Пользователь с таким именем уже существует"
    )

RESTORE_DIR = './'

@app.get('/api/backup')
async def backup(token: str = Depends(get_current_user)):
    
    return FileResponse(path="peers.json",
        media_type="application/octet-stream",
        filename="backup.json"
    )

@app.post('/api/restore')
async def restore(file: UploadFile = File(...), token: str = Depends(get_current_user)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Принимаются только JSON-файлы (.json)")
    contents = await file.read()

    try:
        server_config = json.loads(contents.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    wg.save_config(server_config)
    return JSONResponse(content={"filename": file.filename, "message": "Данные восстановлены"})

@app.put("/api/users/{username}")
def update_user(username:str,user: User, token: str = Depends(get_current_user)):
    """Обновление данных пользователя"""
    wg.editUser(username,user)
    return JSONResponse({"status": "success"})


@app.put("/api/users/{username}/status")
def update_user_status(
    username: str, token: str = Depends(get_current_user)
):
    """Обновление статуса пользователя: активация или деактивация."""
    result = wg.changeUserStatus(username)
    return JSONResponse({"status": "success", "username": username, "isEnable": result})


@app.delete("/api/users/{username}")
def delete_user(username: str, token: str = Depends(get_current_user)):
    """Удаление пользователя"""
    wg.peer_del(username)
    return JSONResponse({"status": "success", "deleted": username})


@app.exception_handler(404)
async def method_not_allowed_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/404")


@app.exception_handler(401)
async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    html_content = openHtmlFile("login.html")
    return HTMLResponse(content=html_content, status_code=401)
log.info("Программа запущена")