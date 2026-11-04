"""Inspect cached HWP/OLE chart objects without launching the OLE application."""
import argparse
import json
import re
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from .initial_score_evidence_audit import compound_streams, digest, write_json
except ImportError:
    from initial_score_evidence_audit import compound_streams, digest, write_json

MAGIC=bytes.fromhex('d0cf11e0a1b11ae1')


def inspect_chart(raw):
    try: data=zlib.decompress(raw,-15)
    except zlib.error: data=raw
    offset=data.find(MAGIC)
    if offset not in (0,4): raise ValueError('Not a recognized raw/prefixed CFB chart')
    streams=compound_streams(data[offset:])
    xmls=[v for name,v in streams if name=='OOXMLChartContents']
    if not xmls: raise ValueError('No editable OOXML chart data')
    output=[]
    for raw_xml in xmls:
        root=ET.fromstring(raw_xml)
        values=[e.text for e in root.iter() if e.text]
        numbers=[]
        for text in values:
            try: value=float(text)
            except ValueError: continue
            if .4925 <= value < .4935: numbers.append(value)
        output.append(dict(xml_sha256=digest(raw_xml),text_values=values,
                           numeric_target_hits=numbers))
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-dir',type=Path,required=True)
    args=p.parse_args();results=[]
    for path in sorted((args.private_dir/'local_scan/unclassified').glob('*.bin')):
        try:results.append(dict(file=path.name,status='chart_xml_read',charts=inspect_chart(path.read_bytes())))
        except Exception as e:results.append(dict(file=path.name,status='unresolved',error=str(e)))
    write_json(args.private_dir/'embedded_chart_final_review.json',results)
    print(json.dumps(dict(objects=len(results),unresolved=sum(r['status']=='unresolved' for r in results),
                         unique_xml=len({v['xml_sha256'] for r in results for v in r.get('charts',[])}),
                         target_hits=sum(len(v['numeric_target_hits']) for r in results for v in r.get('charts',[])))))


if __name__=='__main__':main()
