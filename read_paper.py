# -*- coding: utf-8 -*-
import sys, io, zipfile, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from docx import Document

path = r'C:\Users\user\Desktop\在職碩\OneDrive - 長庚大學\長庚碩班\論文\研討會\長庚大學研討會報告_M1321114_趙威豪_modify.docx'
doc = Document(path)

print("=== 所有段落 ===")
for i, p in enumerate(doc.paragraphs):
    if p.text.strip():
        print(f'[{i}] {p.text[:120]}')

print(f"\n=== 圖片共 {len(doc.inline_shapes)} 張 ===")
for j, img in enumerate(doc.inline_shapes):
    w = img.width/914400
    h = img.height/914400
    print(f'  img[{j}]: {w:.2f}" x {h:.2f}"')

out = r'C:\Users\user\Desktop\在職碩\OneDrive - 長庚大學\長庚碩班\論文\研討會\extracted_imgs'
os.makedirs(out, exist_ok=True)
with zipfile.ZipFile(path, 'r') as z:
    media = [n for n in z.namelist() if n.startswith('word/media/')]
    print(f'\n媒體檔 {len(media)} 個:')
    for n in media:
        print(' ', n)
        z.extract(n, out)
print('已存到:', out)
