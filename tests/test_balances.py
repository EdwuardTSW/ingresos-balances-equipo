from datetime import date, datetime
from decimal import Decimal
from balances import calculate
from models import Account, Company

def test_reference_balance(session, company, accounts, concept, transaction_factory):
    transaction_factory(accounts["Banco"],concept,"INCOME","1000.00",datetime(2026,10,25,12))
    transaction_factory(accounts["Banco"],concept,"INCOME","3000.00",datetime(2026,10,26,12))
    transaction_factory(accounts["Banco"],concept,"EXPENSE","2200.00",datetime(2026,10,27,12))
    rows=calculate(session,company.id,date(2026,10,26),date(2026,10,30))
    assert rows[0]["opening_balance"]==Decimal("1000.00")
    assert rows[0]["closing_balance"]==Decimal("1800.00")

def test_dates_boundaries_and_decimal(session, company, accounts, concept, transaction_factory):
    transaction_factory(accounts["Caja"],concept,"INCOME","0.10",datetime(2026,10,26,0,0))
    transaction_factory(accounts["Caja"],concept,"INCOME","0.20",datetime(2026,10,30,23,59,59))
    transaction_factory(accounts["Caja"],concept,"EXPENSE","0.30",datetime(2026,10,31,0,0))
    row=calculate(session,company.id,date(2026,10,26),date(2026,10,30),accounts["Caja"].id)[0]
    assert row["profit"]==Decimal("0.30")

def test_company_isolation_b12(session, company, accounts, concept, transaction_factory):
    other=Company(name="Otra empresa");session.add(other);session.flush()
    foreign=Account(company_id=other.id,name="Ajena");session.add(foreign);session.commit()
    assert calculate(session,company.id,date(2026,10,26),date(2026,10,30))
    with __import__("pytest").raises(ValueError,match="Cuenta no disponible"):
        calculate(session,company.id,date(2026,10,26),date(2026,10,30),foreign.id)
