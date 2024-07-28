import os
import re
from collections import defaultdict
import pickle

def converter(main_folder):
    # Iterate through each subfolder in the main folder
    for subfolder in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder)
        doc_id = get_doc_id(subfolder)
        
        # Check if it is indeed a subfolder
        if os.path.isdir(subfolder_path):
            # if not subfolder_path.endswith('pg16'):
            #     continue
            # Iterate through each file in the subfolder
            for file in os.listdir(subfolder_path):
                if file.startswith('INITIAL_CAS'):
                    continue

                file_path = os.path.join(subfolder_path, file)
            
                # Check if it is a file (not a subfolder)
                if os.path.isfile(file_path):
                    print(f"Found file: {file_path}")
                    lines = read_tsv(file_path)
                    passages, passage_idx_tokens_entities_relations_mapping = get_entities_and_relations(lines)
                    print("+++++++++++++++++++++")
                    print(passage_idx_tokens_entities_relations_mapping)
                    print("+++++++++++++++++++++")
                    # print(sent_relations)
                    if len(passage_idx_tokens_entities_relations_mapping) != 0:
                        store_passages_entities_relation(doc_id, passages, passage_idx_tokens_entities_relations_mapping)

                    # input()

def read_tsv(file_path):
    with open(file_path, 'r') as f:
        return f.readlines()

