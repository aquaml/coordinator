from pydantic import BaseModel

class MemoryProvider(BaseModel):
    id: int
    address: str
    size: int

class DeleteProvider(BaseModel):
    id: int

class MemoryReclaimRequest(BaseModel):
    id: int
