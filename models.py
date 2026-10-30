from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
 __tablename__="users"; id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(80),unique=True); email:Mapped[str]=mapped_column(String(120),unique=True); password_hash:Mapped[str]=mapped_column(String(128)); is_active:Mapped[bool]=mapped_column(Boolean,default=True); memberships=relationship("CompanyUser",back_populates="user")
class Company(Base):
 __tablename__="companies"; id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(100),unique=True); memberships=relationship("CompanyUser",back_populates="company")
class CompanyUser(Base):
 __tablename__="company_users"; __table_args__=(UniqueConstraint("company_id","user_id",name="uq_company_user"),); id:Mapped[int]=mapped_column(primary_key=True); company_id:Mapped[int]=mapped_column(ForeignKey("companies.id")); user_id:Mapped[int]=mapped_column(ForeignKey("users.id")); is_admin:Mapped[bool]=mapped_column(Boolean,default=False); is_active:Mapped[bool]=mapped_column(Boolean,default=True); company=relationship("Company",back_populates="memberships"); user=relationship("User",back_populates="memberships"); assignments=relationship("CompanyUserRole",back_populates="company_user")
class Role(Base):
 __tablename__="roles"; id:Mapped[int]=mapped_column(primary_key=True); code:Mapped[str]=mapped_column(String(40),unique=True); is_active:Mapped[bool]=mapped_column(Boolean,default=True)
class Permission(Base):
 __tablename__="permissions"; id:Mapped[int]=mapped_column(primary_key=True); code:Mapped[str]=mapped_column(String(60),unique=True); name:Mapped[str]=mapped_column(String(100)); description:Mapped[str]=mapped_column(String(180)); is_active:Mapped[bool]=mapped_column(Boolean,default=True)
class RolePermission(Base):
 __tablename__="role_permissions"; __table_args__=(UniqueConstraint("role_id","permission_id",name="uq_role_permission"),); id:Mapped[int]=mapped_column(primary_key=True); role_id:Mapped[int]=mapped_column(ForeignKey("roles.id")); permission_id:Mapped[int]=mapped_column(ForeignKey("permissions.id")); is_active:Mapped[bool]=mapped_column(Boolean,default=True)
class CompanyUserRole(Base):
 __tablename__="company_user_roles"; __table_args__=(UniqueConstraint("company_user_id","role_id",name="uq_company_user_role"),); id:Mapped[int]=mapped_column(primary_key=True); company_user_id:Mapped[int]=mapped_column(ForeignKey("company_users.id")); role_id:Mapped[int]=mapped_column(ForeignKey("roles.id")); is_active:Mapped[bool]=mapped_column(Boolean,default=True); company_user=relationship("CompanyUser",back_populates="assignments")
class Account(Base):
 __tablename__="accounts"; id:Mapped[int]=mapped_column(primary_key=True); company_id:Mapped[int]=mapped_column(ForeignKey("companies.id")); name:Mapped[str]=mapped_column(String(100)); is_active:Mapped[bool]=mapped_column(Boolean,default=True)
class Concept(Base):
 __tablename__="concepts"; id:Mapped[int]=mapped_column(primary_key=True); company_id:Mapped[int]=mapped_column(ForeignKey("companies.id")); name:Mapped[str]=mapped_column(String(100)); is_active:Mapped[bool]=mapped_column(Boolean,default=True)
class Transaction(Base):
 __tablename__="transactions"; id:Mapped[int]=mapped_column(primary_key=True); company_id:Mapped[int]=mapped_column(ForeignKey("companies.id")); account_id:Mapped[int]=mapped_column(ForeignKey("accounts.id")); concept_id:Mapped[int]=mapped_column(ForeignKey("concepts.id")); type:Mapped[str]=mapped_column(String(15)); amount:Mapped[Decimal]=mapped_column(Numeric(12,2)); description:Mapped[str]=mapped_column(Text); transaction_date:Mapped[datetime]=mapped_column(DateTime); captured_at:Mapped[datetime]=mapped_column(DateTime); is_active:Mapped[bool]=mapped_column(Boolean,default=True)
