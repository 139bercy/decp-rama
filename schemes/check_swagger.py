#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import argparse
import re
import sys
from copy import deepcopy
from collections import defaultdict

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def is_openapi3(doc):
    # OpenAPI 3.x: key "openapi" présent (ex: "3.0.3")
    return isinstance(doc, dict) and "openapi" in doc

def is_swagger2(doc):
    # Swagger 2.0: key "swagger" == "2.0"
    return isinstance(doc, dict) and doc.get("swagger") == "2.0"

def extract_api_schemas(doc):
    """
    Retourne un dict {nom_schema: schema} depuis un document Swagger/OpenAPI.
    Gère:
      - OpenAPI 3.x: doc["components"]["schemas"]
      - Swagger 2.0: doc["definitions"]
    """
    if is_openapi3(doc):
        return deepcopy(doc.get("components", {}).get("schemas", {}))
    if is_swagger2(doc):
        return deepcopy(doc.get("definitions", {}))
    # Par sécurité: tenter les deux
    return deepcopy(doc.get("components", {}).get("schemas", {})) or deepcopy(doc.get("definitions", {}))

def extract_jsonschema_defs(doc):
    """
    Retourne un dict {nom_schema: schema} depuis un document JSON Schema.
    Gère "definitions" ou "$defs".
    """
    # JSON Schema draft-07 ou plus ancien: "definitions"
    # versions récentes: "$defs"
    if "definitions" in doc:
        return deepcopy(doc["definitions"])
    if "$defs" in doc:
        return deepcopy(doc["$defs"])
    # Si le JSON Schema est monolithique sans defs, on considère la racine comme un "nom" unique
    return {"__root__": deepcopy(doc)}

def slug(s):
    # Normalisation pour matcher des noms proches (camelCase, kebab-case...)
    if s is None:
        return ""
    s = s.strip()
    s = s.replace("_", "-")
    s = s.replace(" ", "-")
    s = s.lower()
    s = re.sub(r"[^a-z0-9\-]+", "", s)
    return s

def build_ref_index(doc, is_api=False):
    """
    Construit un index pour résoudre les $ref internes (#/components/schemas/... ou #/definitions/...)
    Retourne une fonction resolve(ref) -> schema
    """
    # Points d'entrée possibles
    candidates = []
    if is_api:
        # Swagger/OpenAPI
        comp = doc.get("components", {}).get("schemas", {})
        defs = doc.get("definitions", {})
        candidates.append(("#/components/schemas", comp))
        candidates.append(("#/definitions", defs))
    else:
        # JSON Schema
        defs = doc.get("definitions", {})
        ddefs = doc.get("$defs", {})
        candidates.append(("#/definitions", defs))
        candidates.append(("#/$defs", ddefs))

    # Mise à plat des chemins
    ref_map = {}
    for base, d in candidates:
        for k, v in d.items():
            ref_map[f"{base}/{k}"] = v

    def resolve(ref):
        """Résout uniquement les $ref internes; renvoie None si non trouvé."""
        if not isinstance(ref, str):
            return None
        if not ref.startswith("#/"):
            return None
        return deepcopy(ref_map.get(ref))

    return resolve

def normalize_type(t):
    """
    Retourne un frozenset de types (pour gérer nullable et tableaux de types).
    """
    if t is None:
        return frozenset()
    if isinstance(t, list):
        return frozenset(sorted(t))
    return frozenset([t])

def merge_allOf(schema, resolver, max_depth=10):
    """
    Aplati sommairement allOf en fusionnant properties/required/type/enum/etc.
    Ne gère pas tous les cas avancés, mais suffit pour une comparaison structurée.
    """
    if not isinstance(schema, dict):
        return schema
    schema = deepcopy(schema)
    visited = 0
    while isinstance(schema, dict) and "allOf" in schema and visited < max_depth:
        visited += 1
        parts = schema.pop("allOf")
        base = {}
        for part in parts:
            part = expand_refs(part, resolver)
            part = merge_allOf(part, resolver, max_depth=max_depth)
            base = shallow_merge_schema(base, part)
        schema = shallow_merge_schema(base, schema)
    return schema

def shallow_merge_schema(a, b):
    """
    Fusion superficielle de deux schémas (dict) pour aplanir allOf:
    - Fusion de properties
    - Union de required
    - Intersection/union prudente pour enum et type
    - Conservation des champs simples si absents dans 'a'
    """
    out = deepcopy(a)
    for k, v in b.items():
        if k == "properties":
            out.setdefault("properties", {})
            out["properties"].update(deepcopy(v))
        elif k == "required":
            r = set(out.get("required", [])) | set(v or [])
            out["required"] = sorted(r)
        elif k == "enum":
            # Si les deux définissent enum, on prend l'intersection pour rester conservateur
            if "enum" in out:
                out["enum"] = sorted(list(set(out["enum"]) & set(v)))
            else:
                out["enum"] = deepcopy(v)
        elif k == "type":
            # Essayer d'unifier sous forme de set
            t1 = normalize_type(out.get("type"))
            t2 = normalize_type(v)
            if t1 and t2:
                out["type"] = sorted(list(t1 & t2)) or sorted(list(t1 | t2))
            else:
                out["type"] = sorted(list(t1 | t2)) if (t1 or t2) else None
        else:
            if k not in out:
                out[k] = deepcopy(v)
    return out

