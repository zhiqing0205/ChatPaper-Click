from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from orm import crud, models, schemas, database
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from datetime import datetime
import requests
import hashlib
import logging
import time
import random
import string
import os

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "https://chatpaper.click",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
fh = logging.FileHandler(filename='log/server.log', encoding='utf-8')
# 按照日期切割日志文件
fh = logging.handlers.TimedRotatingFileHandler(filename='log/server.log', when='D', interval=1, backupCount=7, encoding='utf-8')
formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(funcName)s - line:%(lineno)d - %(levelname)s - %(message)s"
)

ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch) #将日志输出至屏幕
logger.addHandler(fh) #将日志输出至文件


logger = logging.getLogger(__name__)


@app.middleware("http")
async def log_requests(request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
    
    return response

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


def download_pdf(db, url):
    response = requests.get(url)
    if response.headers['Content-Type'] != 'application/pdf':
        raise ValueError("URL does not contain a PDF file.")
    
    logger.info(f"response.status_code={response.status_code}")
    # 使用MD5哈希值作为文件名 如果文件已经存在则直接返回文件路径
    file_md5 = hashlib.md5(response.content).hexdigest()
    file = crud.get_paper_by_md5_hash(db, file_md5)
    logger.info(f"file={file}")
    if file is not None:
        return file.path
    # print('666666')
    
    # 保存文件到本地
    static_dir = 'static'
    pdf_dir = 'pdf'
    date_path = datetime.now().strftime('%Y/%m/%d')
    base_dir = os.path.join(static_dir, pdf_dir, date_path)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    file_name = file_md5 + '.pdf'
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, 'wb') as f:
        f.write(response.content)

    return file_path

def get_time_password():
    now = datetime.now()
    # 生成时间密码，四位数字，如：2020年12月31日 05:30 -> 0530
    time_password = now.strftime('%H%M')
    return time_password


# 写一个接口，接收PDF的URL，下载PDF返回文件url
@app.get("/download")
def upload(pdf_url: str, password: str, db: Session = Depends(get_db)):
    if password != get_time_password():
        raise HTTPException(status_code=400, detail="Password is incorrect.")
    logger.info(f"pdf_url={pdf_url}")
    if not pdf_url:
        raise HTTPException(status_code=400, detail="No PDF URL provided.")
    try:
        file_path = download_pdf(db, pdf_url)
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    logger.info(f"file_path={file_path}")
    # 将文件路径转换成url
    file_url = 'https://chatpaper.click/' + file_path
    return {'url': file_url}


# 获取全部论文
@app.get("/papers/", response_model=list[schemas.Paper])
def read_papers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    papers = crud.get_papers(db, skip=skip, limit=limit)
    return papers