"""
schemas.py
Pydantic models used for request validation and response shaping.
"""

import re
from typing import Optional, List
from pydantic import BaseModel, field_validator


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    roll_number: str
    name: str
    password: str
    role: Optional[str] = "student"

    @field_validator("roll_number")
    @classmethod
    def valid_roll(cls, v):
        if not re.match(r"^[A-Za-z0-9\-/]{3,20}$", v):
            raise ValueError("Invalid roll number format")
        return v

    @field_validator("password")
    @classmethod
    def valid_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v):
        if v not in ("student", "kitchen", "admin"):
            return "student"
        return v


class LoginRequest(BaseModel):
    roll_number: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def valid_new_password(cls, v):
        if len(v) < 6:
            raise ValueError("New password must be at least 6 characters")
        return v


# ---------- Menu ----------
class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    price: float
    is_perishable: bool = False
    stock_count: int = 0
    image_url: Optional[str] = None

    @field_validator("price")
    @classmethod
    def positive_price(cls, v):
        if v <= 0:
            raise ValueError("price must be positive")
        return v


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_perishable: Optional[bool] = None
    image_url: Optional[str] = None


class StockUpdate(BaseModel):
    stock_count: int

    @field_validator("stock_count")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("stock_count cannot be negative")
        return v


# ---------- Orders ----------
class OrderLineItem(BaseModel):
    menu_item_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def positive_qty(cls, v):
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v


class OrderCreate(BaseModel):
    slot_id: int
    items: List[OrderLineItem]


class StatusUpdate(BaseModel):
    status: str
