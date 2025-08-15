import os

def list_project_files(startpath, exclude_dirs=None, exclude_files=None):
    """
    Belirtilen bir dizindeki tüm dosya ve klasörleri ağaç yapısında listeler.
    Belirli klasör ve dosyaları hariç tutar.
    """
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', '.idea', 'venv', '.vscode', 'ui_runs'}
    if exclude_files is None:
        exclude_files = {'.DS_Store', 'list_files.py'}

    for root, dirs, files in os.walk(startpath, topdown=True):
        # Hariç tutulacak klasörleri listeden çıkar
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f'{indent}├─ {os.path.basename(root)}/')

        subindent = ' ' * 4 * (level + 1)
        for f in sorted(files):
            if f not in exclude_files:
                print(f'{subindent}├─ {f}')

if __name__ == "__main__":
    # Bu script'in bulunduğu dizini başlangıç noktası olarak al
    project_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Proje Dizini: {project_path}")
    print("="*40)
    list_project_files(project_path)
    print("="*40)