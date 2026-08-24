"""Tiny dependency-free PNG generator for the simulated camera/image entities."""

from __future__ import annotations

import struct
import zlib

_WIDTH = 320
_HEIGHT = 180
_BAR_HALF_WIDTH = 12


def _chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def png_frame(frame: int = 0, width: int = _WIDTH, height: int = _HEIGHT) -> bytes:
    """Return a PNG of a vertical bar sweeping across a gradient.

    Rendered by hand rather than with Pillow so the integration keeps zero
    requirements. The moving bar makes it obvious the feed is live.
    """
    bar = (frame * 8) % width
    start = max(0, bar - _BAR_HALF_WIDTH)
    end = min(width, bar + _BAR_HALF_WIDTH)

    raw = bytearray()
    for y in range(height):
        value = 30 + (y * 90 // height)
        row = bytearray(bytes((value, value, min(255, value + 20))) * width)
        if end > start:
            row[start * 3 : end * 3] = b"\xff\xd0\x40" * (end - start)
        raw.append(0)  # PNG filter type 0 (none)
        raw += row

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + _chunk(b"IEND", b"")
    )


def demo() -> None:
    """Self-check: the output must be a PNG the stdlib can parse back."""
    data = png_frame(7)
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "missing PNG signature"
    # Walk the chunks and verify every CRC.
    pos, tags = 8, []
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        tag = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length : pos + 12 + length])
        assert crc == zlib.crc32(tag + body) & 0xFFFFFFFF, f"bad CRC in {tag!r}"
        tags.append(tag)
        pos += 12 + length
    assert tags == [b"IHDR", b"IDAT", b"IEND"], tags
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (_WIDTH, _HEIGHT), (width, height)
    pixels = zlib.decompress(_idat(data))
    assert len(pixels) == height * (1 + width * 3), len(pixels)
    assert png_frame(0) != png_frame(7), "frames should differ"
    print("synthetic_image OK")


def _idat(data: bytes) -> bytes:
    pos = 8
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        if data[pos + 4 : pos + 8] == b"IDAT":
            return data[pos + 8 : pos + 8 + length]
        pos += 12 + length
    raise AssertionError("no IDAT chunk")


if __name__ == "__main__":
    demo()
