from .patients import router as patients_router
from .observations import router as observations_router

__all__ = ["patients_router", "observations_router"] 