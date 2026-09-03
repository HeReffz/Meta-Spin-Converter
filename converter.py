import os
import struct
import subprocess
import uuid
from datetime import datetime, timezone
from PIL import Image
import piexif

WIDTH = 1376
HEIGHT = 1840
FPS = 30
DURATION_SECONDS = 5
VIDEO_TIMESCALE = 600
MOVIE_TIMESCALE = 48000
AUDIO_RATE = 48000

DEVICE_MAKE = "Meta AI"
DEVICE_MODEL = "Ray-Ban Meta Smart Glasses 2"

VIDEO_HANDLER = "Core Media Video"
AUDIO_HANDLER = "Core Media Audio"
DATA_HANDLER = "Core Media Data Handler"
COMPRESSOR_NAME = "'hvc1'"


def atom(kind, payload):
    return struct.pack(">I", 8 + len(payload)) + kind + payload


def parse(data, start=0, end=None):
    if end is None:
        end = len(data)
    out = []
    p = start
    while p + 8 <= end:
        size = struct.unpack(">I", data[p:p + 4])[0]
        kind = data[p + 4:p + 8]
        header = 8
        if size == 1:
            size = struct.unpack(">Q", data[p + 8:p + 16])[0]
            header = 16
        elif size == 0:
            size = end - p
        if size < header or p + size > end:
            break
        out.append((kind, p, size, p + header))
        p += size
    return out


def find(children, kind):
    for c in children:
        if c[0] == kind:
            return c
    return None


def pascal(text):
    raw = text.encode("utf-8")
    return bytes([len(raw)]) + raw


def make_tapt(width, height):
    def dims(kind):
        return atom(kind, struct.pack(">III", 0, width << 16, height << 16))
    return atom(b"tapt", dims(b"clef") + dims(b"prof") + dims(b"enof"))


def make_hdlr(component_type, subtype, name):
    payload = struct.pack(">I", 0)
    payload += component_type + subtype + b"appl"
    payload += struct.pack(">II", 0, 0)
    payload += pascal(name)
    return atom(b"hdlr", payload)


def make_meta(created):
    hdlr = atom(b"hdlr", struct.pack(">I", 0) + struct.pack(">I", 0)
                + b"mdta" + b"\x00" * 12 + b"\x00\x00")

    stamp = created.strftime("%Y-%m-%dT%H:%M:%SZ")
    fields = [
        ("com.apple.quicktime.copyright", DEVICE_MAKE),
        ("com.apple.quicktime.comment",
         "app=%s&device=%s&id=%s" % (DEVICE_MAKE, DEVICE_MODEL, str(uuid.uuid4()).upper())),
        ("com.apple.quicktime.model", DEVICE_MODEL),
        ("com.apple.quicktime.creationdate", stamp),
    ]

    entries = b""
    for key, _ in fields:
        raw = key.encode("utf-8")
        entries += struct.pack(">I", 8 + len(raw)) + b"mdta" + raw
    keys = atom(b"keys", struct.pack(">II", 0, len(fields)) + entries)

    items = b""
    for index, (_, value) in enumerate(fields, start=1):
        raw = value.encode("utf-8")
        data_box = atom(b"data", struct.pack(">II", 1, 0) + raw)
        items += struct.pack(">I", 8 + len(data_box)) + struct.pack(">I", index) + data_box
    ilst = atom(b"ilst", items)

    return atom(b"meta", hdlr + keys + ilst)


def rescale(value, old_ts, new_ts):
    return int(round(value * new_ts / float(old_ts)))


def patch_mvhd(blob, new_timescale):
    version = blob[8]
    body = bytearray(blob)
    if version == 1:
        ts_off, dur_off = 12 + 16, 12 + 20
        old_ts = struct.unpack(">I", bytes(body[ts_off:ts_off + 4]))[0]
        old_dur = struct.unpack(">Q", bytes(body[dur_off:dur_off + 8]))[0]
        struct.pack_into(">I", body, ts_off, new_timescale)
        struct.pack_into(">Q", body, dur_off, rescale(old_dur, old_ts, new_timescale))
    else:
        ts_off, dur_off = 12 + 8, 12 + 12
        old_ts = struct.unpack(">I", bytes(body[ts_off:ts_off + 4]))[0]
        old_dur = struct.unpack(">I", bytes(body[dur_off:dur_off + 4]))[0]
        struct.pack_into(">I", body, ts_off, new_timescale)
        struct.pack_into(">I", body, dur_off, rescale(old_dur, old_ts, new_timescale))
    return bytes(body), old_ts