def get_entities_and_relations(lines):
    """
    processed data format:
    sentence = "The capital of the United States is Washington D.C."
    # Golden dataset labels and relations
    golden_labels = ["O", "O", "O", "O", "B-LOC", "I-LOC", "O", "B-LOC", "I-LOC"]
    golden_relations = [(("United States", "B-LOC I-LOC"), "capital", ("Washington D.C.", "B-LOC I-LOC"))]

    # Extraction labels and relations (example extraction)
    extraction_labels = ["O", "O", "O", "O", "B-LOC", "I-LOC", "O", "B-LOC", "I-LOC"]
    extraction_relations = [(("United States", "B-LOC I-LOC"), "capital", ("Washington D.C.", "B-LOC I-LOC"))]
    """
    passages = []
    passage_idx_tokens_entities_relations_mapping = {}
    sent_labels = []
    sent_relations = []
    sent_tokens = []
    # {"label": "PER", "start": 2, "end": 4}
    value_id = None
    begin, end = 0, 0
    entity_dict = {}
    multi_token_entity = []
    relation_dict = defaultdict(list)
    for line in lines:
        # initiate value_id to None
        if len(multi_token_entity) == 0:
            value_id = None
        # print("==>", line)
        
        if line.startswith('#') or len(line.strip()) == 0:
            # print("starts with # or empty line")
            # print("line: ", line)
            # print("entity_dict", entity_dict)
            if line.startswith("#Text"):
                passages.append(line[6:])
            elif len(line.strip()) == 0 and len(sent_tokens) != 0:
                # print("===>>empty")
                # print("entity_dict:", entity_dict)
                # print("relation_dict:", relation_dict)
                for param_id, value_ids in relation_dict.items():
                    for value_id, relation in value_ids:
                        (param, begin_p, end_p) = entity_dict[param_id]
                        (value, begin_v, end_v) = entity_dict[value_id]
                        sent_relations.append((param, relation, value))
                        # print("relation:", (param, relation, value))
                
                if len(sent_tokens) != len(sent_labels):
                    print("#token is inconsistant with #labels")
                    exit()

                # if len(sent_relations) != 0:
                passage_idx_tokens_entities_relations_mapping[len(passages)-1] = (sent_tokens, sent_labels, sent_relations)
                # print((sent_tokens, sent_labels, sent_relations))
                # initializing
                entity_dict = {}
                relation_dict = defaultdict(list)
                sent_tokens = []
                sent_labels = []
                sent_relations = []
            else:
                continue
        else:
            items = line.split()
            # print(items)
            if len(items) < 3: # token is a space
                sent_tokens.append(" ")
            else:
                sent_tokens.append(items[2].strip())
            
            if len(items) <= 3:
                sent_labels.append("O")
                continue
            
            if items[3].strip() != '-' and items[3].strip() != '_':
                print(items)
                if items[3].strip().lower().startswith('value'):
                    if items[3].lower().strip() == 'value':
                        sent_labels.append("B-VALUE")
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
                        # print(str({
                        #         "label":"value",
                        #         "token":token,
                        #         "start":begin,
                        #         "end":end
                        #     }))

                    elif '[' in items[3]:
                        # print("===>>", items)
                        if len(multi_token_entity) == 0:
                            begin = int(items[1].split('-')[0].strip())
                            sent_labels.append("B-VALUE")
                        else:
                            end = int(items[1].split('-')[-1].strip())
                            sent_labels.append("I-VALUE")
                        multi_token_entity.append(items[2].strip())
                        if value_id is None:
                            value_id = items[0].strip()
                            # print("value_id", value_id)

                    # process relation
                    if items[4] != '-' and items[4] != '_':
                        rest_span = " ".join(items[4:])
                        # print("rest_span", rest_span)
                        if '|' in rest_span:
                            # example: 45-5	6076-6077	4	value[6]	Associated With|Associated With	44-5[0_6]|44-7[0_6]	
                            param_relation_spans = rest_span.strip().split('|')
                            for span in param_relation_spans:
                                if '[' in span:
                                    # print("span", span)
                                    param_item_id = span.split()[-1].split('[')[0].strip()
                                    relation = " ".join(span.split()[:-1]).strip()
                                    # print("param_item_id", param_item_id, "value_id", value_id, "relation", relation)
                                    relation_dict[param_item_id].append((value_id, relation))
                                elif '-' in span:
                                    # example: 74-230	11427-11430	16M	value	Associated With|Associated With	74-225|74-227
                                    # print("span", span)
                                    param_item_id = span.split()[-1].strip()
                                    relation = " ".join(span.split()[:-1])
                                    # print("param_item_id", param_item_id)
                                    relation_dict[param_item_id].append((value_id, relation))
                        elif '[' in rest_span:
                            # example: 5-16	2557-2560	50%	value[1]	Associated With	5-11[0_1] 
                            param_item_id = rest_span.strip().split()[-1].split('[')[0].strip()
                            relation = " ".join(rest_span.strip().split()[:-1]).strip()
                            # print("param_item_id", param_item_id, "value_id", value_id, "relation", relation)
                            relation_dict[param_item_id].append((value_id, relation))
                        else:
                            # example: 80-54	9920-9921	5	value	Associated With	80-52
                            # example: 27-7	7134-7135	1	VALUE	EqualTo	27-5
                            param_item_id = rest_span.strip().split()[-1].strip()
                            relation = " ".join(rest_span.strip().split()[:-1]).strip()
                            # print("param_item_id", param_item_id, "value_id", value_id, "relation", relation)
                            relation_dict[param_item_id].append((value_id, relation))
                        # print("relation_dict", relation_dict)
                elif items[3].strip().lower().startswith('param'):
                    sent_labels.append("B-PARAM")
                    item_id = items[0].strip()
                    index = items[1].split('-')
                    begin = int(index[0].strip())
                    end = int(index[1].strip())
                    if len(items[2].strip()) == (end-begin):
                        token = items[2].strip()
                    else:
                        token = items[2].strip()[:end-begin]
                    entity_dict[item_id] = (token, begin, end)
                else:
                    continue
            else:
                sent_labels.append("O")
                if len(multi_token_entity) != 0:
                    token = " ".join(multi_token_entity)
                    # print("===>>>", value_id, token, begin, end)
                    entity_dict[value_id] = (token, begin, end)
                    multi_token_entity = []
                    value_id = None

        # print("passages", len(passages))
        # print("tokens", sent_tokens)
        # print("labels", sent_labels)
    return passages, passage_idx_tokens_entities_relations_mapping

