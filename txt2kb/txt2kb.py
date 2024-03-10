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
from urllib.parse import urlparse, urlunparse
import IPython
from IPython.display import HTML
from pyvis.network import Network

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

#def get_article(url):
#    article = Article(url)
#    article.download()
#    article.parse()
#    return article

class Article:
    def __init__(self, title, text):
        self.title = title
        self.text = text

def get_article(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        # Send a request to the URL
        response = requests.get(url, headers=headers)
        # Raise an HTTPError exception for bad requests (4XX or 5XX)
        response.raise_for_status()

        # Parse the content of the response using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the article title and text
        # Note: You may need to adjust the selectors depending on the site's structure
        title = soup.find('h1').get_text(strip=True)
        # Assuming the main content of the article is within <p> tags
        # Adjust the selector as necessary for different sites
        text = ' '.join(p.get_text(strip=True) for p in soup.find_all('p'))

        # Return an Article object with the title and text
        return Article(title, text)

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Oops: Something Else: {err}")
    # Return None or raise an exception if you prefer to handle it upstream
    return None

def clean_url(url):
    parsed_url = urlparse(url)
    cleaned_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", ""))
    return cleaned_url

def from_url_to_kb(url, tokenizer, model):
    article = get_article(url)
    if article is None:
        print(f"Failed to fetch or parse article from {url}")
        return None  # Or handle the error as appropriate for your use case

    # Assuming `get_article` returns an article object with attributes `title`, `text`, and possibly `publish_date`.
    # If `publish_date` is not part of your Article class, remove it from the config.
    config = {
        "article_title": article.title,
        # Ensure your Article class or the return value of get_article includes 'publish_date' if you use it here
        "article_publish_date": getattr(article, 'publish_date', None)  # Use None as default if not available
    }

    # It's crucial that from_text_to_kb is defined to accept these config values correctly
    kb = from_text_to_kb(article.text, article.url, tokenizer, model, **config)
    return kb

#def from_url_to_kb(url, tokenizer, model):
#    article = get_article(url)
#    config = {
#        "article_title": article.title,
#        "article_publish_date": article.publish_date
#    }
#    # Pass tokenizer and model as arguments to from_text_to_kb
#    kb = from_text_to_kb(article.text, article.url, tokenizer, model, **config)
#    return kb

def get_news_links(query, lang="en", region="US", pages=1, max_links=100000):
    googlenews = GoogleNews(lang=lang, region=region)
    googlenews.search(query)
    all_urls = []
    for page in range(pages):
        googlenews.get_page(page)
        all_urls += googlenews.get_links()
    return list(set(all_urls))[:max_links]

def from_urls_to_kb(news_links, tokenizer, model, verbose=False):
    main_kb = KB()  # Assuming initialization of your KB object
    for url in news_links:
        cleaned_url = clean_url(url)  # Use a different variable name for the cleaned URL
        if verbose:
            print(f"Visiting {cleaned_url}...")
        try:
            kb_article = from_url_to_kb(cleaned_url, tokenizer, model)  # Use cleaned_url here
            if kb_article:
                main_kb.merge_with_kb(kb_article)
            else:
                print(f"Failed to process {cleaned_url}, received None")
        except Exception as e:
            print(f"An error occurred while processing {cleaned_url}: {e}")
    return main_kb

#def from_urls_to_kb(news_links, tokenizer, model, verbose=False):
#    main_kb = KB()  # Assuming initialization of your KB object
#    for url in news_links:
#        clean_url = clean_url(url)  # Clean the URL
#        if verbose:
#            print(f"Visiting {clean_url}...")
#        try:
#            kb_article = from_url_to_kb(clean_url, tokenizer, model)
#            if kb_article:
#                main_kb.merge_with_kb(kb_article)
#            else:
#                print(f"Failed to process {clean_url}, received None")
#        except Exception as e:
#            print(f"An error occurred while processing {clean_url}: {e}")
#    return main_kb

#def from_urls_to_kb(news_links, tokenizer, model, verbose=False):
#    main_kb = KB()  # Assuming this is your main KB object initialization
#    if verbose:
#        print(f"{len(news_links)} links to visit")
#    for url in news_links:
#        if verbose:
#            print(f"Visiting {url}...")
#        try:
#            kb_url = from_url_to_kb(url, tokenizer, model)
#            if kb_url is not None:  # Only merge if kb_url is not None
#                main_kb.merge_with_kb(kb_url)
#            else:
#                if verbose:
#                    print(f"Failed to process {url}, received None")
#        except Exception as e:  # Broad exception handling, consider specifying exception types
#            if verbose:
#                print(f"An error occurred while processing {url}: {e}")
#    return main_kb

#def from_urls_to_kb(urls, tokenizer, model, verbose=False):
#    kb = KB()
#    if verbose:
#        print(f"{len(urls)} links to visit")
#    for url in urls:
#        if verbose:
#            print(f"Visiting {url}...")
#        try:
#            # Now passing tokenizer and model as arguments
#            kb_url = from_url_to_kb(url, tokenizer, model)
#            kb.merge_with_kb(kb_url)
#        except ArticleException:
#            if verbose:
#                print(f"  Couldn't download article at url {url}")
#    return kb
#

# Instead of IPython.display.HTML(filename=filename)
# Just inform the user that the file has been saved and can be viewed in a browser

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

