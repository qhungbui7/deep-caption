from dataclasses import dataclass
from pathlib import Path
import subprocess
import socket
import struct
import time

from app.audio.base import AudioCapture
from app.capture.mac.messages import BridgeControl, decode_framed_audio
from app.models import AudioFrame


@dataclass(slots=True)
class MacBridgeClient(AudioCapture):
    socket_path: Path
    source_id: str = "system"
    helper_path: Path | None = None
    _sock: socket.socket | None = None
    _buffer: bytearray | None = None
    _helper_proc: subprocess.Popen[str] | None = None

    def connect(self) -> None:
        if self._sock is not None:
            return
        if not self.socket_path.exists():
            self._try_launch_helper()
        launched = False
        for _ in range(25):
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(str(self.socket_path))
                self._sock = sock
                self._buffer = bytearray()
                return
            except OSError:
                if not launched:
                    self._try_launch_helper()
                    launched = True
                time.sleep(0.2)
        raise RuntimeError(f"Unable to connect to mac helper socket: {self.socket_path}")

    def start(self) -> None:
        self.connect()
        self._send_control(BridgeControl(action="start", source_id=self.source_id))

    def stop(self) -> None:
        if self._sock is not None:
            try:
                self._send_control(BridgeControl(action="stop", source_id=self.source_id))
            finally:
                self._sock.close()
                self._sock = None
                self._buffer = None
        if self._helper_proc is not None:
            self._helper_proc.terminate()
            self._helper_proc.wait(timeout=2)
            self._helper_proc = None

    def read(self) -> AudioFrame:
        if self._sock is None:
            raise RuntimeError("Mac bridge is not connected")
        prefix = self._recv_exact(4)
        packet_len = struct.unpack(">I", prefix)[0]
        packet = self._recv_exact(packet_len)
        return decode_framed_audio(packet)

    def _send_control(self, msg: BridgeControl) -> None:
        if self._sock is None:
            return
        self._sock.sendall(msg.to_bytes())

    def _recv_exact(self, size: int) -> bytes:
        if self._sock is None:
            raise RuntimeError("Socket is closed")
        chunks = bytearray()
        while len(chunks) < size:
            data = self._sock.recv(size - len(chunks))
            if not data:
                raise RuntimeError("Mac audio helper disconnected")
            chunks.extend(data)
        return bytes(chunks)

    def _try_launch_helper(self) -> None:
        if self.helper_path is None:
            return
        helper = self.helper_path
        if not helper.exists():
            return
        if self._helper_proc is not None and self._helper_proc.poll() is None:
            return
        self._helper_proc = subprocess.Popen(
            [str(helper), str(self.socket_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
