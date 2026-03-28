import zipfile
import os
from .models import ProjectLanguage

# Map extensions to Language Names
EXTENSION_MAP = {
    # Web
    '.py': 'Python',
    '.js': 'JavaScript',
    '.html': 'HTML',
    '.css': 'CSS',
    '.ts': 'TypeScript',
    '.php': 'PHP',
    '.vue': 'Vue',
    '.jsx': 'React',
    
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
    '.m': 'MATLAB',
}

def analyze_zip_and_create_languages(zip_file, project_instance):
    """
    Reads a zip file, counts file extensions, and creates ProjectLanguage entries.
    """
    try:
        # Open the zip file in read mode
        with zipfile.ZipFile(zip_file, 'r') as z:
            # List all file names in the zip
            all_files = z.namelist()
            
            ext_counts = {}
            total_files = 0
            
            for filename in all_files:
                # Ignore folders and hidden files (like .git)
                if filename.endswith('/') or '/.' in filename or filename.startswith('.'):
                    continue
                
                # Get extension (e.g., .py)
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                
                if ext in EXTENSION_MAP:
                    lang = EXTENSION_MAP[ext]
                    ext_counts[lang] = ext_counts.get(lang, 0) + 1
                    total_files += 1

            # If we found code files, calculate percentages and save
            if total_files > 0:
                # Clear old languages (in case of re-upload)
                project_instance.languages.all().delete()
                
                for lang, count in ext_counts.items():
                    percentage = int((count / total_files) * 100)
                    if percentage > 0: # Only save if > 0%
                        ProjectLanguage.objects.create(
                            project=project_instance,
                            language_name=lang,
                            percentage=percentage
                        )
    except Exception as e:
        print(f"Error analyzing zip: {e}")