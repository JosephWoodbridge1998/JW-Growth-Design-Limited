from pathlib import Path
from html.parser import HTMLParser
import json
import re

ROOT = Path(__file__).resolve().parents[1]
EMAIL = 'info@jwgrowthanddesign.com'
RULES = (
    ('How can I help?', 'How can we help?'),
    ('What can I help with?', 'What can we help with?'),
    ('Tell me about your current website', 'Tell us about your current website'),
    ('Send Joseph a message', 'Send us a message'),
    ('send Joseph a message', 'send us a message'),
    ('Tell Joseph', 'Tell us'),
    ('tell Joseph', 'tell us'),
    ('you would like Joseph to review', 'you would like us to review'),
    ('Speak to Joseph', 'Speak to us'),
    ('speak to Joseph', 'speak to us'),
    ('Contact Joseph', 'Contact us'),
    ('contact Joseph', 'contact us'),
    ('Talk to Joseph', 'Talk to us'),
    ('talk to Joseph', 'talk to us'),
    ('Chat with Joseph', 'Chat with us'),
    ('chat with Joseph', 'chat with us'),
    ('Ask Joseph', 'Ask us'),
    ('ask Joseph', 'ask us'),
    ('Joseph will help', 'We will help'),
    ('Joseph can help', 'We can help'),
    ('Looked after afterwards.', 'Supported beyond it.'),
)

def emails(text):
    text = re.sub(r'(?i)(?<![\w.+-])josephwoodbridge85@gmail\.com\b', EMAIL, text)
    return re.sub(r'(?i)(?<![\w.+-])[a-z0-9._%+-]+@jwgrowthanddesign\.com\b', EMAIL, text)

def copy(text):
    for old, new in RULES:
        text = text.replace(old, new)
    return text

class CompanyHTML(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.offsets = [0] + [m.end() for m in re.finditer('\n', text)]
        self.stack = []
        self.edits = []
        self.pending = []
    def handle_starttag(self, tag, attrs):
        protected = any(flag for _, flag in self.stack)
        classes = dict(attrs).get('class', '') or ''
        protected = protected or tag in {'blockquote','q','script','style','code','pre'} or any(c.startswith('testimonial') or c in {'review','reviews','credits','byline','author'} for c in classes.split())
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.stack.append((tag, protected))
    def handle_startendtag(self, tag, attrs):
        pass
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
    def handle_data(self, data):
        if any(flag for _, flag in self.stack):
            return
        new = copy(data)
        if new != data:
            line, col = self.getpos()
            start = self.offsets[line-1] + col
            self.edits.append((start, start+len(data), new))
        if re.search(r'\bJoseph\b', new):
            self.pending.append(re.sub(r'\s+', ' ', new).strip()[:240])
    def result(self):
        result = self.text
        for start, end, new in reversed(self.edits):
            result = result[:start] + new + result[end:]
        return result

def transform(text, suffix):
    text = emails(text)
    if suffix == '.html':
        parser = CompanyHTML(text)
        parser.feed(text)
        return parser.result(), parser.pending
    updated = copy(text)
    pending = [line.strip()[:240] for line in updated.splitlines() if re.search(r'\bJoseph\b', line)]
    return updated, pending

def main():
    planned = {}
    pending = {}
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if path.is_symlink() or not path.is_file() or path.suffix not in {'.html','.js'}:
            continue
        if any(part.startswith('.') for part in rel.parts) or rel.parts[0] in {'showcases','node_modules','vendor','scripts'}:
            continue
        original = path.read_text(encoding='utf-8')
        updated, unresolved = transform(original, path.suffix)
        if updated != original:
            planned[path] = updated
        if unresolved:
            pending[rel.as_posix()] = unresolved
    premium = ROOT / 'services/premium-design.html'
    premium_text = planned.get(premium, premium.read_text(encoding='utf-8'))
    assert 'Built for launch.<br>Supported beyond it.' in premium_text, 'Premium heading not matched; no files written'
    assert 'Tell Joseph' not in premium_text, 'Premium company copy not matched; no files written'
    contact = ROOT / 'contact-us.html'
    contact_text = planned.get(contact, contact.read_text(encoding='utf-8'))
    assert 'mailto:'+EMAIL in contact_text, 'Contact email not matched; no files written'
    for path, updated in planned.items():
        path.write_text(updated, encoding='utf-8')
    report = {'contact_email': EMAIL, 'premium_heading':'Built for launch. Supported beyond it.', 'changed_files':[p.relative_to(ROOT).as_posix() for p in planned], 'unresolved_company_name_copy':pending, 'preserved':'Client quotes, review blocks, credits, showcase sites, technical account names and form delivery credentials.'}
    report_path = ROOT / '.github/company-contact-copy-audit.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
