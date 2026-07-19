"""Debug 工具论 EPUB NCX-to-spine matching"""
import zipfile, os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from bs4 import BeautifulSoup

fp = 'F:/philosophy/西方/亚里士多德/工具论.epub'
z = zipfile.ZipFile(fp)
names = z.namelist()

# Find OPF
opf = [n for n in names if n.endswith('.opf')][0]
print(f'OPF: {opf}')
soup = BeautifulSoup(z.read(opf).decode('utf-8', 'ignore'), 'xml')
opf_dir = os.path.dirname(opf) if '/' in opf else ''

# Build manifest with opf_dir resolution
manifest = {}
for it in soup.find_all('item'):
    iid = it.get('id', '')
    href = it.get('href', '')
    if iid and href:
        if opf_dir:
            full = os.path.normpath(os.path.join(opf_dir, href)).replace('\\', '/')
        else:
            full = href
        manifest[iid] = full

# Spine hrefs
spine_hrefs = []
for ref in soup.find_all('itemref'):
    iid = ref.get('idref', '')
    if iid in manifest:
        spine_hrefs.append(manifest[iid])
print(f'Spine: {len(spine_hrefs)} items')
for i, sh in enumerate(spine_hrefs[:5]):
    print(f'  [{i}] {sh}')

# Find NCX
for n in names:
    if n.endswith('.ncx'):
        c = z.read(n).decode('utf-8', 'ignore')
        pts = re.findall(r'<navPoint[^>]*>.*?</navPoint>', c, re.DOTALL)
        print(f'NCX: {len(pts)} entries')
        for i, pt in enumerate(pts[:8]):
            label = re.search(r'<text>(.*?)</text>', pt)
            src = re.search(r'src="([^"]+)"', pt)
            lt = label.group(1) if label else '?'
            st = src.group(1) if src else '?'
            # Match to spine
            sf = st.split('#')[0]
            matched = []
            for j, sh in enumerate(spine_hrefs):
                if sf and (sh.endswith(sf.split('/')[-1]) or sf.endswith(sh.split('/')[-1])):
                    matched.append(j)
            print(f'  [{i}] {lt} -> {st[:80]}')
            print(f'       spine match: {matched}')
        break

# Check why spine matching fails - compare raw paths
print('\nSpine hrefs (all):')
for i, sh in enumerate(spine_hrefs):
    print(f'  [{i}] {sh}')
