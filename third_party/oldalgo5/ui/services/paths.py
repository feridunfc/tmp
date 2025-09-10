import pathlib, json
def project_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]
def artifacts_dir() -> pathlib.Path:
    d = project_root() / "artifacts"; d.mkdir(exist_ok=True, parents=True); return d
def db_path() -> pathlib.Path: return artifacts_dir() / "experiments.db"
def models_dir() -> pathlib.Path:
    d = artifacts_dir() / "models"; d.mkdir(exist_ok=True, parents=True); return d
def equities_dir() -> pathlib.Path:
    d = artifacts_dir() / "equities"; d.mkdir(exist_ok=True, parents=True); return d
def reports_dir() -> pathlib.Path:
    d = artifacts_dir() / "reports"; d.mkdir(exist_ok=True, parents=True); return d
def save_json(path: pathlib.Path, obj): path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
