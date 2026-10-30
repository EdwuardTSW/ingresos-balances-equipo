import hmac,os,jwt,strawberry
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal,InvalidOperation
from sqlalchemy import select
from strawberry.fastapi import GraphQLRouter
from database import SessionLocal
from models import *
from seed import hash_password
from balances import calculate,limits
SECRET=os.getenv("JWT_SECRET")
if not SECRET: raise RuntimeError("JWT_SECRET es obligatorio")
def actor(db,info):
 h=info.context["request"].headers.get("authorization","")
 if not h.startswith("Bearer "): raise ValueError("Acceso rechazado: falta Authorization")
 try: c=jwt.decode(h[7:],SECRET,algorithms=["HS256"])
 except jwt.PyJWTError: raise ValueError("Acceso rechazado: token inválido o expirado")
 m=db.get(CompanyUser,c.get("companyUserId"))
 if not m or not m.is_active or m.company_id!=c.get("companyId"): raise ValueError("Acceso rechazado: membresía inválida")
 return m
def permit(db,m,code):
 ok=db.scalar(select(RolePermission.id).join(CompanyUserRole,CompanyUserRole.role_id==RolePermission.role_id).join(Permission,Permission.id==RolePermission.permission_id).where(CompanyUserRole.company_user_id==m.id,CompanyUserRole.is_active.is_(True),RolePermission.is_active.is_(True),Permission.code==code))
 if not ok: raise ValueError(f"Acceso rechazado: falta el permiso {code}")
def money(v): return Decimal(v).quantize(Decimal("0.00"))
@strawberry.type
class UserType: id:int; name:str; email:str
@strawberry.type
class AuthPayload: token:str|None; token_type:str|None; user:UserType|None
@strawberry.type
class AccountBalance:
 account_id:strawberry.ID; account_name:str; is_active:bool; opening_balance:Decimal; total_income:Decimal; total_expense:Decimal; profit:Decimal; closing_balance:Decimal; is_in_red:bool
@strawberry.type
class GeneralBalance:
 company_id:strawberry.ID; currency:str; from_date:date; to_date:date; opening_balance:Decimal; total_income:Decimal; total_expense:Decimal; profit:Decimal; closing_balance:Decimal; is_in_red:bool; accounts_in_red:int; accounts:list[AccountBalance]
@strawberry.type
class TransactionType:
 id:int; type:str; amount:Decimal; description:str; transaction_date:datetime; captured_at:datetime
@strawberry.input
class LoginInput: email:str; password:str
def balance_type(x): return AccountBalance(account_id=str(x["account_id"]),account_name=x["account_name"],is_active=x["is_active"],opening_balance=money(x["opening_balance"]),total_income=money(x["total_income"]),total_expense=money(x["total_expense"]),profit=money(x["profit"]),closing_balance=money(x["closing_balance"]),is_in_red=x["is_in_red"])
@strawberry.type
class Query:
 @strawberry.field
 def account_balance(self,info:strawberry.Info,account_id:strawberry.ID,from_date:date,to_date:date)->AccountBalance:
  with SessionLocal() as db:
   m=actor(db,info);permit(db,m,"accounts.read");permit(db,m,"transactions.read");return balance_type(calculate(db,m.company_id,from_date,to_date,int(account_id))[0])
 @strawberry.field
 def general_balance(self,info:strawberry.Info,from_date:date,to_date:date)->GeneralBalance:
  with SessionLocal() as db:
   m=actor(db,info);permit(db,m,"accounts.read");permit(db,m,"transactions.read"); rows=calculate(db,m.company_id,from_date,to_date)
   total=lambda k:money(sum((r[k] for r in rows),Decimal("0.00"))); opening,income,expense=total("opening_balance"),total("total_income"),total("total_expense"); profit=income-expense;closing=opening+profit
   return GeneralBalance(company_id=str(m.company_id),currency="MXN",from_date=from_date,to_date=to_date,opening_balance=opening,total_income=income,total_expense=expense,profit=profit,closing_balance=closing,is_in_red=closing<0,accounts_in_red=sum(r["is_in_red"] for r in rows),accounts=[balance_type(r) for r in rows])
@strawberry.type
class Mutation:
 @strawberry.mutation
 def login(self,input:LoginInput)->AuthPayload:
  with SessionLocal() as db:
   u=db.scalar(select(User).where(User.email==input.email))
   if not u or not hmac.compare_digest(u.password_hash,hash_password(input.password)): return AuthPayload(token=None,token_type=None,user=None)
   m=db.scalar(select(CompanyUser).where(CompanyUser.user_id==u.id,CompanyUser.is_active.is_(True)))
   t=jwt.encode({"companyUserId":m.id,"companyId":m.company_id,"exp":datetime.now(timezone.utc)+timedelta(minutes=30)},SECRET,algorithm="HS256")
   return AuthPayload(token=t,token_type="bearer",user=UserType(id=u.id,name=u.name,email=u.email))
 @strawberry.mutation
 def create_transaction(self,info:strawberry.Info,account_id:int,concept_id:int,type:str,amount:Decimal,description:str,transaction_date:datetime|None=None)->TransactionType:
  with SessionLocal() as db:
   m=actor(db,info);permit(db,m,"transactions.write");a=db.get(Account,account_id);c=db.get(Concept,concept_id)
   if not a or not a.is_active or not c or a.company_id!=m.company_id or c.company_id!=m.company_id: raise ValueError("Cuenta o concepto inválido")
   if type not in ("INCOME","EXPENSE") or amount<=0 or money(amount)!=amount: raise ValueError("Monto o tipo inválido")
   d=(transaction_date or datetime.now(timezone.utc)).replace(tzinfo=None); x=Transaction(company_id=m.company_id,account_id=account_id,concept_id=concept_id,type=type,amount=amount,description=description,transaction_date=d,captured_at=datetime.utcnow());db.add(x);db.commit();db.refresh(x);return TransactionType(id=x.id,type=x.type,amount=x.amount,description=x.description,transaction_date=x.transaction_date,captured_at=x.captured_at)
schema=strawberry.Schema(query=Query,mutation=Mutation)
graphql_app=GraphQLRouter(schema)
