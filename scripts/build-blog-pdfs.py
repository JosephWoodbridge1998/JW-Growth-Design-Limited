from pathlib import Path
import re,sys,hashlib
from html import escape
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,HRFlowable
from pypdf import PdfReader
B="#176b96";T="#252b33";G="#526171"
styles={"body":ParagraphStyle("body",fontName="Helvetica",fontSize=10.3,leading=15,textColor=colors.HexColor(T),spaceAfter=9),"small":ParagraphStyle("small",fontName="Helvetica",fontSize=8.5,leading=12,textColor=colors.HexColor(G),spaceAfter=6),"title":ParagraphStyle("title",fontName="Helvetica-Bold",fontSize=29,leading=34,textColor=colors.HexColor(T),spaceAfter=18),"heading":ParagraphStyle("heading",fontName="Helvetica-Bold",fontSize=17,leading=22,textColor=colors.HexColor(T),spaceAfter=14),"sub":ParagraphStyle("sub",fontName="Helvetica-Bold",fontSize=11.8,leading=16,textColor=colors.HexColor(B),spaceAfter=6)}
logo=Image.open(".build/jw-logo.png")
def para(text,style="body",raw=False):return Paragraph(text if raw else escape(text),styles[style])
def section(text,name):
 m=re.search(r"^## "+re.escape(name)+r"\s*\n(.*?)(?=^## |\Z)",text,re.M|re.S)
 assert m,name
 return m.group(1).strip()
def normal(s):return " ".join(s.split())
records=[]
for source in sorted(Path("blog/sources").glob("*.md")):
 text=source.read_text();title=re.search(r"^# ([^\n]+)",text).group(1);issue=int(re.search(r"Issue (\d+)",text).group(1));deck=text.split("\n\n")[2]
 stem={1:"5-signs-your-website-is-costing-you-customers",2:"why-your-website-matters-six-reasons",3:"common-online-challenges-local-businesses-consultants",4:"getting-found-local-search-starter-guide",5:"first-impressions-trust-website-design"}[issue]
 numbered=re.findall(r"^## (\d{2}) ([^\n]+)\n(.*?)(?=^## |\Z)",text,re.M|re.S);assert len(numbered) in (5,6)
 story=[para(title,"title"),para(deck),Spacer(1,18),para("What you will take away","heading"),para(section(text,"Reader outcome")),Spacer(1,14),para("Start with this quick check","heading")]
 for block in section(text,"Start here").split("\n\n"):
  for line in block.splitlines():story.append(para(line))
 story += [PageBreak(),para("What to check - and why it matters","heading")]
 for number,heading,body in numbered:story += [para(number+"  "+heading,"sub"),para(body.strip()),Spacer(1,5)]
 story += [PageBreak(),para("Your practical action plan","heading")]
 for block in section(text,"Action plan").split("\n\n"):
  if block.startswith("### "):
   heading,body=block[4:].split("\n",1);story += [para(heading,"sub"),para(body)]
  else:story.append(para(block))
  story.append(Spacer(1,12))
 story += [PageBreak(),para("Make the next step specific","heading")]
 for line in section(text,"Worksheet").splitlines():story += [para(line.removeprefix("- "),"sub"),Spacer(1,17),HRFlowable(width="100%",color=colors.HexColor("#d3dfe8")),Spacer(1,16)]
 nxt=section(text,"Next step");url=re.search(r"https://\S+",nxt).group(0)
 story += [para("Discuss your next step with Joseph","sub"),para(nxt.replace(url,"").strip()),para('<link href="'+escape(url)+'" color="'+B+'">Start a conversation with Joseph</link>',raw=True),Spacer(1,10),para("Research notes and further reading","sub")]
 refs=[]
 for line in section(text,"Sources").splitlines():
  label,link=line.rsplit(": https://",1);refs.append("https://"+link);story.append(para('<link href="https://'+escape(link)+'" color="'+B+'">'+escape(label)+'</link>',"small",True))
 story.append(para("Research checked 25 October 2026. Examples are illustrative, not measured client results. Educational guidance, not a full technical, accessibility or legal audit.","small"))
 def header(c,d,issue=issue):
  w,h=d.pagesize;c.setFillColor(colors.HexColor(B));c.rect(0,h-9,w,9,fill=1,stroke=0)
  lw=249;lh=lw*logo.height/logo.width;c.drawImage(".build/jw-logo.png",46,h-20-lh,width=lw,height=lh,mask="auto")
  c.setFont("Helvetica-Bold",8);c.setFillColor(colors.HexColor(G));c.drawRightString(w-46,h-42,f"JOURNAL / ISSUE {issue:02d}")
  c.setStrokeColor(colors.HexColor("#d3dfe8"));c.line(46,54,w-46,54);c.setFont("Helvetica",8);c.drawString(46,38,"Website design and care for local & independent businesses");c.drawRightString(w-46,38,f"{d.page} / 4")
  c.bookmarkPage(f"p{d.page}");c.addOutlineEntry(f"Page {d.page}",f"p{d.page}",0)
 path=Path("blog")/(stem+".pdf");doc=SimpleDocTemplate(str(path),pagesize=(595.276,841.89),leftMargin=46,rightMargin=46,topMargin=100,bottomMargin=68,title=title,author="JW Growth & Design")
 doc.build(story,onFirstPage=header,onLaterPages=header)
 pdf=PdfReader(path);assert len(pdf.pages)==4,(source,len(pdf.pages));full=normal(" ".join(p.extract_text() for p in pdf.pages))
 for _,heading,body in numbered:assert normal(heading) in full and normal(body) in full
 assert all(len(page.images)==1 for page in pdf.pages)
 links=[a.get_object().get("/A",{}).get("/URI") for p in pdf.pages for a in p.get("/Annots",[])];assert url in links and all(ref in links for ref in refs)
 records.append((issue,title,path.name,deck))
assert len(records)==5 and len({r[0] for r in records})==5
if "--pdf-only" not in sys.argv:
 path=Path("blog.html");html=path.read_text();blob=b"blob "+str(len(html.encode())).encode()+b"\0"+html.encode()
 assert hashlib.sha1(blob).hexdigest()=="2f582fd9792aeb2f29bde47862c70baadbf02fc0","Blog changed: review before replacing cards"
 cards="\n".join('<article class="blog-card"><span class="blog-state">Issue '+f'{i:02d}'+' &middot; Available PDF</span><h2>'+escape(t)+'</h2><p>'+escape(d)+'</p><p>4 pages &middot; Action plan, worksheet and research links</p><a class="btn" href="blog/'+f+'?v=20261025-logo" target="_blank" rel="noopener noreferrer" aria-label="Read '+escape(t,quote=True)+' (PDF, opens in a new tab)">Read the guide &rarr;</a></article>' for i,t,f,d in sorted(records))
 html,count=re.subn(r'(<div class="blog-grid">).*?(</div>\s*</div>\s*</section>)',lambda m:m[1]+cards+m[2],html,count=1,flags=re.S);assert count==1
 html=html.replace("Open the published PDF guides below. Upcoming issues are clearly marked and have no broken download links.","Five practical PDF guides, each with an action plan, worksheet and research links. PDFs open in a new tab.")
 assert html.count('class="blog-card"')==5 and "Coming soon" not in html
 path.write_text(html)