def expand_refs(schema, resolver):
    """
    Remplace un schéma référencé par son contenu; gère les $ref internes simples.
    """
    if not isinstance(schema, dict):
        return schema
    if "$ref" in schema:
        target = resolver(schema["$ref"])
        if target is not None:
            # Le $ref peut coexister avec d'autres contraintes; on fusionne
            rest = deepcopy(schema)
            rest.pop("$ref")
            target = deepcopy(target)
            target = shallow_merge_schema(target, rest)
            return target
    return schema

def prepare_schema(schema, resolver):
    """
    Résout $ref et aplanit allOf pour obtenir une forme plus comparable.
    """
    schema = expand_refs(schema, resolver)
    schema = merge_allOf(schema, resolver)
    return schema

def compare_types(a, b, diffs, path):
    ta = normalize_type(a.get("type"))
    tb = normalize_type(b.get("type"))
    if ta != tb:
        diffs.append((path, "type", f"{sorted(list(ta))} != {sorted(list(tb))}"))

    # Gestion OpenAPI 3 nullable
    na = bool(a.get("nullable"))
    nb = bool(b.get("nullable"))
    if na != nb:
        diffs.append((path, "nullable", f"{na} != {nb}"))

def compare_enums(a, b, diffs, path):
    ea = a.get("enum")
    eb = b.get("enum")
    if ea is not None or eb is not None:
        sa = set(ea or [])
        sb = set(eb or [])
        if sa != sb:
            diffs.append((path, "enum", f"{sorted(sa)} != {sorted(sb)}"))

def compare_simple_constraints(a, b, diffs, path):
    keys = [
        "format",
        "pattern",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "uniqueItems",
        "minProperties",
        "maxProperties",
        "additionalProperties",
    ]
    for k in keys:
        va = a.get(k)
        vb = b.get(k)
        # Cas particulier: additionalProperties peut être bool ou schema
        if k == "additionalProperties":
            if isinstance(va, dict) and isinstance(vb, dict):
                # On signale juste présence/absence; comparer profondément serait coûteux
                if json.dumps(va, sort_keys=True) != json.dumps(vb, sort_keys=True):
                    diffs.append((path, "additionalProperties", "diff schema"))
            elif va != vb:
                diffs.append((path, "additionalProperties", f"{va} != {vb}"))
        else:
            if va != vb:
                diffs.append((path, k, f"{va} != {vb}"))

def compare_required(a, b, diffs, path):
    ra = set(a.get("required", []))
    rb = set(b.get("required", []))
    if ra != rb:
        diffs.append((path, "required", f"{sorted(ra)} != {sorted(rb)}"))

def compare_properties(a, b, diffs, path, resolver_a, resolver_b, max_depth=6, _depth=0):
    if _depth > max_depth:
        return
    pa = a.get("properties", {}) or {}
    pb = b.get("properties", {}) or {}

    keys_a = set(pa.keys())
    keys_b = set(pb.keys())
    only_a = sorted(list(keys_a - keys_b))
    only_b = sorted(list(keys_b - keys_a))
    if only_a:
        diffs.append((path, "properties_only_in_A", only_a))
    if only_b:
        diffs.append((path, "properties_only_in_B", only_b))

    for k in sorted(keys_a & keys_b):
        sa = prepare_schema(pa[k], resolver_a)
        sb = prepare_schema(pb[k], resolver_b)
        sub_path = f"{path}.properties.{k}"

        # type, enum, contraintes simples
        compare_types(sa, sb, diffs, sub_path)
        compare_enums(sa, sb, diffs, sub_path)
        compare_simple_constraints(sa, sb, diffs, sub_path)

        # Si type = object -> descendre
        ta = normalize_type(sa.get("type"))
        tb = normalize_type(sb.get("type"))
        if "object" in ta or "object" in tb:
            compare_required(sa, sb, diffs, sub_path)
            compare_properties(sa, sb, diffs, sub_path, resolver_a, resolver_b, max_depth, _depth + 1)

        # Si type = array -> comparer items
        if "array" in ta or "array" in tb:
            ia = sa.get("items")
            ib = sb.get("items")
            if ia is None and ib is None:
                pass
            elif ia is None or ib is None:
                diffs.append((sub_path, "items", f"{bool(ia)} != {bool(ib)}"))
            else:
                ia = prepare_schema(ia, resolver_a)
                ib = prepare_schema(ib, resolver_b)
                compare_types(ia, ib, diffs, sub_path + ".items")
                compare_enums(ia, ib, diffs, sub_path + ".items")
                compare_simple_constraints(ia, ib, diffs, sub_path + ".items")
                # Descente si object
                tia = normalize_type(ia.get("type"))
                tib = normalize_type(ib.get("type"))
                if "object" in tia or "object" in tib:
                    compare_required(ia, ib, diffs, sub_path + ".items")
                    compare_properties(ia, ib, diffs, sub_path + ".items", resolver_a, resolver_b, max_depth, _depth + 1)

