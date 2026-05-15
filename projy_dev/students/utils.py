import zipfile
import os
from .models import ProjectLanguage

EXTENSION_MAP = {
    # Web
    '.py': 'Python',
    '.js': 'JavaScript',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'CSS',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.jsx': 'JavaScript',
    '.php': 'PHP',
    '.vue': 'Vue',

    # Core
    '.java': 'Java',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.c': 'C',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.sh': 'Shell',
    '.ps1': 'PowerShell',

    # Mobile
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.dart': 'Dart',
    '.m': 'Objective-C',

    # Data / Other
    '.rb': 'Ruby',
    '.r': 'R',
    '.sql': 'SQL',
    '.lua': 'Lua',
    '.pl': 'Perl',
    '.scala': 'Scala',
    '.hs': 'Haskell',
    '.ino': 'Arduino',
    '.asm': 'Assembly',
    '.mat': 'MATLAB',
}

# Files/dirs to always skip (vendored code, build output, etc.)
SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', 'venv', 'env',
    'dist', 'build', '.next', '.nuxt', 'vendor', 'bower_components',
    'target', 'bin', 'obj', '.idea', '.vscode',
}


def _should_skip(filename):
    parts = filename.replace('\\', '/').split('/')
    for part in parts:
        if part in SKIP_DIRS or part.startswith('.'):
            return True
    return False


def analyze_zip_and_create_languages(zip_file, project_instance):
    """
    Reads a zip file, counts bytes per language (GitHub-style),
    and saves ProjectLanguage entries that sum to exactly 100%.
    """
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            byte_counts = {}

            for info in z.infolist():
                filename = info.filename

                # Skip directories and vendored/hidden paths
                if filename.endswith('/') or _should_skip(filename):
                    continue

                _, ext = os.path.splitext(filename)
                ext = ext.lower()

                if ext in EXTENSION_MAP:
                    lang = EXTENSION_MAP[ext]
                    # Use uncompressed byte size; treat empty files as 1 byte so they register
                    byte_counts[lang] = byte_counts.get(lang, 0) + max(info.file_size, 1)

            total_bytes = sum(byte_counts.values())

            if total_bytes == 0:
                return

            # Delete old language entries before re-creating
            project_instance.languages.all().delete()

            # --- Largest Remainder Method ---
            # Guarantees integer percentages that sum to exactly 100
            exact = {lang: (b / total_bytes) * 100 for lang, b in byte_counts.items()}
            floors = {lang: int(pct) for lang, pct in exact.items()}
            remainders = {lang: exact[lang] - floors[lang] for lang in floors}

            deficit = 100 - sum(floors.values())
            # Give the +1s to the languages with the biggest fractional remainders
            for lang in sorted(remainders, key=remainders.get, reverse=True)[:deficit]:
                floors[lang] += 1

            # Save sorted by percentage descending; skip any that rounded to 0
            for lang, pct in sorted(floors.items(), key=lambda x: x[1], reverse=True):
                if pct > 0:
                    ProjectLanguage.objects.create(
                        project=project_instance,
                        language_name=lang,
                        percentage=pct,
                    )

    except Exception as e:
        print(f"Error analyzing zip: {e}")
