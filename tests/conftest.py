from datetime import datetime
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import Account, Company, Concept, Transaction

@pytest.fixture
def session():
 engine=create_engine("sqlite:///:memory:"); Base.metadata.create_all(engine); s=sessionmaker(bind=engine)(); yield s; s.close()
@pytest.fixture
def company(session):
 x=Company(name="Prueba");session.add(x);session.flush();return x
@pytest.fixture
def accounts(session,company):
 d={n:Account(company_id=company.id,name=n) for n in ("Banco","Caja","Ahorro")};session.add_all(d.values());session.flush();return d
@pytest.fixture
def concept(session,company):
 x=Concept(company_id=company.id,name="Prueba");session.add(x);session.flush();return x
@pytest.fixture
def transaction_factory(session,company):
 def add(account,concept,typ,amount,dt):
  session.add(Transaction(company_id=company.id,account_id=account.id,concept_id=concept.id,type=typ,amount=Decimal(amount),description="test",transaction_date=dt,captured_at=datetime.utcnow(),is_active=True));session.commit()
 return add
