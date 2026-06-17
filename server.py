import socketserver,http.server,json,base64,io,re,os,traceback
from pypdf import PdfReader,PdfWriter
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
import pypdf

PORT=5000
STATIC=os.path.join(os.path.dirname(__file__),'static')

# ---- ANALYSIS ENGINE ----
def analyze_pdf(data):
  findings=[]
  try:
    reader=PdfReader(io.BytesIO(data))
    for pn,page in enumerate(reader.pages,1):
      txt=page.extract_text() or ''
      lines=[l.strip() for l in txt.splitlines() if l.strip()]

      # --- Rule 1: Extreme tight tolerances (e.g. +/-0.001 or smaller)
      for m in re.finditer(r'[+\-]?\s*0\.0{3,}\d*',txt):
        findings.append({'page':pn,'type':'extreme_tolerance',
          'severity':'high','current':m.group().strip(),
          'suggested':'Review tolerance - may be overly tight',
          'reason':'Tolerance value appears extremely tight. Verify manufacturability.',
          'x':0.3,'y':0.4})

      # --- Rule 2: Missing title block keywords
      tb_keys=['SCALE','REV','DWG','DRAWN','DATE','MATERIAL','FINISH']
      page_upper=txt.upper()
      for kw in tb_keys:
        if kw not in page_upper:
          findings.append({'page':pn,'type':'missing_title_block_field',
            'severity':'medium','current':'(absent)','suggested':f'Add {kw} field',
            'reason':f'Title block field "{kw}" not found on page {pn}.',
            'x':0.85,'y':0.92})

      # --- Rule 3: Conflicting/duplicate dimensions (same value appearing many times)
      dim_vals=re.findall(r'\b(\d+\.\d+|\d+)\s*(?:mm|in|")?\b',txt)
      from collections import Counter
      counts=Counter(dim_vals)
      for val,cnt in counts.items():
        if cnt>=4 and float(val)>0:
          findings.append({'page':pn,'type':'possible_duplicate_dimension',
            'severity':'low','current':val,'suggested':'Verify - value appears many times',
            'reason':f'Value "{val}" appears {cnt} times on page {pn}. Possible duplicate.',
            'x':0.5,'y':0.5})

      # --- Rule 4: All-uppercase notes (shouting / formatting issue)
      for ln in lines:
        if len(ln)>15 and ln.isupper() and not any(k in ln for k in ['SCALE','REV','DWG','DRAWN','DATE','MATERIAL','FINISH','DRAWING','APPROVED']):
          findings.append({'page':pn,'type':'formatting_note',
            'severity':'low','current':ln[:60],'suggested':'Review note formatting',
            'reason':'Note appears in ALL CAPS - verify intentional.',
            'x':0.25,'y':0.6})
          break  # one per page

      # --- Rule 5: No tolerance indicator on page
      if not re.search(r'[+\-]\s*0\.\d+|TOL|TOLERANCE',txt,re.I):
        findings.append({'page':pn,'type':'missing_tolerance_indicator',
          'severity':'medium','current':'(none found)','suggested':'Add general tolerance note',
          'reason':'No tolerance specification found on this page.',
          'x':0.7,'y':0.85})

      # --- Rule 6: Revision block check
      if not re.search(r'REV|REVISION',txt,re.I):
        findings.append({'page':pn,'type':'missing_revision_block',
          'severity':'medium','current':'(none found)','suggested':'Add revision block',
          'reason':'No revision indicator found on page.',
          'x':0.88,'y':0.1})

  except Exception as e:
    traceback.print_exc()
    findings.append({'page':1,'type':'parse_error','severity':'high',
      'current':'','suggested':'','reason':f'Could not parse PDF: {e}','x':0.5,'y':0.5})
  # Deduplicate by (page,type,current)
  seen=set()
  unique=[]
  for f in findings:
    key=(f['page'],f['type'],f.get('current','')[:30])
    if key not in seen:
      seen.add(key)
      unique.append(f)
  return unique

