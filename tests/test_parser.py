import io
import os
import unittest

os.environ.setdefault("EMULATOR_URL", "http://localhost:4588")
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:4588")

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    TextStringObject,
)
from processor.app import InvalidPDF, inspect_pdf


def build_pdf(pages=1, encrypted=False, js=False, embedded=False):
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(72, 72)
    if js:
        w._root_object.update(
            {
                NameObject("/OpenAction"): DictionaryObject(
                    {
                        NameObject("/S"): NameObject("/JavaScript"),
                        NameObject("/JS"): TextStringObject("/* inert */"),
                    }
                )
            }
        )
    if embedded:
        ef = DecodedStreamObject()
        ef.set_data(b"synthetic")
        ef.update({NameObject("/Type"): NameObject("/EmbeddedFile")})
        ref = w._add_object(ef)
        w._root_object.update(
            {
                NameObject("/Names"): DictionaryObject(
                    {
                        NameObject("/EmbeddedFiles"): DictionaryObject(
                            {
                                NameObject("/Names"): ArrayObject(
                                    [
                                        TextStringObject("a.txt"),
                                        DictionaryObject(
                                            {
                                                NameObject("/EF"): DictionaryObject(
                                                    {NameObject("/F"): ref}
                                                )
                                            }
                                        ),
                                    ]
                                )
                            }
                        )
                    }
                )
            }
        )
    if encrypted:
        w.encrypt("synthetic")
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()


class ParserTest(unittest.TestCase):
    def test_empty_signature(self):
        with self.assertRaises(InvalidPDF) as ctx:
            inspect_pdf(b"")
        self.assertEqual(str(ctx.exception), "INVALID_SIGNATURE")

    def test_one_page(self):
        res = inspect_pdf(build_pdf(pages=1))
        self.assertEqual(res["page_count"], 1)
        self.assertEqual(res["warnings"], [])

    def test_multipage(self):
        res = inspect_pdf(build_pdf(pages=3))
        self.assertEqual(res["page_count"], 3)

    def test_corrupt_structure(self):
        with self.assertRaises(InvalidPDF) as ctx:
            inspect_pdf(b"%PDF-1.4\ncorrupt")
        self.assertEqual(str(ctx.exception), "INVALID_STRUCTURE")

    def test_encrypted(self):
        with self.assertRaises(InvalidPDF) as ctx:
            inspect_pdf(build_pdf(encrypted=True))
        self.assertEqual(str(ctx.exception), "ENCRYPTED")

    def test_zero_pages(self):
        with self.assertRaises(InvalidPDF) as ctx:
            inspect_pdf(build_pdf(pages=0))
        self.assertEqual(str(ctx.exception), "PAGE_COUNT")

    def test_javascript_and_embedded_warnings(self):
        res = inspect_pdf(build_pdf(pages=1, js=True, embedded=True))
        self.assertEqual(res["page_count"], 1)
        self.assertIn("has_javascript", res["warnings"])
        self.assertIn("has_embedded_files", res["warnings"])
