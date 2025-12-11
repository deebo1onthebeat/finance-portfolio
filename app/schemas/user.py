from pydantic import BaseModel, EmailStr, ConfigDict

class SUserBase(BaseModel):
    email: EmailStr

class SUserRegister(SUserBase):
    password: str

class SUserResponse(SUserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)