"""Pydantic schemas for Indonesian KTP data structures."""

from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class GenderEnum(str, Enum):
    """Standardized gender representation."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"


class AddressDetail(BaseModel):
    """Structured residential address from KTP."""
    street: Optional[str] = Field(None, description="Street / village address (Alamat)")
    rt: Optional[str] = Field(None, description="Rukun Tetangga (RT)")
    rw: Optional[str] = Field(None, description="Rukun Warga (RW)")
    kel_desa: Optional[str] = Field(None, description="Kelurahan / Desa")
    kecamatan: Optional[str] = Field(None, description="Kecamatan (District)")
    city: Optional[str] = Field(None, description="Kota / Kabupaten")
    province: Optional[str] = Field(None, description="Provinsi")


class NIKDetail(BaseModel):
    """Decoded information directly from the 16-digit NIK."""
    nik: str = Field(..., description="16-digit Indonesian National Identity Number")
    is_valid_format: bool = Field(..., description="Whether NIK adheres to the 16-digit structure")
    province_code: Optional[str] = Field(None, description="2-digit province code")
    province_name: Optional[str] = Field(None, description="Resolved province name")
    city_code: Optional[str] = Field(None, description="2-digit regency/city code")
    district_code: Optional[str] = Field(None, description="2-digit district code")
    extracted_birth_date: Optional[date] = Field(None, description="Birth date derived from NIK digits")
    extracted_gender: Optional[GenderEnum] = Field(None, description="Gender derived from NIK female +40 day rule")
    sequence_number: Optional[str] = Field(None, description="4-digit birth sequence number")


class RawKTPFields(BaseModel):
    """Raw text fields parsed directly from KTP OCR output."""
    provinsi: Optional[str] = Field(None, description="Raw Provinsi line")
    kota_kabupaten: Optional[str] = Field(None, description="Raw Kota/Kabupaten line")
    nik: Optional[str] = Field(None, description="Raw extracted NIK digits")
    nama: Optional[str] = Field(None, description="Raw extracted Nama")
    tempat_lahir: Optional[str] = Field(None, description="Raw Tempat Lahir")
    tanggal_lahir: Optional[str] = Field(None, description="Raw Tanggal Lahir (DD-MM-YYYY)")
    jenis_kelamin: Optional[str] = Field(None, description="Raw Jenis Kelamin")
    golongan_darah: Optional[str] = Field(None, description="Raw Golongan Darah (A/B/AB/O/-)")
    alamat: Optional[str] = Field(None, description="Raw Alamat street")
    rt_rw: Optional[str] = Field(None, description="Raw RT/RW line")
    kel_desa: Optional[str] = Field(None, description="Raw Kel/Desa")
    kecamatan: Optional[str] = Field(None, description="Raw Kecamatan")
    agama: Optional[str] = Field(None, description="Raw Agama")
    status_perkawinan: Optional[str] = Field(None, description="Raw Status Perkawinan")
    pekerjaan: Optional[str] = Field(None, description="Raw Pekerjaan")
    kewarganegaraan: Optional[str] = Field(None, description="Raw Kewarganegaraan (WNI/WNA)")
    berlaku_hingga: Optional[str] = Field(None, description="Raw Berlaku Hingga")


class KTPNormalized(BaseModel):
    """Cleaned, validated, and normalized KTP data."""
    nik: str = Field(..., description="Clean 16-digit NIK")
    nama: str = Field(..., description="Full name formatted")
    tempat_lahir: Optional[str] = Field(None, description="Place of birth")
    tanggal_lahir: Optional[date] = Field(None, description="Validated Date of birth")
    jenis_kelamin: GenderEnum = Field(default=GenderEnum.UNKNOWN, description="Normalized Gender")
    golongan_darah: Optional[str] = Field(None, description="Blood type")
    alamat: AddressDetail = Field(default_factory=AddressDetail, description="Structured address")
    agama: Optional[str] = Field(None, description="Religion")
    status_perkawinan: Optional[str] = Field(None, description="Marital status")
    pekerjaan: Optional[str] = Field(None, description="Occupation")
    kewarganegaraan: str = Field(default="WNI", description="Citizenship")
    berlaku_hingga: Optional[str] = Field(default="SEUMUR HIDUP", description="Expiry date or lifelong")
    nik_detail: Optional[NIKDetail] = Field(None, description="Information decoded from NIK digits")
