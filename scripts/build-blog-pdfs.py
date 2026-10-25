from pathlib import Path
import re,hashlib
from math import sin,cos,atan2
from html import escape as he
from xml.sax.saxutils import escape
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
W,H=595.276,841.89;M=42;CW=W-2*M
INK='#252b33';BLUE='#176b96';NAVY='#173b56';MUTED='#526171';PALE='#e8f0f6';LINE='#d3dfe8'
logo=Image.open('.build/jw-logo.png').convert('RGB');LOGO=ImageReader(logo)
styles={
'body':ParagraphStyle('body',fontName='Helvetica',fontSize=10.5,leading=15.3,textColor=colors.HexColor(INK)),
'fine':ParagraphStyle('fine',fontName='Helvetica',fontSize=8.7,leading=12.7,textColor=colors.HexColor(MUTED)),
'lead':ParagraphStyle('lead',fontName='Helvetica',fontSize=12,leading=17.4,textColor=colors.HexColor(MUTED)),
'hero':ParagraphStyle('hero',fontName='Helvetica-Bold',fontSize=28.5,leading=32.5,textColor=colors.HexColor(INK)),
'h2':ParagraphStyle('h2',fontName='Helvetica-Bold',fontSize=21,leading=26,textColor=colors.HexColor(INK)),
'h3':ParagraphStyle('h3',fontName='Helvetica-Bold',fontSize=12.9,leading=17,textColor=colors.HexColor(NAVY)),
'label':ParagraphStyle('label',fontName='Helvetica-Bold',fontSize=8.4,leading=11.5,textColor=colors.HexColor(BLUE)),
'white':ParagraphStyle('white',fontName='Helvetica',fontSize=11,leading=15.7,textColor=colors.white),
'whitehead':ParagraphStyle('whitehead',fontName='Helvetica-Bold',fontSize=18,leading=22,textColor=colors.white)}
features={1:('DIAGNOSE / PRIORITISE / IMPROVE','Read the warning signs','Make the journey work','Investigate first. Redesign with a reason.'),2:('PURPOSE / VALUE / DIRECTION','Build a useful foundation','Connect attention to action','Start with a customer task, not a page count.'),3:('ALIGN / SIMPLIFY / MAINTAIN','Create clarity across channels','Repair the hand-offs','One evidenced problem. One accountable next step.'),4:('ACCURACY / RELEVANCE / DISCOVERY','Get the foundations right','Build useful local signals','Genuine coverage. Helpful content. No shortcuts.'),5:('CLARITY / EVIDENCE / CONFIDENCE','Make the first screen useful','Support confidence with substance','A confident design needs credible information.')}
firstmoves={1:['Check a key page on a phone before changing its design.','Rewrite one vague headline using your real service and audience.','Complete the same task on mobile and desktop.','Remove one unsupported claim or dummy contact detail.','Test delivery and confirmation, not just the submit button.'],2:['Record who controls your domain and account access.','Answer the buying question you hear most often.','Choose one genuine piece of work that backs up a claim.','Give one important service its own useful explanation.','Explain whether the next step is a request or a booking.','Choose one meaningful action to review against business records.'],3:['Create one accurate master record of your business details.','Organise the first choices around customer needs.','Give every important account and update a named owner.','Follow an enquiry through to its confirmation and reply.','Answer a common question about suitability or process.','Choose a useful outcome before opening an analytics report.'],4:['Review your profile categories, hours and genuine contact details.','Correct the important places where business information differs.','Improve one service page before adding more location pages.','Check that an important page can be reached through normal links.','Use genuine work and honest customer feedback.','Review useful enquiries alongside search information.'],5:['Replace a slogan with a clear explanation of the service.','Check headings, contrast, labels and keyboard focus.','Choose proof that a visitor can genuinely evaluate.','Explain what will happen after an enquiry.','Complete the journey and check the confirmation.']}
icons={1:['speed','search','screen','shield','message'],2:['link','message','shield','search','screen','message'],3:['pin','screen','link','message','search','message'],4:['pin','link','screen','search','shield','message'],5:['screen','search','shield','message','link']}
stems={1:'5-signs-your-website-is-costing-you-customers',2:'why-your-website-matters-six-reasons',3:'common-online-challenges-local-businesses-consultants',4:'getting-found-local-search-starter-guide',5:'first-impressions-trust-website-design'}
def col(c,v):c.setFillColor(colors.HexColor(v))
def rect(c,x,y,w,h,fill=PALE,r=10,stroke=None):
 col(c,fill);c.setStrokeColor(colors.HexColor(stroke or fill));c.roundRect(x,y,w,h,r,fill=1,stroke=bool(stroke))
