from pydantic import BaseModel, ConfigDict

class SCategoryBase(BaseModel):
    name: str

class SCategoryCreate(SCategoryBase):
    pass

class SCategoryResponse(SCategoryBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)