def get_entities_and_relations1(lines):
    """
    input: lines in tsv file
    output:
        passasges: list of passages

        passage_idx_entities_relations_mapping: dict of passage index and corresponding entities and relations mapping
            examples: {passage_idx: (entities, relations)}
            {20: (
                [
                    {'label': 'parameter', 'token': 'max_client_conn', 'start': 9661, 'end': 9676}, 
                    {'label': 'value', 'token': '100', 'start': 9679, 'end': 9682}, 
                    {'label': 'parameter', 'token': 'default_pool_size', 'start': 9797, 'end': 9814}, 
                    {'label': 'value', 'token': '25', 'start': 9817, 'end': 9819}
                ], 
                [
                    {'label': 'EqualTo', 'param': 'max_client_conn', 'value': '100', 'begin_p': 9661, 'end_p': 9676, 'begin_v': 9679, 'end_v': 9682}, 
                    {'label': 'EqualTo', 'param': 'default_pool_size', 'value': '25', 'begin_p': 9797, 'end_p': 9814, 'begin_v': 9817, 'end_v': 9819}
                ]
                )
            }
    """
    passages = []
    passage_idx_entities_relations_mapping = {}
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
            if line.startswith("#Text"):
                passages.append(line[6:])
            elif len(line.strip()) == 0 and len(entity_dict) != 0:
                print(entity_dict)
                print(relation_dict)
                for param_id, (value_id, relation) in relation_dict.items():
                    (param, begin_p, end_p) = entity_dict[param_id]
                    (value, begin_v, end_v) = entity_dict[value_id]
                    sent_relations.append(
                        {
                            "label":relation,
                            "param":param,
                            "value":value,
                            "begin_p":begin_p,
                            "end_p":end_p,
                            "begin_v":begin_v,
                            "end_v":end_v
                        }
                    )
                
                if len(sent_entities) != 0:
                    passage_idx_entities_relations_mapping[len(passages)-1] = (sent_entities, sent_relations)
                
                # initializing
                entity_dict = {}
                relation_dict = {}
                sent_entities = []
                sent_relations = []
            else:
                continue
        else:
            items = line.split()
            # print(items)
            if len(items) <= 3:
                continue
            
            if items[3].strip() != '-' and items[3].strip() != '_':
                print(items)
                if items[3].strip().lower().startswith('value'):
                    if items[3].lower().strip() == 'value':
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
                            # example: 45-5	6076-6077	4	value[6]	Associated With|Associated With	44-5[0_6]|44-7[0_6]	
                            param_relation_spans = rest_span.strip().split('|')
                            for span in param_relation_spans:
                                if '[' in span:
                                    print("span", span)
                                    param_item_id = span.split()[-1].split('[')[0].strip()
                                    relation = " ".join(span.split()[:-1]).strip()
                                    print("param_item_id", param_item_id)
                                    relation_dict[param_item_id] = (value_id, relation)
                                elif '-' in span:
                                    # example: 74-230	11427-11430	16M	value	Associated With|Associated With	74-225|74-227
                                    print("span", span)
                                    param_item_id = span.split()[-1].strip()
                                    relation = " ".join(span.split()[:-1])
                                    print("param_item_id", param_item_id)
                                    relation_dict[param_item_id] = (value_id, relation)
                        elif '[' in rest_span:
                            # example: 5-16	2557-2560	50%	value[1]	Associated With	5-11[0_1] 
                            param_item_id = rest_span.strip().split()[-1].split('[')[0].strip()
                            relation = " ".join(rest_span.strip().split()[:-1]).strip()
                            print("param_item_id", param_item_id)
                            relation_dict[param_item_id] = (value_id, relation)
                        else:
                            # example: 80-54	9920-9921	5	value	Associated With	80-52
                            # example: 27-7	7134-7135	1	VALUE	EqualTo	27-5
                            param_item_id = rest_span.strip().split()[-1].strip()
                            relation = " ".join(rest_span.strip().split()[:-1]).strip()
                            print("param_item_id", param_item_id)
                            relation_dict[param_item_id] = (value_id, relation)

                elif items[3].strip().lower().startswith('param'):
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
                        "label":"parameter",
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

    return passages, passage_idx_entities_relations_mapping

def get_doc_id(folder_name):
    # Regular expression pattern to match digits in the folder names
    pattern = re.compile(r'\d+')

    # Extract digits from the folder name using regular expression
    match = pattern.search(folder_name)
    if match:
        digits = match.group()
        print(f"Folder: {folder_name}, Digits: {digits}")
        return digits

def store_passages_entities_relation(doc_id, passages, passage_idx_entities_relations_mapping):
    # source, destination
    pickle.dump(passages, open(f'postgres_NER_golden/passages_entities_relations/pg{doc_id}_passages', 'wb')) 
    pickle.dump(passage_idx_entities_relations_mapping, open(f'postgres_NER_golden/passages_entities_relations/pg{doc_id}_entities_relations', 'wb'))

if __name__ == '__main__':
    # Define the path to the main folder
    main_folder = 'postgres_NER_golden/annotation'
    converter(main_folder)