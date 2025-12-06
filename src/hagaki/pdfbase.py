from fpdf import FPDF, FlexTemplate
from fpdf.fonts import FontFace

class PdfBase(FPDF):
  """PDF writer"""

  def _header(self):
    pass

  def _footer(self):
    pass
