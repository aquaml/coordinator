from fastapi import FastAPI, Request
from data.allocation import NvAllocateRequest, NvFreeRequest, ResponsiveReclaimRequest
from data.leasing import MemoryProvider, MemoryReclaimRequest, DeleteProvider
from core.memory_manager import memory_manager, memory_store

app = FastAPI()
mm = memory_manager()

@app.middleware("http")
async def extract_source_gpu_header(request: Request, call_next):
    try:
        source_gpu_header = request.headers.get('source-gpu', '-1')
        request.state.source_gpu = int(source_gpu_header)
    except ValueError:
        request.state.source_gpu = -1
    response = await call_next(request)
    return response

@app.post("/lease")
def lease_memory(request: MemoryProvider):
    store_to_add = memory_store(request.size, request.address)
    mm.add_memory_store(request.id, store_to_add)
    mm.print_status()
    return store_to_add

@app.put("/lease")
def lease_memory(request: MemoryProvider):
    store_to_add = memory_store(request.size, request.address)
    mm.update_memory_store(request.id, request.size)
    mm.print_status()
    return store_to_add

@app.delete("/unlease")
def unlease_memory(request: DeleteProvider):
    deleted = mm.delete_memory_store(request.id)
    
    mm.print_status()
    return {"deleted": deleted}

@app.post("/reclaim_request")
def reclaim_request(request: MemoryReclaimRequest):
    added = mm.add_to_reclaim_queue(request.id)
    return {"added": added}

@app.delete("/reclaim_request")
def done_with_reclaim_request(request: MemoryReclaimRequest):
    added = mm.remove_from_reclaim_queue(request.id)
    return {"added": added}

@app.post("/reclaim_status")
def reclaim_status(request: MemoryReclaimRequest):
    status = mm.get_reclaim_status(request.id)
    return status

@app.post("/responsive_reclaim")
def reclaim_status(request: ResponsiveReclaimRequest):
    status = mm.get_responsive_measures(request.allocations)
    return status

@app.post("/nv_allocate")
def nv_allocate(http_request: Request, request: NvAllocateRequest):
    allocated = mm.allocate_memory(request.memory, http_request.state.source_gpu)
    mm.print_status()
    return allocated

@app.delete("/nv_free")
def nv_free(request: NvFreeRequest):
    freed = mm.free_memory(request.allocation_id)
    mm.print_status()
    return {"freed": freed}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
