#!/usr/bin/env python
"""Structural conformance check for an analysis under cafpybara/analyses/.

Formalizes the manual `conformance_check()` from
`analyses/_template/examples/build_a_new_analysis.ipynb` into a standalone,
reusable script, and extends it with two checks that notebook only covers
by hand. Every check here is purely structural (module attributes,
function/dataclass signatures, notebook source via ast) -- no real data,
no Fermilab/EAF access needed. Run with the parent of `cafpybara/` on your
PYTHONPATH, same requirement as every other script in this package.

Usage:
    python scripts/verify_new_analysis.py <name> [<name> ...]
    python scripts/verify_new_analysis.py --all

Exits non-zero (with a per-check PASS/FAIL summary) if any check fails.

What this catches (checks 1-2 mirror the notebook's conformance_check();
3-4 are new):
  1. Every core.* submodule the template's __init__.py re-exports is fully
     re-exported by the analysis too -- catches missing `from ...core.X
     import *` lines (found repeatedly while building this project:
     core.io/funcs/plotting/selection/physics all went missing at least
     once, each a live AttributeError the moment a notebook hit it).
  2. `analysis.get_total_cov is core.funcs.get_total_cov`, and a
     `systs_input` factory exists -- catches reintroducing a per-analysis
     get_total_cov wrapper, i.e. the Path A/B divergence bug this
     project's core redesign closed.
  3. A curated per-analysis list of "this preprocess_fn default must not
     still be core's generic no-op" -- catches an analysis's load_mc/
     load_data/load_mchnl-style loader silently defaulting to
     core.preprocess.preprocess_mc/preprocess_data instead of its own real
     bundler (the original, most consequential bug found this way: nueCC's
     own load_mc/load_data, then hnlpi0.load_mchnl, were each
     independently found wired to the no-op).
  4. ast-parses every notebook under analyses/<name>/examples/ and checks
     every keyword argument to <alias>.systs_input(...)/SystematicsInput(
     ...)/PlottingConfig(...) against the real parameter/field names --
     catches a dead kwarg surviving a signature change (e.g. the
     select_region='all' argument that lingered in hnl_analysis_v6.ipynb
     after SystematicsInput dropped that field, undetected until a live run).

Explicit non-goals: this catches "wiring is wrong," not "physics is
wrong" -- it cannot replace a real live run against real data (e.g.
verify_1shw_drift_check.ipynb's detvar-drift test, which needed an actual
row-count change to confirm). It also inherits conformance_check()'s one
known limitation: it can't detect a missing re-export for a name the
analysis's own file locally shadows, only total absence.
"""
from __future__ import annotations

import argparse
import ast
import dataclasses
import importlib
import inspect
import json
import pkgutil
import sys
from pathlib import Path

import cafpybara.core as core
from cafpybara.core.classes import SystematicsInput, PlottingConfig

ANALYSES_DIR = Path(__file__).resolve().parents[1] / 'analyses'

FAILURES = []


def check(label, cond, detail=None):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}")
    if detail and not cond:
        print(f"         {detail}")
    if not cond:
        FAILURES.append(label)
    return cond


def info(msg):
    print(f"  [INFO] {msg}")


# ---------------------------------------------------------------------------
# Check 1: full core.* re-export, using _template/__init__.py's own
# `from ...core.X import *` block as the canonical list of modules every
# analysis must re-export (its docstring already designates it as the
# source of truth: "Keep this re-export block exactly as-is when copying
# the template"). Avoids hardcoding a list that could silently go stale.
# ---------------------------------------------------------------------------

def canonical_core_modules():
    template_init = ANALYSES_DIR / '_template' / '__init__.py'
    tree = ast.parse(template_init.read_text())
    mods = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.ImportFrom) and node.level == 3
                and node.module and node.module.startswith('core.')
                and any(a.name == '*' for a in node.names)):
            mods.append(node.module.split('.', 1)[1])
    return mods


