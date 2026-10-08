"""Minimal headless libretro host (child process of gpgx_harness.py).

Original code written against the public libretro C ABI; it contains no emulator code.
Loads a libretro core with CONTENT (system directory = WORKDIR/system), runs N frames,
writes RAM dumps in 68000 byte order to WORKDIR (<space>.init.bin right after load =
power-on state, <space>.bin after the last frame) and prints one JSON object on stdout.

usage: python -I libretro_host.py CORE CONTENT FRAMES WORKDIR REGION
"""
import ctypes as C
import hashlib
import json
import os
import sys

ENV_EXPERIMENTAL = 0x10000
ENV_GET_SYSTEM_DIRECTORY = 9
ENV_SET_PIXEL_FORMAT = 10
ENV_GET_VARIABLE = 15
ENV_GET_LOG_INTERFACE = 27
ENV_GET_SAVE_DIRECTORY = 31
ENV_SET_MEMORY_MAPS = 36
SAMPLE_EVERY = 60


class GameInfo(C.Structure):
    _fields_ = [("path", C.c_char_p), ("data", C.c_void_p), ("size", C.c_size_t), ("meta", C.c_char_p)]


class SystemInfo(C.Structure):
    _fields_ = [("library_name", C.c_char_p), ("library_version", C.c_char_p), ("valid_extensions", C.c_char_p),
                ("need_fullpath", C.c_bool), ("block_extract", C.c_bool)]


class Variable(C.Structure):
    _fields_ = [("key", C.c_char_p), ("value", C.c_char_p)]


class MemDesc(C.Structure):
    _fields_ = [("flags", C.c_uint64), ("ptr", C.c_void_p), ("offset", C.c_size_t), ("start", C.c_size_t),
                ("select", C.c_size_t), ("disconnect", C.c_size_t), ("len", C.c_size_t), ("addrspace", C.c_char_p)]


class MemMap(C.Structure):
    _fields_ = [("descriptors", C.POINTER(MemDesc)), ("num_descriptors", C.c_uint)]


# Variadic printf-style log callback: only the format string is captured (args are ignored).
LOG_CB = C.CFUNCTYPE(None, C.c_int, C.c_char_p)


class LogInterface(C.Structure):
    _fields_ = [("log", LOG_CB)]


ENV_CB = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO_CB = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDIO_BATCH_CB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL_CB = C.CFUNCTYPE(None)
INPUT_CB = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)


def unswap(raw):
    """GPGX LSB_FIRST builds store 68K RAM byte-swapped per 16-bit word."""
    out = bytearray(raw)
    out[0::2], out[1::2] = raw[1::2], raw[0::2]
    return bytes(out)


def main(core_path, rom_path, frames, workdir, region):
    frames = int(frames)
    sysdir = os.path.join(workdir, "system").encode()
    os.makedirs(sysdir, exist_ok=True)
    logs, regions = [], {}
    options = {} if region == "auto" else {b"genesis_plus_gx_region_detect": region.encode()}

    def env(cmd, data):
        cmd &= ~ENV_EXPERIMENTAL
        if cmd in (ENV_GET_SYSTEM_DIRECTORY, ENV_GET_SAVE_DIRECTORY):
            C.cast(data, C.POINTER(C.c_char_p))[0] = sysdir  # `sysdir` outlives the core
            return True
        if cmd == ENV_SET_PIXEL_FORMAT:
            return True
        if cmd == ENV_GET_VARIABLE:
            var = C.cast(data, C.POINTER(Variable))[0]
            var.value = options.get(var.key)
            return var.value is not None
        if cmd == ENV_GET_LOG_INTERFACE:
            C.cast(data, C.POINTER(LogInterface))[0].log = log_cb
            return True
        if cmd == ENV_SET_MEMORY_MAPS:
            mm = C.cast(data, C.POINTER(MemMap))[0]
            for i in range(mm.num_descriptors):
                d = mm.descriptors[i]
                name = (d.addrspace or b"").decode(errors="replace")
                regions[name] = (d.ptr, d.len)
            return True
        return False

    @LOG_CB
    def log_cb(level, fmt):
        logs.append(f"[{level}] " + (fmt or b"").decode(errors="replace").rstrip())

    cbs = [ENV_CB(env), VIDEO_CB(lambda *a: None), AUDIO_CB(lambda *a: None),
           AUDIO_BATCH_CB(lambda d, n: n), POLL_CB(lambda: None), INPUT_CB(lambda *a: 0)]
    core = C.CDLL(os.path.abspath(core_path))
    core.retro_api_version.restype = C.c_uint
    core.retro_load_game.restype = C.c_bool
    core.retro_load_game.argtypes = [C.POINTER(GameInfo)]
    for fn, cb in zip(["environment", "video_refresh", "audio_sample", "audio_sample_batch",
                       "input_poll", "input_state"], cbs):
        getattr(core, "retro_set_" + fn)(cb)

    si = SystemInfo()
    core.retro_get_system_info(C.byref(si))
    result = {"api_version": core.retro_api_version(),
              "library_version": (si.library_version or b"").decode(errors="replace"),
              "loaded": False, "frames_run": 0, "regions": [], "samples": [], "core_log": logs}
    core.retro_init()
    info = GameInfo(os.path.abspath(rom_path).encode(), None, 0, None)
    result["loaded"] = bool(core.retro_load_game(C.byref(info)))
    if result["loaded"]:
        # 68KRAM = main CPU work RAM ($FF0000), PRGRAM = sub CPU program RAM ($000000).
        # The core only publishes these maps when it is in Mega-CD mode.
        result["regions"] = sorted(regions)
        dumps = {"main": regions.get("68KRAM"), "prg": regions.get("PRGRAM")}

        def snap():
            return {k: unswap(C.string_at(p, n)) for k, (p, n) in
                    ((k, v) for k, v in dumps.items() if v)}

        def save(suffix):
            for k, v in snap().items():
                with open(os.path.join(workdir, k + suffix), "wb") as fh:
                    fh.write(v)

        save(".init.bin")  # retro_load_game has reset the system: this is the power-on state
        for f in range(1, frames + 1):
            core.retro_run()
            result["frames_run"] = f
            if f % SAMPLE_EVERY == 0 or f == frames or f == 1:
                result["samples"].append({"frame": f, **{f"{k}_sha256": hashlib.sha256(v).hexdigest()
                                                         for k, v in snap().items()}})
        save(".bin")
        core.retro_unload_game()
    core.retro_deinit()
    print(json.dumps(result))


if __name__ == "__main__":
    main(*sys.argv[1:6])
