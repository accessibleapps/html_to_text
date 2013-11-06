from StringIO import StringIO
from logging import getLogger
logger = getLogger('html_to_text')

import lxml
import lxml.etree
import lxml.html
import urllib
import posixpath
import re
_collect_string_content = lxml.etree.XPath("string()")
HR_TEXT = "\n"+('-'*80)

class LXMLParser(object):
 def __init__(self, item):
  self.parse_tag(item)

 def parse_tag(self, item):
  if item.tag != lxml.etree.Comment:
   self.handle_starttag(item.tag, item.attrib)
   if item.text is not None:
    self.handle_data(item.text, item.tag)
   for tag in item:
    self.parse_tag(tag)
   self.handle_endtag(item.tag, item)
  if item.tail:
   self.handle_data(item.tail, None)

class HTMLParser(LXMLParser):
 _heading_tags = "h1 h2 h3 h4 h5 h6".split(' ')
 _pre_tags = ('pre', 'code')
 _ignored = ['script', 'style', 'title']
 whitespace_re = re.compile(r'\s+')
 _block = ('p', 'div', 'center', 'blockquote')
 heading_levels = {"h1": 1, "h2": 2, "h3": 3,
"h4": 4, "h5": 5, "h6": 6}

 def __init__(self, item, node_parsed_callback=None, startpos=0, file=""):
  self.node_parsed_callback = node_parsed_callback
  self.startpos = startpos
  self.file = file
  self.output = StringIO()
  self.add = ""
  self.initial_space = False
  self.ignoring = False
  self.in_pre = False
  self.last_data = ""
  self.out = ['']
  self.starting = True #Haven't written anything yet
  self.final_space = False
  self.heading_stack = []
  self.last_page = None
  LXMLParser.__init__(self, item)

 def handle_starttag(self, tag, attrs):
  if self.ignoring:
   return
  if tag in self._block:
   self.add = "\n\n"
  elif tag in self._ignored or attrs.get('class', None) == 'pagenum':
   self.ignoring = True
  elif tag in self._heading_tags:
   self.add = '\n\n'
   level = self.heading_levels[tag]
   start = self.output.tell()+self.startpos+(len(self.add) if not self.starting else 0)+(1 if self.final_space else 0)
   if self.node_parsed_callback:
    self.heading_stack.append((level, start, None))
  if tag in self._pre_tags:
   self.add = "\n"
   self.in_pre = True
  if tag == 'a' and 'href' in attrs:
   self.link_start = self.output.tell()+self.startpos+(len(self.add) if not self.starting else 0)+(1 if self.final_space else 0)
  if 'id' in attrs and self.node_parsed_callback:
   self.node_parsed_callback(None, 'id', self.file+"#"+attrs['id'], start=self.output.tell()+self.startpos+len(self.add))

 def handle_endtag(self, tag, item):
  if 'class' in item.attrib and item.attrib['class'] == 'pagenum':
   if self.last_page is not None:
    self.last_page['end'] = self.output.tell()+self.startpos
   if self.node_parsed_callback:
    self.last_page = self.node_parsed_callback(None, 'page', item.attrib['id'], start=self.output.tell()+self.startpos, pagenum=parse_pagenum(item.attrib['id']))
  if tag in self._ignored or item.attrib.get('class', None) == 'pagenum':
   self.ignoring = False
   return
  if tag in self._ignored:
   self.ignoring = False
   return
  if tag in self._block:
   self.add = "\n\n"
  elif tag == 'br':
   self.write_data('\n')
  elif tag in self._heading_tags:
   self.add = '\n\n'
   if self.node_parsed_callback:
    self.add_heading_node(tag)
  elif tag in self._pre_tags:
   self.in_pre = False
  elif tag == 'a' and 'href' in item.attrib and self.node_parsed_callback:
   self.add_link(item)
  elif tag == 'hr':
   self.output.write(HR_TEXT)
  self.last_start = tag

 def handle_data(self, data, start_tag):
  if self.ignoring:
   return
  if self.in_pre:
   if self.add:
    self.write_data(self.add)
    self.add = ""
   self.write_data(data)
   return
  data = self.whitespace_re.sub(' ', data)
  #The newline after <br> will turn into space above. Also,
  #<span>a</span> <span>b</span> will return a space after a. We want to keep it
  if data[0] == ' ':
   self.initial_space = True
   data = data[1:]
  if not data:
   return
  if not self.add and self.final_space:
   self.write_data(' ')
   self.final_space = False
  if data and data[-1] == ' ':
   self.final_space = True
   data = data[:-1]
  if self.starting:
   self.initial_space = False
   self.add = ""
  if self.add:
   self.write_data(self.add)
   self.add = ''
  if self.initial_space and not self.last_newline:
   self.write_data(' ')
  self.write_data(data)
  self.add = ""
  self.initial_space = False

 def write_data(self, data):
  self.output.write(data)
  self.last_newline = data[-1] == '\n'
  self.last_data = data
  self.starting = False

 def add_heading_node(self, item):
  """Adds a heading to the list of nodes.
  We can't have an end heading without a start heading."""
  (level, start, node_id) = self.heading_stack.pop()
  end = self.output.tell()+self.startpos
  while self.need_heading_pop(level):
   self.heading_stack.pop()
  #The last element of the stack is our parent. If it's empty, we have no parent.
  parent = None
  if len(self.heading_stack):
   parent = self.heading_stack[-1][2]
  #parent should be set, create the heading. We need to put it back on the stack for the next heading to grab
  #its parent if needed.
  name = None #self.output.getvalue()[start:end+1]
  id = self.node_parsed_callback(parent, 'heading', name, start=start, end=end, tag=item, level=item[-1])['id']
  self.heading_stack.append((level, start, id))

 def need_heading_pop(self, level):
  if len(self.heading_stack) == 0:
   return False #nothing to pop
  prev_level = self.heading_stack[-1][0]
  if level <= prev_level:
   return True
 def add_link(self, item):
  text = _collect_string_content(item)
  #Is this an internal link?
  href = item.attrib['href']
  if '://' not in href:
   href = urllib.unquote(item.attrib['href'])
   href = posixpath.normpath(posixpath.join(posixpath.dirname(self.file), href))
  self.node_parsed_callback(None, 'link', text, start=self.link_start, end=self.output.tell()+self.startpos, href=href)

def html_to_text(item, node_parsed_callback=None, startpos=0, file=""):
 if isinstance(item, basestring):
  item = tree_from_string(item)
 lxml.html.xhtml_to_html(item)
 parser = HTMLParser(item, node_parsed_callback, startpos, file)
 text = parser.output.getvalue()
 if parser.last_page is not None:
  parser.last_page['end'] = parser.output.tell()
 return text

pagenum_re = re.compile(r'(\d+)$')
def parse_pagenum(num):
 r = pagenum_re.search(num)
 if r:
  return str(int(r.group(1)))
 elif num.startswith('p'):
  return num[1:].lower()
 else:
  logger.warn("unable to parse page %r" % num)
  return None

def tree_from_string(html):
 try:
  return lxml.etree.fromstring(html)
 except lxml.etree.XMLSyntaxError:
  pass
 return lxml.html.fromstring(html)
