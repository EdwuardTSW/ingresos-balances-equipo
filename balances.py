from datetime import date, datetime, time, timedelta
from decimal import Decimal
from sqlalchemy import select
from models import Account, Transaction

ZERO=Decimal("0.00")
def limits(from_date:date,to_date:date):
 if from_date>to_date: raise ValueError("fromDate no puede ser posterior a toDate")
 start=datetime.combine(from_date,time.min); end=datetime.combine(to_date+timedelta(days=1),time.min)
 return start,end
def calculate(db,company_id:int,from_date:date,to_date:date,account_id:int|None=None):
 start,end=limits(from_date,to_date)
 q=select(Account).where(Account.company_id==company_id)
 if account_id is not None: q=q.where(Account.id==account_id)
 accounts=db.scalars(q.order_by(Account.id)).all()
 if account_id is not None and not accounts: raise ValueError("Cuenta no disponible")
 rows=db.scalars(select(Transaction).where(Transaction.company_id==company_id,Transaction.is_active.is_(True),Transaction.transaction_date<end)).all()
 by={a.id:{"account_id":a.id,"account_name":a.name,"is_active":a.is_active,"opening_balance":ZERO,"total_income":ZERO,"total_expense":ZERO} for a in accounts}
 for tx in rows:
  item=by.get(tx.account_id)
  if not item: continue
  signed=tx.amount if tx.type=="INCOME" else -tx.amount
  if tx.transaction_date<start: item["opening_balance"]+=signed
  else:
   if tx.type=="INCOME": item["total_income"]+=tx.amount
   else: item["total_expense"]+=tx.amount
 for item in by.values():
  item["profit"]=item["total_income"]-item["total_expense"]; item["closing_balance"]=item["opening_balance"]+item["profit"]; item["is_in_red"]=item["closing_balance"]<ZERO
 return list(by.values())
