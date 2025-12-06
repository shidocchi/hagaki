import os
import argparse
import yaml
from pathlib import Path
from .pdfbase import FontFace, PdfBase, FlexTemplate

__version__ = '0.1.0'

class Hagaki:
  """addressee printer for japanese postcard"""

  def __init__(self):
    self.conf = self.load_conf()
    self.font, self.mono = self.search_font()
    if not self.font:
      raise ValueError('No available fonts')
    self.args = self.get_args()
    self.pdf = self.init_pdf()
    self.tpl = self.get_template()
    self.table = self.init_table()
    self.repl = {
      '郵便番号': lambda x:' '.join(list(x)),
      '住所1': lambda x:self.tr(x),
      '住所2': lambda x:self.tr(x),
      '姓1': lambda x:self.justname(x),
      '名1': lambda x:self.justname(x),
      '名2': lambda x:self.justname(x),
    }

  def tr(self, x):
    """Replace yoko (horizontal) into tate (vertical)"""
    return x.translate(self.table)

  def justname(self, x):
    """Justification for surname and given name"""
    if len(x) > 3:
      raise ValueError
    v = list(x)
    if len(v) == 2:
      v.insert(1, '')
    elif len(v) == 1:
      v.insert(2, '')
      v.insert(0, '')
    return "\n".join(v)

  def load_conf(self) -> dict:
    """Load configulation file"""
    fpath = Path(__file__).resolve().parent / 'config.yaml'
    with open(fpath, 'r', encoding='utf8') as f:
      conf = yaml.safe_load(f)
    return conf

  def search_font(self) -> dict:
    """Search available font"""
    pdf = PdfBase()
    d = {}
    mono = []
    for key in self.conf['font']:
      for path in self.conf['fontpath']:
        p = Path(os.path.expandvars(path),
                 self.conf['font'][key])
        if p.exists():
          try:
            pdf.add_font(key, '', p)
            d[key] = p
            if key in self.conf['mono']:
              mono.append(key)
          except (NotImplementedError, ValueError):
            pass
          break
    return d, mono

  def get_args(self) -> argparse.Namespace:
    """Get command options"""
    parser = argparse.ArgumentParser(
      prog='hagaki',
      description='addressee printer for Japanese postcard')
    parser.add_argument('--out', help='output filename')
    parser.add_argument('--page', help='page size',
      choices=self.conf['page'].keys())
    parser.add_argument('--margin', help='margin mm',
      type=float)
    parser.add_argument('--font', help='font',
      choices=self.font.keys())
    parser.add_argument('--mono', help='monospace font',
      choices=self.mono)
    parser.add_argument('--do', help='operation',
      choices=self.conf['choices']['do'])
    parser.set_defaults(**self.conf['default'])
    return parser.parse_args()

  def init_pdf(self) -> PdfBase:
    """Setup postcard PDF"""
    pdf = PdfBase(
      unit='mm',
      orientation='P',
      format=tuple(self.conf['page'][self.args.page])
    )
    pdf.set_margin(self.args.margin)
    pdf.set_auto_page_break(auto=True, margin=5)
    pdf.add_font(self.args.font, '', self.font[self.args.font])
    if self.args.font != self.args.mono:
      pdf.add_font(self.args.mono, '', self.font[self.args.mono])
    return pdf

  def get_template(self) -> FlexTemplate:
    """Setup postcard template"""
    elems = []
    for key in self.conf['elements']:
      val = self.conf['elements'][key]
      e = {'name':key, 'type':'T',
           'font':self.args.font, 'size':val['size'],
           'multiline':True, 'wrapmode':'CHAR',
           'x1':val['pos'][0],
           'y1':val['pos'][1],
           'x2':val['pos'][0]+val['rect'][0],
           'y2':val['pos'][1]+val['rect'][1]}
      if val.get('mono', False):
        e['font'] = self.args.mono
      elems.append(e)
    return FlexTemplate(self.pdf, elements=elems)

  def init_table(self):
    """Make char translate table"""
    return {
      ord(k):v
      for k,v in self.conf['translate'].items()}

  def add_card(self, data):
    """Add page and fill placeholder"""
    self.pdf.add_page()
    for key in data:
      if key in self.repl:
        data[key] = self.repl[key](data[key])
      self.tpl.set(key, data[key])
    self.tpl.render()

  def save(self):
    """Output for file"""
    self.pdf.output(self.args.out)
    if self.args.do:
      os.startfile(self.args.out, operation=self.args.do)
