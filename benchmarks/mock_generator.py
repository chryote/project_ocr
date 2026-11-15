"""Synthetic Indonesian KTP image generator.

Renders photorealistic synthetic KTP document images with simulated cards,
text fields, headers, and backgrounds for automated testing and benchmarking.
Ensures zero citizen PII leakage (UU PDP compliance).
"""

from dataclasses import dataclass
import io
import math
from typing import Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass
class SyntheticKTPConfig:
    """Parameters for synthetic KTP image generation."""
    nik: str = "3171011505900001"
    nama: str = "BUDI SANTOSO"
    tempat_lahir: str = "JAKARTA"
    tanggal_lahir: str = "15-05-1990"
    jenis_kelamin: str = "LAKI-LAKI"
    golongan_darah: str = "O"
    alamat: str = "JL. MH THAMRIN NO. 28"
    rt_rw: str = "005/002"
    kel_desa: str = "GONDANGDIA"
    kecamatan: str = "MENTENG"
    agama: str = "ISLAM"
    status_perkawinan: str = "KAWIN"
    pekerjaan: str = "KARYAWAN SWASTA"
    kewarganegaraan: str = "WNI"
    berlaku_hingga: str = "SEUMUR HIDUP"
    provinsi: str = "PROVINSI DKI JAKARTA"
    kota: str = "JAKARTA PUSAT"
    skew_angle: float = 0.0
    add_noise: bool = False


class SyntheticKTPGenerator:
    """Generates synthetic KTP images for testing and benchmarking."""

    @classmethod
    def generate_image_bytes(cls, config: Optional[SyntheticKTPConfig] = None) -> bytes:
        """Renders an image from configuration and returns PNG bytes."""
        img = cls.generate_image(config)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @classmethod
    def generate_image(cls, config: Optional[SyntheticKTPConfig] = None) -> Image.Image:
        """Renders an Indonesian KTP styled card on an RGB canvas."""
        cfg = config or SyntheticKTPConfig()

        # Standard KTP aspect ratio ~85.6mm x 53.98mm (~1.586). Canvas: 1000 x 630
        width, height = 1000, 630
        # Typical cyan/light blue KTP card background
        img = Image.new("RGB", (width, height), color=(185, 215, 235))
        draw = ImageDraw.Draw(img)

        # Draw card header
        cls._draw_header(draw, cfg.provinsi, cfg.kota, width)

        # Draw primary fields
        cls._draw_fields(draw, cfg)

        # Draw decorative card elements (photo frame, chip, signature box)
        cls._draw_card_decorations(draw, width, height)

        # Apply skew/rotation if requested
        if cfg.skew_angle != 0.0:
            img = img.rotate(cfg.skew_angle, expand=True, fillcolor=(240, 240, 240))

        # Apply noise if requested
        if cfg.add_noise:
            img = cls._add_noise_to_image(img)

        return img

    @classmethod
    def _draw_header(cls, draw: ImageDraw.ImageDraw, provinsi: str, kota: str, width: int) -> None:
        """Renders header banner."""
        font_large = cls._get_font(24, bold=True)
        font_sub = cls._get_font(20, bold=True)

        draw.text((width // 2, 25), provinsi.upper(), fill=(0, 30, 80), anchor="mm", font=font_large)
        draw.text((width // 2, 55), f"KOTA/KABUPATEN {kota.upper()}", fill=(0, 30, 80), anchor="mm", font=font_sub)

    @classmethod
    def _draw_fields(cls, draw: ImageDraw.ImageDraw, cfg: SyntheticKTPConfig) -> None:
        """Renders KTP text rows."""
        font_nik = cls._get_font(28, bold=True)
        font_labels = cls._get_font(18, bold=True)
        font_values = cls._get_font(18, bold=False)

        # NIK Line
        draw.text((40, 95), "NIK", fill=(0, 0, 0), font=font_nik)
        draw.text((220, 95), f": {cfg.nik}", fill=(0, 0, 0), font=font_nik)

        # Data Rows
        rows = [
            ("Nama", f": {cfg.nama}"),
            ("Tempat/Tgl Lahir", f": {cfg.tempat_lahir}, {cfg.tanggal_lahir}"),
            ("Jenis Kelamin", f": {cfg.jenis_kelamin}   Gol. Darah : {cfg.golongan_darah}"),
            ("Alamat", f": {cfg.alamat}"),
            ("   RT/RW", f": {cfg.rt_rw}"),
            ("   Kel/Desa", f": {cfg.kel_desa}"),
            ("   Kecamatan", f": {cfg.kecamatan}"),
            ("Agama", f": {cfg.agama}"),
            ("Status Perkawinan", f": {cfg.status_perkawinan}"),
            ("Pekerjaan", f": {cfg.pekerjaan}"),
            ("Kewarganegaraan", f": {cfg.kewarganegaraan}"),
            ("Berlaku Hingga", f": {cfg.berlaku_hingga}"),
        ]

        y_pos = 145
        line_spacing = 33

        for label, val in rows:
            draw.text((40, y_pos), label, fill=(10, 10, 10), font=font_labels)
            draw.text((240, y_pos), val, fill=(10, 10, 10), font=font_values)
            y_pos += line_spacing

    @classmethod
    def _draw_card_decorations(cls, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        """Renders photo placeholder and signature block."""
        # Photo placeholder on the right
        photo_x0, photo_y0 = width - 240, 140
        photo_x1, photo_y1 = width - 50, 400
        draw.rectangle([photo_x0, photo_y0, photo_x1, photo_y1], outline=(100, 120, 140), width=2, fill=(200, 220, 235))

        font_sm = cls._get_font(14)
        draw.text(((photo_x0 + photo_x1) // 2, (photo_y0 + photo_y1) // 2), "PAS FOTO", fill=(120, 140, 160), anchor="mm", font=font_sm)

        # Signature box
        sig_x0, sig_y0 = width - 230, 425
        sig_x1, sig_y1 = width - 60, 480
        draw.rectangle([sig_x0, sig_y0, sig_x1, sig_y1], outline=(150, 170, 190), width=1)
        draw.text(((sig_x0 + sig_x1) // 2, (sig_y0 + sig_y1) // 2), "Tanda Tangan", fill=(150, 170, 190), anchor="mm", font=font_sm)

    @classmethod
    def _add_noise_to_image(cls, img: Image.Image) -> Image.Image:
        """Adds salt-and-pepper noise to simulate real-world mobile camera photos."""
        arr = np.array(img).astype(np.float32)
        noise = np.random.normal(0, 15, arr.shape)
        noisy_arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy_arr)

    @classmethod
    def _get_font(cls, size: int, bold: bool = False) -> ImageFont.ImageFont:
        """Attempts to load a standard system font, falling back to default."""
        font_names = [
            "arialbd.ttf" if bold else "arial.ttf",
            "segoeuib.ttf" if bold else "segoeui.ttf",
            "calibrib.ttf" if bold else "calibri.ttf",
        ]
        for name in font_names:
            try:
                return ImageFont.truetype(name, size)
            except IOError:
                continue
        return ImageFont.load_default()
