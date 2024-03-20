#!/bin/env python3
import argparse
import json
import logging
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import os
import math
import torch
import wikipedia
import requests
import IPython
from urllib.parse import urlparse, parse_qs, quote_plus, unquote
from IPython.display import HTML
from pyvis.network import Network


# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Initialize the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")


def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_relations_from_model_output(text):
    relations = []
    relation, subject, relation, object_ = '', '', '', ''
    text = text.strip()
    current = 'x'
    text_replaced = text.replace("<s>", "").replace("<pad>", "").replace("</s>", "")
    for token in text_replaced.split():
        if token == "<triplet>":
            current = 't'
            if relation != '':
                relations.append({
                    'head': subject.strip(),
                    'type': relation.strip(),
                    'tail': object_.strip()
                })
                relation = ''
            subject = ''
        elif token == "<subj>":
            current = 's'
            if relation != '':
                relations.append({
                    'head': subject.strip(),
                    'type': relation.strip(),
                    'tail': object_.strip()
                })
            object_ = ''
        elif token == "<obj>":
            current = 'o'
            relation = ''
        else:
            if current == 't':
                subject += ' ' + token
            elif current == 's':
                object_ += ' ' + token
            elif current == 'o':
                relation += ' ' + token
    if subject != '' and relation != '' and object_ != '':
        relations.append({
            'head': subject.strip(),
            'type': relation.strip(),
            'tail': object_.strip()
        })
    return relations


class KB():
    def __init__(self):
        self.relations = []
        self.entities = {}
        # meta: { article_url: { spans: [...] } } ]
        self.sources = {} # { article_url: {...} }

    def are_relations_equal(self, r1, r2):
        return all(r1[attr] == r2[attr] for attr in ["head", "type", "tail"])

    def exists_relation(self, r1):
        return any(self.are_relations_equal(r1, r2) for r2 in self.relations)

    def merge_relations(self, r2):
        r1 = [r for r in self.relations
              if self.are_relations_equal(r2, r)][0]

        # if different article
        article_url = list(r2["meta"].keys())[0]
        if article_url not in r1["meta"]:
            r1["meta"][article_url] = r2["meta"][article_url]

        # if existing article
        else:
            spans_to_add = [span for span in r2["meta"][article_url]["spans"]
                            if span not in r1["meta"][article_url]["spans"]]
            r1["meta"][article_url]["spans"] += spans_to_add

    def get_wikipedia_data(self, candidate_entity):
        try:
            page = wikipedia.page(candidate_entity, auto_suggest=False)
            entity_data = {
                "title": page.title,
                "url": page.url,
                "summary": page.summary
            }
            return entity_data
        except:
            return None

    def add_entity(self, e, article_uuid, article_url, article_date, article_source):
        self.entities[e["title"]] = {
            **{k:v for k,v in e.items() if k != "title"},
            "article_uuid": article_uuid,
            "article_url": article_url,
            "article_date": article_date,
            "article_source": article_source
        }


    def add_relation(self, r, article_title, article_publish_date, article_uuid, article_url, article_source):

        # check on wikipedia
        candidate_entities = [r["head"], r["tail"]]
        entities = [self.get_wikipedia_data(ent) for ent in candidate_entities]

        # if one entity does not exist, stop
        if any(ent is None for ent in entities):
            return

        # manage new entities
        for e in entities:
            self.add_entity(e, article_uuid, article_url, article_publish_date, article_source)

        # rename relation entities with their wikipedia titles
        r["head"] = entities[0]["title"]
        r["tail"] = entities[1]["title"]

        # add source if not in kb
        article_url = list(r["meta"].keys())[0]
        if article_url not in self.sources:
            self.sources[article_url] = {
                "article_title": article_title,
                "article_publish_date": article_publish_date
            }

        # manage new relation
        if not self.exists_relation(r):
            self.relations.append(r)
        else:
            self.merge_relations(r)

    def merge_with_kb(self, kb2):
        for r in kb2.relations:
            article_url = list(r["meta"].keys())[0]
            source_data = kb2.sources[article_url]
            self.add_relation(r, source_data["article_title"],
                              source_data["article_publish_date"])

    def print(self):
        print("Entities:")
        for e in self.entities.items():
            print(f"  {e}")
        print("Relations:")
        for r in self.relations:
            print(f"  {r}")
        print("Sources:")
        for s in self.sources.items():
            print(f"  {s}")

def from_small_text_to_kb(text, verbose=False):
    kb = KB()

    # Tokenizer text
    model_inputs = tokenizer(text, max_length=512, padding=True, truncation=True,
                            return_tensors='pt')
    if verbose:
        print(f"Num tokens: {len(model_inputs['input_ids'][0])}")

    # Generate
    gen_kwargs = {
        "max_length": 216,
        "length_penalty": 0,
        "num_beams": 3,
        "num_return_sequences": 3
    }
    generated_tokens = model.generate(
        **model_inputs,
        **gen_kwargs,
    )

    logging.info("Generated tokens:", generated_tokens)

    decoded_preds = tokenizer.batch_decode(generated_tokens, skip_special_tokens=False)

    logging.info("Decoded predictions:", decoded_preds)

    # create kb
    for sentence_pred in decoded_preds:
        relations = extract_relations_from_model_output(sentence_pred)
        for r in relations:
            kb.add_relation(r)

    return kb

