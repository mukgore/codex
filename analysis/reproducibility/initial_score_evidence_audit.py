"""Read-only inventory, text and embedded-image audit of explicit research paths.

All paths, file fingerprints, extracted content and OCR inputs are private.
This tool never writes into an input directory and never executes input code.
"""
from __future__ import annotations
import argparse
import base64
import csv
import hashlib
import io
import json
import re
import struct
import zipfile
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
from pypdf import PdfReader
import openpyxl

TARGETS = (.493, .528, .546, .522)
PATTERN = re.compile(r'(?<![\d.])(?:0?[.,](?:493\d*|492[5-9]\d*|528\d*|546\d*|522\d*)|49[.,]3\s*%)(?!\w)')
SUFFIXES = {'.py','.js','.cjs','.ipynb','.html','.md','.txt','.csv','.tsv','.json',
            '.xlsx','.zip','.pdf','.hwp','.hwpx','.docx','.pptx','.png','.jpg','.jpeg',
            '.svg','.webp','.bak','.old','.log'}


def now(): return datetime.now(timezone.utc).isoformat()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write_json(p, data):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def compound_streams(raw):
    """Read CFB regular and mini streams, with bounded chain validation."""
    if raw[:8] != bytes.fromhex('d0cf11e0a1b11ae1'): raise ValueError('Not CFB')
    sector_size = 1 << struct.unpack_from('<H',raw,30)[0]
    mini_size = 1 << struct.unpack_from('<H',raw,32)[0]
    def sector(i): return raw[(i+1)*sector_size:(i+2)*sector_size]
    dif = list(struct.unpack_from('<109I',raw,76))
    nxt, count = struct.unpack_from('<II',raw,68)
    for _ in range(count):
        entries=struct.unpack('<'+'I'*(sector_size//4),sector(nxt))
        dif.extend(entries[:-1]); nxt=entries[-1]
    fat=[]
    for i in dif:
        if i < 0xfffffffa: fat.extend(struct.unpack('<'+'I'*(sector_size//4),sector(i)))
    def chain(start, table, reader):
        chunks=[]; visited=set(); i=start
        while i < 0xfffffffa:
            if i in visited or i >= len(table): raise ValueError('Invalid CFB chain')
            visited.add(i); chunks.append(reader(i)); i=table[i]
        return b''.join(chunks)
    directory=chain(struct.unpack_from('<I',raw,48)[0],fat,sector)
    entries=[]
    for pos in range(0,len(directory),128):
        d=directory[pos:pos+128]; length=struct.unpack_from('<H',d,64)[0]
        if length:
            entries.append((d[:length-2].decode('utf-16le'),d[66],
                            struct.unpack_from('<I',d,116)[0],struct.unpack_from('<Q',d,120)[0]))
    root=next(e for e in entries if e[1]==5)
    ministream=chain(root[2],fat,sector)[:root[3]]
    mini_raw=chain(struct.unpack_from('<I',raw,60)[0],fat,sector)
    mini_fat=list(struct.unpack('<'+'I'*(len(mini_raw)//4),mini_raw)) if mini_raw else []
    out=[]
    for name,typ,start,length in entries:
        if typ != 2: continue
        value=(chain(start,mini_fat,lambda i:ministream[i*mini_size:(i+1)*mini_size])
               if length < 4096 else chain(start,fat,sector))[:length]
        out.append((name,value))
    return out


def hwp_text(streams):
    lookup=dict(streams); compressed=bool(struct.unpack_from('<I',lookup['FileHeader'],36)[0]&1)
    for name,data in streams:
        if name == 'PrvText': yield name,data.decode('utf-16le',errors='replace')
        if not re.fullmatch(r'Section\d+',name): continue
        raw=zlib.decompress(data,-15) if compressed else data
        pos=0; text=[]
        while pos+4 <= len(raw):
            head=struct.unpack_from('<I',raw,pos)[0];pos+=4;size=head>>20
            if size==4095: size=struct.unpack_from('<I',raw,pos)[0];pos+=4
            value=raw[pos:pos+size];pos+=size
            if head&1023 == 67: text.append(value.decode('utf-16le',errors='replace'))
        yield name,'\n'.join(text)


class Audit:
    def __init__(self, out):
        self.out=out; self.hits=[]; self.media={}; self.attachments=[]; self.parts=[]; self.books=[]
        (out/'media').mkdir(parents=True,exist_ok=True)
        (out/'text').mkdir(exist_ok=True)
        (out/'unclassified').mkdir(exist_ok=True)

    def scan(self, text, source, location):
        # Store every extracted text part so visual and numerical contexts remain inspectable.
        part=digest(text.encode('utf-8'))
        (self.out/'text'/f'{part}.txt').write_text(text,encoding='utf-8')
        self.parts.append(dict(source=source,location=location,text_file=part+'.txt'))
        for m in PATTERN.finditer(text):
            self.hits.append(dict(source=source,location=location,match=m.group(),
                context=text[max(0,m.start()-180):m.end()+200]))

    def image(self, raw, source, location):
        variants=[raw]
        try: variants.append(zlib.decompress(raw,-15))
        except zlib.error: pass
        for data in variants:
            try:
                with Image.open(io.BytesIO(data)) as im:
                    im.load(); sha=digest(data)
                    if sha not in self.media:
                        path=self.out/'media'/f'{sha}.png'
                        im.convert('RGB').save(path)
                        self.media[sha]=dict(alias=f'image-{len(self.media)+1:04d}',
                            file=str(path.resolve()),sha256_original_bytes=sha,width=im.width,height=im.height,
                            origins=[])
                    self.media[sha]['origins'].append(dict(source=source,location=location))
                    return True
            except (OSError,ValueError): pass
        sha=digest(raw)
        (self.out/'unclassified'/f'{sha}.bin').write_bytes(raw)
        return False

    def workbook(self, raw, source):
        record=dict(source=source,sheets=[],numeric_hits=[],formulas=0,external_links=0)
        for data_only in (False,True):
            book=openpyxl.load_workbook(io.BytesIO(raw),read_only=False,data_only=data_only,keep_links=True)
            record['external_links']=len(book._external_links)
            for sheet in book:
                if not data_only: record['sheets'].append(dict(name=sheet.title,state=sheet.sheet_state,rows=sheet.max_row,columns=sheet.max_column))
                for row in sheet:
                    for cell in row:
                        v=cell.value
                        if isinstance(v,str):
                            if v.startswith('='): record['formulas']+=not data_only
                            self.scan(v,source,f'xlsx:{sheet.title}!{cell.coordinate}:cached={data_only}') if PATTERN.search(v) else None
                        elif isinstance(v,(int,float)) and not isinstance(v,bool):
                            if any(abs(float(v)-t)<.0005 for t in TARGETS):
                                record['numeric_hits'].append(dict(sheet=sheet.title,cell=cell.coordinate,value=v,cached=data_only))
                                self.scan(str(v),source,f'xlsx-number:{sheet.title}!{cell.coordinate}:cached={data_only}')
            book.close()
        self.books.append(record)

    def process(self, raw, suffix, source, depth=0):
        if depth > 3: raise ValueError('Nested archive depth exceeded')
        if suffix in {'.png','.jpg','.jpeg','.webp'}:
            if not self.image(raw,source,'standalone'): raise ValueError('Unreadable image')
        elif suffix == '.pdf':
            reader=PdfReader(io.BytesIO(raw))
            for i,page in enumerate(reader.pages,1):
                self.scan(page.extract_text() or '',source,f'pdf-page-{i}')
                for j,im in enumerate(page.images): self.image(im.data,source,f'pdf-page-{i}-image-{j}')
            for name,attachment in (getattr(reader,'attachments',{}) or {}).items():
                self.attachments.append(dict(source=source,name=name,classification='pdf-attachment'))
                for data in attachment: self.process(data,Path(name).suffix.lower(),source+'::'+name,depth+1)
        elif suffix == '.hwp':
            streams=compound_streams(raw)
            for name,text in hwp_text(streams): self.scan(text,source,'hwp:'+name)
            for name,data in streams:
                if name.lower().startswith('bin') or name.lower().endswith(('.png','.jpg','.jpeg','.bmp','.gif','.ole')):
                    recognized=self.image(data,source,'hwp:'+name)
                    self.attachments.append(dict(source=source,name=name,classification='image' if recognized else 'unclassified_binary',
                        raw_sha256=digest(data)))
        elif suffix == '.ipynb':
            nb=json.loads(raw.decode('utf-8-sig'))
            for i,cell in enumerate(nb.get('cells',[])):
                self.scan(''.join(cell.get('source',[])),source,f'cell-{i}-source')
                for j,out in enumerate(cell.get('outputs',[])):
                    self.scan(''.join(out.get('text',[])),source,f'cell-{i}-output-{j}')
                    for mime,data in out.get('data',{}).items():
                        text=''.join(data) if isinstance(data,list) else str(data)
                        if mime.startswith('text/') or mime=='image/svg+xml': self.scan(text,source,f'cell-{i}-output-{j}:{mime}')
                        elif mime.startswith('image/'): self.image(base64.b64decode(text),source,f'cell-{i}-output-{j}:{mime}')
        elif suffix == '.xlsx': self.workbook(raw,source)
        elif suffix in {'.zip','.docx','.hwpx','.pptx'}:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                for info in z.infolist():
                    if info.is_dir(): continue
                    if info.file_size > 64*1024*1024:
                        self.attachments.append(dict(source=source,name=info.filename,classification='over_64MiB_not_read'));continue
                    name=info.filename; ext=Path(name).suffix.lower()
                    if '/media/' in name or name.startswith(('BinData/','Pictures/')):
                        if not self.image(z.read(info),source,name):
                            self.attachments.append(dict(source=source,name=name,classification='unclassified_media'))
                    elif '/embeddings/' in name or suffix=='.zip' and ext in SUFFIXES:
                        self.attachments.append(dict(source=source,name=name,classification='embedded_or_archive_file'))
                        self.process(z.read(info),ext,source+'::'+name,depth+1)
                    elif name.endswith('.xml'):
                        root=ET.fromstring(z.read(info));self.scan(' '.join(root.itertext()),source,name)
                        # Include field/formula attributes, which may not be visible text nodes.
                        attrs=' '.join(v for e in root.iter() for v in e.attrib.values())
                        if PATTERN.search(attrs): self.scan(attrs,source,name+':attributes')
        elif suffix == '.json':
            data=json.loads(raw.decode('utf-8-sig'))
            def walk(value,location):
                if isinstance(value,dict):
                    for k,v in value.items():
                        if k not in {'landmarks','landmarks_px','lm','frames','sessionLog','keyframes'}:walk(v,location+'/'+k)
                elif isinstance(value,list):
                    for i,v in enumerate(value):walk(v,location+'/'+str(i))
                elif isinstance(value,(str,int,float)) and not isinstance(value,bool):
                    if PATTERN.search(str(value)):self.scan(str(value),source,location)
            walk(data,'json-noncoordinate-fields')
        else:self.scan(raw.decode('utf-8-sig',errors='replace'),source,'text')

    def run(self, paths):
        inventory=[]; seen={}; start=now()
        for i,p in enumerate(paths):
            raw=p.read_bytes();sha=digest(raw);entry=dict(path=str(p.resolve()),sha256=sha,bytes=len(raw),status='read')
            if sha in seen:entry.update(status='hash_duplicate',duplicate_of=seen[sha])
            else:
                seen[sha]=str(p.resolve())
                try:self.process(raw,p.suffix.lower(),str(p.resolve()))
                except Exception as e:entry.update(status='parse_error',error=type(e).__name__+': '+str(e))
            inventory.append(entry)
            if i%25==0:print(f'processed {i+1}/{len(paths)} images={len(self.media)}',flush=True)
        unchanged=all(digest(Path(r['path']).read_bytes())==r['sha256'] for r in inventory)
        for name,data in [('inventory',inventory),('hits',self.hits),('media',list(self.media.values())),
                          ('attachments',self.attachments),('parts',self.parts),('workbooks',self.books)]:write_json(self.out/(name+'.json'),data)
        summary=dict(start_utc=start,end_utc=now(),input_files=len(inventory),unique_contents=len(seen),
            statuses=dict(Counter(r['status'] for r in inventory)),text_hits=len(self.hits),unique_media=len(self.media),
            media_occurrences=sum(len(r['origins']) for r in self.media.values()),attachments=len(self.attachments),
            input_hashes_unchanged=unchanged)
        write_json(self.out/'run.json',summary); print(json.dumps(summary,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-list',type=Path,required=True,help='Private JSON array of explicit input paths')
    p.add_argument('--private-dir',type=Path,required=True)
    args=p.parse_args();paths=[Path(x).resolve() for x in read_json(args.input_list)]
    if any(args.private_dir.resolve()==x or args.private_dir.resolve() in x.parents for x in paths):
        raise ValueError('Output directory contains an input; use a separate private directory')
    args.private_dir.mkdir(parents=True,exist_ok=True)
    Audit(args.private_dir).run(paths)


if __name__=='__main__':main()
