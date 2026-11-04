"""Supplementary numeric-format scan over private cached text, without re-reading sources."""
import argparse
import json
import re
from pathlib import Path

ALTERNATE = re.compile(r'(?<![\w.])(?:[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)[eE][+-]?\d+|(?:49[.,]3\d*|0\s*,\s*493\d*)\s*%?)(?![\w.])')


def candidates(text):
    for match in ALTERNATE.finditer(text):
        token=match.group().replace(' ','').replace(',','.')
        try: value=float(token.rstrip('%'))/(100 if token.endswith('%') else 1)
        except ValueError: continue
        if .4925 <= value < .4935:
            yield dict(token=match.group(),value=value,
                       context=text[max(0,match.start()-100):match.end()+100])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-dir',type=Path,required=True)
    args=p.parse_args();root=args.private_dir
    parts=json.loads((root/'local_scan/parts.json').read_text(encoding='utf-8'))
    hits=[]
    for part in parts:
        text=(root/'local_scan/text'/part['text_file']).read_text(encoding='utf-8')
        hits.extend(dict(source=part['source'],location=part['location'],**hit) for hit in candidates(text))
    (root/'alternate_numeric_format_hits.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(text_parts=len(parts),alternate_numeric_hits=len(hits))))


if __name__=='__main__':main()