def public_names(module):
    """Names `module` intends to export: its own __all__, plus (for a
    subpackage with no __all__ of its own, e.g. core.detvar) the union of
    its submodules' __all__ -- otherwise a subpackage whose __init__.py
    never sets __all__ would trivially "pass" this check with zero names
    actually verified.
    """
    names = set(getattr(module, '__all__', []))
    if hasattr(module, '__path__'):
        for _, subname, _ in pkgutil.iter_modules(module.__path__):
            if subname.startswith('_'):
                continue
            try:
                submod = importlib.import_module(f'{module.__name__}.{subname}')
            except ImportError:
                continue
            names |= set(getattr(submod, '__all__', []))
    return names


def check_reexports(analysis_module):
    print("-- Check 1: core.* re-export completeness --")
    for mod_name in canonical_core_modules():
        core_mod = importlib.import_module(f'cafpybara.core.{mod_name}')
        names = public_names(core_mod)
        missing = sorted(n for n in names if not hasattr(analysis_module, n))
        check(f"core.{mod_name} ({len(names)} names)", not missing,
              detail=f"missing: {missing}" if missing else None)


# ---------------------------------------------------------------------------
# Check 2: get_total_cov identity + systs_input presence.
# ---------------------------------------------------------------------------

def check_get_total_cov(analysis_module):
    print("-- Check 2: get_total_cov / systs_input --")
    check(
        "get_total_cov is core.funcs.get_total_cov (no analysis-local override)",
        getattr(analysis_module, 'get_total_cov', None) is core.funcs.get_total_cov,
    )
    check(
        "systs_input() factory exists",
        hasattr(analysis_module, 'systs_input') and callable(analysis_module.systs_input),
    )


# ---------------------------------------------------------------------------
# Check 3: curated no-op-preprocess-default audit. One entry per analysis
# that has a loader needing real (non-generic) preprocessing. Not derivable
# from core's own structure -- this encodes project-specific knowledge, so
# it needs upkeep as new analyses/loaders are added. An analysis absent
# from this table isn't a failure, just unaudited (printed as INFO).
#
# Each entry: (module_name, function_name, param_name, forbidden_default).
# `forbidden_default` is looked up as an attribute path off `core`.
# ---------------------------------------------------------------------------

NOOP_DEFAULT_CHECKS = {
    'nuecc': [
        ('io', 'load_mc', 'preprocess_fn', 'preprocess.preprocess_mc'),
        ('io', 'load_data', 'preprocess_fn', 'preprocess.preprocess_data'),
    ],
    'hnlpi0': [
        # load_mc/load_data deliberately default to core's no-op here (see
        # their own docstrings -- real preprocessing is passed per-call,
        # e.g. preprocess_mcbnb); only load_mchnl has a real default to check.
        ('io', 'load_mchnl', 'preprocess_fn', 'preprocess.preprocess_mc'),
    ],
    '_template': [
        ('io', 'load_mc', 'preprocess_fn', 'preprocess.preprocess_mc'),
        ('io', 'load_data', 'preprocess_fn', 'preprocess.preprocess_data'),
    ],
}


def check_noop_defaults(name, analysis_module):
    print("-- Check 3: no-op preprocessing default audit --")
    entries = NOOP_DEFAULT_CHECKS.get(name)
    if not entries:
        info(f"no entries configured for '{name}' in NOOP_DEFAULT_CHECKS -- "
             f"add some in scripts/verify_new_analysis.py if this analysis "
             f"has a loader that needs real (non-generic) preprocessing.")
        return
    for mod_name, fn_name, param_name, forbidden_path in entries:
        mod = importlib.import_module(f'cafpybara.analyses.{name}.{mod_name}')
        fn = getattr(mod, fn_name)
        forbidden = core
        for part in forbidden_path.split('.'):
            forbidden = getattr(forbidden, part)
        default = inspect.signature(fn).parameters[param_name].default
        check(
            f"{name}.{mod_name}.{fn_name}'s {param_name}= is not core.{forbidden_path}",
            default is not forbidden,
            detail=f"defaults to core.{forbidden_path} -- the generic no-op",
        )


# ---------------------------------------------------------------------------
# Check 4: ast-audit every example notebook's SystematicsInput/systs_input/
# PlottingConfig call sites' keyword arguments against the real signatures.
# ---------------------------------------------------------------------------

