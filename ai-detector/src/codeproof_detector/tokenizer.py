"""Language-aware tokenization for Python and Java (no code execution).

- Ignores whitespace and comments for similarity purposes.
- Preserves keywords, identifiers, literals, operators and punctuation.
- Handles string/char literals (including ``#`` or ``//`` markers inside
  them) via real lexing instead of naive comment stripping.
- Falls back to a generic regex tokenizer on malformed source so the
  detector never crashes on unparseable input.
"""

from __future__ import annotations

import io
import re
import token as _py_token
import tokenize as _py_tokenize
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Token:
    """A single lexical token with character offsets into the source."""

    text: str
    kind: str
    start: int
    end: int


@dataclass(frozen=True)
class TokenizeResult:
    """Tokens plus diagnostics about how tokenization behaved."""

    tokens: list[Token]
    used_fallback: bool
    warnings: list[str] = field(default_factory=list)

    def texts(self) -> list[str]:
        return [t.text for t in self.tokens]


# Tokens skipped for similarity: whitespace is implicit, comments and
# purely positional tokens carry no lexical signal.
_PY_SKIP = frozenset(
    {
        _py_token.COMMENT,
        _py_token.NL,
        _py_token.NEWLINE,
        _py_token.INDENT,
        _py_token.DEDENT,
        _py_token.ENDMARKER,
        _py_token.ENCODING,
    }
)

_GENERIC_TOKEN_RE = re.compile(
    r"""
    (?P<string>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
    | (?P<number>\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b)
    | (?P<ident>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<op>\*\*|//|<<|>>|<=|>=|==|!=|->|\+=|-=|\*=|/=|%=|:=|[+\-*/%<>=!&|^~@(){}\[\],.:;])
    """,
    re.VERBOSE,
)

_JAVA_MULTI_OPS = (
    ">>>=",
    "<<=",
    ">>=",
    ">>>",
    "<<",
    ">>",
    "==",
    "!=",
    "<=",
    ">=",
    "&&",
    "||",
    "++",
    "--",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "&=",
    "|=",
    "^=",
    "->",
    "::",
    "...",
)

_JAVA_KEYWORDS = frozenset(
    "abstract assert boolean break byte case catch char class const continue "
    "default do double else enum extends final finally float for goto if "
    "implements import instanceof int interface long native new package "
    "private protected public return short static strictfp super switch "
    "synchronized this throw throws transient try void volatile while "
    "var record sealed permits yield true false null".split()
)


def _line_offsets(source: str) -> list[int]:
    """Return the char offset where each 1-based line starts."""
    offsets = [0]
    for match in re.finditer("\n", source):
        offsets.append(match.end())
    return offsets


def tokenize_python(source: str) -> TokenizeResult:
    """Tokenize Python source with the stdlib ``tokenize`` module."""
    warnings: list[str] = []
    line_offsets = _line_offsets(source)
    tokens: list[Token] = []
    try:
        gen = _py_tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in gen:
            if tok.type in _PY_SKIP:
                continue
            if tok.type == _py_token.ERRORTOKEN:
                warnings.append(
                    f"Skipped undecodable character {tok.string!r} "
                    f"at {tok.start}."
                )
                continue
            srow, scol = tok.start
            erow, ecol = tok.end
            start = line_offsets[srow - 1] + scol if srow - 1 < len(line_offsets) else len(source)
            end = line_offsets[erow - 1] + ecol if erow - 1 < len(line_offsets) else len(source)
            kind = _py_token.tok_name.get(tok.type, "OTHER")
            tokens.append(Token(text=tok.string, kind=kind, start=start, end=end))
        return TokenizeResult(tokens=tokens, used_fallback=False, warnings=warnings)
    except (SyntaxError, _py_tokenize.TokenError, IndentationError, ValueError) as exc:
        # Malformed source: fall back instead of failing the whole batch.
        fallback = _generic_tokenize(source)
        return TokenizeResult(
            tokens=fallback,
            used_fallback=True,
            warnings=[f"Python lexer fallback used ({exc.__class__.__name__})."]
            + warnings,
        )


def _generic_tokenize(source: str) -> list[Token]:
    """Best-effort regex tokenizer used as a fallback."""
    tokens: list[Token] = []
    for match in _GENERIC_TOKEN_RE.finditer(source):
        kind = match.lastgroup or "OTHER"
        tokens.append(
            Token(text=match.group(0), kind=kind.upper(), start=match.start(), end=match.end())
        )
    return tokens


