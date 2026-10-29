"""Syntax / dependency parser: stage 4 of the pipeline.

Deliberately shallow and honest: Latin word order is free, so this
parser does not pretend to build a full dependency tree. It finds
what the roadmap asks for, with the rule it used, so a reader can
check it:

- nominative subject: a nominative noun/pronoun/adjective whose
  number agrees with a 3rd-person finite verb, or an implied pronoun
  for 1st/2nd-person verbs (ego/tu/nos/vos are usually omitted)
- accusative direct object: an accusative noun/pronoun not governed
  by a preceding preposition (ad/in/per/ob + accusative is a
  prepositional phrase, not a direct object)
- ablative constructions: an ablative token, classified by its
  preposition if any, or as an ablative absolute when a noun and a
  participle share ablative case + gender + number, otherwise as
  ablative of means / instrument / separation (context decides
  between those three, and the parser says so)

Vocative is not a subject: a nominative-looking token followed by
a comma before an imperative (Musa, memora) is an address.
"""

from __future__ import annotations

from .schemas import (
    AblativeConstruction,
    IndirectStatement,
    ParseResponse,
    PrepositionalPhrase,
    TokenAnalysis,
    TokenResult,
)

ACC_PREPS = {"ad", "in", "per", "ob", "circum", "contra", "inter", "sub", "trans", "super"}
ABL_PREPS = {"ab", "a", "cum", "sine", "pro", "in", "de", "ex", "e", "sub"}
TIME_LEMMAS = {"annus", "dies", "tempus", "hora", "nox", "mensis", "aetas", "saeculum"}
PLACE_LEMMAS = {"locus", "aequor", "terra", "mare", "campus", "mens", "orbis"}
ABL_PREP_KIND = {
    "ab": "ablative of separation / agent",
    "a": "ablative of separation / agent",
    "cum": "ablative of accompaniment",
    "sine": "ablative of separation (privation)",
    "pro": "ablative of behalf / in front of",
    "in": "ablative of place where",
    "sub": "ablative of place where / under",
    "de": "ablative of concerning / down from",
    "ex": "ablative of separation (out of)",
    "e": "ablative of separation (out of)",
}


def _best(token: TokenResult) -> TokenAnalysis | None:
    """Best analysis, preferring finite-verb and case-marked readings."""
    if not token.analyses:
        return None
    return token.analyses[0]


def _has(token: TokenResult, **kwargs) -> TokenAnalysis | None:
    for a in token.analyses:
        if all(getattr(a, k, None) == v for k, v in kwargs.items()):
            return a
    return None


