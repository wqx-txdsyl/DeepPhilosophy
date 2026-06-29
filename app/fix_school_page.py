"""Inline 10 new school DATA objects directly into SchoolDetailPage.jsx"""
import re

# Read main file
with open('src/pages/SchoolDetailPage.jsx', 'r', encoding='utf-8') as f:
    main = f.read()

# Read generated DATA
with open('src/pages/_new_schools_data.jsx', 'r', encoding='utf-8') as f:
    school_data = f.read()

# Strip SCHOOL_MAP entries from school_data
school_data = re.sub(r'\n// SCHOOL_MAP entries.*', '', school_data, flags=re.DOTALL).strip()

# Insert DATA objects before GREEK_DATA
insert_pos = main.find('const GREEK_DATA = {')
main = main[:insert_pos] + school_data + '\n\n' + main[insert_pos:]

# Remove old _json entries for new schools
new_schools = ['韩国哲学','西藏哲学','北欧哲学','玛雅哲学','阿兹特克哲学',
               '澳洲原住民哲学','蒙古中亚哲学','东欧斯拉夫哲学','北美哲学','美索不达米亚哲学']
for name in new_schools:
    # Remove any entry with this school name (both _json and non-_json versions)
    pattern = rf"  '{re.escape(name)}':\s*\{{[^}}]*\}},\n"
    main = re.sub(pattern, '', main)

# Add new entries with inline DATA variables
for name in new_schools:
    var_name = re.sub(r'[^\w]', '', name).upper() + '_DATA'
    new_entry = f"  '{name}': {{ data:{var_name}, sub:{{}}, ci:[], bg:'url(/schools/{name}.jpg)' }},\n"
    # Insert before the closing }; of SCHOOL_MAP
    main = main.replace("};\n  const m = SCHOOL_MAP[name]", new_entry + "};\n  const m = SCHOOL_MAP[name]")

# Simplify: remove dynamic loading, just use m.data directly
main = re.sub(
    r"const \[dynamicData, setDynamicData\] = useState\(null\);\s*\n\s*const \[loadingJson, setLoadingJson\] = useState\(!!m\._json\);\s*\n\s*useEffect.*?setLoadingJson\(false\);\s*\}\); \}\) }, \[name\]\);\s*\n\s*const data = loadingJson \? null : \(dynamicData \|\| m\.data \|\| GREEK_DATA\);",
    "const data = m.data || GREEK_DATA;",
    main, flags=re.DOTALL
)

main = main.replace(
    "const subSchools = dynamicData?.sub || m.sub || (m.data ? GREEK_SUB_SCHOOLS : {});",
    "const subSchools = m.sub || (m.data ? GREEK_SUB_SCHOOLS : {});"
)

main = main.replace(
    "const cihai = dynamicData?.cihai || m.ci || GREEK_CIHAI;",
    "const cihai = m.ci || GREEK_CIHAI;"
)

# Remove unused states
main = main.replace("const [jsonError, setJsonError] = useState(false);\n", "")
main = main.replace("const [renderError, setRenderError] = useState(null);\n", "")
# Remove the loading div that checks !data
main = re.sub(r"\s*if \(!data\).*?</div>;", "", main, flags=re.DOTALL)

with open('src/pages/SchoolDetailPage.jsx', 'w', encoding='utf-8') as f:
    f.write(main)
print('Done - DATA inlined, dynamic loading removed')