def text(c,t,x,y,size=9,color=MUTED,font='Helvetica'):
 c.setFont(font,size);col(c,color);c.drawString(x,y,t)
def measure(t,w,sty='body',raw=False):
 q=Paragraph(t if raw else escape(t),styles[sty]);return q.wrap(w,H)[1]
def p(c,t,x,y,w,sty='body',raw=False):
 q=Paragraph(t if raw else escape(t),styles[sty]);_,h=q.wrap(w,H);assert y-h>62,(t[:50],y-h);q.drawOn(c,x,y-h);return y-h
def header(c,a,n,tag):
 col(c,'#ffffff');c.rect(0,0,W,H,fill=1,stroke=0);col(c,BLUE);c.rect(0,H-6,W,6,fill=1,stroke=0)
 lw=238;lh=lw*logo.height/logo.width;assert lh<62;c.drawImage(LOGO,M,H-18-lh,lw,lh,mask='auto')
 text(c,f'JOURNAL / {a["issue"]:02d}',W-M-82,H-37,8.3,BLUE,'Helvetica-Bold');text(c,'LOCAL BUSINESS EDITION',W-M-126,H-52,7.2)
 c.setStrokeColor(colors.HexColor(LINE));c.line(M,52,W-M,52);text(c,'jwgrowthanddesign.com',M,34,8,BLUE);c.linkURL('https://jwgrowthanddesign.com/',(M,25,M+130,46),relative=0);text(c,f'{n:02d} / 05',W-M-38,34,8)
 c.bookmarkPage(f'p{n}');c.addOutlineEntry(tag,f'p{n}',0);return H-97
def arrow(c,x1,y1,x2,y2,color=BLUE):
 c.setStrokeColor(colors.HexColor(color));c.setLineWidth(1.2);c.line(x1,y1,x2,y2);ang=atan2(y2-y1,x2-x1)
 for delta in [-.55,.55]:c.line(x2,y2,x2-5*cos(ang+delta),y2-5*sin(ang+delta))
def icon(c,x,y,kind,color=BLUE,s=24):
 c.saveState();c.translate(x,y);c.scale(s/24,s/24);c.setStrokeColor(colors.HexColor(color));c.setLineWidth(1.35)
 if kind=='screen':
  c.roundRect(2,6,20,15,2,fill=0,stroke=1);c.line(9,2,15,2);c.line(12,2,12,6);c.line(5,16,19,16);c.line(5,12,14,12)
 elif kind=='pin':
  c.circle(12,15,7,fill=0,stroke=1);c.line(6,11,12,2);c.line(18,11,12,2);c.circle(12,15,2,fill=0,stroke=1)
 elif kind=='shield':
  path=c.beginPath();path.moveTo(12,22);path.lineTo(21,18);path.lineTo(20,10);path.curveTo(19,6,15,3,12,1);path.curveTo(9,3,5,6,4,10);path.lineTo(3,18);path.close();c.drawPath(path,stroke=1,fill=0);c.line(7,12,11,8);c.line(11,8,17,16)
 elif kind=='message':
  c.roundRect(2,6,20,15,3,fill=0,stroke=1);c.line(6,6,5,2);c.line(5,2,11,6);c.line(6,16,18,16);c.line(6,12,15,12)
 elif kind=='search':
  c.circle(10,14,7,fill=0,stroke=1);c.line(15,8,22,1);c.line(6,14,14,14)
 elif kind=='speed':
  c.arc(2,2,22,22,0,180);c.line(12,12,18,18);c.circle(12,12,1.5,fill=0,stroke=1);c.line(4,10,20,10)
 elif kind=='link':
  c.roundRect(1,6,14,10,4,fill=0,stroke=1);c.roundRect(9,9,14,10,4,fill=0,stroke=1)
 else:
  c.roundRect(3,2,18,20,2,fill=0,stroke=1);c.line(7,16,17,16);c.line(7,11,17,11);c.line(7,6,13,6)
 c.restoreState()
