import io
import os
import unittest
os.environ.setdefault("EMULATOR_URL","http://localhost:4588")
os.environ.setdefault("FIRESTORE_EMULATOR_HOST","localhost:4588")
from processor.app import InvalidPDF, inspect_pdf
from pypdf import PdfWriter

class ParserTest(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(InvalidPDF):
            inspect_pdf(b"")
    def test_one_page(self):
        w=PdfWriter()
        w.add_blank_page(72,72)
        output=io.BytesIO()
        w.write(output)
        self.assertEqual(inspect_pdf(output.getvalue())["page_count"],1)
