"""
WordNet Synonym Expansion
=========================
Expands query tokens with synonyms from WordNet synsets.
Engineering decision: limit to top-2 synonyms per word, lemma form only,
to avoid excessive noise. Duplicates are removed.

Research basis: research paper cites WordNet as a component for improving
semantic coverage of user queries.
"""
from __future__ import annotations

from typing import List, Set

from nltk.corpus import wordnet


def expand_with_wordnet(lemmas: List[str], max_synonyms: int = 2) -> List[str]:
    """
    Given a list of lemmas, return a deduplicated expanded list
    that includes the original lemmas + WordNet synonyms.
    """
    expanded: List[str] = list(lemmas)
    seen: Set[str] = set(lemmas)

    for lemma in lemmas:
        synsets = wordnet.synsets(lemma)
        count = 0
        for syn in synsets:
            if count >= max_synonyms:
                break
            for syn_lemma in syn.lemmas():
                word = syn_lemma.name().replace("_", " ").lower()
                if word not in seen and word.isalpha():
                    expanded.append(word)
                    seen.add(word)
                    count += 1
                    if count >= max_synonyms:
                        break

    return expanded
