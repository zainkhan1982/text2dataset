"""
Test script to verify dataset history functionality
"""

from dataset_history import DatasetHistory
import os

def test_dataset_history():
    print("Testing Dataset History Functionality")
    print("=" * 40)
    
    # Create history instance
    history = DatasetHistory("test_history.json")
    
    # Clear any existing test history
    history.clear_history()
    
    # Add some test entries
    print("Adding test entries...")
    history.add_to_history("test_dataset_1.csv", "fast", "csv", 150)
    history.add_to_history("test_dataset_2.json", "smart", "json", 200)
    history.add_to_history("test_dataset_3_spacy.json", "fast", "spacy", 175)
    
    # Retrieve history
    print("\nRetrieving history...")
    all_history = history.get_history()
    print(f"Total entries: {len(all_history)}")
    
    # Display entries
    for entry in all_history:
        print(f"  ID: {entry['id']}, File: {entry['filename']}, Mode: {entry['mode']}, "
              f"Format: {entry['format']}, Entities: {entry['entity_count']}")
    
    # Test recent datasets
    print("\nRecent datasets (limit 2)...")
    recent = history.get_recent_datasets(2)
    for entry in recent:
        print(f"  ID: {entry['id']}, File: {entry['filename']}, Created: {entry['timestamp'][:19]}")
    
    # Test get by ID
    print("\nGetting dataset by ID (ID: 2)...")
    dataset = history.get_dataset_by_id(2)
    if dataset:
        print(f"  Found: {dataset['filename']}")
    else:
        print("  Not found")
    
    # Test file info
    print("\nTesting file info...")
    file_info = history.get_file_info("test_history.json")
    print(f"  File exists: {file_info['exists']}")
    
    # Clean up test history file
    test_history_path = os.path.join(history.history_dir, "test_history.json")
    if os.path.exists(test_history_path):
        os.remove(test_history_path)
        print("\nCleaned up test history file")
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_dataset_history()