def parse_tokens(text: str, tokens: list[TokenResult]) -> ParseResponse:
    words = [t for t in tokens if t.analyses or t.original.strip() not in (",", ";", ":", ".", "!", "?")]
    # main verb: first finite verb (indicative/subjunctive/imperative)
    verb: TokenAnalysis | None = None
    verb_idx = -1
    for i, t in enumerate(tokens):
        if i > 0:
            prev = _best(tokens[i - 1])
            if prev and prev.pos == "preposition":
                continue
        for a in t.analyses:
            if a.pos == "verb" and a.mood in ("indicative", "subjunctive", "imperative") and a.person:
                verb = a
                verb_idx = i
                break
        if verb:
            break

    subject: list[str] = []
    subject_expl = ""
    used_indices: set[int] = set()
    if verb_idx >= 0:
        used_indices.add(verb_idx)
    # Vocative address (Musa, memora): a token followed by a comma before
    # an imperative is an address, never a subject, object, or ablative.
    if verb and verb.mood == "imperative":
        for i, t in enumerate(tokens):
            if i + 1 < len(tokens) and tokens[i + 1].original == "," and _has(t, case="vocative"):
                used_indices.add(i)
    if verb:
        if verb.person in ("1", "2"):
            implied = {"1": "ego (implied, 1st person)", "2": "tu (implied, 2nd person)"}[verb.person]
            if verb.number == "plural":
                implied = {"1": "nos (implied, 1st person plural)", "2": "vos (implied, 2nd person plural)"}[verb.person]
            subject = [implied]
            subject_expl = f"Verb {verb.form} is {verb.person} person, so the subject is the implied pronoun, not a nominative noun in the sentence."
        else:
            # 3rd person: nominative agreeing in number
            for i, t in enumerate(tokens):
                # vocative address: nominative form + following comma + imperative verb
                if verb.mood == "imperative" and i + 1 < len(tokens) and tokens[i + 1].original == ",":
                    continue
                a = _has(t, case="nominative")
                if a and a.number == verb.number and a.pos in ("noun", "pronoun", "adjective"):
                    subject.append(t.original)
                    used_indices.add(i)
                    break
            if subject:
                subject_expl = f"Nominative {subject[0]} agrees in number ({verb.number}) with 3rd-person verb {verb.form}."
            else:
                subject_expl = "No nominative token agreeing with the verb was found; the subject may be in another clause (common in poetry) or implied."
    else:
        subject_expl = "No finite verb found; no subject can be assigned."

    # prepositional phrases with accusative (e.g., "per annos", "multosque per annos", "ad urbem")
    prepositional_phrases: list[PrepositionalPhrase] = []
    for i, t in enumerate(tokens):
        if i in used_indices:
            continue
        t_prep = None
        for a in t.analyses:
            if a.pos == "preposition" and a.lemma.lower() in ACC_PREPS:
                t_prep = a
                break
        if not t_prep:
            continue

        prep_lemma = t_prep.lemma.lower()
        phrase_indices = [i]
        governed_tok = None

        # Look ahead for governed accusative token
        j = i + 1
        while j < len(tokens) and j <= i + 2:
            if j in used_indices:
                j += 1
                continue
            acc_a = _has(tokens[j], case="accusative")
            if acc_a:
                phrase_indices.append(j)
                governed_tok = tokens[j]
                if acc_a.pos in ("noun", "pronoun"):
                    break
            else:
                break
            j += 1

        # Look behind for anastrophe / hyperbaton modifier (e.g. "multosque per annos")
        if i > 0 and (i - 1) not in used_indices:
            prev_tok = tokens[i - 1]
            prev_a = _has(prev_tok, case="accusative")
            if prev_a and prev_a.pos in ("adjective", "noun", "pronoun"):
                phrase_indices.insert(0, i - 1)

        if governed_tok:
            for idx in phrase_indices:
                used_indices.add(idx)

            gov_a = _has(governed_tok, case="accusative")
            gov_lemma = (gov_a.lemma or "").lower() if gov_a else ""

            if prep_lemma == "per" and gov_lemma in TIME_LEMMAS:
                kind = "accusative of duration under per"
                explanation = (
                    f"per + accusative {governed_tok.original} expresses duration of time "
                    f"('through/for {governed_tok.original}'), not a direct object or ablative of time."
                )
            else:
                kind = f"prepositional phrase ({prep_lemma} + accusative)"
                explanation = f"{prep_lemma} + accusative {governed_tok.original}."

            prepositional_phrases.append(
                PrepositionalPhrase(
                    tokens=[tokens[idx].original for idx in phrase_indices],
                    preposition=prep_lemma,
                    case="accusative",
                    kind=kind,
                    explanation=explanation,
                )
            )

    # direct object: accusative, not after an accusative preposition
    objects: list[str] = []
    for i, t in enumerate(tokens):
        if i in used_indices:
            continue
        a = _has(t, case="accusative")
        if not a or a.pos not in ("noun", "pronoun", "adjective"):
            continue
        prev_lemma = None
        if i > 0:
            prev = _best(tokens[i - 1])
            if prev and prev.pos == "preposition":
                prev_lemma = prev.lemma.lower()
        if prev_lemma in ACC_PREPS:
            continue
        objects.append(t.original)
        used_indices.add(i)
    object_expl = ""
    if objects:
        object_expl = f"Accusative {', '.join(objects)} not governed by a preposition, so read as direct object(s) of {verb.form if verb else 'the verb'}."
    elif verb:
        object_expl = "No ungoverned accusative found; the verb may be intransitive, copular, or its object may be in another clause."

    # ablatives
    ablatives: list[AblativeConstruction] = []
    used: set[int] = set(used_indices)
    for i, t in enumerate(tokens):
        if i in used:
            continue
        a = _has(t, case="ablative")
        if not a:
            continue
        prev_lemma = None
        if i > 0:
            prev = _best(tokens[i - 1])
            if prev and prev.pos == "preposition":
                prev_lemma = prev.lemma.lower()
        if prev_lemma in ABL_PREPS:
            abl_kind = ABL_PREP_KIND.get(prev_lemma, "ablative with preposition")
            abl_expl = f"{prev_lemma} + ablative {t.original}."
            ablatives.append(AblativeConstruction(
                tokens=[tokens[i - 1].original, t.original],
                kind=abl_kind,
                explanation=abl_expl))
            prepositional_phrases.append(PrepositionalPhrase(
                tokens=[tokens[i - 1].original, t.original],
                preposition=prev_lemma,
                case="ablative",
                kind=abl_kind,
                explanation=abl_expl))
            used.add(i)
            continue
        # ablative absolute: ablative noun + ablative participle, same gender/number
        for j in range(max(0, i - 2), min(len(tokens), i + 3)):
            if j == i or j in used:
                continue
            b = _has(tokens[j], case="ablative")
            if b and b.mood == "participle" and b.gender == a.gender and b.number == a.number:
                pair = [t.original, tokens[j].original] if i < j else [tokens[j].original, t.original]
                ablatives.append(AblativeConstruction(
                    tokens=pair,
                    kind="ablative absolute",
                    explanation="Noun + participle both in the ablative, grammatically detached from the main clause."))
                used.add(i); used.add(j)
                break
        else:
            lem = (a.lemma or "").lower()
            has_modifier = False
            for adj_i in (i - 1, i + 1):
                if 0 <= adj_i < len(tokens):
                    adj_a = _has(tokens[adj_i], case="ablative")
                    if adj_a and getattr(adj_a, "lemma", "").lower() in ("totus", "altus"):
                        has_modifier = True
                        break
            if lem in TIME_LEMMAS:
                ablatives.append(AblativeConstruction(
                    tokens=[t.original],
                    kind="ablative of time (when / within which)",
                    explanation=f"Ablative {t.original} indicates time when or within which."))
            elif lem in PLACE_LEMMAS or has_modifier:
                ablatives.append(AblativeConstruction(
                    tokens=[t.original],
                    kind="ablative of place where",
                    explanation=f"Ablative {t.original} expresses poetic place where without a preposition."))
            else:
                ablatives.append(AblativeConstruction(
                    tokens=[t.original],
                    kind="ablative of means / instrument / separation",
                    explanation="Bare ablative with no preposition. Means, instrument, manner and separation share this form; context decides which."))

    # indirect statement (accusative-plus-infinitive / oratio obliqua)
    indirect_statements: list[IndirectStatement] = []
    for inf_idx, t in enumerate(tokens):
        inf_a = None
        for a in t.analyses:
            if a.pos == "verb" and a.mood == "infinitive":
                inf_a = a
                break
        if not inf_a:
            continue
        acc_tok = None
        for acc_i, at in enumerate(tokens):
            if acc_i == inf_idx:
                continue
            acc_a = _has(at, case="accusative")
            if acc_a and acc_a.pos in ("noun", "pronoun", "adjective"):
                acc_tok = at
                break
        if acc_tok:
            indirect_statements.append(IndirectStatement(
                subject_accusative=acc_tok.original,
                infinitive=t.original,
                head_verb=verb.form if verb else None,
                explanation=f"Accusative subject '{acc_tok.original}' with infinitive '{t.original}' forming an indirect statement (accusative-plus-infinitive)."
            ))

    return ParseResponse(text=text, verb=verb, subject=subject,
                         subject_explanation=subject_expl,
                         direct_object=objects, object_explanation=object_expl,
                         ablatives=ablatives,
                         indirect_statements=indirect_statements,
                         prepositional_phrases=prepositional_phrases,
                         tokens=tokens)
