
from bs4 import BeautifulSoup
import sys

try:
    with open('yahoo_playwright_debug.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print("Page Title:", soup.title.string if soup.title else "No Title")
    
    print("\n--- Links (first 50) ---")
    links = soup.find_all('a')
    for i, link in enumerate(links[:50]):
        print(f"{i+1}. {link.get_text(strip=True)} -> {link.get('href')}")
        
    print("\n--- Searching for '上映' ---")
    # Find all elements containing "上映" text
    targets = soup.find_all(string=lambda text: "上映" in text if text else False)
    for i, target in enumerate(targets[:10]):
        parent = target.parent
        print(f"Match {i+1}: {target[:50]}...")
        print(f"  Parent: {parent.name} class={parent.get('class')} id={parent.get('id')}")
        # Print parent's parent to see context
        if parent.parent:
            grandparent = parent.parent
            print(f"  Grandparent: {grandparent.name} class={grandparent.get('class')}")

    print("\n--- Deep Inspection of #Main ---")
    main_div = soup.find('div', id='Main')
    if main_div:
        # Traverse down to find where content might be
        # looking for lists (ul/li) or repeated divs
        print("Found #Main. Children:")
        for child in main_div.find_all(recursive=False):
            print(f"  {child.name} class={child.get('class')} id={child.get('id')}")
            # If it's a div, look inside
            if child.name == 'div':
                for grand in child.find_all(recursive=False):
                    print(f"    {grand.name} class={grand.get('class')} id={grand.get('id')}")
                    if grand.name == 'div' or grand.name == 'ul':
                         for great in grand.find_all(recursive=False):
                             print(f"      {great.name} class={great.get('class')}")


except Exception as e:
    print(f"Error: {e}")
