import pandas as pd
import pickle
import copy
from collections import defaultdict

def align(extraction_file, passage_mapping_filepath):
    df_extraction = pd.read_csv(extraction_file) # schema: doc_id, passage, recommendation, parameter, value,hint_type
    
    # format: {doc_id: {passage: [(parameter, value, hint_type), ...]}}
    doc_mapping = defaultdict(dict)
    for row_idx, row in df_extraction.iterrows():
        doc_id = int(row['doc_id']) 
        passage = row['passage']
        parameter = row['parameter']
        value = row['value']
        hint_type = row['hint_type']

        if doc_id in doc_mapping.keys():
            if passage in doc_mapping[doc_id].keys():
                doc_mapping[doc_id][passage].append((parameter, value, hint_type))
            else:
                doc_mapping[doc_id][passage] = [(parameter, value, hint_type)]
        else:
            doc_mapping[doc_id] = {passage:[(parameter, value, hint_type)]}
        # print(doc_mapping[doc_id])
        # input()

    ## align
    doc_golden_labels = [] # an element is a list of labels for a passage
    doc_extracted_labels = []
    doc_golden_relations = [] 
    doc_extracted_relations = []
    for doc_id, passages_dbbert in doc_mapping.items():
        # if doc_id != 49:
        #     continue
        print("\n===============================")
        print("doc_id:", doc_id)
        passage_mapping_file = f"{passage_mapping_filepath}pg{doc_id}_map"
        df_passage_mapping = pd.read_csv(passage_mapping_file) # schema: passage_dbbert, passage_ner
        golden_passages = pickle.load(open(f'../demo_docs/postgres_NER_golden/passages_entities_relations/pg{doc_id}_passages', 'rb'))
        passage_idx_tokens_labels_relations = pickle.load(open(f'../demo_docs/postgres_NER_golden/passages_entities_relations/pg{doc_id}_entities_relations', 'rb'))

        
        for passage_dbbert, extractions in passages_dbbert.items():
            passage_ner_list = df_passage_mapping[df_passage_mapping['passage_dbbert'] == passage_dbbert]['passage_ner'].values
            if len(passage_ner_list) == 0:
                print("Cannot find corresponding passage in passage_dbbert and passage_ner mapping")
                print("passage_dbbert:", passage_dbbert)
                continue
            passage_ner = passage_ner_list[0]

            passage_idx = None
            for p_idx, p in enumerate(golden_passages):
                if p.strip() == passage_ner.strip():
                    passage_idx = p_idx
                    break
            if passage_idx is None:
                print("passage_idx is None")
                print("passage_dbbert:", passage_dbbert)
                continue
            # if passage_idx != 408:
            #     continue
            print("\n---------------------------")
            print("passage_idx", passage_idx)
            tokens, labels, relations = passage_idx_tokens_labels_relations[passage_idx]
            print("tokens", tokens)
            print("labels", labels)
            print("relations", relations)
            
            # initializing extracted entities and relations
            extracted_relations = []
            adjusted_golden_labels = copy.copy(labels)
            extracted_labels = ["O"] * len(tokens)
            extracted_entities = []
            unexpected_parameters = []
            unexpected_values = []
            param_found = False
            value_found = False
            for e_idx, (parameter, value, hint_type) in enumerate(extractions):
                extracted_entities.append(parameter)
                extracted_entities.append(copy.copy(value))
                value_copy = copy.copy(value)
                print((parameter, value, hint_type))
                value_started = False
                for t_idx, token in enumerate(tokens):
                    # print("\n=====")
                    # print("token", token)
                    if parameter.strip() == token.strip() and not param_found:
                        extracted_labels[t_idx] = "B-PARAM"
                        param_found = True
                    elif not value_started and value.strip().startswith(token.strip()):
                        value_started = True
                        value = value[len(token.strip()):].strip()
                        extracted_labels[t_idx] = "B-VALUE"
                        value_found = True
                    elif value_started:
                        if len(value) == 0:
                            value_started = False
                        else:
                            extracted_labels[t_idx] = "I-VALUE"
                            value = value[len(token.strip()):].strip()
                    else:
                        continue
                    # print("value_started", value_started)
                    # print("value", value)
                    # print("=====\n")
                
                rel = "RelativeTo"
                if hint_type.strip().startswith("Absolute"):
                    rel = "EqualTo"
                # print(parameter, rel, value_copy)
                extracted_relations.append((parameter, rel, value_copy))

                if not param_found:
                    unexpected_parameters.append(parameter)
                if not value_found:
                    unexpected_values.append(value_copy)
            
                param_found = False
                value_found = False

            for param_entity in unexpected_parameters:
                items = param_entity.split()
                
                adjusted_golden_labels.extend(["O"]*len(items))
                temp_labels = ['I-PARAM']*len(items)
                temp_labels[0] = 'B-PARAM'

                extracted_labels.extend(temp_labels)

            print("\n++++++++++++++++++++++++++")
            print("extrac_labels:", extracted_labels)
            print("golden_labels:", adjusted_golden_labels)
            print("extrac_relations:", extracted_relations)
            print("golden_relations:", relations)
            doc_extracted_labels.append(extracted_labels)
            doc_golden_labels.append(adjusted_golden_labels)
            doc_extracted_relations.append(extracted_relations)
            doc_golden_relations.append(relations)
            print("++++++++++++++++++++++++\n")

            input()
                
if __name__ == '__main__':
    extraction_file = "../demo_docs/extracted_hints.csv"
    passage_mapping_filepath = "./postgres_documents/"
    align(extraction_file, passage_mapping_filepath)


