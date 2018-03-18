import sys
import os
import json
import datetime
import uuid
import zipfile
import shutil
import codecs

if len(sys.argv) < 2:
    print('missing directory with chapter xhtml pages')
    sys.exit()

dir = sys.argv[1]
settings_path = sys.argv[2] if 2 < len(sys.argv) else None
settings = {}

#create dictionary with chapter name and file name if its not given
if not settings_path:
    now = datetime.datetime.now().isoformat('T')
    settings['uuid'] = str(uuid.uuid4())
    settings['date'] = now
    settings['modified_date'] = now
    settings['title'] = ''
    settings['language'] = 'en-US'
    settings['author'] = ''
    settings['chapters'] = {}

    for file in sorted(os.listdir(dir)):
        name, ext = os.path.splitext(file)
        settings['chapters'][name] = file
    with open('settings.json', 'w') as s:
        json.dump(settings, s, indent=4)
    print('created settings.json, give as second argument to create ebook')
    sys.exit()

with open(settings_path, 'r') as s:
    settings = json.load(s)

item_template = '    <item id="{file_without_ext}" href="{file}" media-type="application/xhtml+xml" />'
itemref_template = '    <itemref idref="{file_without_ext}" />'
navitem_template = '    <li id="toc-li-{i}">\n      <a href="{file}">{chapter_title}</a>\n    </li>'
navpoint_template = '    <navPoint id="navPoint-{i}">\n      <navLabel>\n        <text>{chapter_title}</text>\n      </navLabel>\n      <content src="{file}" />\n    </navPoint>'

#settings['items'] = ''.join([item_template.format(file_without_ext=os.path.splitext(f).first, file=f) for title, f in settings['chapters']])
items = []
itemrefs = []
navitems = []
navpoints = []
i = 0
for title, file in settings['chapters'].items():
    i += 1
    name, ext = os.path.splitext(file)
    data = {
        'i': i,
        'file': file,
        'file_without_ext': name,
        'chapter_title': title,
    }
    items.append(item_template.format(**data))
    itemrefs.append(itemref_template.format(**data))
    navitems.append(navitem_template.format(**data))
    navpoints.append(navpoint_template.format(**data))

settings['items'] = '\n'.join(items)
settings['itemrefs'] = '\n'.join(itemrefs)
settings['navitems'] = '\n'.join(navitems)
settings['navpoints'] = '\n'.join(navpoints)

def inject_data(source_path, target_path):
    with open(source_path, 'r') as source, open(target_path, 'w') as target:
        target.write(source.read().format(**settings))

shutil.rmtree('tmp/', ignore_errors=True)
os.mkdir('tmp/')
inject_data('skeleton/OEBPS/content.opf', 'tmp/content.opf')
inject_data('skeleton/OEBPS/nav.xhtml', 'tmp/nav.xhtml')
inject_data('skeleton/OEBPS/title_page.xhtml', 'tmp/title_page.xhtml')
inject_data('skeleton/OEBPS/toc.ncx', 'tmp/toc.ncx')

with open('skeleton/OEBPS/chapter_template.xhtml') as s:
    chapter_template = s.read()

i = 0
for title, filename in settings['chapters'].items():
    i += 1
    with codecs.open(os.path.join(dir, filename), 'r', encoding='utf8') as source, codecs.open(os.path.join('tmp/', filename), 'w', encoding='utf8') as target:
        target.write(chapter_template.format(i=i, chapter_title=title, chapter_content=source.read()))

with zipfile.ZipFile('ebook.epub', 'w', zipfile.ZIP_DEFLATED) as archive:
    archive.write('skeleton/mimetype', 'mimetype')
    for f in os.listdir('skeleton/META-INF/'):
        archive.write(os.path.join('skeleton/META-INF/', f), os.path.join('META-INF/', f))
    archive.write('skeleton/OEBPS/stylesheet.css', 'OEBPS/stylesheet.css')
    for f in os.listdir('tmp/'):
        archive.write(os.path.join('tmp/', f), os.path.join('OEBPS/', f))