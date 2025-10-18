import json

# Test data
test_data = [
  {
    "text": "Apple is a technology company.",
    "entities": [
      {
        "text": "Apple",
        "label": "ORG",
        "start": 0,
        "end": 5
      }
    ]
  },
  {
    "text": "Microsoft is also a technology company.",
    "entities": [
      {
        "text": "Microsoft",
        "label": "ORG",
        "start": 0,
        "end": 9
      }
    ]
  },
  {
    "text": "Google is a search engine company.",
    "entities": [
      {
        "text": "Google",
        "label": "ORG",
        "start": 0,
        "end": 6
      }
    ]
  }
]

def process_json_for_visualization(data):
    """Process JSON data for visualization"""
    try:
        # Handle spaCy format data
        if isinstance(data, list) and len(data) > 0:
            # Check if it's spaCy format
            if isinstance(data[0], dict) and "text" in data[0] and "entities" in data[0]:
                # Process spaCy format - focus only on entities and labels
                entity_counts = {}
                entity_texts = {}
                for item in data:
                    for entity in item.get("entities", []):
                        label = entity.get("label", "Unknown")
                        text = entity.get("text", "Unknown")
                        entity_counts[label] = entity_counts.get(label, 0) + 1
                        if label not in entity_texts:
                            entity_texts[label] = []
                        entity_texts[label].append(text)
                
                # Get unique entity texts per label
                unique_entity_texts = {label: list(set(texts)) for label, texts in entity_texts.items()}
                
                return {
                    "type": "spacy",
                    "entity_counts": entity_counts,
                    "entity_texts": unique_entity_texts,
                    "total_entities": sum(entity_counts.values()),
                    "total_samples": len(data)
                }
            else:
                # Handle generic JSON array
                return {
                    "type": "json_array",
                    "item_count": len(data)
                }
        elif isinstance(data, dict):
            # Handle JSON object
            return {
                "type": "json_object"
            }
        else:
            return {"type": "unknown"}
    except Exception as e:
        return {"error": f"Error processing JSON: {str(e)}"}

# Test the function
result = process_json_for_visualization(test_data)
print("Processing result:")
print(json.dumps(result, indent=2))