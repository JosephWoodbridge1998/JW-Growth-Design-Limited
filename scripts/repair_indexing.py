from pathlib import Path
from html.parser import HTMLParser
from html import escape
from urllib.parse import urlsplit,urljoin,urlunsplit
import re,xml.etree.ElementTree as ET
BASE='https://jwgrowthanddesign.com'
PAGES=['index.html','about.html','clients.html','contact-us.html','blog.html','why-jw-growth-design.html','services/website-design.html','services/Website-Growth.html','services/website-health-check.html','privacy.html']
def canonical(name):return BASE+('/' if name=='index.html' else '/'+name)
def direct(value,name):
 if not value or value.startswith(('#','mailto:','tel:','data:','javascript:')):return value
 u=urlsplit(urljoin(canonical(name),value))
 if u.hostname not in ('jwgrowthanddesign.com','www.jwgrowthanddesign.com') or u.scheme not in ('http','https'):return value
 path={'/index.html':'/','/work.html':'/clients.html'}.get(u.path,u.path or '/')
 if urlsplit(value).netloc:return urlunsplit(('https','jwgrowthanddesign.com',path,u.query,u.fragment))
 if path!=u.path:return urlunsplit(('','',path,u.query,u.fragment))
 return value
class Edit(HTMLParser):
 def __init__(self,text,name):
  super().__init__(convert_charrefs=False);self.text=text;self.name=name;self.ops=[];self.head=None;self.footer=None;self.has_privacy=False;self.offsets=[0]
  for m in re.finditer('\n',text):self.offsets.append(m.end())
 def pos(self):
  line,col=self.getpos();return self.offsets[line-1]+col
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs);raw=self.get_starttag_text();start=self.pos()
  if tag=='link' and 'canonical' in (attrs.get('rel') or '').lower().split():self.ops.append((start,start+len(raw),''));return
  key='href' if tag=='a' else 'content' if tag=='meta' and (attrs.get('property') or '').lower()=='og:url' else None
  if key:
   old=attrs.get(key) or '';new=direct(old,self.name) if tag=='a' else canonical(self.name)
   if tag=='a' and urlsplit(urljoin(canonical(self.name),old)).path=='/privacy.html':self.has_privacy=True
   if old!=new:
    pattern=r'(\s'+key+r'\s*=\s*)([\'\"])(.*?)\2'
    updated=re.sub(pattern,lambda m:m[1]+m[2]+escape(new,quote=True)+m[2],raw,count=1,flags=re.I|re.S)
    assert updated!=raw,(self.name,key);self.ops.append((start,start+len(raw),updated))
 def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs)
 def handle_endtag(self,tag):
  if tag=='head':self.head=self.pos()
  if tag=='footer':self.footer=self.pos()
def rewrite(text,name):
 e=Edit(text,name);e.feed(text);assert e.head is not None,name
 e.ops.append((e.head,e.head,'<link rel="canonical" href="'+canonical(name)+'">'))
 if e.footer is not None and not e.has_privacy:e.ops.append((e.footer,e.footer,'<p style="max-width:1180px;margin:14px auto 0;padding:0 24px;font-size:12px"><a href="/privacy.html" style="text-decoration:underline">Privacy &amp; cookies</a></p>'))
 for start,end,value in sorted(e.ops,key=lambda x:(x[0],x[1]),reverse=True):text=text[:start]+value+text[end:]
 return text
def enrich_blog():
 p=Path('blog.html');html=p.read_bytes().decode('utf-8')
 def enrich(m):
  article=m[0]
  if 'data-jw-guide-summary' in article:return article
  link=re.search(r'href="blog/([^"?]+)\.pdf(?:\?[^\"]*)?"',article)
  if not link:return article
  source=Path('blog/sources')/(link[1]+'.md');assert source.is_file(),source;text=source.read_text()
  result=re.search(r'^## Reader outcome\s*\n(.*?)(?=^## |\Z)',text,re.M|re.S);assert result,source
  outcome=' '.join(result[1].split());start=re.search(r'^## Start here\s*\n(.*?)(?=^## |\Z)',text,re.M|re.S);assert start,source
  checks=re.findall(r'^- (.+)$',start[1],re.M);assert len(checks)==3,source
  extra='<details data-jw-guide-summary style="border-top:1px solid #d3dfe8;padding-top:12px;font-size:12px;line-height:1.7"><summary style="cursor:pointer;color:#176b96;font-weight:700">What this guide helps you do</summary><p>'+escape(outcome)+'</p><ul style="padding-left:18px">'+''.join('<li>'+escape(x)+'</li>' for x in checks)+'</ul></details>'
  return article.replace('<a class="btn"',extra+'<a class="btn"',1)
 html=re.sub(r'<article\b[^>]*>.*?</article>',enrich,html,flags=re.S);p.write_text(html,encoding='utf-8')
def run():
 assert Path('CNAME').read_text().strip()=='jwgrowthanddesign.com','Domain changed; review required'
 assert all(Path(p).is_file() for p in PAGES),'Expected content page missing'
 for name in PAGES:
  path=Path(name);path.write_text(rewrite(path.read_bytes().decode('utf-8'),name),encoding='utf-8')
 shared=Path('jw-site-refinements.js');text=shared.read_text();shared.write_text(text.replace('/index.html#services','/#services'))
 enrich_blog()
 builder=Path('scripts/build-blog-pdfs.py');text=builder.read_text();hook='from repair_indexing import enrich_blog\nenrich_blog()'
 if hook not in text:
  assert 'path.write_text(html)' in text,'PDF publisher changed; review required'
  builder.write_text(text.rstrip()+'\n\n'+hook+'\n')
 urls=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
 for name in PAGES:ET.SubElement(ET.SubElement(urls,'url'),'loc').text=canonical(name)
 ET.indent(urls);Path('sitemap.xml').write_bytes(ET.tostring(urls,encoding='utf-8',xml_declaration=True))
 robots=Path('robots.txt');text=robots.read_text() if robots.exists() else 'User-agent: *\nAllow: /\n'
 text=re.sub(r'^Sitemap:.*\n?','',text,flags=re.M|re.I).rstrip()+'\nSitemap: '+BASE+'/sitemap.xml\n';robots.write_text(text)
 for name in PAGES:
  text=Path(name).read_text();links=re.findall(r'<link\s+rel="canonical"\s+href="([^"]+)"',text);assert links==[canonical(name)],(name,links)
 blog=Path('blog.html').read_text();assert blog.count('data-jw-guide-summary')==5 and blog.count('class="blog-card"')==5
 assert '/work.html' not in Path('sitemap.xml').read_text()
 print('Canonical, direct-link, privacy-link, blog-summary and sitemap checks passed.')
if __name__=='__main__':run()