def browser(c,x,y,w,h,good=True,label='YOUR BUSINESS'):
 rect(c,x+3,y-3,w,h,'#dbe5ec',8);rect(c,x,y,w,h,'#ffffff',8,LINE);rect(c,x,y+h-22,w,22,'#edf3f7',8)
 for j in range(3):col(c,['#9db6c7','#bdd0dc','#d6e1e9'][j]);c.circle(x+12+j*9,y+h-11,2,stroke=0,fill=1)
 text(c,label,x+12,y+h-42,8.3,NAVY,'Helvetica-Bold')
 if good:
  text(c,'Clear services. A clear next step.',x+12,y+h-58,7.8,INK);rect(c,x+12,y+h-73,w-24,6,'#e8f0f6',2);rect(c,x+12,y+12,min(113,w-24),18,BLUE,4);text(c,'Make an enquiry',x+20,y+18,7.8,'#ffffff','Helvetica-Bold')
 else:
  for j,length in enumerate([.77,.49,.68]):rect(c,x+12,y+h-56-j*10,(w-24)*length,4,'#c7d5df',1)
  for j in range(3):rect(c,x+12+j*(w-24)/3,y+12,(w-34)/3,14,'#e8edf1',3)
def hero_art(c,a,x,y,w,h):
 issue=a['issue'];rect(c,x,y,w,h,'#edf3f7',14);c.setStrokeColor(colors.HexColor('#dce7ef'));c.setLineWidth(.5)
 for gx in range(20,int(w),24):c.line(x+gx,y+10,x+gx,y+h-10)
 for gy in range(16,int(h),24):c.line(x+10,y+gy,x+w-10,y+gy)
 if issue==1:
  browser(c,x+25,y+23,238,h-45,True,'THE CUSTOMER JOURNEY')
  for i,(ico,label) in enumerate([('speed','Loading'),('shield','Confidence'),('message','Enquiry')]):
   yy=y+h-39-i*39;rect(c,x+w-166,yy-10,145,32,'#ffffff',7,LINE);icon(c,x+w-157,yy-5,ico,s=19);text(c,label,x+w-130,yy+2,8.5,NAVY,'Helvetica-Bold')
  arrow(c,x+276,y+h/2,x+w-176,y+h/2)
 elif issue==2:
  cx=x+w/2;cy=y+h/2;rect(c,cx-53,cy-29,106,58,NAVY,11);text(c,'YOUR WEBSITE',cx-41,cy-3,10,'#ffffff','Helvetica-Bold')
  for i,label in enumerate(['Control','Clarity','Trust','Discovery','Access','Learning']):
   right=i>=3;yy=y+h-43-(i%3)*42;xx=x+w-133 if right else x+17;rect(c,xx,yy-8,116,30,'#ffffff',6,LINE);text(c,label,xx+12,yy+3,9,BLUE,'Helvetica-Bold');arrow(c,cx+(55 if right else -55),cy,xx-5 if right else xx+121,yy+7)
 elif issue==3:
  labels=[('pin','LISTINGS','Accurate details'),('screen','WEBSITE','Clear offer'),('link','BOOKING','Keep context'),('message','REPLY','Close the loop')];bw=(w-62)/4
  for i,(ico,title,subtitle) in enumerate(labels):
   xx=x+16+i*(bw+10);rect(c,xx,y+37,bw,94,'#ffffff',8,LINE);icon(c,xx+12,y+91,ico,s=23);text(c,title,xx+12,y+74,8.2,BLUE,'Helvetica-Bold');text(c,subtitle,xx+12,y+57,7.3)
   if i<3:arrow(c,xx+bw+1,y+84,xx+bw+9,y+84)
 elif issue==4:
  rect(c,x+15,y+15,w*.54,h-30,'#e1edf3',10);c.setStrokeColor(colors.white);c.setLineWidth(7)
  for j in range(3):c.line(x+25,y+37+j*34,x+w*.53,y+66+j*20)
  c.line(x+80,y+22,x+136,y+h-22);c.line(x+206,y+23,x+171,y+h-22)
  for xx,yy,ss in [(92,76,30),(184,116,23),(221,49,20)]:rect(c,x+xx-16,y+yy-16,32,35,'#ffffff',7);icon(c,x+xx-12,y+yy-10,'pin',s=ss)
  for j,label in enumerate(['Relevant services','Genuine coverage','Accurate details']):
   xx=x+w*.59;yy=y+h-43-j*39;rect(c,xx,yy-9,w*.36,31,'#ffffff',7,LINE);text(c,label,xx+10,yy+3,8.2,NAVY,'Helvetica-Bold')
 elif issue==5:
  ww=(w-60)/2;browser(c,x+18,y+22,ww,h-48,False,'UNCLEAR PRESENTATION');browser(c,x+w-ww-18,y+22,ww,h-48,True,'A CLEARER NEXT STEP');arrow(c,x+w/2-8,y+h/2,x+w/2+8,y+h/2)
