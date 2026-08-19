import re

with open('frontend/src/app/page.js', 'r') as f:
    content = f.read()

# I will replace the <select> tag logic with a ternary operator:
# {loadingOptions && (!options.Marka || options.Marka.length === 0) ? <div className="w-full h-11 bg-slate-200 animate-pulse rounded-lg"></div> : <select ... > }

def replace_select(match):
    full_block = match.group(0)
    name = match.group(1)
    
    # Check if this is Kimden or Garanti_Durumu which has a custom <option value=""> string
    # Actually, all selects have an <option value="">.
    
    # We will inject the ternary around the select tag
    new_block = f"{{loadingOptions && (!options.{name} || options.{name}.length === 0) ? (\n                    <div className=\"w-full h-[46px] bg-slate-200 animate-pulse rounded-lg\"></div>\n                  ) : (\n                    <select"
    
    return full_block.replace("<select", new_block) + "\n                  )}"

# Find all blocks that look like <select ... name="X" ...> ... </select>
# Wait, this might be tricky with regex. Let's just find <select and </select>.
import sys

def modify():
    global content
    pattern = r'(<select.*?name="([^"]+)".*?>.*?</select>)'
    
    def replacer(m):
        full_select = m.group(1)
        name = m.group(2)
        # Avoid double replacing
        if "animate-pulse" in full_select:
            return full_select
            
        return f"{{loadingOptions && (!options.{name} || options.{name}.length === 0) ? (\n                    <div className=\"w-full h-[46px] bg-slate-200 animate-pulse rounded-lg\"></div>\n                  ) : (\n                    {full_select}\n                  )}}"
        
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)
    
    with open('frontend/src/app/page.js', 'w') as f:
        f.write(content)

modify()
print("Replaced selects with Skeleton loader ternary")
