import os
import re
from collections import defaultdict




def converter(main_folder):
    # Iterate through each subfolder in the main folder
    for subfolder in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder)
        doc_id = get_doc_id(subfolder)
        
        # Check if it is indeed a subfolder
        if os.path.isdir(subfolder_path):
            
            # Iterate through each file in the subfolder
            for file in os.listdir(subfolder_path):
                if file.startswith('INITIAL_CAS'):
                    continue

                file_path = os.path.join(subfolder_path, file)
                
                # Check if it is a file (not a subfolder)
                if os.path.isfile(file_path):
                    print(f"Found file: {file_path}")
                    lines = read_tsv(file_path)

                    sent_entities, sent_relations = get_entities_and_relations(lines)
                    print("+++++++++++++++++++++")
                    print(sent_entities)
                    print("+++++++++++++++++++++")
                    print(sent_relations)

                    input()

def read_tsv(file_path):
    with open(file_path, 'r') as f:
        return f.readlines()

def get_entities_and_relations(lines):
    sent_entities = []
    sent_relations = []
    # {"label": "PER", "start": 2, "end": 4}
    value_id = None
    begin, end = 0, 0
    entity_dict = {}
    multi_token_entity = []
    relation_dict = {}
    for line in lines:
        # initiate value_id to None
        if len(multi_token_entity) == 0:
            value_id = None
        # print("==>", line)
        if line.startswith('#') or len(line.strip()) == 0:
            continue
        else:
            items = line.split()
            if len(items) <= 3:
                continue

            if items[3].strip() != '-' and items[3].strip() != '_':
                
                if items[3].strip().startswith('value'):
                    if items[3].strip() == 'value':
                        # process entity
                        if value_id is None:
                            value_id = items[0].strip()
                        
                        index = items[1].split('-')
                        begin = int(index[0].strip())
                        end = int(index[1].strip())
                        if len(items[2].strip()) == (end-begin):
                            token = items[2].strip()
                        else:
                            token = items[2].strip()[:end-begin]
                        entity_dict[value_id] = (token, begin, end)
                        print(str({
                                "label":"value",
                                "token":token,
                                "start":begin,
                                "end":end
                            }))
                        sent_entities.append(
                            {
                                "label":"value",
                                "token":token,
                                "start":begin,
                                "end":end
                            }
                        )

                        # # process relation
                        # if items[4] != '-':
                        #     span = " ".join(items[4:])
                        #     param_item_id = span.strip().split()[-1].strip()
                        #     relation_dict[param_item_id] = item_id
                    elif '[' in items[3]:
                        print("===>>", items)
                        if len(multi_token_entity) == 0:
                            begin = int(items[1].split('-')[0].strip())
                        else:
                            end = int(items[1].split('-')[-1].strip())
                        multi_token_entity.append(items[2].strip())
                        if value_id is None:
                            value_id = items[0].strip()
                            print("value_id", value_id)

                    # process relation
                    if items[4] != '-' and items[4] != '_':
                        rest_span = " ".join(items[4:])
                        print("rest_span", rest_span)
                        if '|' in rest_span:
                            param_relation_spans = rest_span.strip().split('|')
                            for span in param_relation_spans:
                                if '[' in span:
                                    print("span", span)
                                    param_item_id = span.split()[-1].split('[')[0].strip()
                                    print("param_item_id", param_item_id)
                                    relation_dict[param_item_id] = value_id
                                elif '-' in span:
                                    print("span", span)
                                    param_item_id = span.split()[-1].strip()
                                    print("param_item_id", param_item_id)
                                    relation_dict[param_item_id] = value_id
                        elif '[' in rest_span:
                            param_item_id = rest_span.strip().split()[-1].split('[')[0].strip()
                            print("param_item_id", param_item_id)
                            relation_dict[param_item_id] = item_id
                        else:
                            param_item_id = rest_span.strip().split()[-1].strip()
                            print("param_item_id", param_item_id)
                            relation_dict[param_item_id] = item_id

                elif items[3].strip().startswith('parameter'):
                    item_id = items[0].strip()
                    index = items[1].split('-')
                    begin = int(index[0].strip())
                    end = int(index[1].strip())
                    if len(items[2].strip()) == (end-begin):
                        token = items[2].strip()
                    else:
                        token = items[2].strip()[:end-begin]
                    entity_dict[item_id] = (token, begin, end)
                    print(str({
                        "label":"value",
                        "token":token,
                        "start":begin,
                        "end":end
                    }))
                    sent_entities.append(
                        {
                            "label":"parameter",
                            "token":token,
                            "start":begin,
                            "end":end
                        }
                    )
                else:
                    continue
            else:
                if len(multi_token_entity) != 0:
                    token = " ".join(multi_token_entity)
                    print("===>>>", value_id, token, begin, end)
                    entity_dict[value_id] = (token, begin, end)
                    sent_entities.append(
                        {
                            "label":"value",
                            "token":token,
                            "start":begin,
                            "end":end
                        }
                    )
                    multi_token_entity = []
                    value_id = None
    print(entity_dict)
    print(relation_dict)
    for param_id, value_id in relation_dict.items():
        (param, begin_p, end_p) = entity_dict[param_id]
        (value, begin_v, end_v) = entity_dict[value_id]
        sent_relations.append(
            {
                "label":"associated_with",
                "param":param,
                "value":value,
                "begin_p":begin_p,
                "end_p":end_p,
                "begin_v":begin_v,
                "end_v":end_v
            }
        )

    return sent_entities, sent_relations

def get_doc_id(folder_name):
    # Regular expression pattern to match digits in the folder names
    pattern = re.compile(r'\d+')

    # Extract digits from the folder name using regular expression
    match = pattern.search(folder_name)
    if match:
        digits = match.group()
        print(f"Folder: {folder_name}, Digits: {digits}")
        return digits


if __name__ == '__main__':
    # Define the path to the main folder
    main_folder = 'mysql_NER_golden/annotation'
    converter(main_folder)