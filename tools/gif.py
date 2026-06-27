#!/usr/bin/env python3
"""Assemble raw RGB frames (from game/tools/record.gd) into an animated GIF.

Stdlib only — this environment has no ffmpeg/ImageMagick/Pillow and no pip. Reads
<cap_dir>/meta.txt ("W H N") and <cap_dir>/NNN.rgb (W*H*3 bytes each), quantizes to a
shared <=256-colour palette, and writes a looping GIF89a.

Usage:
    python3 tools/gif.py <cap_dir> <out.gif> [delay_cs]
        delay_cs : per-frame delay in centiseconds (default 5 => ~20 fps)
"""
from __future__ import annotations

import sys
from pathlib import Path


# ---- quantisation ------------------------------------------------------------
def distinct_colours(frames, limit):
    seen = set()
    for data in frames:
        for off in range(0, len(data) - 2, 3):
            seen.add(data[off:off + 3])
            if len(seen) > limit:
                return None
    return [tuple(c) for c in seen]


def median_cut(frames, max_colours=256):
    # sample pixels (bounded) for the palette
    pixels = []
    for data in frames:
        step = max(1, (len(data) // 3) // 30000) * 3
        pixels.extend((data[o], data[o + 1], data[o + 2]) for o in range(0, len(data) - 2, step))
    boxes = [pixels]
    while len(boxes) < max_colours:
        # split the box with the largest colour range along its widest axis
        best = max(range(len(boxes)), key=lambda i: _box_range(boxes[i]) if len(boxes[i]) > 1 else -1)
        if len(boxes[best]) <= 1:
            break
        box = boxes.pop(best)
        axis = _widest_axis(box)
        box.sort(key=lambda c: c[axis])
        mid = len(box) // 2
        boxes.append(box[:mid])
        boxes.append(box[mid:])
    palette = []
    for box in boxes:
        if not box:
            palette.append((0, 0, 0)); continue
        n = len(box)
        palette.append((sum(c[0] for c in box) // n, sum(c[1] for c in box) // n,
                        sum(c[2] for c in box) // n))
    return palette


def _box_range(box):
    return sum(max(c[a] for c in box) - min(c[a] for c in box) for a in range(3))


def _widest_axis(box):
    ranges = [max(c[a] for c in box) - min(c[a] for c in box) for a in range(3)]
    return ranges.index(max(ranges))


def build_palette(frames):
    exact = distinct_colours(frames, 256)
    if exact is not None:
        return exact
    return median_cut(frames, 256)


def index_frames(frames, palette):
    cache = {}
    pal = palette

    def nearest(c):
        idx = cache.get(c)
        if idx is None:
            r, g, b = c
            best, bd = 0, 1 << 30
            for i, (pr, pg, pb) in enumerate(pal):
                d = (pr - r) ** 2 + (pg - g) ** 2 + (pb - b) ** 2
                if d < bd:
                    bd, best = d, i
                    if d == 0:
                        break
            cache[c] = best
            idx = best
        return idx

    out = []
    for data in frames:
        idxs = bytearray(len(data) // 3)
        for p in range(len(idxs)):
            o = p * 3
            idxs[p] = nearest(data[o:o + 3])
        out.append(bytes(idxs))
    return out


# ---- LZW (GIF variant) -------------------------------------------------------
def lzw_encode(indices: bytes, min_code_size: int) -> bytes:
    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    out = bytearray()
    bitbuf = 0
    bitcnt = 0
    code_size = min_code_size + 1

    def emit(code):
        nonlocal bitbuf, bitcnt
        bitbuf |= code << bitcnt
        bitcnt += code_size
        while bitcnt >= 8:
            out.append(bitbuf & 0xFF)
            bitbuf >>= 8
            bitcnt -= 8

    table = {bytes([i]): i for i in range(clear_code)}
    next_code = end_code + 1
    emit(clear_code)
    if not indices:
        emit(end_code)
        if bitcnt:
            out.append(bitbuf & 0xFF)
        return bytes(out)

    cur = indices[0:1]
    for i in range(1, len(indices)):
        nxt = cur + indices[i:i + 1]
        if nxt in table:
            cur = nxt
        else:
            emit(table[cur])
            table[nxt] = next_code
            next_code += 1
            if next_code > (1 << code_size) and code_size < 12:
                code_size += 1
            if next_code > 4095:
                emit(clear_code)
                table = {bytes([i2]): i2 for i2 in range(clear_code)}
                next_code = end_code + 1
                code_size = min_code_size + 1
            cur = indices[i:i + 1]
    emit(table[cur])
    emit(end_code)
    if bitcnt:
        out.append(bitbuf & 0xFF)
    return bytes(out)


def _sub_blocks(data: bytes) -> bytes:
    out = bytearray()
    for i in range(0, len(data), 255):
        chunk = data[i:i + 255]
        out.append(len(chunk))
        out.extend(chunk)
    out.append(0)
    return bytes(out)


# ---- GIF assembly ------------------------------------------------------------
def write_gif(path, w, h, palette, idx_frames, delay_cs):
    # pad palette to a power of two >= 2
    size = 2
    while size < len(palette):
        size <<= 1
    pal = list(palette) + [(0, 0, 0)] * (size - len(palette))
    gct_bits = size.bit_length() - 2  # log2(size)-1
    min_code_size = max(2, size.bit_length() - 1)  # log2(size)

    out = bytearray()
    out += b"GIF89a"
    out += w.to_bytes(2, "little") + h.to_bytes(2, "little")
    out += bytes([0x80 | (gct_bits & 7) | ((7) << 4), 0, 0])  # GCT present, 8-bit colour res
    for (r, g, b) in pal:
        out += bytes([r, g, b])
    # NETSCAPE loop forever
    out += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"
    for idxs in idx_frames:
        out += b"\x21\xF9\x04\x00" + delay_cs.to_bytes(2, "little") + b"\x00\x00"  # GCE
        out += b"\x2C" + (0).to_bytes(2, "little") + (0).to_bytes(2, "little")
        out += w.to_bytes(2, "little") + h.to_bytes(2, "little") + b"\x00"  # image descriptor
        out += bytes([min_code_size])
        out += _sub_blocks(lzw_encode(idxs, min_code_size))
    out += b"\x3B"
    Path(path).write_bytes(out)


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    cap = Path(argv[0])
    out = argv[1]
    delay = int(argv[2]) if len(argv) > 2 else 5
    meta = (cap / "meta.txt").read_text().split()
    w, h, n = int(meta[0]), int(meta[1]), int(meta[2])
    frames = [(cap / f"{i:03d}.rgb").read_bytes() for i in range(n)]
    frames = [f for f in frames if len(f) == w * h * 3]
    if not frames:
        print("gif.py: no valid frames"); return 1
    palette = build_palette(frames)
    idx = index_frames(frames, palette)
    write_gif(out, w, h, palette, idx, delay)
    print(f"gif.py: wrote {out} ({w}x{h}, {len(frames)} frames, {len(palette)} colours)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
