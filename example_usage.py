"""
Example usage of Text2Dataset application
"""

# Example text for testing
sample_text = """
Apple Inc. is an American multinational technology company headquartered in Cupertino, California. 
It was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976 to develop, sell, 
and support personal computers. Apple is the world's largest technology company by revenue, 
with US$394.3 billion in 2022 revenue. As of March 2023, Apple is the world's biggest smartphone 
manufacturer by market capitalization. Apple is the fourth-largest PC vendor by unit sales and 
fourth-largest smartphone manufacturer.

Apple's products include the iPhone smartphone, iPad tablet computer, Mac personal computers, 
iPod portable media player, Apple Watch smartwatch, Apple TV digital media player, and AirPods 
wireless earbuds. Apple's software includes the macOS and iOS operating systems, the iTunes 
media player, the Safari web browser, and the iLife and iWork creativity and productivity suites. 
Apple also offers cloud services such as iCloud, Apple Music, and the App Store.
"""

def save_sample_text():
    """Save sample text to a file for testing"""
    with open("sample_text.txt", "w", encoding="utf-8") as f:
        f.write(sample_text)
    print("Sample text saved to 'sample_text.txt'")

def demonstrate_api_usage():
    """Demonstrate how to use the API"""
    print("To use the Text2Dataset web application:")
    print("1. Open your browser and go to http://localhost:8000")
    print("2. Paste the sample text or upload the 'sample_text.txt' file")
    print("3. Select output format (CSV or JSON)")
    print("4. Select processing mode (Fast or Smart)")
    print("5. Click 'Generate Dataset'")
    print("6. Download the processed dataset")

if __name__ == "__main__":
    save_sample_text()
    print("\nSample text for testing the Text2Dataset application:\n")
    print(sample_text)
    print("\n" + "="*50 + "\n")
    demonstrate_api_usage()