def from_text_to_kb(text, article_url, tokenizer, model, span_length=128, article_title=None, article_publish_date=None, article_uuid=None, article_source=None, verbose=False):

    logging.debug("Starting to process text for KB creation")
    # tokenize whole text
    inputs = tokenizer([text], return_tensors="pt")

    # compute span boundaries
    num_tokens = len(inputs["input_ids"][0])
    if verbose:
        print(f"Input has {num_tokens} tokens")
    num_spans = math.ceil(num_tokens / span_length)
    if verbose:
        print(f"Input has {num_spans} spans")
    overlap = math.ceil((num_spans * span_length - num_tokens) /
                        max(num_spans - 1, 1))
    spans_boundaries = []
    start = 0
    for i in range(num_spans):
        spans_boundaries.append([start + span_length * i,
                                 start + span_length * (i + 1)])
        start -= overlap
    if verbose:
        print(f"Span boundaries are {spans_boundaries}")

    # transform input with spans
    tensor_ids = [inputs["input_ids"][0][boundary[0]:boundary[1]]
                  for boundary in spans_boundaries]
    tensor_masks = [inputs["attention_mask"][0][boundary[0]:boundary[1]]
                    for boundary in spans_boundaries]
    inputs = {
        "input_ids": torch.stack(tensor_ids),
        "attention_mask": torch.stack(tensor_masks)
    }

    # generate relations
    num_return_sequences = 3
    gen_kwargs = {
        "max_length": 256,
        "length_penalty": 0,
        "num_beams": 3,
        "num_return_sequences": num_return_sequences
    }
    generated_tokens = model.generate(
        **inputs,
        **gen_kwargs,
    )

    # decode relations
    print("Generated tokens:", generated_tokens)
    decoded_preds = tokenizer.batch_decode(generated_tokens,
                                           skip_special_tokens=False)
    print("Decoded predictions:", decoded_preds)

    # create kb
    kb = KB()
    i = 0
    for sentence_pred in decoded_preds:
        current_span_index = i // num_return_sequences
        relations = extract_relations_from_model_output(sentence_pred)
        for relation in relations:
            relation["meta"] = {
                article_url: {
                    "spans": [spans_boundaries[current_span_index]]
                }
            }

            kb.add_relation(relation, article_title, article_publish_date, article_uuid, article_url, article_source)

        i += 1

    return kb

def save_network_html(kb, filename="network.html"):
    net = Network(directed=True, width="700px", height="700px", bgcolor="#333333")
    color_entity = "#AAAAAA"
    for e, data in kb.entities.items():
        net.add_node(e, shape="circle", color=color_entity,
                     article_uuid=data.get('article_uuid', ''),
                     article_url=data.get('article_url', ''),
                     article_date=data.get('article_date', ''),
                     article_source=data.get('article_source', ''))
    for r in kb.relations:
        net.add_edge(r["head"], r["tail"], title=r["type"], label=r["type"])
    net.repulsion(node_distance=200, central_gravity=0.2, spring_length=200, spring_strength=0.05, damping=0.09)
    net.set_edge_smooth('dynamic')
    net.save_graph(filename)
    print(f"Network visualization saved to {filename}. Open this file in your web browser to view the network.")




def process_json_file(json_file_path, tokenizer, model):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        article_data = json.load(file)

    # Safely access 'body' and 'url' keys, providing default values if they are missing
    text = article_data.get('body', "")
    article_url = article_data.get('url', "No URL available")
    article_uuid = article_data.get('id', "")
    article_date = article_data.get('date', "")
    article_source = article_data.get('source', "")

    if not text:  # If 'text' is empty (either 'body' was missing or empty in the JSON)
        logging.warning(f"No content found in 'body' for {json_file_path}. Skipping file.")
        return

    logging.debug(f"Processing {json_file_path}...")
    kb = from_text_to_kb(text, article_url, tokenizer, model, verbose=True,
                         article_title=article_data.get('title'),
                         article_publish_date=article_data.get('date'),
                         article_uuid=article_uuid,
                         article_source=article_source)
    kb.print()
    # Generating network visualization for each processed file
    visualization_filename = f"{os.path.splitext(os.path.basename(json_file_path))[0]}_network.html"
    save_network_html(kb, filename=visualization_filename)


def process_directory(directory_path, tokenizer, model):
    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            json_file_path = os.path.join(directory_path, filename)
            process_json_file(json_file_path, tokenizer, model)

def main():
    parser = argparse.ArgumentParser(description='Process a directory of JSON files to extract and visualize knowledge graph.')
    parser.add_argument('directory_path', type=str, help='Path to the directory containing JSON files')
    args = parser.parse_args()

    process_directory(args.directory_path, tokenizer, model)

if __name__ == "__main__":
    main()


