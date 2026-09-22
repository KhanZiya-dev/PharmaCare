import os

app_dir = r'd:\BSc.CS\Sem5\Pharmacare\frontend\src\app'
for root, _, files in os.walk(app_dir):
    for f in files:
        if f.endswith('.tsx') and f != 'layout.tsx':
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Remove import
            content = content.replace('import { Navbar } from "@/components/Navbar";\n', '')
            content = content.replace('import { Navbar } from "@/components/Navbar"\n', '')
            # Remove component
            content = content.replace('      <Navbar />\n', '')
            content = content.replace('    <Navbar />\n', '')
            content = content.replace('  <Navbar />\n', '')
            content = content.replace('<Navbar />\n', '')
            
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)
print('Done!')
