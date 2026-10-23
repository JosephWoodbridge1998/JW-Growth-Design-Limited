from pathlib import Path
from html.parser import HTMLParser
import os
import re

root = Path(__file__).resolve().parents[1]
routes = [('About Us','/about.html'),('Services','/index.html#services'),('Clients','/clients.html'),('Why JW','/why-jw-growth-design.html'),('See Our Work','/work.html'),('Contact Us','/contact-us.html'),('Blog','/blog.html')]
required = ['index.html','about.html','clients.html','why-jw-growth-design.html','work.html','contact-us.html','blog.html']
if any(not (root/name).is_file() for name in required):
    raise SystemExit('Expected pages missing; no HTML changes made.')

class Ends(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.offsets = [0] + [m.end() for m in re.finditer('\n',text)]
        self.ends = {}
    def handle_endtag(self,tag):
        line,col = self.getpos()
        self.ends[tag] = self.offsets[line-1] + col

def closing(text, tag):
    parser = Ends(text)
    parser.feed(text)
    if tag not in parser.ends:
        raise ValueError('Missing real '+tag+' closing tag')
    return parser.ends[tag]

def transform(text, relative):
    if '<html' not in text.lower():
        raise ValueError('Invalid HTML: '+str(relative))
    name = relative.name
    nav = '<ul>' + ''.join('<li><a href="'+url+'"'+(' class="active"' if url.split('#')[0]=='/'+name else '')+'>'+label+'</a></li>' for label,url in routes) + '</ul>'
    text,count = re.subn(r'(<nav\b[^>]*\bid=["\']mainNav["\'][^>]*>).*?(</nav>)',lambda m:m[1]+nav+m[2],text,count=1,flags=re.I|re.S)
    if name in required and count != 1:
        raise ValueError('Expected one main navigation in '+str(relative))
    text = re.sub(r'(</nav>)\s*<li>\s*<a[^>]*>\s*Blog\s*</a>\s*</li>',r'\1',text,flags=re.I)
    text = re.sub(r'<link\b[^>]*href=["\'][^"\']*jw-light-theme\.css[^"\']*["\'][^>]*>\n?', '',text,flags=re.I)
    text = re.sub(r'<script\b[^>]*src=["\'][^"\']*(?:jw-site-refinements|jw-home-demos)\.js[^"\']*["\'][^>]*>\s*</script>\n?', '',text,flags=re.I)
    base = Path(os.path.relpath(root, (root/relative).parent)).as_posix()
    prefix = '' if base=='.' else base+'/'
    i = closing(text,'head')
    text = text[:i]+'<link rel="stylesheet" href="'+prefix+'jw-light-theme.css?v=20261023-site">\n'+text[i:]
    scripts = '<script defer src="'+prefix+'jw-site-refinements.js?v=20261023-site"></script>\n'
    if relative.as_posix()=='index.html':
        scripts += '<script defer src="jw-home-demos.js?v=20261023-site"></script>\n'
    i = closing(text,'body')
    text = text[:i]+scripts+text[i:]
    text = re.sub(r'rgba\(\s*0\s*,\s*234\s*,\s*255\s*,', 'rgba(23,107,150,',text,flags=re.I)
    text = re.sub(r'rgba\(\s*79\s*,\s*195\s*,\s*255\s*,', 'rgba(57,125,162,',text,flags=re.I)
    text = re.sub('#00eaff','#176b96',text,flags=re.I)
    text = re.sub('#4fc3ff','#397da2',text,flags=re.I)
    return text

changes = {}
for path in sorted(root.rglob('*.html')):
    rel = path.relative_to(root)
    if any(part.startswith('.') for part in rel.parts):
        continue
    changes[path] = transform(path.read_text(encoding='utf-8'),rel)
for path,text in changes.items():
    path.write_text(text,encoding='utf-8')
print('Refreshed navigation, theme links and scripts in '+str(len(changes))+' HTML files. Sinclair showcase scripts preserved.')
