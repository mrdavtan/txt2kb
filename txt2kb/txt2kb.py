#!/bin/env python3
import argparse
import logging
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import math
import torch
import wikipedia
from newspaper import Article, ArticleException
from GoogleNews import GoogleNews
import requests
from bs4 import BeautifulSoup
import IPython
from urllib.parse import urlparse, parse_qs, quote_plus, unquote
from IPython.display import HTML
from pyvis.network import Network
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry



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

    def add_entity(self, e):
        self.entities[e["title"]] = {k:v for k,v in e.items() if k != "title"}

    def add_relation(self, r, article_title, article_publish_date):
        # check on wikipedia
        candidate_entities = [r["head"], r["tail"]]
        entities = [self.get_wikipedia_data(ent) for ent in candidate_entities]

        # if one entity does not exist, stop
        if any(ent is None for ent in entities):
            return

        # manage new entities
        for e in entities:
            self.add_entity(e)

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


def from_text_to_kb(text, article_url, tokenizer, model, span_length=128, article_title=None, article_publish_date=None, verbose=False):

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
            kb.add_relation(relation, article_title, article_publish_date)
        i += 1

    return kb


def from_url_to_kb(url, tokenizer, model):
    # First, try to directly fetch the article
    article = get_article(url)

    # If direct fetch fails, attempt to fetch via Google search fallback
    if article is None:
        print(f"Direct fetch failed for {url}, attempting Google search fallback.")
        fallback_url = search_google_for_article("Extracted search terms from URL")  # Implement this
        if fallback_url:
            article = get_article(fallback_url)  # Try fetching the article from the fallback URL
            if article is None:
                print(f"Failed to fetch article from {url} even after Google search fallback.")
                return None
        else:
            print(f"No fallback URL found for {url}.")
            return None

    # Proceed with processing if the article is successfully fetched
    config = {
        "article_title": article.title,
        "article_publish_date": getattr(article, 'publish_date', None)  # Appropriately handle publish_date
    }

    # Use the fetched article to build the KB
    kb = from_text_to_kb(article.text, url, tokenizer, model, **config)
    return kb


def from_urls_to_kb(news_links, tokenizer, model, verbose=False):
    kb = KB()  # Assuming initialization of your KB object
    for url in news_links:
        if verbose:
            print(f"Visiting {url}...")

        # Attempt to fetch the article using the direct method or fallback to Google search
        article = get_article_with_fallback(url)
        if article:
            # If article fetching was successful, process and add it to the KB
            config = {
                "article_title": article.title,
                "article_publish_date": getattr(article, 'publish_date', None)  # Handle publish_date appropriately
            }
            # Use the fetched article's text and other details to build part of the KB
            kb_article = from_text_to_kb(article.text, url, tokenizer, model, **config)
            if kb_article:
                kb.merge_with_kb(kb_article)
            else:
                if verbose:
                    print(f"Failed to process article from {url}.")
        else:
            if verbose:
                print(f"Failed to fetch article from {url}.")

    return kb


#####################################################
class Article:
    def __init__(self, title, text, url):
        self.title = title
        self.text = text
        self.url = url

def fetch_article(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error while fetching article: {e}")
    return None

def parse_article(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'No Title Found'
    text = ' '.join(p.get_text(strip=True) for p in soup.find_all('p'))
    return Article(title, text, url)

def search_google_for_article(query):
    search_url = f"https://www.google.com/search?q={quote_plus(query)}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if "url?q=" in href and not href.startswith("/url?q=https://maps.google.com"):
                clean_href = unquote(href.split("url?q=")[-1].split("&")[0])
                return clean_href
    except Exception as e:
        print(f"Failed to search Google for {query}: {e}")
    return None


def get_news_links(query, pages=1, max_links=20):
    googlenews = GoogleNews()
    googlenews.search(query)
    result_links = []

    for page in range(pages):
        googlenews.get_page(page)
        for result in googlenews.results():
            if len(result_links) < max_links:
                result_links.append(result['link'])
            else:
                break
        if len(result_links) >= max_links:
            break

    return result_links[:max_links]

def get_article_with_fallback(original_url):
    article_content = fetch_article(original_url)
    if article_content:
        return parse_article(article_content, original_url)

    # Extract search terms from the original URL
    search_terms = extract_search_terms(original_url)
    new_url = search_google_for_article(search_terms)
    if new_url:
        article_content = fetch_article(new_url)
        if article_content:
            return parse_article(article_content, new_url)
    return None

def extract_search_terms(url):
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split('/')
    meaningful_segments = [segment for segment in path_segments if segment and not segment.isdigit() and '.' not in segment]
    search_terms = ' '.join([unquote(segment).replace('-', ' ') for segment in meaningful_segments])
    return search_terms
###################################################################


def save_network_html(kb, filename="network.html"):
    # create network
    net = Network(directed=True, width="700px", height="700px", bgcolor="#eeeeee")

    # nodes
    color_entity = "#00FF00"
    for e in kb.entities:
        net.add_node(e, shape="circle", color=color_entity)

    # edges
    for r in kb.relations:
        net.add_edge(r["head"], r["tail"], title=r["type"], label=r["type"])

    # save network
    net.repulsion(node_distance=200, central_gravity=0.2, spring_length=200, spring_strength=0.05, damping=0.09)
    net.set_edge_smooth('dynamic')
    net.save_graph(filename)
    print(f"Network visualization saved to {filename}. Open this file in your web browser to view the network.")    #net.show(filename)


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("urllib3").setLevel(logging.WARNING)

tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")


#Single URL source
#url = "https://finance.yahoo.com/news/microstrategy-bitcoin-millions-142143795.html"
#kb = from_url_to_kb(url)
#kb.print()

#Multi URL source Search
#news_links = get_news_links("Google", pages=1, max_links=3)
#kb = from_urls_to_kb(news_links, verbose=True)
#kb.print()

# Example usage

# Visualize Multi URL source
news_links = get_news_links("Google", pages=5, max_links=20)
kb = from_urls_to_kb(news_links, tokenizer, model, verbose=True)

filename = "network_3_google.html"
save_network_html(kb, filename=filename)

# Inform the user that the visualization is available
print(f"Network visualization saved to {filename}. Open this file in your web browser to view the network.")



def main():

    try:

        # Define command line arguments
        parser = argparse.ArgumentParser(description='Extract knowledge base from text in a file.')
        parser.add_argument('file_path', type=str, help='Path to the text file to be processed')
        parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')
        args = parser.parse_args()

        # Configure logging based on the verbose argument
        if args.verbose:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        else:
            # Only log warnings and above if not in verbose mode
            logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

        # Reading text from the file
        text = read_text_from_file(args.file_path)  # Direct use of 'text' as per function expectations
        logging.debug("Text successfully read from the file.")
        #logging.debug("text= ", text)

        relations = extract_relations_from_model_output(text)
        logging.debug(f"Extracted {len(relations)} relations from the text.")

        # Process the text to extract knowledge base
        kb = from_text_to_kb(article.text, article.url, tokenizer, model, **config)


        kb.print()

    except Exception as e:
        #print(f"Error: {e}")
        logging.error(f"Error: {e}", exc_info=True)
        raise  # This will print the stack trace.

if __name__ == "__main__":
    main()