# ---- EXPORT ENGINE ----
def export_pdf(data,findings):
  reader=PdfReader(io.BytesIO(data))
  writer=PdfWriter()
  by_page={}
  for f in findings:
    by_page.setdefault(f.get('page',1),[]).append(f)
  COLORS={'high':'#B71C1C','medium':'#E65100','low':'#1565C0'}
  for pn,page in enumerate(reader.pages,1):
    if pn in by_page:
      try:
        mb=page.mediabox
        pw,ph=float(mb.width),float(mb.height)
        pkt=io.BytesIO()
        c=Canvas(pkt,pagesize=(pw,ph))
        # Header banner
        c.setFillColor(HexColor('#0D47A1'))
        c.rect(8,ph-24,pw-16,20,fill=1,stroke=0)
        c.setFillColor(HexColor('#FFFFFF'))
        c.setFont('Helvetica-Bold',7)
        c.drawString(12,ph-14,f'DRAWING REVIEW - APPROVED CHANGES | Page {pn}')
        y=ph-34
        for item in by_page[pn]:
          if y<50: break
          col=COLORS.get(item.get('severity','low'),'#333333')
          c.setFillColor(HexColor('#FAFAFA'))
          c.roundRect(8,y-36,pw-16,38,3,fill=1,stroke=0)
          c.setFillColor(HexColor(col))
          c.rect(8,y-36,5,38,fill=1,stroke=0)
          c.setFillColor(HexColor('#111111'))
          c.setFont('Helvetica-Bold',6.5)
          c.drawString(18,y-4,f"[{item.get('id','')}] {item.get('type','').replace('_',' ').upper()}")
          c.setFont('Helvetica',6)
          c.drawString(18,y-14,f"Was: {str(item.get('current',''))[:100]}")
          c.drawString(18,y-23,f"Change to: {str(item.get('suggested',''))[:100]}")
          c.setFillColor(HexColor('#555555'))
          c.drawString(18,y-32,f"Reason: {str(item.get('reason',''))[:110]}")
          y-=44
        c.save()
        pkt.seek(0)
        overlay=pypdf.PdfReader(pkt).pages[0]
        page.merge_page(overlay)
      except Exception as e:
        print(f'[server] overlay error page {pn}: {e}')
    writer.add_page(page)
  out=io.BytesIO()
  writer.write(out)
  return out.getvalue()

# ---- HTTP HANDLER ----
class Handler(http.server.SimpleHTTPRequestHandler):
  def __init__(self,*a,**kw):
    super().__init__(*a,directory=STATIC,**kw)

  def do_GET(self):
    if self.path=='/favicon.ico':
      self.send_response(204); self.end_headers(); return
    super().do_GET()

  def do_POST(self):
    try:
      length=int(self.headers['Content-Length'])
      body=json.loads(self.rfile.read(length))
      if self.path=='/analyze':
        pdf_data=base64.b64decode(body['pdf'])
        findings=analyze_pdf(pdf_data)
        resp=json.dumps({'findings':findings}).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Content-Length',str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)
      elif self.path=='/export':
        pdf_data=base64.b64decode(body['pdf'])
        findings=body.get('findings',[])
        result=export_pdf(pdf_data,findings)
        self.send_response(200)
        self.send_header('Content-Type','application/pdf')
        self.send_header('Content-Disposition','attachment; filename="reviewed_drawing.pdf"')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Content-Length',str(len(result)))
        self.end_headers()
        self.wfile.write(result)
      else:
        self.send_response(404); self.end_headers()
    except Exception as e:
      traceback.print_exc()
      self.send_response(500); self.end_headers()

  def do_OPTIONS(self):
    self.send_response(200)
    self.send_header('Access-Control-Allow-Origin','*')
    self.send_header('Access-Control-Allow-Methods','POST,GET,OPTIONS')
    self.send_header('Access-Control-Allow-Headers','Content-Type')
    self.end_headers()

  def log_message(self,fmt,*args):
    print(f'[server] {fmt%args}')

if __name__=='__main__':
  socketserver.TCPServer.allow_reuse_address=True
  with socketserver.TCPServer(('',PORT),Handler) as s:
    print(f'\n Drawing Reviewer V2  ->  http://localhost:{PORT}')
    print(' Press Ctrl+C to stop\n')
    s.serve_forever()
