"""Extract trade goods data from Python code to JSON format."""
import re
import json
from pathlib import Path

def extract_trade_goods():
    """Parse T5RandomTradeGoods.py and extract all data to JSON."""
    
    source_file = Path('src/t5code/T5RandomTradeGoods.py')
    content = source_file.read_text()
    
    # Extract all classification table definitions
    classifications = {}
    aliases = {}
    
    # Pattern to match table creation: xxx_table = TradeClassificationGoodsTable("XXX")
    table_pattern = r'(\w+)_table = TradeClassificationGoodsTable\("([^"]+)"\)'
    
    # Pattern to match add_type_table calls
    type_table_pattern = r'\.add_type_table\(\s*"([^"]+)",\s*\[(.*?)\],?\s*\)'
    
    # Find all table definitions
    tables = re.findall(table_pattern, content)
    
    for var_name, classification_code in tables:
        print(f"Processing {classification_code}...")
        classifications[classification_code] = {"types": {}}
        
        # Find all add_type_table calls for this table
        # Look for pattern: var_name_table.add_type_table(...)
        section_pattern = f'{var_name}_table\\.add_type_table\\(\\s*"([^"]+)",\\s*\\[([^\\]]+)\\]'
        
        # More robust: find the table variable and extract until next table or end
        table_start_pattern = f'{var_name}_table = TradeClassificationGoodsTable'
        table_start_match = re.search(re.escape(table_start_pattern), content)
        if not table_start_match:
            continue
        table_start = table_start_match.start()
            
        # Find the end: look for T5RTGTable.add_classification_table for this classification
        add_classification_pattern = f'T5RTGTable\\.add_classification_table\\("{re.escape(classification_code)}"'
        add_match = re.search(add_classification_pattern, content[table_start:])
        
        if add_match:
            table_end = table_start + add_match.start()
        else:
            # Use next table or end of file
            next_table_match = re.search(r'\w+_table = TradeClassificationGoodsTable', content[table_start + 10:])
            if next_table_match:
                table_end = table_start + 10 + next_table_match.start()
            else:
                table_end = len(content)
            
        table_section = content[table_start:table_end]
        
        # Extract all type tables - they span multiple lines
        # Pattern: .add_type_table(\n    "TypeName",\n    [\n        "item1",\n        ...items...\n    ],\n)
        type_matches = list(re.finditer(
            r'\.add_type_table\s*\(\s*"([^"]+)"\s*,\s*\[(.*?)\]\s*,?\s*\)',
            table_section,
            re.DOTALL
        ))
        
        for match in type_matches:
            type_name = match.group(1)
            items_str = match.group(2)
            
            # Parse items
            items = []
            
            # Check if this is Imbalances (contains ImbalanceTradeGood)
            if 'ImbalanceTradeGood' in items_str:
                # Extract reroll classifications
                imbalance_pattern = r'ImbalanceTradeGood\("([^"]+)"'
                for reroll_match in re.finditer(imbalance_pattern, items_str):
                    items.append({
                        "type": "imbalance",
                        "reroll_classification": reroll_match.group(1)
                    })
            else:
                # Regular string items
                # Extract quoted strings and constants
                item_pattern = r'"([^"]+)"|([A-Z_]+(?:_[A-Z_]+)*)\s*(?:,|$)'
                for item_match in re.finditer(item_pattern, items_str):
                    if item_match.group(1):
                        items.append(item_match.group(1))
                    elif item_match.group(2):
                        # It's a constant like BULK_NITRATES
                        const_name = item_match.group(2)
                        # Map constants to their values
                        const_map = {
                            'BULK_NITRATES': 'Bulk Nitrates',
                            'STRANGE_SEEDS': 'Strange Seeds',
                            'BULK_MINERALS': 'Bulk Minerals',
                            'EXOTIC_FAUNA': 'Exotic Fauna',
                            'EXOTIC_FLORA': 'Exotic Flora',
                            'EXPERT_SYSTEMS': 'Expert Systems',
                            'VARIABLE_TATTOOS': 'Variable Tattoos',
                            'BRANDED_DRINKS': 'Branded Drinks',
                            'BRANDED_CLOTHES': 'Branded Clothes',
                        }
                        if const_name in const_map:
                            items.append(const_map[const_name])
            
            classifications[classification_code]["types"][type_name] = items
    
    # Extract aliases (clone_classification_table calls)
    alias_pattern = r'clone_classification_table\("([^"]+)",\s*(\w+)_table'
    for match in re.finditer(alias_pattern, content):
        alias_code = match.group(1)
        source_var = match.group(2)
        
        # Find what classification this variable represents
        source_pattern = f'{source_var}_table = TradeClassificationGoodsTable\\("([^"]+)"\\)'
        source_match = re.search(source_pattern, content)
        if source_match:
            aliases[alias_code] = source_match.group(1)
    
    return {"classifications": classifications, "aliases": aliases}

if __name__ == '__main__':
    data = extract_trade_goods()
    
    # Save to JSON
    output_path = Path('resources/trade_goods_tables.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Extracted {len(data['classifications'])} classifications")
    print(f"✅ Extracted {len(data['aliases'])} aliases")
    print(f"✅ Saved to {output_path}")
    
    # Validate
    for code, classification in data['classifications'].items():
        num_types = len(classification['types'])
        # Most classifications have 6 types, but some (like In) may have fewer
        for type_name, items in classification['types'].items():
            if len(items) != 6:
                print(f"⚠️  WARNING: {code}/{type_name} has {len(items)} items (expected 6)")
