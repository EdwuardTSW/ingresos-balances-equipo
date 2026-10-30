import hashlib
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from models import *
PERMISSIONS={"accounts.read":("Ver cuentas","Ver cuentas"),"accounts.write":("Crear cuentas","Crear cuentas"),"concepts.read":("Ver conceptos","Ver conceptos"),"concepts.write":("Crear conceptos","Crear conceptos"),"transactions.read":("Ver movimientos","Ver movimientos"),"transactions.write":("Registrar movimientos","Registrar movimientos"),"roles.read":("Ver roles","Ver roles"),"roles.write":("Configurar roles","Configurar roles"),"company.users.read":("Ver usuarios","Ver usuarios"),"company.users.write":("Administrar usuarios","Administrar usuarios")}
ROLE_PERMISSIONS={"ADMINISTRADOR":set(PERMISSIONS),"CONTADOR":{"accounts.read","accounts.write","concepts.read","concepts.write","transactions.read","transactions.write","roles.read"},"CAPTURISTA":{"accounts.read","concepts.read","transactions.read","transactions.write"},"CONSULTA":{"accounts.read","concepts.read","transactions.read"}}
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def seed_database(db):
 roles={}
 for code in ROLE_PERMISSIONS:
  r=db.scalar(select(Role).where(Role.code==code))
  if not r: r=Role(code=code);db.add(r);db.flush()
  roles[code]=r
 for code,(name,desc) in PERMISSIONS.items():
  p=db.scalar(select(Permission).where(Permission.code==code))
  if not p: p=Permission(code=code,name=name,description=desc);db.add(p);db.flush()
  for role_code,grants in ROLE_PERMISSIONS.items():
   if code in grants and not db.scalar(select(RolePermission).where(RolePermission.role_id==roles[role_code].id,RolePermission.permission_id==p.id)): db.add(RolePermission(role_id=roles[role_code].id,permission_id=p.id))
 company=db.scalar(select(Company).where(Company.name=="Sistema General de Ingresos"))
 if not company: company=Company(name="Sistema General de Ingresos");db.add(company);db.flush()
 for name,email,role in [("Ana","ana@empresa.test","ADMINISTRADOR"),("Luis","luis@empresa.test","CONTADOR"),("María","maria@empresa.test","CAPTURISTA"),("Pedro","pedro@empresa.test","CONSULTA")]:
  u=db.scalar(select(User).where(User.email==email))
  if not u: u=User(name=name,email=email,password_hash=hash_password("secreto"));db.add(u);db.flush()
  m=db.scalar(select(CompanyUser).where(CompanyUser.company_id==company.id,CompanyUser.user_id==u.id))
  if not m: m=CompanyUser(company_id=company.id,user_id=u.id,is_admin=role=="ADMINISTRADOR");db.add(m);db.flush();db.add(CompanyUserRole(company_user_id=m.id,role_id=roles[role].id))
 accounts={}
 for name in ["Banco","Caja","Ahorro"]:
  a=db.scalar(select(Account).where(Account.company_id==company.id,Account.name==name))
  if not a: a=Account(company_id=company.id,name=name);db.add(a);db.flush()
  accounts[name]=a
 c=db.scalar(select(Concept).where(Concept.company_id==company.id))
 if not c: c=Concept(company_id=company.id,name="Operación");db.add(c);db.flush()
 data=[("Banco","2026-10-25T12:00:00","INCOME","1000.00","Ingreso de apertura"),("Banco","2026-10-26T12:00:00","INCOME","3000.00","Cobro de servicios"),("Banco","2026-10-27T12:00:00","EXPENSE","1200.00","Pago de renta"),("Banco","2026-10-28T12:00:00","EXPENSE","1000.00","Compra de materiales"),("Caja","2026-10-26T12:00:00","INCOME","500.00","Venta de contado"),("Caja","2026-10-29T12:00:00","EXPENSE","700.00","Pago de insumos")]
 if not db.scalar(select(Transaction.id).where(Transaction.company_id==company.id)):
  for account,dt,typ,amount,desc in data: db.add(Transaction(company_id=company.id,account_id=accounts[account].id,concept_id=c.id,type=typ,amount=Decimal(amount),description=desc,transaction_date=datetime.fromisoformat(dt),captured_at=datetime.utcnow()))
 db.commit()
