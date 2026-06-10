"""Доменные ошибки service layer."""

from __future__ import annotations


class ServiceError(RuntimeError):
    """Базовая ошибка прикладного сценария."""


class BadRequestError(ServiceError):
    """Ошибка некорректного пользовательского запроса."""


class NotFoundError(ServiceError):
    """Ошибка отсутствия запрошенных данных."""
