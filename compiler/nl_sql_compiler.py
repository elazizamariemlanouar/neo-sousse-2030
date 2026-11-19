"""
compiler/nl_sql_compiler.py
NL → SQL Compiler for Smart City Neo-Sousse 2030

Pipeline:
  Input (NL string)
    → Lexer        (tokenisation)
    → Parser       (syntactic analysis + grammar)
    → AST          (Abstract Syntax Tree)
    → SQLGenerator (code generation)
    → SQL string

Grammaire (simplifiée BNF):
  query       ::= afficher_clause | compter_clause | donner_clause
  afficher_clause ::= ("affiche" | "montre" | "liste") [limit_clause] entity [condition_clause] [order_clause]
  compter_clause  ::= ("combien" | "nombre") [de_clause] entity [condition_clause]
  donner_clause   ::= ("donne" | "trouve") entity [condition_clause] [order_clause]
  entity      ::= TOKEN_ENTITY
  condition_clause ::= ("où" | "qui" | "avec" | "ayant" | "dont") field comparator value
  order_clause ::= ("classés" | "triés" | "ordonné") "par" field [("asc"|"desc")]
  limit_clause ::= "les" NUMBER (("plus" | "premiers") | "derniers")?
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional, List, Any
from enum import Enum, auto


# ══════════════════════════════════════════════════════════════
# TOKEN TYPES
# ══════════════════════════════════════════════════════════════
class TokenType(Enum):
    # Keywords — verbs
    AFFICHER   = auto()   # affiche, montre, liste, afficher
    COMPTER    = auto()   # combien, nombre, compter
    DONNER     = auto()   # donne, trouve, donner
    # Keywords — structure
    LES        = auto()   # les, des
    DE         = auto()   # de, d'
    PAR        = auto()   # par
    OU         = auto()   # où, qui, avec, ayant, dont
    ORDONNER   = auto()   # classés, triés, ordonné, order
    PLUS       = auto()   # plus (+ adj like pollués, récents)
    ASC        = auto()   # asc, croissant
    DESC       = auto()   # desc, décroissant
    # Entities
    ENTITY     = auto()
    # Fields
    FIELD      = auto()
    # Comparators
    GT         = auto()   # >, supérieur, plus grand
    LT         = auto()   # <, inférieur, plus petit
    GTE        = auto()   # >=
    LTE        = auto()   # <=
    EQ         = auto()   # =, est, égal
    # Values
    NUMBER     = auto()
    STRING     = auto()
    # Meta
    EOF        = auto()
    UNKNOWN    = auto()


# ══════════════════════════════════════════════════════════════
# TOKEN
# ══════════════════════════════════════════════════════════════
@dataclass
class Token:
    type: TokenType
    value: Any
    pos: int = 0

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r})"


# ══════════════════════════════════════════════════════════════
# LEXER
# ══════════════════════════════════════════════════════════════
KEYWORDS: dict[str, TokenType] = {
    # Verbs
    "quels":    TokenType.AFFICHER, "quel":     TokenType.AFFICHER,
    "affiche":  TokenType.AFFICHER, "afficher": TokenType.AFFICHER,
    "montre":   TokenType.AFFICHER, "liste":    TokenType.AFFICHER,
    "lister":   TokenType.AFFICHER, "afficher": TokenType.AFFICHER,
    "combien":  TokenType.COMPTER,  "nombre":   TokenType.COMPTER,
    "compter":  TokenType.COMPTER,  "comptes":  TokenType.COMPTER,
    "donne":    TokenType.DONNER,   "donner":   TokenType.DONNER,
    "trouve":   TokenType.DONNER,   "trouver":  TokenType.DONNER,
    # Structure
    "les":      TokenType.LES,      "des":      TokenType.LES,
    "de":       TokenType.DE,       "d":        TokenType.DE,
    "par":      TokenType.PAR,
    "où":       TokenType.OU,       "qui":      TokenType.OU,
    "ont":      TokenType.OU,       "ayant":    TokenType.OU,
    "avec":     TokenType.OU,       "ayant":    TokenType.OU,
    "dont":     TokenType.OU,       "have":     TokenType.OU,
    "classés":  TokenType.ORDONNER, "triés":    TokenType.ORDONNER,
    "ordonné":  TokenType.ORDONNER, "trié":     TokenType.ORDONNER,
    "classé":   TokenType.ORDONNER, "classees": TokenType.ORDONNER,
    "classées": TokenType.ORDONNER, "classés":  TokenType.ORDONNER,
    "triées":   TokenType.ORDONNER, "ordonnés": TokenType.ORDONNER,
    "ordonnées":TokenType.ORDONNER,
    "plus":     TokenType.PLUS,
    "asc":      TokenType.ASC,      "croissant":TokenType.ASC,
    "desc":     TokenType.DESC,     "décroissant":TokenType.DESC,
    # Comparators (multi-word handled in parser)
    "supérieur": TokenType.GT,      "supérieure": TokenType.GT,
    "inférieur": TokenType.LT,      "inférieure": TokenType.LT,
    "est":      TokenType.EQ,       "égal":     TokenType.EQ,
    "égale":    TokenType.EQ,
}

# Entity mapping: NL words → (table, alias)
ENTITY_MAP = {
    "capteurs":         ("capteurs",      "c"),
    "capteur":          ("capteurs",      "c"),
    "sensors":          ("capteurs",      "c"),
    "mesures":          ("mesures",       "m"),
    "mesure":           ("mesures",       "m"),
    "interventions":    ("interventions", "i"),
    "intervention":     ("interventions", "i"),
    "citoyens":         ("citoyens",      "ct"),
    "citoyen":          ("citoyens",      "ct"),
    "véhicules":        ("vehicules",     "v"),
    "vehicules":        ("vehicules",     "v"),
    "véhicule":         ("vehicules",     "v"),
    "vehicule":         ("vehicules",     "v"),
    "trajets":          ("trajets",       "t"),
    "trajet":           ("trajets",       "t"),
    "zones":            ("zones",         "z"),
    "zone":             ("zones",         "z"),
    "techniciens":      ("techniciens",   "tech"),
    "technicien":       ("techniciens",   "tech"),
}

# Field mapping: NL words → SQL column
FIELD_MAP = {
    "pollution":        "valeur",
    "statut":           "statut",
    "état":             "statut",
    "score":            "score_ecolo",
    "score_ecolo":      "score_ecolo",
    "écologique":       "score_ecolo",
    "ecological":       "score_ecolo",
    "co2":              "economie_co2",
    "économie_co2":     "economie_co2",
    "economie_co2":     "economie_co2",
    "économie":         "economie_co2",
    "économique":       "economie_co2",
    "economique":       "economie_co2",
    "polluées":         "valeur",
    "polluée":          "valeur",
    "pollués":          "valeur",
    "pollué":           "valeur",
    "polluees":         "valeur",
    "taux_erreur":      "taux_erreur",
    "erreur":           "taux_erreur",
    "coût":             "cout",
    "cout":             "cout",
    "coûts":            "cout",
    "durée":            "duree_heures",
    "duree":            "duree_heures",
    "date":             "date_debut",
    "nom":              "nom",
    "zone":             "zone_id",
    "type":             "type_capteur",
}

class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, text: str):
        self.text = text.lower().strip()
        self.pos = 0
        self.tokens: List[Token] = []

    def _peek(self) -> Optional[str]:
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def _advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        return ch

    def _skip_whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos] in " \t\n":
            self.pos += 1

    def _read_word(self) -> str:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalpha() or self.text[self.pos] in "_-àâéèêëîïôùûüç"):
            self.pos += 1
        return self.text[start:self.pos]

    def _read_number(self) -> float:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
            self.pos += 1
        return float(self.text[start:self.pos])

    def _read_string(self) -> str:
        self._advance()  # skip opening quote
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] not in ('"', "'"):
            self.pos += 1
        val = self.text[start:self.pos]
        if self.pos < len(self.text):
            self._advance()  # skip closing quote
        return val

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.text):
            self._skip_whitespace()
            if self.pos >= len(self.text):
                break

            ch = self.text[self.pos]

            # Comparators (symbols)
            if ch == '>':
                self.pos += 1
                if self.pos < len(self.text) and self.text[self.pos] == '=':
                    self.pos += 1
                    self.tokens.append(Token(TokenType.GTE, '>=', self.pos))
                else:
                    self.tokens.append(Token(TokenType.GT, '>', self.pos))
                continue

            if ch == '<':
                self.pos += 1
                if self.pos < len(self.text) and self.text[self.pos] == '=':
                    self.pos += 1
                    self.tokens.append(Token(TokenType.LTE, '<=', self.pos))
                else:
                    self.tokens.append(Token(TokenType.LT, '<', self.pos))
                continue

            if ch == '=':
                self.pos += 1
                self.tokens.append(Token(TokenType.EQ, '=', self.pos))
                continue

            # Numbers
            if ch.isdigit():
                num = self._read_number()
                self.tokens.append(Token(TokenType.NUMBER, num, self.pos))
                continue

            # Strings
            if ch in ('"', "'"):
                s = self._read_string()
                self.tokens.append(Token(TokenType.STRING, s, self.pos))
                continue

            # Words
            if ch.isalpha() or ch in "àâéèêëîïôùûüç_":
                word = self._read_word()
                # strip trailing punctuation
                word = word.strip(".,?!;:")
                # "donne-moi", "affiche-moi" -> keep the verb
                if "-" in word and word.split("-")[0] in KEYWORDS:
                    word = word.split("-")[0]

                if word in KEYWORDS:
                    self.tokens.append(Token(KEYWORDS[word], word, self.pos))
                elif word in ENTITY_MAP:
                    self.tokens.append(Token(TokenType.ENTITY, word, self.pos))
                elif word in FIELD_MAP:
                    self.tokens.append(Token(TokenType.FIELD, word, self.pos))
                # common stop words
                elif word in ("le","la","un","une","en","au","aux","sur","dans","du","et","ou","à","a",
                              "sont","ont","ont","pas","service","hors","maintenance","actif","actifs",
                              "inactif","signalé","terminé","cours","status","actuellement","qui"):
                    # attempt to map as value token (e.g. "hors_service")
                    self.tokens.append(Token(TokenType.STRING, word, self.pos))
                else:
                    # unknown — keep as string (might be value)
                    self.tokens.append(Token(TokenType.STRING, word, self.pos))
                continue

            # Skip unknown chars (punctuation etc)
            self.pos += 1

        self.tokens.append(Token(TokenType.EOF, None, self.pos))
        return self.tokens


# ══════════════════════════════════════════════════════════════
# AST NODES
# ══════════════════════════════════════════════════════════════
@dataclass
class ASTNode:
    pass

@dataclass
class SelectNode(ASTNode):
    entity: str                          # table name
    alias: str                           # table alias
    columns: List[str]                   # projected columns
    aggregate: Optional[str] = None     # COUNT, AVG, SUM
    where: Optional["WhereNode"] = None
    order_by: Optional[str] = None
    order_dir: str = "ASC"
    limit: Optional[int] = None
    is_count: bool = False

@dataclass
class WhereNode(ASTNode):
    field: str
    comparator: str                      # =, >, <, >=, <=
    value: Any


# ══════════════════════════════════════════════════════════════
# PARSER
# ══════════════════════════════════════════════════════════════
class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek_type(self) -> TokenType:
        return self.tokens[self.pos].type

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def _expect(self, ttype: TokenType) -> Token:
        tok = self._current()
        if tok.type != ttype:
            raise ParseError(f"Expected {ttype.name}, got {tok.type.name} ({tok.value!r}) at pos {self.pos}")
        return self._advance()

    def _match(self, *ttypes) -> bool:
        return self._peek_type() in ttypes

    def parse(self) -> SelectNode:
        """Entry point — parse the full query."""
        tok = self._current()

        if self._match(TokenType.AFFICHER):
            return self._parse_afficher()
        elif self._match(TokenType.COMPTER):
            return self._parse_compter()
        elif self._match(TokenType.DONNER):
            return self._parse_donner()
        else:
            # try to recover — look for entity
            return self._parse_afficher()

    def _parse_limit(self) -> Optional[int]:
        """Parse 'les N (plus|premiers|derniers)'."""
        if self._match(TokenType.LES):
            self._advance()  # consume "les"
            if self._match(TokenType.NUMBER):
                n = int(self._advance().value)
                # consume optional "plus", "premiers", "derniers" etc.
                while self._match(TokenType.PLUS, TokenType.STRING):
                    self._advance()
                return n
        return None

    def _parse_entity(self) -> tuple[str, str]:
        """Parse entity token → (table, alias)."""
        # skip filler words
        while self._match(TokenType.DE, TokenType.LES, TokenType.STRING):
            word = self._current().value
            if word in ENTITY_MAP:
                break
            self._advance()

        if self._match(TokenType.ENTITY):
            tok = self._advance()
            table, alias = ENTITY_MAP[tok.value]
            return table, alias
        # try STRING token that might be an entity
        if self._match(TokenType.STRING) and self._current().value in ENTITY_MAP:
            tok = self._advance()
            table, alias = ENTITY_MAP[tok.value]
            return table, alias
        raise ParseError(f"Expected entity, got {self._current()}")

    def _parse_where(self) -> Optional[WhereNode]:
        """Parse optional WHERE clause."""
        if not self._match(TokenType.OU):
            return None
        self._advance()  # consume "où/qui/avec..."

        # field — scan up to 4 tokens, skipping stop words to find a known field
        field_sql = None
        for _ in range(5):
            if self._match(TokenType.FIELD):
                field_sql = FIELD_MAP[self._advance().value]
                break
            elif self._match(TokenType.STRING):
                word = self._current().value
                if word in FIELD_MAP:
                    field_sql = FIELD_MAP[word]
                    self._advance()
                    break
                else:
                    self._advance()  # skip stop word
            else:
                break
        if not field_sql:
            return None

        # skip trailing adjective FIELDs (e.g. 'écologique' after 'score')
        while self._match(TokenType.FIELD):
            self._advance()

        # comparator
        cmp_map = {
            TokenType.GT: ">", TokenType.LT: "<",
            TokenType.GTE: ">=", TokenType.LTE: "<=",
            TokenType.EQ: "=",
        }
        # handle natural language comparators
        if self._match(TokenType.GT, TokenType.LT, TokenType.GTE, TokenType.LTE, TokenType.EQ):
            cmp = cmp_map[self._advance().type]
        elif self._match(TokenType.STRING):
            word = self._current().value
            nl_cmp = {"supérieur":">","supérieure":">","inférieur":"<","inférieure":"<","est":"=","égal":"=","égale":"="}
            if word in nl_cmp:
                cmp = nl_cmp[self._advance().value]
            else:
                cmp = "="
        elif self._match(TokenType.PLUS):
            self._advance()
            # "plus grand que" → GT
            cmp = ">"
        else:
            cmp = "="

        # skip filler like "à", "que", "de"
        while self._match(TokenType.DE, TokenType.STRING) and self._current().value in ("à","que","de","d"):
            self._advance()

        # value
        if self._match(TokenType.NUMBER):
            val = self._advance().value
        elif self._match(TokenType.STRING):
            val = f"'{self._advance().value}'"
        else:
            val = "''"

        return WhereNode(field=field_sql, comparator=cmp, value=val)

    def _parse_order(self) -> tuple[Optional[str], str]:
        """Parse optional ORDER BY clause."""
        # skip articles: "le plus ...", "les plus ..."
        while self._match(TokenType.LES, TokenType.STRING) and self._current().value in ("le", "la", "les", "l"):
            self._advance()
        if not self._match(TokenType.ORDONNER, TokenType.PLUS):
            return None, "ASC"

        self._advance()  # consume "classés/triés" or "plus"

        # skip "par" or adjective like "polluées" (DESC implied)
        direction = "DESC"  # default for "plus [adj]"

        if self._match(TokenType.PAR):
            self._advance()
            direction = "ASC"

        # field (skip up to 3 filler words such as "en", "de")
        field_sql = None
        for _ in range(3):
            if self._match(TokenType.FIELD):
                field_sql = FIELD_MAP[self._advance().value]
                break
            if self._match(TokenType.STRING, TokenType.DE) and self._current().value in FIELD_MAP:
                field_sql = FIELD_MAP[self._advance().value]
                break
            if self._match(TokenType.STRING, TokenType.DE) and self._current().value in ("en", "de", "d", "du", "des"):
                self._advance()
                continue
            break
        # "le plus économique en co2": the adjective already gave the field, skip the noun
        while self._match(TokenType.FIELD) or (self._match(TokenType.STRING) and self._current().value in ("en", "co2")):
            self._advance()

        # direction
        if self._match(TokenType.DESC):
            self._advance(); direction = "DESC"
        elif self._match(TokenType.ASC):
            self._advance(); direction = "ASC"

        return field_sql, direction

    def _parse_afficher(self) -> SelectNode:
        if self._match(TokenType.AFFICHER):
            self._advance()

        limit = self._parse_limit()

        table, alias = self._parse_entity()

        where = self._parse_where()

        order_field, order_dir = self._parse_order()
        if order_field is None and limit and table == "zones":
            # "les 5 zones les plus polluées" → order by pollution DESC
            order_field = "valeur"
            order_dir = "DESC"

        return SelectNode(
            entity=table, alias=alias,
            columns=["*"], where=where,
            order_by=order_field, order_dir=order_dir,
            limit=limit, is_count=False
        )

    def _parse_compter(self) -> SelectNode:
        self._advance()  # consume "combien/nombre"
        # skip "de"
        while self._match(TokenType.DE, TokenType.LES):
            self._advance()

        table, alias = self._parse_entity()
        where = self._parse_where()

        return SelectNode(
            entity=table, alias=alias,
            columns=["COUNT(*) AS total"],
            aggregate="COUNT",
            where=where, is_count=True
        )

    def _parse_donner(self) -> SelectNode:
        self._advance()
        limit = self._parse_limit()
        table, alias = self._parse_entity()
        where = self._parse_where()
        order_field, order_dir = self._parse_order()

        return SelectNode(
            entity=table, alias=alias,
            columns=["*"], where=where,
            order_by=order_field, order_dir=order_dir,
            limit=limit or 1
        )


# ══════════════════════════════════════════════════════════════
# SQL GENERATOR
# ══════════════════════════════════════════════════════════════
class SQLGenerator:
    """Walks the AST and emits SQL."""

    # Smart column selection per table
    DEFAULT_COLUMNS = {
        "capteurs":      "capteur_id, code_capteur, type_capteur, statut, taux_erreur, date_installation",
        "mesures":       "mesure_id, capteur_id, timestamp_mesure, valeur, unite, anomalie",
        "interventions": "intervention_id, capteur_id, nature, statut, cout, duree_heures, impact_co2, date_debut",
        "citoyens":      "citoyen_id, nom, prenom, score_ecolo, preference_mobilite",
        "vehicules":     "vehicule_id, immatriculation, type_vehicule, energie, statut",
        "trajets":       "trajet_id, vehicule_id, origine, destination, economie_co2, distance_km",
        "zones":         "zone_id, nom, superficie, population",
        "techniciens":   "technicien_id, matricule, nom, prenom, specialite, disponible",
    }

    def generate(self, node: SelectNode) -> str:
        # Zones have no pollution column: rank them with the v_zones_polluees view
        if node.entity == "zones" and node.order_by == "valeur" and not node.is_count:
            sql = ("SELECT zone, pollution_moyenne, nb_mesures, derniere_mesure\n"
                   f"FROM v_zones_polluees\nORDER BY pollution_moyenne {node.order_dir}")
            if node.limit:
                sql += f"\nLIMIT {node.limit}"
            return sql + ";"

        cols = self.DEFAULT_COLUMNS.get(node.entity, "*")
        if node.is_count:
            cols = "COUNT(*) AS total"

        sql = f"SELECT {cols}\nFROM {node.entity}"

        if node.where:
            val = node.where.value
            sql += f"\nWHERE {node.where.field} {node.where.comparator} {val}"

        if node.order_by:
            sql += f"\nORDER BY {node.order_by} {node.order_dir}"

        if node.limit:
            sql += f"\nLIMIT {node.limit}"

        return sql + ";"


# ══════════════════════════════════════════════════════════════
# COMPILER — Public API
# ══════════════════════════════════════════════════════════════
@dataclass
class CompilationResult:
    success: bool
    sql: Optional[str]
    ast: Optional[SelectNode]
    tokens: List[Token]
    error: Optional[str] = None

# Sensor status phrases → value of capteurs.statut
STATUS_PATTERNS = [
    (r"hors[ _-]?service",        "hors_service"),
    (r"en[ _-]?maintenance",      "en_maintenance"),
    (r"\binactifs?\b",            "inactif"),
    (r"\bactifs?\b",              "actif"),
    (r"\bsignal[ée]s?\b",         "signale"),
]

def _detect_status(query: str) -> Optional[str]:
    q = query.lower()
    for pattern, value in STATUS_PATTERNS:
        if re.search(pattern, q):
            return value
    return None

def compile_nl(query: str) -> CompilationResult:
    """
    Main entry point.
    Returns CompilationResult with sql, ast, tokens, error.
    """
    try:
        lexer = Lexer(query)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        ast = parser.parse()

        # "capteurs hors service", "en maintenance"... → WHERE statut = '...'
        if ast.where is None and ast.entity == "capteurs":
            status = _detect_status(query)
            if status:
                ast.where = WhereNode(field="statut", comparator="=", value=f"'{status}'")

        generator = SQLGenerator()
        sql = generator.generate(ast)

        return CompilationResult(success=True, sql=sql, ast=ast, tokens=tokens)

    except (ParseError, LexerError) as e:
        return CompilationResult(success=False, sql=None, ast=None,
                                 tokens=[], error=str(e))
    except Exception as e:
        return CompilationResult(success=False, sql=None, ast=None,
                                 tokens=[], error=f"Compilation error: {e}")


# ══════════════════════════════════════════════════════════════
# DEMO / TEST
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    test_queries = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score écologique > 80 ?",
        "Donne-moi le trajet le plus économique en co2",
        "Liste les interventions en cours",
        "Montre les capteurs avec taux_erreur > 10",
        "Affiche les 10 mesures les plus récentes",
        "Combien d'interventions sont terminées ?",
    ]

    for q in test_queries:
        result = compile_nl(q)
        print(f"\n📝 NL: {q}")
        if result.success:
            print(f"✅ SQL:\n{result.sql}")
        else:
            print(f"❌ Error: {result.error}")
