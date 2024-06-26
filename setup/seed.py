import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

outputDirectory = Path(__file__).absolute().parent.parent

# Paramètres initiaux
BASE_URL = "http://api.conceptnet.io/query"
LANGUAGES = ["en", "fr"]
FACTS_PER_LANG = 50  # Nombre de faits à récupérer par langue
MIN_CONCEPTS_PER_LANG = 20  # Nombre minimum de concepts par langue
MIN_RELATIONS = 10  # Nombre minimum de relations


def get_facts_by_lang(lang, required_concepts, existing_relations, existing_facts):
    facts = []
    concepts = []
    relations = set(existing_relations)
    offset = 0

    while len(facts) < FACTS_PER_LANG or len(concepts) < required_concepts or len(relations) < MIN_RELATIONS:
        params = {
            "start": f"/c/{lang}",
            "limit": 50,
            "offset": offset,
            "end": f"/c/{lang}"

        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        for edge in data['edges']:
            start_label = edge['start']['label']
            end_label = edge['end']['label']

            start_term = edge['start']['term'] #Pour obtenir le nom du concept tel que dans l'URL API
            start_term = start_term[6:]

            end_term = edge['end']['term']
            end_term = end_term[6:]

            relation = edge['rel']['label']
            if edge['start']['language'] == lang and edge['end']['language'] == lang:
                if (start_label, relation, end_label) not in existing_facts:
                    facts.append((start_label, start_term, relation, end_label, end_term, lang))
                    concepts.append((start_label, start_term))
                    concepts.append((end_label, end_term))
                    relations.add(relation)
        offset += 50
        if offset > 1000:  # Limite pour éviter une boucle infinie en cas de contraintes non satisfaisables
            break

    return facts, concepts, relations


def generate_html_table(facts):
    soup = BeautifulSoup('', 'html.parser')
    table = soup.new_tag('table')
    for fact in facts:
        row = soup.new_tag('tr')
        for item in fact:
            cell = soup.new_tag('td')
            cell.string = item
            row.append(cell)
        table.append(row)
    soup.append(table)
    return soup.prettify()


def save_data(facts):
    JSONOutputPath = outputDirectory / "app" / "facts_data.json"
    with open(JSONOutputPath, "w") as f:
        json.dump(facts, f)


# Collecter les faits pour chaque langue en respectant les contraintes
all_facts = []
all_concepts = []
all_relations = set()

for lang in LANGUAGES:
    new_facts, new_concepts, new_relations = get_facts_by_lang(lang, MIN_CONCEPTS_PER_LANG, all_relations, all_facts)
    all_facts += new_facts
    all_concepts += new_concepts
    all_relations.update(new_relations)

# Générer et écrire la table HTML dans un fichier
html_table = generate_html_table(all_facts)
HTMLOutputPath = outputDirectory / "app" / "conceptnet_facts.html"
with open(HTMLOutputPath, "w", encoding="utf-8") as file:
    file.write(html_table)
save_data(all_facts)

print("Finit!")
