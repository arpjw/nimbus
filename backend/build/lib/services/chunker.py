import hashlib
from typing import Optional


def _detect_language(file_path: str) -> str:
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    return {
        "py": "python",
        "ts": "typescript",
        "tsx": "typescript",
        "js": "javascript",
        "jsx": "javascript",
        "rs": "rust",
        "go": "go",
    }.get(ext, "unknown")


def _chunk_id(repo_id: str, file_path: str, start_line: int) -> str:
    return hashlib.sha256(f"{repo_id}:{file_path}:{start_line}".encode()).hexdigest()[:16]


def _make_chunk(
    repo_id: str,
    file_path: str,
    language: str,
    start_line: int,
    end_line: int,
    text: str,
    symbol_name: Optional[str],
    symbol_type: str,
) -> dict:
    return {
        "chunk_id": _chunk_id(repo_id, file_path, start_line),
        "repo_id": repo_id,
        "file_path": file_path,
        "language": language,
        "start_line": start_line,
        "end_line": end_line,
        "text": text,
        "symbol_name": symbol_name,
        "symbol_type": symbol_type,
    }


def _line_chunks(
    file_path: str,
    content: str,
    repo_id: str,
    language: str,
    chunk_size: int = 80,
    overlap: int = 10,
) -> list[dict]:
    lines = content.splitlines()
    chunks = []
    i = 0
    while i < len(lines):
        text = "\n".join(lines[i : i + chunk_size])
        if text.strip():
            chunks.append(
                _make_chunk(
                    repo_id,
                    file_path,
                    language,
                    i + 1,
                    min(i + chunk_size, len(lines)),
                    text,
                    None,
                    "chunk",
                )
            )
        i += chunk_size - overlap
    return chunks


def _split_if_large(
    chunk: dict,
    lines: list[str],
    chunk_size: int = 80,
    overlap: int = 10,
) -> list[dict]:
    start_0 = chunk["start_line"] - 1
    end_0 = chunk["end_line"]
    node_lines = lines[start_0:end_0]

    if len(node_lines) <= 120:
        return [chunk]

    result = []
    i = 0
    while i < len(node_lines):
        text = "\n".join(node_lines[i : i + chunk_size])
        if text.strip():
            abs_start = start_0 + i + 1
            abs_end = start_0 + min(i + chunk_size, len(node_lines))
            result.append(
                _make_chunk(
                    chunk["repo_id"],
                    chunk["file_path"],
                    chunk["language"],
                    abs_start,
                    abs_end,
                    text,
                    chunk["symbol_name"],
                    chunk["symbol_type"],
                )
            )
        i += chunk_size - overlap
    return result


def _node_text(node) -> str:
    return node.text.decode("utf8", errors="replace") if node.text else ""


def _get_name(node) -> Optional[str]:
    name_node = node.child_by_field_name("name")
    if name_node and name_node.text:
        return name_node.text.decode("utf8", errors="replace")
    return None


def _node_chunk(
    node,
    repo_id: str,
    file_path: str,
    language: str,
    symbol_name: Optional[str],
    symbol_type: str,
) -> dict:
    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    return _make_chunk(repo_id, file_path, language, start_line, end_line, _node_text(node), symbol_name, symbol_type)


# --- Python extraction ---

def _python_class_methods(class_node, repo_id: str, file_path: str, lines: list[str]) -> list[dict]:
    chunks = []
    body = class_node.child_by_field_name("body")
    if not body:
        return chunks
    class_name = _get_name(class_node)
    for node in body.named_children:
        if node.type == "function_definition":
            method_name = _get_name(node)
            full_name = f"{class_name}.{method_name}" if class_name and method_name else method_name
            base = _node_chunk(node, repo_id, file_path, "python", full_name, "method_definition")
            chunks.extend(_split_if_large(base, lines))
        elif node.type == "decorated_definition":
            inner = node.child_by_field_name("definition")
            method_name = _get_name(inner) if inner else None
            full_name = f"{class_name}.{method_name}" if class_name and method_name else method_name
            base = _node_chunk(node, repo_id, file_path, "python", full_name, "method_definition")
            chunks.extend(_split_if_large(base, lines))
    return chunks


def _extract_python(root, repo_id: str, file_path: str, lines: list[str]) -> list[dict]:
    chunks = []
    for node in root.named_children:
        if node.type == "function_definition":
            base = _node_chunk(node, repo_id, file_path, "python", _get_name(node), "function_definition")
            chunks.extend(_split_if_large(base, lines))
        elif node.type == "class_definition":
            base = _node_chunk(node, repo_id, file_path, "python", _get_name(node), "class_definition")
            chunks.extend(_split_if_large(base, lines))
            chunks.extend(_python_class_methods(node, repo_id, file_path, lines))
        elif node.type == "decorated_definition":
            inner = node.child_by_field_name("definition")
            name = _get_name(inner) if inner else None
            base = _node_chunk(node, repo_id, file_path, "python", name, "decorated_definition")
            chunks.extend(_split_if_large(base, lines))
            if inner and inner.type == "class_definition":
                chunks.extend(_python_class_methods(inner, repo_id, file_path, lines))
    return chunks


