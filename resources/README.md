# Trade Goods Tables JSON Format

This directory contains JSON data files for Traveller 5 random trade goods generation.

## File: `trade_goods_tables.json`

Contains trade goods organized by world classification codes (Ag, As, De, etc.).

### Structure

```json
{
  "classifications": {
    "<classification_code>": {
      "types": {
        "<type_name>": [
          "item1",
          "item2",
          ...
        ],
        "Imbalances": [
          {
            "type": "imbalance",
            "reroll_classification": "<target_classification>"
          },
          ...
        ]
      }
    }
  },
  "aliases": {
    "<alias_code>": "<source_classification>"
  }
}
```

### Rules

- Each classification must have exactly **6 type tables**
- Each type table must have exactly **6 goods**
- Imbalances are special entries that reroll on another classification
- Aliases create a copy of an existing classification with a different code

### Example

```json
{
  "classifications": {
    "Ag-1": {
      "types": {
        "Raws": ["Bulk Protein", "Bulk Carbs", ...],
        "Imbalances": [
          {"type": "imbalance", "reroll_classification": "As"}
        ]
      }
    }
  },
  "aliases": {
    "Ga": "Ag-1"
  }
}
```

## Usage

```python
from pathlib import Path
from t5code.T5RandomTradeGoods import RandomTradeGoodsTable

# Load from JSON
json_path = Path("resources/trade_goods_tables.json")
table = RandomTradeGoodsTable.from_json(json_path)

# Use the table
random_good = table.get_random("Ag-1")
print(random_good)
```

## Current Status

The JSON file currently contains a **sample** with 3 classifications (Ag-1, Ag-2, As) for demonstration.

To complete the implementation, add all 12 classifications from the original T5 rules:
- Ag-1 (Agricultural-1) ✅
- Ag-2 (Agricultural-2) ✅  
- As (Asteroid) ✅
- De (Desert)
- Fl (Fluid)
- Ic (Ice-capped)
- Na (Non-agricultural)
- In (Industrial)
- Po (Poor)
- Ri (Rich)
- Va (Vacuum)
- Cp (Capital/Government)

Plus aliases: Ga, Fa, Cs, Cx
