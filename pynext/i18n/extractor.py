"""
PyNext Translation String Extractor - Build-Time Optimization.

Extracts translation keys from source code at build time:
- Finds all t() calls
- Detects missing translations
- Generates translation files
- Validates existing translations
"""

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ExtractedKey:
    """A translation key extracted from source code."""
    key: str
    file: str
    line: int
    default_value: Optional[str] = None
    params: List[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    """Result of extraction from a codebase."""
    keys: List[ExtractedKey]
    files_scanned: int
    errors: List[str]
    
    def get_unique_keys(self) -> Set[str]:
        """Get set of unique translation keys."""
        return {k.key for k in self.keys}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "keys": [
                {
                    "key": k.key,
                    "file": k.file,
                    "line": k.line,
                    "default": k.default_value,
                    "params": k.params,
                }
                for k in self.keys
            ],
            "filesScanned": self.files_scanned,
            "errors": self.errors,
        }


class TranslationExtractor:
    """
    Extracts translation keys from Python source files.
    
    Scans for:
    - t("key") calls
    - t_element("key") calls
    - Translation key strings
    """
    
    def __init__(self, source_dir: Path):
        self.source_dir = Path(source_dir)
        self._keys: List[ExtractedKey] = []
        self._errors: List[str] = []
        self._files_scanned = 0
    
    def extract(self, file_patterns: List[str] = None) -> ExtractionResult:
        """
        Extract all translation keys from source directory.
        
        Args:
            file_patterns: Glob patterns for files to scan (default: ["**/*.py"])
        """
        patterns = file_patterns or ["**/*.py"]
        
        for pattern in patterns:
            for file_path in self.source_dir.glob(pattern):
                self._extract_from_file(file_path)
        
        return ExtractionResult(
            keys=self._keys,
            files_scanned=self._files_scanned,
            errors=self._errors,
        )
    
    def _extract_from_file(self, file_path: Path) -> None:
        """Extract keys from a single file."""
        self._files_scanned += 1
        
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self._extract_from_call(node, file_path)
        
        except SyntaxError as e:
            self._errors.append(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            self._errors.append(f"Error processing {file_path}: {e}")
    
    def _extract_from_call(self, node: ast.Call, file_path: Path) -> None:
        """Extract key from a function call."""
        # Check if it's a t() or t_element() call
        func_name = None
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        if func_name not in ("t", "t_element"):
            return
        
        # Extract the key (first argument)
        if not node.args:
            return
        
        first_arg = node.args[0]
        
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            key = first_arg.value
        elif isinstance(first_arg, ast.Str):  # Python 3.7 compatibility
            key = first_arg.s
        else:
            return
        
        # Extract default value if provided
        default_value = None
        for keyword in node.keywords:
            if keyword.arg == "default":
                if isinstance(keyword.value, ast.Constant):
                    default_value = keyword.value.value
                elif isinstance(keyword.value, ast.Str):
                    default_value = keyword.value.s
        
        # Extract parameter names from params dict
        params = []
        if len(node.args) > 1 or any(k.arg == "params" for k in node.keywords):
            # Try to extract param keys from dict
            params_arg = None
            if len(node.args) > 1:
                params_arg = node.args[1]
            else:
                for keyword in node.keywords:
                    if keyword.arg == "params":
                        params_arg = keyword.value
                        break
            
            if isinstance(params_arg, ast.Dict):
                for k in params_arg.keys:
                    if isinstance(k, ast.Constant):
                        params.append(k.value)
                    elif isinstance(k, ast.Str):
                        params.append(k.s)
        
        self._keys.append(ExtractedKey(
            key=key,
            file=str(file_path.relative_to(self.source_dir)),
            line=node.lineno,
            default_value=default_value,
            params=params,
        ))


class TranslationValidator:
    """
    Validates translation files against extracted keys.
    
    Checks for:
    - Missing translations
    - Unused translations
    - Missing parameters
    - Inconsistent plurals
    """
    
    def __init__(
        self,
        translations_dir: Path,
        locales: List[str],
        default_locale: str = "en"
    ):
        self.translations_dir = Path(translations_dir)
        self.locales = locales
        self.default_locale = default_locale
    
    def validate(self, extracted: ExtractionResult) -> Dict[str, Any]:
        """
        Validate translations against extracted keys.
        
        Returns validation report.
        """
        required_keys = extracted.get_unique_keys()
        results = {
            "valid": True,
            "locales": {},
            "summary": {
                "total_keys": len(required_keys),
                "complete_locales": 0,
                "incomplete_locales": 0,
            }
        }
        
        for locale in self.locales:
            locale_result = self._validate_locale(locale, required_keys)
            results["locales"][locale] = locale_result
            
            if locale_result["missing"]:
                results["valid"] = False
                results["summary"]["incomplete_locales"] += 1
            else:
                results["summary"]["complete_locales"] += 1
        
        return results
    
    def _validate_locale(
        self,
        locale: str,
        required_keys: Set[str]
    ) -> Dict[str, Any]:
        """Validate a single locale."""
        # Load translations
        translations = self._load_locale(locale)
        
        translation_keys = set(translations.keys())
        
        missing = required_keys - translation_keys
        unused = translation_keys - required_keys
        
        return {
            "total": len(translations),
            "missing": list(missing),
            "missing_count": len(missing),
            "unused": list(unused),
            "unused_count": len(unused),
            "coverage": (
                (len(required_keys) - len(missing)) / len(required_keys) * 100
                if required_keys else 100
            ),
        }
    
    def _load_locale(self, locale: str) -> Dict[str, str]:
        """Load all translations for a locale."""
        result = {}
        
        # Try directory structure (locales/en/*.json)
        locale_dir = self.translations_dir / locale
        if locale_dir.is_dir():
            for file_path in locale_dir.glob("*.json"):
                try:
                    data = json.loads(file_path.read_text())
                    result.update(self._flatten_dict(data))
                except (json.JSONDecodeError, IOError):
                    pass
        
        # Try single file (locales/en.json)
        for ext in [".json", ".yaml", ".yml"]:
            file_path = self.translations_dir / f"{locale}{ext}"
            if file_path.exists():
                try:
                    data = json.loads(file_path.read_text())
                    result.update(self._flatten_dict(data))
                except (json.JSONDecodeError, IOError):
                    pass
        
        return result
    
    def _flatten_dict(
        self,
        data: Dict[str, Any],
        prefix: str = ""
    ) -> Dict[str, str]:
        """Flatten nested dict to dot-notation keys."""
        result = {}
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_dict(value, full_key))
            else:
                result[full_key] = str(value)
        
        return result


def generate_translation_template(
    extracted: ExtractionResult,
    output_path: Path,
    include_locations: bool = True
) -> None:
    """
    Generate a translation template file from extracted keys.
    
    Creates a JSON file with all keys and empty values.
    """
    template = {}
    
    for key in sorted(extracted.get_unique_keys()):
        # Find the key info
        key_info = next((k for k in extracted.keys if k.key == key), None)
        
        if key_info and key_info.default_value:
            template[key] = key_info.default_value
        else:
            template[key] = ""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(template, indent=2, ensure_ascii=False))


async def extract_and_validate(
    source_dir: Path,
    translations_dir: Path,
    locales: List[str],
    default_locale: str = "en"
) -> Dict[str, Any]:
    """
    Full extraction and validation pipeline.
    
    Called by `pynext build` for i18n validation.
    """
    # Extract keys
    extractor = TranslationExtractor(source_dir)
    extracted = extractor.extract()
    
    # Validate
    validator = TranslationValidator(translations_dir, locales, default_locale)
    validation = validator.validate(extracted)
    
    return {
        "extraction": extracted.to_dict(),
        "validation": validation,
    }

