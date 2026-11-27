"""Create only synthetic fixtures under samples/generated."""

from pathlib import Path
from pypdf import PdfWriter
from pypdf.generic import NameObject, DictionaryObject

root = Path("samples/generated")
root.mkdir(parents=True, exist_ok=True)


def make(name, pages, kind=""):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(72, 72)
    if kind == "encrypted":
        writer.encrypt("sample")
    if kind == "attachment":
        writer.add_attachment("synthetic.txt", b"harmless")
    if kind == "marker":
        writer.root_object[NameObject("/DocuFlowMarker")] = writer._add_object(
            DictionaryObject({NameObject("/S"): NameObject("/JavaScript")})
        )
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as stream:
        writer.write(stream)


make("valid.pdf", 1)
make("multipage.pdf", 3)
make("same-name/valid.pdf", 2)
make("empty-pages.pdf", 0)
make("encrypted.pdf", 1, "encrypted")
make("attachment.pdf", 1, "attachment")
make("marker.pdf", 1, "marker")
(root / "identical.pdf").write_bytes((root / "valid.pdf").read_bytes())
for name, data in {
    "empty.pdf": b"",
    "unsupported.txt": b"synthetic",
    "unsupported.exe": b"synthetic",
    "renamed.pdf": b"synthetic",
    "corrupt.pdf": b"%PDF-1.4 incomplete",
    "oversized.pdf": bytes(10485761),
}.items():
    (root / name).write_bytes(data)
print(
    "Fixtures written. The traversal case uses a multipart display name supplied by the test."
)