def patch_tkhd(blob, old_ts, new_ts):
    version = blob[8]
    body = bytearray(blob)
    if version == 1:
        off = 12 + 16 + 4 + 4
        old = struct.unpack(">Q", bytes(body[off:off + 8]))[0]
        struct.pack_into(">Q", body, off, rescale(old, old_ts, new_ts))
    else:
        off = 12 + 8 + 4 + 4
        old = struct.unpack(">I", bytes(body[off:off + 4]))[0]
        struct.pack_into(">I", body, off, rescale(old, old_ts, new_ts))
    return bytes(body)


def patch_elst(blob, old_ts, new_ts):
    version = blob[8]
    body = bytearray(blob)
    count = struct.unpack(">I", bytes(body[12:16]))[0]
    p = 16
    for _ in range(count):
        if version == 1:
            dur = struct.unpack(">Q", bytes(body[p:p + 8]))[0]
            struct.pack_into(">Q", body, p, rescale(dur, old_ts, new_ts))
            p += 20
        else:
            dur = struct.unpack(">I", bytes(body[p:p + 4]))[0]
            struct.pack_into(">I", body, p, rescale(dur, old_ts, new_ts))
            p += 12
    return bytes(body)


def patch_stsd(blob):
    body = bytearray(blob)
    for kind, start, size, payload in parse(bytes(body), 16, len(body)):
        if kind != b"hvc1":
            continue
        field = start + 50
        name = pascal(COMPRESSOR_NAME)
        body[field:field + 32] = name + b"\x00" * (32 - len(name))
    return bytes(body)


def rebuild_stbl(data, node):
    kids = parse(data, node[3], node[1] + node[2])
    out = b""
    for kind, start, size, _ in kids:
        blob = data[start:start + size]
        out += patch_stsd(blob) if kind == b"stsd" else blob
    return atom(b"stbl", out)


def rebuild_minf(data, node, is_video):
    kids = parse(data, node[3], node[1] + node[2])
    out = b""
    for kind, start, size, _ in kids:
        if kind == b"hdlr":
            out += make_hdlr(b"dhlr", b"alis", DATA_HANDLER)
        elif kind == b"stbl" and is_video:
            out += rebuild_stbl(data, (kind, start, size, start + 8))
        else:
            out += data[start:start + size]
    return atom(b"minf", out)


def rebuild_mdia(data, node, is_video):
    kids = parse(data, node[3], node[1] + node[2])
    out = b""
    for kind, start, size, _ in kids:
        if kind == b"minf":
            out += rebuild_minf(data, (kind, start, size, start + 8), is_video)
        elif kind == b"hdlr":
            name = VIDEO_HANDLER if is_video else AUDIO_HANDLER
            out += make_hdlr(b"mhlr", b"vide" if is_video else b"soun", name)
        else:
            out += data[start:start + size]
    return atom(b"mdia", out)


def rebuild_trak(data, node, old_ts, new_ts):
    kids = parse(data, node[3], node[1] + node[2])
    mdia = find(kids, b"mdia")
    is_video = False
    if mdia:
        for kind, start, size, body in parse(data, mdia[3], mdia[1] + mdia[2]):
            if kind == b"hdlr":
                is_video = data[body + 8:body + 12] == b"vide"

    out = b""
    for kind, start, size, _ in kids:
        blob = data[start:start + size]
        if kind == b"tkhd":
            out += patch_tkhd(blob, old_ts, new_ts)
            if is_video:
                out += make_tapt(WIDTH, HEIGHT)
        elif kind == b"tapt":
            continue
        elif kind == b"edts":
            inner = b""
            for k2, s2, sz2, _ in parse(data, start + 8, start + size):
                inner += patch_elst(data[s2:s2 + sz2], old_ts, new_ts) if k2 == b"elst" \
                    else data[s2:s2 + sz2]
            out += atom(b"edts", inner)
        elif kind == b"mdia":
            out += rebuild_mdia(data, (kind, start, size, start + 8), is_video)
        else:
            out += blob
    return atom(b"trak", out)


def rebuild_moov(data, node, created):
    kids = parse(data, node[3], node[1] + node[2])
    mvhd = find(kids, b"mvhd")
    new_mvhd, old_ts = patch_mvhd(data[mvhd[1]:mvhd[1] + mvhd[2]], MOVIE_TIMESCALE)

    out = new_mvhd
    for kind, start, size, _ in kids:
        if kind in (b"mvhd", b"udta", b"meta"):
            continue
        if kind == b"trak":
            out += rebuild_trak(data, (kind, start, size, start + 8),
                                old_ts, MOVIE_TIMESCALE)
        else:
            out += data[start:start + size]
    out += make_meta(created)
    return atom(b"moov", out)


