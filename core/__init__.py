"""Núcleo de acceso y validación de datos de SIPCA."""

from .database import SIPCADatabase, SIPCADataError

__all__ = ["SIPCADatabase", "SIPCADataError"]
