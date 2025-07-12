from enum import Enum
from typing import List

from pydantic import BaseModel, model_validator,Field

class ErrorResponse(BaseModel):
    status: str
    text: str

class Status(str, Enum):
    success = "success"
    error = "error"
class TokenData(BaseModel):
    sub: str
class User(BaseModel):
    new_username: str = Field(None, example='Anton')
    allowedIps: str = Field(None, example="10.0.0.2/32")
    @model_validator(mode="after")
    def check_new_username_or_allowed_ips(self) -> 'User':
        if not self.new_username and not self.allowedIps:
            raise ValueError("Вам нужно указать 'new_username' или 'allowedIps' или все вместе.")
        return self

class Login(BaseModel):
    password:str

class UserCreate(BaseModel):
    username: str

class UserInfo(BaseModel):
    username: str = "Alan"
    allowedIps: str = "10.0.0.2/32"
    isOnline: bool
    isActive: bool
    latestHandshake: str = "5 seconds ago"
    received: str = "23.11 KiB"
    send: str = "19.32 KiB"


class ServerInfo(BaseModel):
    status: Status
    serverenable: bool
    users: List[UserInfo]


class Token(BaseModel):
    access_token: str
    token_type: str