def tokenize_java(source: str) -> TokenizeResult:
    """Tokenize Java source with a comment/string-aware scanner."""
    tokens: list[Token] = []
    warnings: list[str] = []
    i = 0
    n = len(source)

    def ident_kind(word: str) -> str:
        return "KEYWORD" if word in _JAVA_KEYWORDS else "IDENT"

    while i < n:
        ch = source[i]
        # Whitespace.
        if ch.isspace():
            i += 1
            continue
        # Line comment.
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            j = source.find("\n", i + 2)
            i = n if j == -1 else j + 1
            continue
        # Block comment.
        if ch == "/" and i + 1 < n and source[i + 1] == "*":
            j = source.find("*/", i + 2)
            if j == -1:
                warnings.append("Unterminated block comment; rest treated as comment.")
                break
            i = j + 2
            continue
        # Text block (Java 15+): """ ... """
        if source.startswith('"""', i):
            j = source.find('"""', i + 3)
            end = n if j == -1 else j + 3
            if j == -1:
                warnings.append("Unterminated text block.")
            tokens.append(Token(text=source[i:end], kind="STRING", start=i, end=end))
            i = end
            continue
        # String literal.
        if ch == '"':
            j = i + 1
            closed = False
            while j < n:
                if source[j] == "\\":
                    j += 2
                    continue
                if source[j] == '"':
                    closed = True
                    j += 1
                    break
                if source[j] == "\n":
                    break
                j += 1
            if not closed:
                warnings.append(f"Unterminated string literal at offset {i}.")
            tokens.append(Token(text=source[i:j], kind="STRING", start=i, end=j))
            i = j
            continue
        # Char literal.
        if ch == "'":
            j = i + 1
            closed = False
            while j < n:
                if source[j] == "\\":
                    j += 2
                    continue
                if source[j] == "'":
                    closed = True
                    j += 1
                    break
                if source[j] == "\n":
                    break
                j += 1
            if not closed:
                warnings.append(f"Unterminated char literal at offset {i}.")
            tokens.append(Token(text=source[i:j], kind="CHAR", start=i, end=j))
            i = j
            continue
        # Identifier / keyword.
        if ch.isalpha() or ch == "_" or ch == "$":
            j = i + 1
            while j < n and (source[j].isalnum() or source[j] in "_$"):
                j += 1
            tokens.append(Token(text=source[i:j], kind=ident_kind(source[i:j]), start=i, end=j))
            i = j
            continue
        # Number literal (best effort).
        if ch.isdigit():
            m = re.match(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[lLfFdD]?", source[i:])
            assert m is not None
            tokens.append(Token(text=m.group(0), kind="NUMBER", start=i, end=i + len(m.group(0))))
            i += len(m.group(0))
            continue
        # Multi-char operators first.
        matched = False
        for op in _JAVA_MULTI_OPS:
            if source.startswith(op, i):
                tokens.append(Token(text=op, kind="OP", start=i, end=i + len(op)))
                i += len(op)
                matched = True
                break
        if matched:
            continue
        # Single punctuation / operator (including @ for annotations).
        if ch in "+-*/%<>=!&|^~?:;,.(){}[]@":
            tokens.append(Token(text=ch, kind="OP", start=i, end=i + 1))
            i += 1
            continue
        warnings.append(f"Skipped unexpected character {ch!r} at offset {i}.")
        i += 1

    return TokenizeResult(tokens=tokens, used_fallback=False, warnings=warnings)


def tokenize(source: str, language: str) -> TokenizeResult:
    """Tokenize ``source`` for ``language`` (``python`` or ``java``).

    Raises:
        ValueError: For unsupported languages.
    """
    lang = language.strip().lower() if isinstance(language, str) else ""
    if lang == "python":
        return tokenize_python(source)
    if lang == "java":
        return tokenize_java(source)
    raise ValueError(f"Unsupported language '{language}'. Expected 'python' or 'java'.")


def token_texts(result: TokenizeResult) -> list[str]:
    """Return the plain token-text sequence for similarity computation."""
    return result.texts()


def to_dict_result(result: TokenizeResult) -> dict[str, Any]:
    return {
        "tokens": [
            {"text": t.text, "kind": t.kind, "start": t.start, "end": t.end}
            for t in result.tokens
        ],
        "used_fallback": result.used_fallback,
        "warnings": list(result.warnings),
    }