# --- JavaScript / TypeScript extraction ---

def _js_class_methods(class_node, repo_id: str, file_path: str, language: str, lines: list[str]) -> list[dict]:
    chunks = []
    body = class_node.child_by_field_name("body")
    if not body:
        return chunks
    class_name = _get_name(class_node)
    for node in body.named_children:
        if node.type == "method_definition":
            method_name = _get_name(node)
            full_name = f"{class_name}.{method_name}" if class_name and method_name else method_name
            base = _node_chunk(node, repo_id, file_path, language, full_name, "method_definition")
            chunks.extend(_split_if_large(base, lines))
    return chunks


def _js_arrow_functions(decl_node, wrap_node, repo_id: str, file_path: str, language: str, lines: list[str]) -> list[dict]:
    chunks = []
    for child in decl_node.named_children:
        if child.type == "variable_declarator":
            value = child.child_by_field_name("value")
            if value and value.type == "arrow_function":
                name_node = child.child_by_field_name("name")
                name = name_node.text.decode("utf8", errors="replace") if name_node and name_node.text else None
                base = _node_chunk(wrap_node, repo_id, file_path, language, name, "arrow_function")
                chunks.extend(_split_if_large(base, lines))
    return chunks


def _extract_js_node(node, repo_id: str, file_path: str, language: str, lines: list[str]) -> list[dict]:
    chunks = []
    if node.type == "function_declaration":
        base = _node_chunk(node, repo_id, file_path, language, _get_name(node), "function_declaration")
        chunks.extend(_split_if_large(base, lines))
    elif node.type == "class_declaration":
        base = _node_chunk(node, repo_id, file_path, language, _get_name(node), "class_declaration")
        chunks.extend(_split_if_large(base, lines))
        chunks.extend(_js_class_methods(node, repo_id, file_path, language, lines))
    elif node.type == "export_statement":
        for child in node.named_children:
            if child.type == "function_declaration":
                base = _node_chunk(node, repo_id, file_path, language, _get_name(child), "function_declaration")
                chunks.extend(_split_if_large(base, lines))
            elif child.type == "class_declaration":
                base = _node_chunk(node, repo_id, file_path, language, _get_name(child), "class_declaration")
                chunks.extend(_split_if_large(base, lines))
                chunks.extend(_js_class_methods(child, repo_id, file_path, language, lines))
            elif child.type in ("lexical_declaration", "variable_declaration"):
                chunks.extend(_js_arrow_functions(child, node, repo_id, file_path, language, lines))
    elif node.type in ("lexical_declaration", "variable_declaration"):
        chunks.extend(_js_arrow_functions(node, node, repo_id, file_path, language, lines))
    return chunks


def _extract_js(root, repo_id: str, file_path: str, language: str, lines: list[str]) -> list[dict]:
    chunks = []
    for node in root.named_children:
        chunks.extend(_extract_js_node(node, repo_id, file_path, language, lines))
    return chunks


# --- Parser setup ---

def _get_parser(language: str, file_path: str):
    from tree_sitter import Language, Parser

    if language == "python":
        import tree_sitter_python as tspython
        lang = Language(tspython.language())
    elif language == "typescript":
        import tree_sitter_typescript as tsts
        ext = file_path.rsplit(".", 1)[-1].lower()
        lang = Language(tsts.language_tsx() if ext == "tsx" else tsts.language_typescript())
    else:
        import tree_sitter_javascript as tsjs
        lang = Language(tsjs.language())

    return Parser(lang)


def _ast_chunks(file_path: str, content: str, repo_id: str, language: str, lines: list[str]) -> list[dict]:
    parser = _get_parser(language, file_path)
    tree = parser.parse(bytes(content, "utf8"))
    root = tree.root_node

    if language == "python":
        chunks = _extract_python(root, repo_id, file_path, lines)
    else:
        chunks = _extract_js(root, repo_id, file_path, language, lines)

    if not chunks:
        raise ValueError("no AST nodes extracted")

    return chunks


async def chunk_file(file_path: str, content: str, repo_id: str) -> list[dict]:
    language = _detect_language(file_path)
    lines = content.splitlines()

    if language in ("python", "typescript", "javascript"):
        try:
            return _ast_chunks(file_path, content, repo_id, language, lines)
        except Exception:
            pass

    return _line_chunks(file_path, content, repo_id, language)
