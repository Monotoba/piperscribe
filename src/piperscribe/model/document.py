from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .spans import Span


@dataclass(slots=True)
class PiperSettings:
    model_path: str = ""
    length_scale: float = 1.0
    noise_scale: float = 0.667
    noise_w: float = 0.8

    def to_args(self) -> list[str]:
        args = []
        if self.model_path:
            args += ["--model", self.model_path]
        args += ["--length_scale", str(self.length_scale)]
        args += ["--noise_scale", str(self.noise_scale)]
        args += ["--noise_w", str(self.noise_w)]
        return args

    def as_dict(self) -> Dict[str, Any]:
        return {
            "model_path": self.model_path,
            "length_scale": self.length_scale,
            "noise_scale": self.noise_scale,
            "noise_w": self.noise_w,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PiperSettings":
        return PiperSettings(
            model_path=str(d.get("model_path", "")),
            length_scale=float(d.get("length_scale", 1.0)),
            noise_scale=float(d.get("noise_scale", 0.667)),
            noise_w=float(d.get("noise_w", 0.8)),
        )


@dataclass(slots=True)
class Document:
    """Single document within a project."""
    id: str
    title: str
    text: str = ""
    source_path: Optional[str] = None
    manual_exclusions: List[Span] = field(default_factory=list)
    exclusions: List[Span] = field(default_factory=list)
    piper: PiperSettings = field(default_factory=PiperSettings)
    audio_path: Optional[str] = None
    audio_duration: float = 0.0
    # Fingerprint of the voice, settings, and text the audio was made from
    audio_signature: str = ""
    enabled: bool = True
    order: int = 0

    @staticmethod
    def generate_id() -> str:
        """Generate a unique document ID."""
        return str(uuid.uuid4())

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "source_path": self.source_path,
            "manual_exclusions": [{"start": s.start, "end": s.end, "reason": s.reason} for s in self.manual_exclusions],
            "exclusions": [{"start": s.start, "end": s.end, "reason": s.reason} for s in self.exclusions],
            "piper": self.piper.as_dict(),
            "audio_path": self.audio_path,
            "audio_duration": self.audio_duration,
            "audio_signature": self.audio_signature,
            "enabled": self.enabled,
            "order": self.order,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Document":
        return Document(
            id=str(d.get("id", Document.generate_id())),
            title=str(d.get("title", "Untitled")),
            text=str(d.get("text", "")),
            source_path=d.get("source_path"),
            manual_exclusions=[Span(int(s["start"]), int(s["end"]), str(s.get("reason", ""))) for s in d.get("manual_exclusions", [])],
            exclusions=[Span(int(s["start"]), int(s["end"]), str(s.get("reason", ""))) for s in d.get("exclusions", [])],
            piper=PiperSettings.from_dict(d.get("piper", {})),
            audio_path=d.get("audio_path"),
            audio_duration=float(d.get("audio_duration", 0.0)),
            audio_signature=str(d.get("audio_signature", "")),
            enabled=bool(d.get("enabled", True)),
            order=int(d.get("order", 0)),
        )


@dataclass(slots=True)
class DocumentProject:
    title: str = "Untitled Project"
    documents: List[Document] = field(default_factory=list)
    theme: str = "system"  # system | light | dark
    default_piper: PiperSettings = field(default_factory=PiperSettings)

    # Legacy fields for backward compatibility (deprecated, use documents instead)
    source_path: Optional[str] = None
    text: str = ""
    manual_exclusions: List[Span] = field(default_factory=list)
    exclusions: List[Span] = field(default_factory=list)
    piper: PiperSettings = field(default_factory=PiperSettings)

    def add_document(self, doc: Document) -> None:
        """Add a document to the project."""
        self.documents.append(doc)

    def remove_document(self, doc_id: str) -> None:
        """Remove a document by ID."""
        self.documents = [d for d in self.documents if d.id != doc_id]

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None

    def reorder_documents(self, doc_ids: List[str]) -> None:
        """Reorder documents based on list of IDs."""
        # Create a mapping of id to document
        doc_map = {d.id: d for d in self.documents}
        # Rebuild list in new order
        self.documents = [doc_map[doc_id] for doc_id in doc_ids if doc_id in doc_map]
        # Update order field
        for i, doc in enumerate(self.documents):
            doc.order = i

    def get_playlist_order(self) -> List[Document]:
        """Get enabled documents in playlist order."""
        enabled = [d for d in self.documents if d.enabled]
        return sorted(enabled, key=lambda d: d.order)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "documents": [d.as_dict() for d in self.documents],
            "theme": self.theme,
            "default_piper": self.default_piper.as_dict(),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "DocumentProject":
        # Check if this is an old single-document project
        if "text" in d and "documents" not in d:
            # Migrate old format to new format with single document
            doc_id = Document.generate_id()

            # Get exclusions - handle both old and new format
            manual_excl = []
            if "manual_exclusions" in d:
                manual_excl = [Span(int(s["start"]), int(s["end"]), str(s.get("reason", ""))) for s in d.get("manual_exclusions", [])]
            else:
                # Backward compat: treat legacy exclusions as manual
                manual_excl = [Span(int(s["start"]), int(s["end"]), str(s.get("reason", ""))) for s in d.get("exclusions", [])]

            exclusions = [Span(int(s["start"]), int(s["end"]), str(s.get("reason", ""))) for s in d.get("exclusions", [])]

            # Create single document from legacy fields
            doc = Document(
                id=doc_id,
                title=str(d.get("title", "Untitled")),
                text=str(d.get("text", "")),
                source_path=d.get("source_path"),
                manual_exclusions=manual_excl,
                exclusions=exclusions,
                piper=PiperSettings.from_dict(d.get("piper", {})),
                order=0,
                enabled=True,
            )

            proj = DocumentProject(
                title=str(d.get("title", "Untitled Project")),
                documents=[doc],
                theme=str(d.get("theme", "system")),
                default_piper=PiperSettings.from_dict(d.get("piper", {})),
                # Also populate legacy fields for backward compatibility with existing UI code
                source_path=d.get("source_path"),
                text=str(d.get("text", "")),
                manual_exclusions=manual_excl,
                exclusions=exclusions,
                piper=PiperSettings.from_dict(d.get("piper", {})),
            )
            return proj

        # New multi-document format
        proj = DocumentProject(
            title=str(d.get("title", "Untitled Project")),
            documents=[Document.from_dict(dd) for dd in d.get("documents", [])],
            theme=str(d.get("theme", "system")),
            default_piper=PiperSettings.from_dict(d.get("default_piper", {})),
        )
        return proj
