from pydantic import BaseModel
from typing import List
from dataclasses import dataclass

class NvAllocateRequest(BaseModel):
    memory: int

class NvFreeRequest(BaseModel):
    allocation_id: str

class ResponsiveReclaimRequest(BaseModel):
    allocations: List[str]

# @dataclass
# class memory_allocation_to_return(BaseModel):
#     size: int
#     address: str
#     store_id: str
#     allocation_id: str

# @dataclass
# class reclaim_status_to_return(BaseModel):
#     capacity: int
#     available: int
#     can_reclaim: bool

# @dataclass
# class responsive_reclaims(BaseModel):
#     allocation_ids: List[str]

# class mem_store_to_return(BaseModel):
#     capacity: int
#     allocated: int
#     address: str