# TXT2KB Utility

The TXT2KB utility is designed to facilitate the creation of knowledge bases (KBs) and graphs from article databases, leveraging advanced natural language processing techniques to extract and organize information systematically.

## Features

- **Knowledge Base Creation**: Automate the extraction of structured information from textual data to build comprehensive knowledge bases.
- **Graph Generation**: Transform extracted information into graphical representations, enabling intuitive analysis and insights.

## Reference Material

This utility is inspired by and builds upon cutting-edge research in the field of Relation Extraction. Specifically, it references the paper titled "RED: A Filtered Multilingual Relation Extraction Dataset," published in June 2023 on arXiv (ID: 2306.09802). The methodologies and datasets described in this paper have been instrumental in the development of this tool.

For practical application examples and a deeper understanding of the concepts utilized in this utility, please refer to the following article on Medium: [Building a Knowledge Base from Texts: A Full Practical Example](https://medium.com/nlplanet/building-a-knowledge-base-from-texts-a-full-practical-example-8dbbffb912fa).

## Getting Started

### 1. Prerequisites

It is recommended to use a virtual environment (venv) for managing dependencies and isolating the project setup. This approach ensures that the project does not interfere with your global Python setup and vice versa.

### 2. Installation Steps

#### 2.1 Clone the Repository

Begin by cloning this repository to your local machine.

```bash
git clone https://github.com/mrdavtan/txt2kb.git
cd txt2kb
```

#### 2.2 Setup a Virtual Environment

Create and activate a virtual environment in the project directory to manage dependencies more effectively and isolate the project environment.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

#### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

This will install essential libraries such as torch, torchvision, and lxml, as well as the custom-forked wikipedia package tailored for this project, which addresses specific issues such as the 'beautifulsoup_warning_fix' branch.

#### 2.3 Testing

run the example txt2kb.py in the test folder and see the printed output.
```bash
python3 txt2kb.py
```

This should print the following:

```bash

Input has 726 tokens
Input has 6 spans
Span boundaries are [[0, 128], [119, 247], [238, 366], [357, 485], [476, 604], [595, 723]]
Entities:
  ('Napoleon', {'url': 'https://en.wikipedia.org/wiki/Napoleon', 'summary': "Napoleon Bonaparte (born Napoleone di Buonaparte; 15 August 1769 – 5 May 1821), later known by his regnal name Napoleon...

... artificial hill constructed from earth taken from the battlefield itself, but the topography of the battlefield near the mound has not been preserved.'})
Relations:
  {'head': 'Napoleon', 'type': 'participant in', 'tail': 'French Revolution', 'meta': {'spans': [[0, 128], [119, 247]]}}
  {'head': 'French Revolution', 'type': 'participant', 'tail': 'Napoleon', 'meta': {'spans': [[0, 128]]}}
  {'head': 'French Revolution', 'type': 'country', 'tail': 'France', 'meta': {'spans': [[0, 128]]}}
  {'head': 'Napoleon', 'type': 'place of birth', 'tail': 'Corsica', 'meta': {'spans': [[119, 247]]}}
  {'head': 'French Directory', 'type': 'facet of', 'tail': 'French Revolution', 'meta': {'spans': [[119, 247]]}}
  {'head': 'War of the Fourth Coalition', 'type': 'start time', 'tail': '1806', 'meta': {'spans': [[238, 366]]}}
  {'head': 'Ulm campaign', 'type': 'part of', 'tail': 'War of the Third Coalition', 'meta': {'spans': [[238, 366]]}}
  {'head': 'Battle of Austerlitz', 'type': 'part of', 'tail': 'War of the Third Coalition', 'meta': {'spans': [[238, 366]]}}
  {'head': 'War of the Third Coalition', 'type': 'start time', 'tail': '1805', 'meta': {'spans': [[238, 366]]}}
  {'head': 'Battle of Wagram', 'type': 'part of', 'tail': 'War of the Fifth Coalition', 'meta': {'spans': [[357, 485]]}}
  {'head': 'War of the Fourth Coalition', 'type': 'followed by', 'tail': 'War of the Fifth Coalition', 'meta': {'spans': [[357, 485]]}}
  {'head': 'War of the Sixth Coalition', 'type': 'start time', 'tail': '1813', 'meta': {'spans': [[476, 604]]}}
  {'head': 'Hundred Days', 'type': 'has part', 'tail': 'Battle of Waterloo', 'meta': {'spans': [[595, 723]]}}
  {'head': 'Battle of Waterloo', 'type': 'part of', 'tail': 'Hundred Days', 'meta': {'spans': [[595, 723]]}}

```

### 3. Usage Instructions

The `txt2kb.py` utility is designed to be executed with a command-line argument that specifies the text chunk to be processed. This allows for flexible and direct invocation of the utility for generating knowledge bases and graphs from specified textual data.

## Running the Script

To use the `txt2kb.py` utility, run it from the command line, providing the path to the text chunk as an argument. Here’s a basic example of how to execute the script:

```bash
python txt2kb.py /path/to/your/text/chunk.txt