def callout(c,y,title,body,fill=PALE,dark=False):
 sty='white' if dark else 'body';hs=measure(title,CW-34,'whitehead' if dark else 'h3');bh=measure(body,CW-34,sty);height=hs+bh+39;rect(c,M,y-height,CW,height,fill,12)
 yy=p(c,title,M+17,y-16,CW-34,'whitehead' if dark else 'h3');yy=p(c,body,M+17,yy-8,CW-34,sty);assert yy>=y-height+8;return y-height
def card(c,y,num,heading,body,move,ico):
 tx=M+67;tw=CW-84;hh=measure(heading,tw,'h3');bh=measure(body,tw);mh=measure('FIRST MOVE  '+move,tw,'fine');height=16+hh+7+bh+12+mh+15
 rect(c,M,y-height,CW,height,'#f5f8fa',12,LINE);rect(c,M+14,y-50,36,36,'#e2edf4',8);icon(c,M+20,y-44,ico,s=24)
 yy=p(c,heading,tx,y-15,tw,'h3');yy=p(c,body,tx,yy-7,tw);c.setStrokeColor(colors.HexColor(LINE));c.line(tx,yy-6,M+CW-16,yy-6)
 yy=p(c,'<font color="'+BLUE+'"><b>FIRST MOVE</b></font>  '+escape(move),tx,yy-12,tw,'fine',True);text(c,num,M+24,y-height+13,8,BLUE,'Helvetica-Bold');assert yy>=y-height+8;return y-height
def mini_summary(c,a,y):
 if a['issue']==1:
  for i,(label,value) in enumerate([('LCP','<= 2.5s'),('INP','<= 200ms'),('CLS','<= 0.1')]):
   xx=M+i*(CW+12)/3;ww=(CW-24)/3;rect(c,xx,y-66,ww,66,NAVY,9);text(c,label,xx+13,y-20,8.3,'#c9dce9','Helvetica-Bold');text(c,value,xx+13,y-46,19,'#ffffff','Helvetica-Bold')
  p(c,'Good Core Web Vitals targets at the 75th percentile of real visits. Not a prediction of sales. [1]',M,y-75,CW,'fine')
 else:
  captions={2:['UNDERSTAND','EVALUATE','TAKE ACTION'],3:['CONSISTENT DETAILS','CLEAR OWNERSHIP','WORKING HAND-OFFS'],4:['RELEVANCE','DISTANCE','PROMINENCE'],5:['IS THIS FOR ME?','CAN I BELIEVE IT?','WHAT HAPPENS NEXT?']}[a['issue']]
  for i,label in enumerate(captions):
   xx=M+i*(CW+12)/3;ww=(CW-24)/3;rect(c,xx,y-44,ww,44,PALE,8);p(c,label,xx+10,y-15,ww-20,'label')
articles=[]
for source in sorted(Path('blog/sources').glob('*.md')):
 value=source.read_text().strip();sections=dict(re.findall(r'^## ([^\n]+)\n(.*?)(?=^## |\Z)',value,re.M|re.S));issue=int(re.search(r'Issue (\d+)',value).group(1))
 numbered=[(k[:2],k[3:],v.strip()) for k,v in sections.items() if re.match(r'^\d{2} ',k)];plan=sections['Action plan'].strip();ex=re.search(r'\n\n(Illustrative.*)',plan,re.S);example=ex.group(1).strip() if ex else '';plan=plan[:ex.start()] if ex else plan
 articles.append({'issue':issue,'title':re.search(r'^# ([^\n]+)',value).group(1),'deck':value.split('\n\n')[2],'sections':sections,'numbered':numbered,'steps':re.findall(r'^### ([^\n]+)\n(.*?)(?=^### |\Z)',plan,re.M|re.S),'example':example})
