from fastapi import FastAPI, Depends, HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
 
import re

# Assuming you have a 'models' module with 'Assign' and 'Base' defined
from models import Base, User, Company
from database import SessionLocal, engine

app = FastAPI()

def parse(url: str, db: Session):
    options = webdriver.ChromeOptions()
    options.headless = True  # Run in headless mode
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    data = {}
    try:
        partners = driver.find_elements(By.CSS_SELECTOR, 'div.px-3.pb-4')
        print("Found Partners:", len(partners))
        data = {}                                  
        cat = driver.find_element(By.XPATH, '/html/body/div[3]/div/main/div[2]/div/div[2]/div/div/div[2]/div[2]').text
        data[cat] = None
        temp = {}
        for partner in partners:
            company_name = partner.find_element(By.CSS_SELECTOR, 'div.block > span').text
            bonuses = partner.find_elements(By.CSS_SELECTOR, 'div.rounded-2xl')
            bonus_texts = [bonus.text for bonus in bonuses]
            bonus_ints = [int(re.search(r'\d+', bonus_text).group()) for bonus_text in bonus_texts if re.search(r'\d+', bonus_text)]
            bonus_ints.sort()
            temp[company_name] = bonus_ints[-1]
        data[cat] = temp
        pass

    finally:
        driver.quit()
    
    for cat, companies in data.items():
        for name, bonus in companies.items():
            # Check if company already exists to avoid duplicates
            existing_company = db.query(Company).filter_by(name=name, cat=cat).first()
            if existing_company:
                existing_company.bonus = bonus  # update the bonus if the company exists
            else:
                new_company = Company(cat=cat, name=name, Bonus=bonus)
                db.add(new_company)
    db.commit()
    return data

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserBase(BaseModel):
    username: str
    name: str
    surname: str
    password: str

class CompanyBase(BaseModel):
    cat : str
    name : str
    Bonus : int

Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users", response_model=UserBase)
async def create_user(user: UserBase, db: Session = Depends(get_db)):
    user_data = user.dict()
    new_user = User(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users")
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return {"username": user.username, "name": user.name, "surname": user.surname}
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.get("/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.username == username)
                                 & (User.password == password)).first()
    return user


@app.get("/init")
async def initialize_data():
    db = SessionLocal()
    try:
        loop = asyncio.get_running_loop()
        urls = ['https://halykbank.kz/halykclub#!/1501/list?category_code=supermarketi&filter',
                'https://halykbank.kz/halykclub#!/1501/list?category_code=azs&filter',
                'https://halykbank.kz/halykclub#!/1501/list?category_code=restorani_kafe&filter',
                'https://halykbank.kz/halykclub#!/1501/list?category_code=detskie_tovari&filter']
        for url in urls:
            await loop.run_in_executor(None, parse, url, db)
    finally:
        db.close()

@app.get("/companies")
async def read_companies():
    db = SessionLocal()
    try:
        return db.query(Company).all()  # This will fetch all companies
    finally:
        db.close()

@app.get("/companies/")
async def company_data(id: int, db: Session = Depends(get_db)):
    try:
        return db.query(Company).filter((Company.id == id)).first() 
    finally:
        db.close()