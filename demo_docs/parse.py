import pandas as pd
import json
import copy
from collections import defaultdict

def read_and_parse_file(file_path):
    data = []
    current_entry = {}
    current_keyword = None
    current_content = []

    def finalize_current_content():
        if current_keyword:
            current_entry[current_keyword] = '\n'.join(current_content).strip()
            print(current_entry)

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

def read_and_parse_file2(file_path):
    data = []
    # current_entry = {}
    # current_keyword = None
    # current_content = []
    current_content = []
    def finalize_current_content():
        if current_content:
            return '\n'.join(current_content).strip()
        return ""

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                line = line.replace('\\', '\\\\')
                if line.endswith("}"):
                    # Finalize the content for the previous keyword
                    current_content.append(line)
                    entry = '\\n'.join(current_content).strip()
                    # entry.replace
                    print(entry)
                    entry_json = json.loads(entry)
                    data.append(copy.copy(entry_json))
                    current_content = []
                else:
                    current_content.append(line)

    return data

def get_passages_only(file_path):
    df = pd.read_csv(file_path)
    df_passage = df['passage']
    df_passage.to_csv('passage_only.txt', index=False)

def get_documents(file_path):
    df = pd.read_csv(file_path)
    file_dict = defaultdict(list)
    for row_idx, row in df.iterrows():
        file_nr = row['filenr']
        sentence = row['sentence']
        file_dict[file_nr].append(sentence)
    
    for file_nr in file_dict.keys():
        with open("./mysql_documents/mysql{}".format(file_nr), "w") as f:
            for sent in file_dict[file_nr]:
                f.write("{}\n".format(sent))

        

if __name__ == '__main__':
    # Example usage
    # file_path = './postgres100_hints'
    # parsed_data = read_and_parse_file2(file_path)

    # Print the parsed data
    # for entry in parsed_data:
    #     print(entry)

    # df = pd.DataFrame(parsed_data)
    # df.to_csv('./extracted_hints.csv')

    # get_passages_only('./extracted_hints.csv')
    file_path = './mysql100'
    get_documents(file_path)

    