def valid_kwargs_for(name, analysis_module):
    """Valid keyword-argument names for each checked call shape.

    systs_input's own explicit parameters, plus SystematicsInput's field
    names (every real systs_input() implementation forwards **kwargs
    straight into SystematicsInput(...) -- true for every analysis today;
    if a future analysis's systs_input does something else with **kwargs,
    this heuristic would need revisiting).
    """
    systs_input_fn = getattr(analysis_module, 'systs_input', None)
    systs_input_params = set()
    if systs_input_fn is not None:
        for pname, p in inspect.signature(systs_input_fn).parameters.items():
            if p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                systs_input_params.add(pname)
    si_fields = {f.name for f in dataclasses.fields(SystematicsInput)}
    pc_fields = {f.name for f in dataclasses.fields(PlottingConfig)}
    return {
        'systs_input': systs_input_params | si_fields,
        'SystematicsInput': si_fields,
        'PlottingConfig': pc_fields,
    }


def find_analysis_alias(tree, name):
    """Find the `as X` alias bound to `import cafpybara.analyses.<name>`."""
    target = f'cafpybara.analyses.{name}'
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == target:
                    return alias.asname or alias.name.rsplit('.', 1)[-1]
    return None


def audit_notebook(path, name, valid_kwargs):
    nb = json.loads(path.read_text())
    source = "\n".join(
        "".join(cell.get('source', []))
        for cell in nb.get('cells', [])
        if cell.get('cell_type') == 'code'
    )
    # Strip IPython magics/shell escapes -- not valid Python syntax.
    clean_lines = [ln for ln in source.splitlines()
                   if not ln.lstrip().startswith(('%', '!'))]
    tree = ast.parse("\n".join(clean_lines))

    alias = find_analysis_alias(tree, name)
    if alias is None:
        info(f"{path.name}: no 'import cafpybara.analyses.{name} as X' found, skipping")
        return

    checked_any = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        call_name = node.func.attr
        if call_name not in valid_kwargs:
            continue
        if not (isinstance(node.func.value, ast.Name) and node.func.value.id == alias):
            continue
        checked_any = True
        bad = sorted(kw.arg for kw in node.keywords
                     if kw.arg is not None and kw.arg not in valid_kwargs[call_name])
        check(
            f"{path.name}: {alias}.{call_name}(...) at line {node.lineno}",
            not bad,
            detail=f"unknown kwarg(s): {bad}",
        )
    if not checked_any:
        info(f"{path.name}: no systs_input/SystematicsInput/PlottingConfig calls found")


def check_notebooks(name, analysis_module):
    print("-- Check 4: notebook SystematicsInput/PlottingConfig kwargs --")
    examples_dir = ANALYSES_DIR / name / 'examples'
    if not examples_dir.is_dir():
        info(f"no examples/ directory for '{name}', skipping")
        return
    valid_kwargs = valid_kwargs_for(name, analysis_module)
    notebooks = sorted(examples_dir.glob('*.ipynb'))
    if not notebooks:
        info(f"no notebooks under {examples_dir}, skipping")
        return
    for nb_path in notebooks:
        audit_notebook(nb_path, name, valid_kwargs)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run(name):
    print(f"\n=== {name} ===")
    analysis_module = importlib.import_module(f'cafpybara.analyses.{name}')
    check_reexports(analysis_module)
    check_get_total_cov(analysis_module)
    check_noop_defaults(name, analysis_module)
    check_notebooks(name, analysis_module)


def discover_analyses():
    return sorted(
        p.name for p in ANALYSES_DIR.iterdir()
        if p.is_dir() and (p / '__init__.py').is_file()
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('names', nargs='*', help="analysis name(s), e.g. hnlpi0 nuecc")
    parser.add_argument('--all', action='store_true', help="check every analysis under analyses/")
    args = parser.parse_args()

    names = discover_analyses() if args.all else args.names
    if not names:
        parser.error("pass at least one analysis name, or --all")

    for name in names:
        run(name)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == '__main__':
    main()
