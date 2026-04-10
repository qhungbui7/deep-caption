from dataclasses import dataclass
import json
import subprocess


@dataclass(slots=True)
class AudioSource:
    id: str
    name: str
    kind: str


def list_sources() -> list[AudioSource]:
    sources: list[AudioSource] = []
    sources.extend(_pipewire_sources())
    sources.extend(_pulse_sources())
    dedup: dict[str, AudioSource] = {}
    for source in sources:
        dedup[source.id] = source
    return list(dedup.values())


def _pipewire_sources() -> list[AudioSource]:
    try:
        output = subprocess.run(
            ["pw-dump"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if output.returncode != 0 or not output.stdout.strip():
        return []
    try:
        payload = json.loads(output.stdout)
    except json.JSONDecodeError:
        return []
    sources: list[AudioSource] = []
    for node in payload:
        if not isinstance(node, dict):
            continue
        info = node.get("info", {})
        props = info.get("props", {}) if isinstance(info, dict) else {}
        media_class = str(props.get("media.class", ""))
        if media_class not in {"Audio/Source", "Stream/Input/Audio"}:
            continue
        node_id = str(node.get("id", ""))
        name = str(props.get("node.description") or props.get("node.name") or f"PipeWire {node_id}")
        if node_id:
            sources.append(AudioSource(id=f"pw:{node_id}", name=name, kind="pipewire"))
    return sources


def _pulse_sources() -> list[AudioSource]:
    try:
        output = subprocess.run(
            ["pactl", "list", "short", "sources"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if output.returncode != 0:
        return []
    sources: list[AudioSource] = []
    for line in output.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        source_name = parts[1].strip()
        source_id = parts[0].strip()
        sources.append(AudioSource(id=f"pulse:{source_name}", name=source_name, kind="pulseaudio"))
        if source_id:
            sources.append(AudioSource(id=f"pulse-id:{source_id}", name=source_name, kind="pulseaudio"))
    return sources