def restructure(path_in, path_out, created):
    data = open(path_in, "rb").read()
    top = parse(data)
    out = b""
    for kind, start, size, _ in top:
        if kind == b"ftyp":
            out += atom(b"ftyp", b"qt  " + struct.pack(">I", 0) + b"qt  ")
        elif kind == b"moov":
            out += rebuild_moov(data, (kind, start, size, start + 8), created)
        elif kind == b"free" or kind == b"skip":
            continue
        else:
            out += data[start:start + size]
    open(path_out, "wb").write(out)


def process_image_to_meta_jpg(input_path, output_path):
    img = Image.open(input_path).convert("RGB")
    
    target_ratio = WIDTH / HEIGHT
    current_ratio = img.width / img.height

    if current_ratio > target_ratio:
        new_width = int(img.height * target_ratio)
        offset_x = (img.width - new_width) // 2
        img_cropped = img.crop((offset_x, 0, offset_x + new_width, img.height))
    else:
        new_height = int(img.width / target_ratio)
        offset_y = (img.height - new_height) // 2
        img_cropped = img.crop((0, offset_y, img.width, offset_y + new_height))

    img_final = img_cropped.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    zeroth_ifd = {
        piexif.ImageIFD.Make: "Meta",
        piexif.ImageIFD.Model: "Ray-Ban Meta Smart Glasses",
        piexif.ImageIFD.Software: "Meta View 175.0.0",
    }
    exif_dict = {"0th": zeroth_ifd, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    exif_bytes = piexif.dump(exif_dict)
    img_final.save(output_path, "jpeg", exif=exif_bytes, quality=95)
    return output_path


def process_to_spin_mov(input_path, output_dir, is_video=False, duration=10):
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    raw_mov = os.path.join(output_dir, f".{base_name}.raw.mov")
    final_mov = os.path.join(output_dir, f"{base_name}_SPIN.MOV")

    dur_val = int(duration) if duration else 10

    if not is_video:
        # For image inputs, encode directly to limited TV range YUV420P
        filter_chain = (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},fps={FPS},format=yuv420p,"
            "zscale=primariesin=bt709:transferin=bt709:matrixin=bt709:"
            "primaries=bt2020:transfer=arib-std-b67:matrix=bt2020nc:range=limited"
        )
        encode_cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-loop", "1", "-i", input_path,
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-t", str(dur_val),
            "-vf", filter_chain,
            "-color_range", "tv",
            "-c:v", "libx265", "-profile:v", "main", "-pix_fmt", "yuv420p",
            "-x265-params", "info=0:log-level=none:colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:range=limited",
            "-tag:v", "hvc1", "-r", str(FPS),
            "-color_primaries", "bt2020", "-color_trc", "arib-std-b67",
            "-colorspace", "bt2020nc",
            "-video_track_timescale", str(VIDEO_TIMESCALE),
            "-c:a", "aac", "-b:a", "192k", "-ar", str(AUDIO_RATE), "-ac", "2",
            "-shortest",
            "-map_metadata", "-1", "-map_metadata:s:v", "-1",
            "-f", "mov", raw_mov
        ]
        subprocess.check_call(encode_cmd)
    else:
        # Video inputs
        filter_chain = (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},fps={FPS},format=yuv420p,"
            "zscale=primariesin=bt709:transferin=bt709:matrixin=bt709:"
            "primaries=bt2020:transfer=arib-std-b67:matrix=bt2020nc:range=limited"
        )
        encode_cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", input_path,
            "-map", "0:v:0", "-map", "0:a:0?",
            "-vf", filter_chain,
            "-color_range", "tv",
            "-c:v", "libx265", "-profile:v", "main", "-pix_fmt", "yuv420p",
            "-x265-params", "info=0:log-level=none:colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:range=limited",
            "-tag:v", "hvc1", "-r", str(FPS),
            "-color_primaries", "bt2020", "-color_trc", "arib-std-b67",
            "-colorspace", "bt2020nc",
            "-video_track_timescale", str(VIDEO_TIMESCALE),
            "-c:a", "aac", "-b:a", "192k", "-ar", str(AUDIO_RATE), "-ac", "2",
            "-map_metadata", "-1", "-map_metadata:s:v", "-1",
            "-f", "mov", raw_mov
        ]
        subprocess.check_call(encode_cmd)

    # Restructure QuickTime Atoms to match Ray-Ban Meta specs
    restructure(raw_mov, final_mov, datetime.now(timezone.utc))

    if os.path.exists(raw_mov):
        os.remove(raw_mov)

    return final_mov
