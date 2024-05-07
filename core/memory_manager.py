from typing import Dict, Set, List
import threading
from dataclasses import dataclass
import uuid
import os

STORE_MATCHING_ENV = 'AQUA_MATCH'

class memory_store:
    def __init__(self, capacity: int, address: str) -> None:
        self.capacity = capacity
        self.allocated = 0
        self.address = address

    def malloc(self, size: int) -> int:
        if self.capacity - self.allocated - size < 0: 
            return 0
        self.allocated += size
        return size
    
    def free(self, size: int) -> int:
        if self.allocated < size:
            return size
        self.allocated -= size
        return size

    def add_capacity(self, size: int):
        self.capacity += size

    @property
    def available(self) -> int:
        return self.capacity - self.allocated

@dataclass
class memory_allocation:
    size: int
    address: str
    store_id: str
    allocation_id: str

@dataclass
class reclaim_status:
    capacity: int
    available: int
    can_reclaim: bool

class memory_manager:

    def __init_store_matchings(self):
        matching_str: str = os.environ.get(STORE_MATCHING_ENV)
        if matching_str == None:
            raise Exception("Matching string not found in environment variables. Format = src:dst,src:dst")
        # "s:d,s:d"
        matchings = matching_str.split(',')
        for matching in matchings:
            parts = matching.split(':')
            assert len(parts) == 2
            src = int(parts[0])
            dst = int(parts[1])
            self.source_to_dst[src] = dst


    def __init__(self) -> None:
        self.stores: Dict[int, memory_store] = {}
        self.mutexes: Dict[int, threading.Lock] = {}
        
        self.allocations: Dict[str, memory_allocation] = {}
        self.allocation_mutex: threading.Lock = threading.Lock()
        
        self.reclamation_queue: Set[int] = set()
        self.source_to_dst: Dict[int, int] = {}
        self.__init_store_matchings()

    def add_memory_store(self, store_id: int, store: memory_store) -> None:
        assert store_id not in self.stores
        self.stores[store_id] = store
        self.mutexes[store_id] = threading.Lock()
    
    def delete_memory_store(self, store_id: int) -> bool:
        if store_id not in self.stores:
            return False
        self.stores.pop(store_id, None)
        self.mutexes.pop(store_id, None)
        return True

    def update_memory_store(self, store_id: int, size: int) -> None:
        assert store_id in self.stores
        with self.mutexes[store_id]:
            self.stores[store_id].add_capacity(size)

    def allocate_memory(self, size:int, source: int) -> memory_allocation:
        store_id = self.source_to_dst[source]
        
        with self.allocation_mutex:
            if store_id in self.reclamation_queue:
                return None

        if store_id not in self.mutexes:
            return None
        
        with self.mutexes[store_id]:
            if self.stores[store_id].available >= size:
                allocated = self.stores[store_id].malloc(size)
                assert allocated == size
                allocation = memory_allocation(size=size, address=self.stores[store_id].address, store_id=store_id, allocation_id=str(uuid.uuid4()))
                
                with self.allocation_mutex:
                    self.allocations[allocation.allocation_id] = allocation
                return allocation

        return None
    
    def free_memory(self, allocation_id: str) -> bool:
        allocation: memory_allocation = None
        with self.allocation_mutex:
            allocation = self.allocations[allocation_id]
            self.allocations.pop(allocation_id, None)
        assert allocation != None
        with self.mutexes[allocation.store_id]:
            return self.stores[allocation.store_id].free(allocation.size) == allocation.size
    
    def print_status(self) -> None:
        for store_id in self.stores:
            store = self.stores[store_id]
            print("Store {} has total capacity: {}, allocated: {}, available {}".format(store_id, store.capacity, store.allocated, store.available))

    def add_to_reclaim_queue(self, store_id: int) -> bool:
        with self.allocation_mutex:
            self.reclamation_queue.add(store_id)
            return True
    
    def remove_from_reclaim_queue(self, store_id: int) -> None:
        with self.allocation_mutex:
            if store_id in self.reclamation_queue:
                self.reclamation_queue.remove(store_id)
    
    def get_reclaim_status(self, store_id: int) -> reclaim_status:
        with self.mutexes[store_id]:
            store = self.stores[store_id]
            store_status = reclaim_status(capacity=store.capacity, 
                                          available=store.available, 
                                          can_reclaim=store.capacity == store.available)
            return store_status
        
    def get_responsive_measures(self, allocation_ids: List[str]) -> List[str]:
        with self.allocation_mutex:
            return [allocation_id for allocation_id in allocation_ids if allocation_id in self.allocations and self.allocations[allocation_id].store_id in self.reclamation_queue]