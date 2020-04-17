#!/usr/bin/env python3
#
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
# Built on top of Unicorn emulator (www.unicorn-engine.org)

import struct
from qiling.os.windows.const import *
from qiling.os.windows.fncc import *
from qiling.os.const import *
from qiling.os.windows.utils import *
from qiling.os.windows.thread import *
from qiling.os.windows.handle import *
from qiling.exception import *


# typedef struct _OSVERSIONINFOW {
#   ULONG dwOSVersionInfoSize;
#   ULONG dwMajorVersion;
#   ULONG dwMinorVersion;
#   ULONG dwBuildNumber;
#   ULONG dwPlatformId;
#   WCHAR szCSDVersion[128];
# }


# NTSYSAPI NTSTATUS RtlGetVersion(
#   PRTL_OSVERSIONINFOW lpVersionInformation
# );
@winapi(cc=CDECL, params={
    "lpVersionInformation": POINTER
})
def hook_RtlGetVersion(self, address, params):
    pointer = params["lpVersionInformation"]
    size = int.from_bytes(self.ql.mem.read(pointer, 4), byteorder="little")
    os_version_info_asked = {"dwOSVersionInfoSize": size,
                             VER_MAJORVERSION: int.from_bytes(self.ql.mem.read(pointer + 4, 4), byteorder="little"),
                             VER_MINORVERSION: int.from_bytes(self.ql.mem.read(pointer + 8, 4), byteorder="little"),
                             VER_BUILDNUMBER: int.from_bytes(self.ql.mem.read(pointer + 12, 4), byteorder="little"),
                             VER_PLATFORMID: int.from_bytes(self.ql.mem.read(pointer + 16, 4), byteorder="little"),
                             "szCSDVersion": int.from_bytes(self.ql.mem.read(pointer + 20, 128), byteorder="little"),
                             }
    self.ql.mem.write(pointer + 4, self.profile.getint("SYSTEM", "majorVersion").to_bytes(4, byteorder="little"))
    self.ql.mem.write(pointer + 8, self.profile.getint("SYSTEM", "minorVersion").to_bytes(4, byteorder="little"))

    self.ql.dprint(D_RPRT, "[=] The sample is checking the windows Version!")
    return STATUS_SUCCESS


# NTSYSAPI NTSTATUS ZwSetInformationThread(
#   HANDLE          ThreadHandle,
#   THREADINFOCLASS ThreadInformationClass,
#   PVOID           ThreadInformation,
#   ULONG           ThreadInformationLength
# );
@winapi(cc=CDECL, params={
    "ThreadHandle": HANDLE,
    "ThreadInformationClass": INT,
    "ThreadInformation": POINTER,
    "ThreadInformationLength": ULONGLONG,

})
def hook_ZwSetInformationThread(self, address, params):
    thread = params["ThreadHandle"]
    if thread == self.thread_manager.cur_thread.id:
        size = params["ThreadInformationLength"]
        if size == 0:
            return STATUS_INFO_LENGTH_MISMATCH
        dst = params["ThreadInformation"]
        if dst == 0:
            return STATUS_INFO_LENGTH_MISMATCH

        information = params["ThreadInformationClass"]
        if information == ThreadHideFromDebugger:
            self.ql.dprint(D_RPRT, "[=] Sample is checking debugger via SetInformationThread")
            self.ql.mem.write(dst, 0x0.to_bytes(1, byteorder="little"))
        else:
            raise QlErrorNotImplemented("[!] API not implemented")

    else:
        raise QlErrorNotImplemented("[!] API not implemented")
    return STATUS_SUCCESS


# NTSYSAPI NTSTATUS ZwClose(
#   HANDLE Handle
# );
@winapi(cc=CDECL, params={
    "Handle": HANDLE

})
def hook_ZwClose(self, address, params):
    value = params["Handle"]
    handle = self.handle_manager.get(value)
    if handle is None:
        return STATUS_INVALID_HANDLE
    return STATUS_SUCCESS
