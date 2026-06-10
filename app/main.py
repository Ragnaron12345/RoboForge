from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.generator import generate_project_files
from app.report_exporter import export_report_pdf
from app.wokwi_exporter import export_wokwi

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

EDITABLE_EXTENSIONS = {".md", ".ino", ".py", ".txt", ".json", ".scad"}

app = FastAPI(title="Robo Forge")
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = value.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "projekt"


def list_projects() -> list[str]:
    return sorted([p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()], reverse=True)


def safe_project_dir(project_name: str) -> Path:
    project_dir = (PROJECTS_DIR / project_name).resolve()
    if PROJECTS_DIR.resolve() not in project_dir.parents and project_dir != PROJECTS_DIR.resolve():
        raise ValueError("Ungültiger Projektpfad.")
    if not project_dir.exists() or not project_dir.is_dir():
        raise ValueError("Projekt wurde nicht gefunden.")
    return project_dir


def safe_file_path(project_name: str, filename: str) -> Path:
    project_dir = safe_project_dir(project_name)
    path = (project_dir / filename).resolve()
    if project_dir not in path.parents and path != project_dir:
        raise ValueError("Ungültiger Dateipfad.")
    if path.suffix.lower() not in EDITABLE_EXTENSIONS:
        raise ValueError("Dieser Dateityp kann im Editor nicht bearbeitet werden.")
    return path


def list_project_files(project_name: str | None) -> list[str]:
    if not project_name:
        return []
    try:
        project_dir = safe_project_dir(project_name)
    except ValueError:
        return []
    files: list[str] = []
    for path in project_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in EDITABLE_EXTENSIONS:
            files.append(str(path.relative_to(project_dir)).replace("\\", "/"))
    return sorted(files)


def read_project_meta(project_dir: Path) -> tuple[str, str]:
    idea = project_dir / "project_idea.md"
    title = project_dir.name
    description = ""
    if idea.exists():
        text = idea.read_text(encoding="utf-8")
        lines = text.splitlines()
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
            description = "\n".join(lines[1:]).strip()
    return title, description


def read_selected_file(project_name: str | None, filename: str | None) -> tuple[str, str]:
    if not project_name or not filename:
        return "", ""
    try:
        path = safe_file_path(project_name, filename)
        if not path.exists():
            return "", f"Datei {filename} existiert noch nicht."
        return path.read_text(encoding="utf-8"), ""
    except Exception as error:
        return "", str(error)


def available_outputs(project_name: str | None) -> dict[str, bool]:
    if not project_name:
        return {"pdf": False, "wokwi": False, "scad": False}
    try:
        project_dir = safe_project_dir(project_name)
        return {
            "pdf": (project_dir / "report.pdf").exists(),
            "wokwi": (project_dir / "wokwi" / "diagram.json").exists(),
            "scad": (project_dir / "model.scad").exists(),
        }
    except Exception:
        return {"pdf": False, "wokwi": False, "scad": False}


def page_context(
    request: Request,
    selected_project: str | None = None,
    selected_file: str | None = None,
    file_content: str = "",
    status: str | None = None,
    warnings: list[str] | None = None,
):

    if selected_project and not selected_file:
        files = list_project_files(selected_project)
        selected_file = files[0] if files else None
        if selected_file and not file_content:
            file_content, err = read_selected_file(selected_project, selected_file)
            if err:
                warnings = (warnings or []) + [err]
    return {
        "request": request,
        "projects": list_projects(),
        "selected_project": selected_project,
        "project_files": list_project_files(selected_project),
        "selected_file": selected_file,
        "file_content": file_content,
        "status": status,
        "warnings": warnings or [],
        "outputs": available_outputs(selected_project),
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request, project: str | None = None, file: str | None = None):
    content, err = read_selected_file(project, file)
    warnings = [err] if err else []
    return templates.TemplateResponse("index.html", page_context(request, project, file, content, warnings=warnings))


