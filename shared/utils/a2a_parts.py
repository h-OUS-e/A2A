
from a2a.types import Part, TextPart
from a2a.utils.parts import get_text_parts





def get_metadata_parts(parts: list[Part]) -> list[str]:
    """Extracts metadata dict from all TextPart objects in a list of Parts.

    Args:
        parts: A list of `Part` objects.

    Returns:
        A list of strings containing the text content from any `TextPart` objects found.
    """
    return [part.root.metadata for part in parts if isinstance(part.root, TextPart)][0]


def extract_text(parts: list[Part]) -> str:
    """Extract text from a list of A2A Part objects."""
    return "\n".join(get_text_parts(parts))


def extract_metadata(parts: list[Part]) -> str:
    """Extract metadata from a list of A2A Part objects."""
    return "\n".join(get_metadata_parts(parts))