assert len(articles)==5 and {a['issue'] for a in articles}=={1,2,3,4,5}
records=[]
for a in sorted(articles,key=lambda a:a['issue']):
 issue=a['issue'];dest=Path('blog')/(stems[issue]+'.pdf');c=canvas.Canvas(str(dest),pagesize=(W,H),pageCompression=1,invariant=1);c.setTitle(a['title']+' | Creative Edition');c.setAuthor('JW Growth & Design');c.setSubject(a['deck'])
 y=header(c,a,1,'Start here');text(c,features[issue][0],M,y,8.5,BLUE,'Helvetica-Bold');y-=23;y=p(c,a['title'],M,y,CW,'hero')-13;y=p(c,a['deck'],M,y,CW,'lead')-17
 hero_h=156;hero_art(c,a,M,y-hero_h,CW,hero_h);y-=hero_h+13;y=p(c,'ILLUSTRATIVE DESIGN / NOT CLIENT RESULTS OR PERFORMANCE DATA',M,y,CW,'fine')-12
 y=callout(c,y,'What you will take away',a['sections']['Reader outcome'].strip(),NAVY,True)-17
 quick=a['sections']['Start here'].strip();items=[q[2:] for q in quick.splitlines() if q.startswith('- ')];principle=' '.join(q for q in quick.splitlines() if q and not q.startswith('- '));assert len(items)==3
 y=p(c,'Start here',M,y,CW,'h3')-10;qh=max(measure(q,(CW-28)/3-24,'fine') for q in items)+43
 for i,item in enumerate(items):
  xx=M+i*(CW+14)/3;ww=(CW-28)/3;rect(c,xx,y-qh,ww,qh,'#f4f7fa',8);text(c,f'0{i+1}',xx+12,y-18,10,BLUE,'Helvetica-Bold');p(c,item,xx+12,y-28,ww-24,'fine')
 y-=qh+12;y=p(c,principle,M,y,CW,'fine');assert y>65;c.showPage()
 y=header(c,a,2,'Understand');text(c,'THE PRACTICAL CHECKS / PART 1',M,y,8.4,BLUE,'Helvetica-Bold');y-=19;y=p(c,features[issue][1],M,y,CW,'h2')-18
 for j,(num,heading,body) in enumerate(a['numbered'][:3]):y=card(c,y,num,heading,body,firstmoves[issue][j],icons[issue][j])-13
 if y>169:mini_summary(c,a,y-4)
 assert y>66;c.showPage()
 y=header(c,a,3,'Apply');text(c,'THE PRACTICAL CHECKS / PART 2',M,y,8.4,BLUE,'Helvetica-Bold');y-=19;y=p(c,features[issue][2],M,y,CW,'h2')-18
 for j,(num,heading,body) in enumerate(a['numbered'][3:],3):y=card(c,y,num,heading,body,firstmoves[issue][j],icons[issue][j])-13
 if a['example']:
  eh=measure(a['example'],CW-34,'body')+56
  if y-eh<67:
   eh=measure(a['example'],CW-34,'fine')+56;rect(c,M,y-eh,CW,eh,PALE,10);yy=p(c,'In practice / illustrative example',M+17,y-15,CW-34,'h3');yy=p(c,a['example'],M+17,yy-8,CW-34,'fine');y-=eh
  else:y=callout(c,y,'In practice / illustrative example',a['example'])
 if issue in (1,5) and y>265:
  y-=17;p(c,'A CHANGE TO TEST / NOT A MEASURED RESULT',M,y,CW,'label');y-=20
  labels=['Vague button','Book a haircut','Completed bookings'] if issue==1 else ['Generic slogan','Clear local service','Request a quote'];ww=(CW-30)/3
  for k,label in enumerate(labels):
   xx=M+k*(ww+15);rect(c,xx,y-46,ww,46,PALE,8);p(c,label,xx+12,y-15,ww-24,'fine')
   if k<2:arrow(c,xx+ww+2,y-23,xx+ww+13,y-23)
  y-=46
 assert y>65;c.showPage()
 y=header(c,a,4,'Action plan');text(c,'A PLAN YOU CAN USE',M,y,8.4,BLUE,'Helvetica-Bold');y-=19;y=p(c,'Turn insight into a next step',M,y,CW,'h2')-16
 for j,(heading,body) in enumerate(a['steps']):
  bh=measure(body.strip(),CW-73);hh=measure(heading,CW-73,'h3');height=hh+bh+33;rect(c,M+42,y-height,CW-42,height,'#f4f7fa',9);rect(c,M,y-30,30,30,NAVY,7);text(c,str(j+1),M+11,y-20,11,'#ffffff','Helvetica-Bold')
  if j<2:c.setStrokeColor(colors.HexColor(LINE));c.line(M+15,y-35,M+15,y-height-8)
  yy=p(c,heading,M+56,y-13,CW-73,'h3');p(c,body.strip(),M+56,yy-7,CW-73);y-=height+11
 y-=5;y=p(c,'Your working brief',M,y,CW,'h3')-12;labels=[q[2:] for q in a['sections']['Worksheet'].strip().splitlines() if q.startswith('- ')];assert len(labels)==4;cellh=85;ww=(CW-14)/2
 for j,label in enumerate(labels):
  xx=M+(j%2)*(ww+14);top=y-(j//2)*(cellh+12);rect(c,xx,top-cellh,ww,cellh,'#ffffff',9,LINE);p(c,label,xx+13,top-13,ww-26,'fine');c.setStrokeColor(colors.HexColor(LINE));c.line(xx+13,top-cellh+19,xx+ww-13,top-cellh+19)
 y-=2*cellh+12;assert y>65;c.showPage()
 y=header(c,a,5,'Next step and research');text(c,'KEEP THE NEXT STEP USEFUL',M,y,8.4,BLUE,'Helvetica-Bold');y-=19;y=p(c,features[issue][3],M,y,CW,'h2')-18
 nxt=a['sections']['Next step'].strip();url=re.search(r'https://\S+',nxt).group(0);copy=nxt.replace(url,'').strip();y=callout(c,y,'Talk through your website with Joseph',copy,NAVY,True)-12
 bh=38;rect(c,M,y-bh,245,bh,BLUE,7);text(c,'Start a conversation with Joseph  >',M+15,y-24,10,'#ffffff','Helvetica-Bold');c.linkURL(url,(M,y-bh,M+245,y),relative=0);y-=bh+21
 y=callout(c,y,'A useful decision, not a bigger to-do list','Choose one issue you can evidence. Agree the next action and who owns it. Review an outcome relevant to your business rather than treating a visual refresh as proof of better results.')-19;y=p(c,'Research notes and further reading',M,y,CW,'h3')-9;refs=[]
 for line in a['sections']['Sources'].strip().splitlines():
  m=re.match(r'\[(\d+)\] (.*?): (https://\S+)',line);assert m,line;num,label,link=m.groups();refs.append(link)
  y=p(c,f'<font color="{BLUE}"><b>[{num}]</b></font> <link href="{escape(link)}" color="{BLUE}">{escape(label)}</link>',M,y,CW,'fine',True)-2;y=p(c,f'<link href="{escape(link)}" color="{MUTED}">{escape(link)}</link>',M+19,y,CW-19,'fine',True)-8
 y-=2;y=p(c,'Research checked 25 October 2026. Examples and diagrams are illustrative, not client results. This guide is educational, not a full technical, accessibility or legal audit. Outcomes depend on the business, implementation and market.',M,y,CW,'fine');assert y>65;c.save()
 pdf=PdfReader(dest);assert len(pdf.pages)==5;full=' '.join(' '.join(page.extract_text().split()) for page in pdf.pages)
 for _,heading,body in a['numbered']:assert ' '.join(heading.split()) in full and ' '.join(body.split()) in full
 assert ' '.join(a['example'].split()) in full
 for heading,body in a['steps']:assert ' '.join(body.split()) in full
 assert all(len(page.images)==1 for page in pdf.pages)
 links=[x.get_object().get('/A',{}).get('/URI') for pg in pdf.pages for x in pg.get('/Annots',[])];assert url in links and all(ref in links for ref in refs)
 records.append((issue,a['title'],dest.name,a['deck'],hashlib.sha256(dest.read_bytes()).hexdigest()[:12]))
path=Path('blog.html');html=path.read_text();match=re.search(r'(<div class="blog-grid">).*?(</div>\s*</div>\s*</section>)',html,re.S);assert match
assert len(re.findall(r'<article\b',match[0]))==5
cards='\n'.join('<article class="blog-card"><span class="blog-state">Issue '+f'{i:02d}'+' &middot; Available PDF</span><h2>'+he(t)+'</h2><p>'+he(d)+'</p><p>5 pages &middot; Illustrated guide, action plan and worksheet</p><a class="btn" href="blog/'+f+'?v='+v+'" target="_blank" rel="noopener noreferrer" aria-label="Read '+he(t,quote=True)+' (PDF, opens in a new tab)">Read the guide &rarr;</a></article>' for i,t,f,d,v in sorted(records))
html=html[:match.start()]+match[1]+cards+match[2]+html[match.end():]
assert html.count('class="blog-card"')==5 and '4 pages &middot;' not in html and 'Coming soon' not in html
assert re.findall(r'Issue (\d{2}) &middot; Available PDF',html)==['01','02','03','04','05']
path.write_text(html)