@app.post("/projects", response_class=HTMLResponse)
def create_project(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    project_name = f"{timestamp}-{slugify(title)}"
    project_dir = PROJECTS_DIR / project_name
    project_dir.mkdir(parents=True, exist_ok=False)
    (project_dir / "project_idea.md").write_text(f"# {title}\n\n{description}\n", encoding="utf-8")
    generated: list[str] = ["project_idea.md"]
    warnings: list[str] = []
    files, gen_warnings = generate_project_files(project_dir, title, description)
    generated.extend(files)
    warnings.extend(gen_warnings)

    report_files, report_warnings = export_report_pdf(project_dir, title, description)
    generated.extend(report_files)
    warnings.extend(report_warnings)
    status = f"Projekt '{project_name}' wurde erstellt. Dateien: {', '.join(generated)}"
    return templates.TemplateResponse("index.html", page_context(request, project_name, status=status, warnings=warnings))


@app.get("/projects/{project_name}", response_class=HTMLResponse)
def open_project(request: Request, project_name: str, file: str | None = None):
    content, err = read_selected_file(project_name, file)
    warnings = [err] if err else []
    return templates.TemplateResponse("index.html", page_context(request, project_name, file, content, warnings=warnings))


@app.post("/projects/{project_name}/save", response_class=HTMLResponse)
def save_project_file(request: Request, project_name: str, filename: str = Form(...), content: str = Form("")):
    warnings: list[str] = []
    try:
        path = safe_file_path(project_name, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        status = f"Datei '{filename}' wurde gespeichert."
    except Exception as error:
        status = None
        warnings.append(f"Speichern fehlgeschlagen: {error}")
    return templates.TemplateResponse("index.html", page_context(request, project_name, filename, content, status=status, warnings=warnings))


@app.post("/projects/{project_name}/export-report", response_class=HTMLResponse)
def build_report(request: Request, project_name: str):
    warnings: list[str] = []
    try:
        project_dir = safe_project_dir(project_name)
        title, description = read_project_meta(project_dir)
        files, report_warnings = export_report_pdf(project_dir, title, description)
        warnings.extend(report_warnings)
        status = f"Bericht wurde erstellt: {', '.join(files)}" if files else "Bericht konnte nicht erstellt werden."
    except Exception as error:
        status = None
        warnings.append(f"PDF-Erstellung fehlgeschlagen: {error}")
    return templates.TemplateResponse("index.html", page_context(request, project_name, status=status, warnings=warnings))


@app.post("/projects/{project_name}/export-wokwi", response_class=HTMLResponse)
def build_wokwi(request: Request, project_name: str):
    warnings: list[str] = []
    try:
        project_dir = safe_project_dir(project_name)
        title, description = read_project_meta(project_dir)
        spec = (project_dir / "project_spec.md").read_text(encoding="utf-8") if (project_dir / "project_spec.md").exists() else ""
        files = export_wokwi(project_dir, title, description, spec)
        status = f"Wokwi-Dateien wurden erstellt: {', '.join(files)}"
    except Exception as error:
        status = None
        warnings.append(f"Wokwi-Dateien konnten nicht erstellt werden: {error}")
    return templates.TemplateResponse("index.html", page_context(request, project_name, status=status, warnings=warnings))


@app.get("/projects/{project_name}/open/{file_path:path}")
def open_project_file(project_name: str, file_path: str):
    project_dir = safe_project_dir(project_name)
    path = (project_dir / file_path).resolve()
    if project_dir not in path.parents and path != project_dir:
        raise ValueError("Ungültiger Dateipfad.")
    if not path.exists():
        raise ValueError("Datei wurde nicht gefunden.")
    media = "application/pdf" if path.suffix.lower() == ".pdf" else "text/plain; charset=utf-8"
    return FileResponse(path, media_type=media, filename=path.name, content_disposition_type="inline")


def open_file_with_os(path: Path) -> None:
    # Keep imports inside the function as well, so this route still works
    # even if an older server process or a copied main.py misses a global import.
    import shutil as _shutil
    import subprocess as _subprocess

    if path.suffix.lower() == ".scad":
        candidates = [_shutil.which("openscad")]
        if sys.platform.startswith("win"):
            candidates += [
                "C:/Program Files/OpenSCAD/openscad.exe",
                "C:/Program Files (x86)/OpenSCAD/openscad.exe",
            ]
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                _subprocess.Popen([str(candidate), str(path)])
                return
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        _subprocess.Popen(["open", str(path)])
    else:
        _subprocess.Popen(["xdg-open", str(path)])


@app.post("/projects/{project_name}/open-model-local", response_class=HTMLResponse)
def open_model_local(request: Request, project_name: str):
    warnings: list[str] = []
    status: str | None = None
    try:
        project_dir = safe_project_dir(project_name)
        path = (project_dir / "model.scad").resolve()
        if not path.exists():
            raise ValueError("model.scad wurde nicht gefunden.")
        open_file_with_os(path)
        status = "model.scad wurde mit der Standard-App des Computers geöffnet."
    except Exception as error:
        warnings.append(f"model.scad konnte nicht lokal geöffnet werden: {error}")
    return templates.TemplateResponse("index.html", page_context(request, project_name, status=status, warnings=warnings))


@app.get("/projects/{project_name}/wokwi", response_class=HTMLResponse)
def wokwi_export_page(request: Request, project_name: str):
    project_dir = safe_project_dir(project_name)
    diagram = project_dir / "wokwi" / "diagram.json"
    if not diagram.exists():
        title, description = read_project_meta(project_dir)
        spec = (project_dir / "project_spec.md").read_text(encoding="utf-8") if (project_dir / "project_spec.md").exists() else ""
        export_wokwi(project_dir, title, description, spec)
    diagram_text = diagram.read_text(encoding="utf-8")
    return templates.TemplateResponse("wokwi_export.html", {"request": request, "project_name": project_name, "diagram_text": diagram_text})
