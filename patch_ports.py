import os
import glob

# Files to update
frontend_files = [
    'frontend/lib/api.ts',
    'frontend/app/statistics/page.tsx',
    'frontend/app/page.tsx',
    'frontend/app/compare/page.tsx',
    'win_start.py'
]

for file in frontend_files:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Safe replacement mapping
        old = "127.0.0.1:8000"
        new = "127.0.0.1:8001"
        
        # Only in win_start.py
        if file == 'win_start.py':
            content = content.replace('port", "8000"', 'port", "8001"')
            content = content.replace('kill_port(8000)', 'kill_port(8001)')
            content = content.replace('Port 8000', 'Port 8001')
        else:
            content = content.replace(old, new)
            
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
