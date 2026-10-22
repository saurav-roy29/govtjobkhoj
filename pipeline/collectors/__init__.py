"""
Official recruitment collectors for GovtJobKhoj
"""
from .base import BaseCollector
from .upsc import UPSCCollector
from .ibps import IBPSCollector
from .feed import FeedCollector

__all__ = ["BaseCollector", "UPSCCollector", "IBPSCollector", "FeedCollector"]