def match_definitions(api_defs, json_defs, mapping=None):
    """
    Renvoie:
      - pairs: liste de tuples (name_api, name_json) appariés
      - only_api: noms sans correspondance côté API
      - only_json: noms sans correspondance côté JSON Schema
    """
    mapping = mapping or {}
    # Index par slug
    api_by_slug = {slug(k): k for k in api_defs.keys()}
    json_by_slug = {slug(k): k for k in json_defs.keys()}

    pairs = []
    used_json = set()

    # 1) Mapping explicite
    for a_name, b_name in mapping.items():
        if a_name in api_defs and b_name in json_defs:
            pairs.append((a_name, b_name))
            used_json.add(b_name)

    # 2) Correspondance par nom exact
    for a in api_defs.keys():
        if a in json_defs and (a not in [p[0] for p in pairs]):
            pairs.append((a, a))
            used_json.add(a)

    # 3) Correspondance par slug
    for a in api_defs.keys():
        if a in [p[0] for p in pairs]:
            continue
        s = slug(a)
        if s in json_by_slug:
            bj = json_by_slug[s]
            if bj not in used_json:
                pairs.append((a, bj))
                used_json.add(bj)

    only_api = [k for k in api_defs.keys() if k not in [p[0] for p in pairs]]
    only_json = [k for k in json_defs.keys() if k not in used_json]

    return pairs, only_api, only_json

def compare_schema_pair(name_api, schema_api, name_json, schema_json, resolver_api, resolver_json):
    diffs = []

    sa = prepare_schema(schema_api, resolver_api)
    sb = prepare_schema(schema_json, resolver_json)

    path = f"{name_api} <-> {name_json}"

    # Comparaisons au niveau racine
    compare_types(sa, sb, diffs, path)
    compare_enums(sa, sb, diffs, path)
    compare_simple_constraints(sa, sb, diffs, path)
    compare_required(sa, sb, diffs, path)

    # Propriétés
    compare_properties(sa, sb, diffs, path, resolver_api, resolver_json)

    return diffs

def print_report(pairs, only_api, only_json, all_diffs, outfile=None):
    lines = []
    lines.append("=== Résumé comparaison API vs JSON Schema ===")
    lines.append(f"Nombre d'appariements: {len(pairs)}")
    lines.append(f"Schémas uniquement côté API: {len(only_api)} -> {only_api}")
    lines.append(f"Schémas uniquement côté JSON: {len(only_json)} -> {only_json}")
    lines.append("")

    total = 0
    for (na, nj), diffs in all_diffs.items():
        lines.append(f"[Schéma] {na} <-> {nj}")
        if not diffs:
            lines.append("  - Aucune différence")
        else:
            for p, kind, msg in diffs:
                lines.append(f"  - {p} :: {kind} :: {msg}")
                total += 1
        lines.append("")
    lines.append(f"Total différences: {total}")

    text = "\n".join(lines)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)

def main():
    parser = argparse.ArgumentParser(description="Comparer un Swagger/OpenAPI et un JSON Schema.")
    parser.add_argument("--swagger", required=True, help="Chemin du Swagger/OpenAPI (JSON)")
    parser.add_argument("--schema", required=True, help="Chemin du JSON Schema (JSON)")
    parser.add_argument("--mapping", default=None,
                        help='Mapping JSON des noms: ex. \'{"MarchePublic":"marche","ContratConcession":"contrat-concession"}\'')
    parser.add_argument("--out", default=None, help="Fichier de sortie pour le rapport (txt)")
    args = parser.parse_args()

    try:
        api_doc = load_json(args.swagger)
        schema_doc = load_json(args.schema)
    except Exception as e:
        print(f"Erreur de lecture des fichiers: {e}", file=sys.stderr)
        sys.exit(1)

    api_defs = extract_api_schemas(api_doc)
    json_defs = extract_jsonschema_defs(schema_doc)

    mapping = None
    if args.mapping:
        try:
            mapping = json.loads(args.mapping)
        except Exception as e:
            print(f"Mapping invalide (doit être un JSON dico): {e}", file=sys.stderr)
            sys.exit(1)

    pairs, only_api, only_json = match_definitions(api_defs, json_defs, mapping)

    # Résolveurs de $ref
    resolver_api = build_ref_index(api_doc, is_api=True)
    resolver_json = build_ref_index(schema_doc, is_api=False)

    all_diffs = {}
    for (na, nj) in pairs:
        diffs = compare_schema_pair(na, api_defs[na], nj, json_defs[nj], resolver_api, resolver_json)
        all_diffs[(na, nj)] = diffs

    print_report(pairs, only_api, only_json, all_diffs, outfile=args.out)

if __name__ == "__main__":
    main()