"""Validadores de formato para campos de identificación y correo."""

from __future__ import annotations

import re


CEDULA_REGEX = re.compile(r"^\d{6,12}$")
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def normalize_cedula(value: str) -> str:
    return (value or "").strip().replace(" ", "")


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def is_valid_cedula(value: str) -> bool:
    return bool(CEDULA_REGEX.fullmatch(normalize_cedula(value)))


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(normalize_email(value)))