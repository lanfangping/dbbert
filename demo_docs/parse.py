import pandas as pd

def read_and_parse_file(file_path):
    data = []
    current_entry = {}
    current_keyword = None
    current_content = []

    def finalize_current_content():
        if current_keyword:
            current_entry[current_keyword] = '\n'.join(current_content).strip()

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                if ':' in line:
                    # Finalize the content for the previous keyword
                    finalize_current_content()
                    # Split the new line into keyword and content
                    keyword, content = line.split(':', 1)
                    keyword = keyword.strip()
                    content = content.strip()
                    
                    if keyword == 'doc_id' and current_entry:
                        data.append(current_entry)
                        current_entry = {}
                    
                    current_keyword = keyword
                    current_content = [content]
                else:
                    current_content.append(line)
        
        # Finalize the content for the last keyword
        finalize_current_content()
        if current_entry:
            data.append(current_entry)
    
    return data

if __name__ == '__main__':
    # Example usage
    file_path = './postgres100_hints'
    parsed_data = read_and_parse_file(file_path)

    # Print the parsed data
    for entry in parsed_data:
        print(entry)

    df = pd.DataFrame(parsed_data)
    df.to_csv('./extracted_hints.csv')

    