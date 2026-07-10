from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.change_planner import ChangePlanner
from app.conversation_agent import ConversationAgent
from app.conversation_store import ConversationStore, validate_session_id
from app.data_table import DataTableManager
from app.document_manager import DocumentManager
from app.pending_store import PendingStore
from app.rag import RagStore
from app.rag_service import RAGService
from app.settings import PROJECT_ROOT, Settings
from app.source_gdd_builder import SourceGddBuilder
from app.validators import ConsistencyChecker
from app.web_models import PendingChange, PendingFile


app = FastAPI(title="SpellTalker Design Agent")
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "static"), name="static")
templates = Jinja2Templates(directory=PROJECT_ROOT / "templates")

settings = Settings()
manager = DocumentManager(settings)
data_manager = DataTableManager(settings)
pending_change: PendingChange | None = None
flash_message = ""
conversation_store = ConversationStore(settings)
pending_store = PendingStore(settings)


def render(request: Request, template: str, **context: Any) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        template,
        {
            "active": "",
            "pending_change": pending_change,
            "flash_message": flash_message,
            "settings": settings,
            **context,
        },
    )


def set_flash(message: str) -> None:
    global flash_message
    flash_message = message


def clear_flash() -> str:
    global flash_message
    message = flash_message
    flash_message = ""
    return message


def safe_doc_path(raw_path: str) -> Path:
    decoded = raw_path.strip("/")
    candidate = (PROJECT_ROOT / decoded).resolve()
    allowed_roots = [
        settings.docs_workspace.resolve(),
        settings.source_docs.resolve(),
        settings.reports_path.resolve(),
    ]
    if not any(candidate == root or root in candidate.parents for root in allowed_roots):
        raise HTTPException(status_code=404, detail="Document path is not allowed.")
    if not candidate.exists() or candidate.suffix.lower() != ".md":
        raise HTTPException(status_code=404, detail="Markdown document not found.")
    return candidate


def build_chat_pending(idea: str) -> PendingChange:
    rag = RAGService(settings)
    planner = ChangePlanner(settings)
    context = rag.search(idea)
    plan = planner.create_plan(idea, context)
    files = []
    for target in plan["targets"]:
        path, _old, new = manager.build_update(str(target), idea, str(plan["markdown"]))
        diff = manager.diff(path, path.read_text(encoding="utf-8") if path.exists() else "", new)
        files.append(PendingFile(path=str(path), content=new, diff=diff))
    return PendingChange(
        kind="chat",
        title="기획 변경 제안",
        idea=idea,
        plan=str(plan["markdown"]),
        files=files,
        metadata={"targets": ", ".join(str(target) for target in plan["targets"])},
    )


def build_gdd_pending() -> PendingChange:
    builder = SourceGddBuilder(settings)
    sources = builder.load_sources()
    if not sources:
        return PendingChange(
            kind="build-gdd",
            title="GDD 자동 생성",
            files=[],
            message=f"source_docs에 Markdown 문서가 없습니다: {settings.source_docs}",
        )
    mapped = builder.map_sources(sources)
    drafts = builder.build_drafts(mapped, sources)
    files = []
    for path, new in drafts.items():
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        files.append(PendingFile(path=str(path), content=new, diff=manager.diff(path, old, new)))
    return PendingChange(
        kind="build-gdd",
        title="source_docs 기반 GDD 초안",
        files=files,
        message=f"{len(sources)}개 source 문서에서 {len(files)}개 GDD 초안을 생성했습니다.",
    )


def markdown_docs() -> list[dict[str, str]]:
    roots = [
        ("GDD", settings.docs_workspace / "GDD"),
        ("Dev", settings.docs_workspace / "Dev"),
        ("Source", settings.source_docs),
        ("Reports", settings.reports_path),
    ]
    docs = []
    for label, root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            docs.append(
                {
                    "group": label,
                    "name": path.name,
                    "path": path.relative_to(PROJECT_ROOT).as_posix(),
                }
            )
    return docs


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    message = clear_flash()
    return render(request, "index.html", active="home", flash_message=message)


@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request) -> HTMLResponse:
    message = clear_flash()
    conversation = conversation_store.create()
    return render(
        request,
        "chat.html",
        active="chat",
        flash_message=message,
        sessions=conversation_store.list_sessions(),
        conversation=conversation,
        session_pending=None,
    )


@app.post("/chat", response_class=HTMLResponse)
def chat_submit(request: Request, idea: str = Form(...)) -> HTMLResponse:
    global pending_change
    idea = idea.strip()
    if not idea:
        return render(request, "chat.html", active="chat", error="아이디어를 입력하세요.")
    try:
        pending_change = build_chat_pending(idea)
    except Exception as exc:
        return render(request, "chat.html", active="chat", idea=idea, error=f"분석 실패: {exc}")
    return render(
        request,
        "chat.html",
        active="chat",
        idea=idea,
        plan=pending_change.plan,
        targets=[file.path for file in pending_change.files],
    )


@app.get("/chat/sessions")
def chat_sessions() -> JSONResponse:
    return JSONResponse({"sessions": conversation_store.list_sessions()})


@app.post("/chat/new")
def chat_new() -> RedirectResponse:
    conversation = conversation_store.create()
    return RedirectResponse(f"/chat/{conversation['session_id']}", status_code=303)


@app.get("/chat/{session_id}", response_class=HTMLResponse)
def chat_session_page(request: Request, session_id: str) -> HTMLResponse:
    try:
        conversation = conversation_store.get(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    message = clear_flash()
    return render(
        request,
        "chat.html",
        active="chat",
        flash_message=message,
        sessions=conversation_store.list_sessions(),
        conversation=conversation,
        session_pending=pending_store.load_raw(session_id),
    )


@app.post("/chat/message")
async def chat_message(request: Request) -> JSONResponse:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    message = str(payload.get("message", "")).strip()
    session_id = payload.get("session_id") or None
    write_mode = str(payload.get("write_mode", "")).lower() in {"1", "true", "on", "yes"}
    if not message:
        return JSONResponse({"error": "메시지를 입력하세요."}, status_code=400)

    try:
        result = ConversationAgent(settings).handle_message(str(session_id) if session_id else None, message, write_mode)
    except Exception as exc:
        return JSONResponse({"error": f"대화 처리 실패: {exc}"}, status_code=500)
    return JSONResponse(result)


@app.post("/chat/{session_id}/apply")
def apply_session_pending(session_id: str) -> RedirectResponse:
    raw = pending_store.load_raw(session_id)
    if not raw:
        set_flash("저장할 pending change가 없습니다.")
        return RedirectResponse(f"/chat/{session_id}", status_code=303)
    try:
        writes = [(manager.validate_relative_save_path(str(rel)), content) for rel, content in raw.get("new_contents", {}).items()]
        snapshot = manager.snapshot_docs()
        for path, content in writes:
            manager.save(path, content)
        pending_store.delete(session_id)
        conversation_store.add_message(
            session_id,
            "assistant",
            f"문서 저장을 완료했습니다. Snapshot: {snapshot}",
            intent="doc_write",
        )
        set_flash(f"{len(raw.get('new_contents', {}))}개 문서를 저장했습니다. Snapshot: {snapshot}")
    except Exception as exc:
        set_flash(f"저장 실패: {exc}")
    return RedirectResponse(f"/chat/{session_id}", status_code=303)


@app.post("/chat/{session_id}/discard")
def discard_session_pending(session_id: str) -> RedirectResponse:
    pending_store.delete(session_id)
    try:
        conversation_store.add_message(session_id, "assistant", "pending change를 폐기했습니다.", intent="doc_write")
    except FileNotFoundError:
        pass
    set_flash("pending change를 폐기했습니다.")
    return RedirectResponse(f"/chat/{session_id}", status_code=303)


@app.post("/chat/{session_id}/delete")
def delete_chat_session(session_id: str) -> RedirectResponse:
    if not validate_session_id(session_id):
        set_flash("잘못된 session_id입니다. 대화를 삭제하지 않았습니다.")
        return RedirectResponse("/chat", status_code=303)
    try:
        deleted = conversation_store.delete_conversation(session_id)
        pending_store.delete(session_id)
    except Exception as exc:
        set_flash(f"대화 삭제 실패: {exc}")
        return RedirectResponse(f"/chat/{session_id}", status_code=303)
    set_flash("대화가 삭제되었습니다." if deleted else "삭제할 대화를 찾지 못했습니다.")
    return RedirectResponse("/chat", status_code=303)


@app.post("/chat/delete-all")
def delete_all_chat_sessions() -> RedirectResponse:
    try:
        conversation_count = conversation_store.delete_all_conversations()
        pending_count = pending_store.delete_all()
    except Exception as exc:
        set_flash(f"전체 대화 삭제 실패: {exc}")
        return RedirectResponse("/chat", status_code=303)
    set_flash(f"대화 {conversation_count}개와 pending change {pending_count}개를 삭제했습니다.")
    return RedirectResponse("/chat", status_code=303)


@app.get("/diff", response_class=HTMLResponse)
def diff_page(request: Request) -> HTMLResponse:
    message = clear_flash()
    return render(request, "diff.html", active="diff", flash_message=message)


@app.post("/apply")
def apply_pending() -> RedirectResponse:
    global pending_change
    if not pending_change:
        set_flash("저장할 pending change가 없습니다.")
        return RedirectResponse("/diff", status_code=303)
    if not pending_change.files:
        set_flash(pending_change.message or "저장할 파일이 없습니다.")
        pending_change = None
        return RedirectResponse("/", status_code=303)
    try:
        writes = [(manager.validate_save_path(Path(file.path)), file.content) for file in pending_change.files]
        snapshot = manager.snapshot_docs()
        for path, content in writes:
            manager.save(path, content)
    except Exception as exc:
        set_flash(f"저장 실패: {exc}")
        return RedirectResponse("/diff", status_code=303)
    count = len(pending_change.files)
    pending_change = None
    set_flash(f"{count}개 문서를 저장했습니다. Snapshot: {snapshot}")
    return RedirectResponse("/", status_code=303)


@app.post("/discard")
def discard_pending() -> RedirectResponse:
    global pending_change
    pending_change = None
    set_flash("pending change를 폐기했습니다.")
    return RedirectResponse("/", status_code=303)


@app.get("/docs", response_class=HTMLResponse)
def docs_page(request: Request) -> HTMLResponse:
    message = clear_flash()
    return render(request, "docs.html", active="docs", docs=markdown_docs(), flash_message=message)


@app.get("/docs/{doc_path:path}", response_class=HTMLResponse)
def doc_detail(request: Request, doc_path: str) -> HTMLResponse:
    path = safe_doc_path(doc_path)
    message = clear_flash()
    return render(
        request,
        "docs.html",
        active="docs",
        flash_message=message,
        docs=markdown_docs(),
        selected_path=path.relative_to(PROJECT_ROOT).as_posix(),
        selected_content=path.read_text(encoding="utf-8"),
    )


@app.get("/data", response_class=HTMLResponse)
def data_page(request: Request) -> HTMLResponse:
    message = clear_flash()
    return render(
        request,
        "data.html",
        active="data",
        flash_message=message,
        tables=data_manager.list_tables(),
        table=None,
    )


@app.get("/data/{table_name}", response_class=HTMLResponse)
def data_table_page(request: Request, table_name: str) -> HTMLResponse:
    try:
        table = data_manager.load(table_name)
    except Exception as exc:
        set_flash(f"CSV 로드 실패: {exc}")
        return RedirectResponse("/data", status_code=303)
    message = clear_flash()
    return render(
        request,
        "data.html",
        active="data",
        flash_message=message,
        tables=data_manager.list_tables(),
        table=table,
    )


@app.post("/data/{table_name}/save")
def data_table_save(table_name: str, payload: str = Form(...)) -> RedirectResponse:
    try:
        data = json.loads(payload)
        headers = [str(header) for header in data.get("headers", [])]
        rows = data.get("rows", [])
        if not isinstance(rows, list):
            raise ValueError("rows payload must be a list.")
        clean_rows = [row for row in rows if isinstance(row, dict)]
        table = data_manager.save(table_name, headers, clean_rows)
        set_flash(f"{table.name} 저장 완료: {len(table.rows)}개 행")
    except Exception as exc:
        set_flash(f"CSV 저장 실패: {exc}")
    return RedirectResponse(f"/data/{table_name}", status_code=303)


@app.post("/data/{table_name}/export-unity")
def data_table_export_unity(table_name: str) -> RedirectResponse:
    try:
        export_path = data_manager.export_unity_json(table_name)
        rel = export_path.relative_to(PROJECT_ROOT).as_posix()
        set_flash(f"Unity JSON export 완료: {rel}")
    except Exception as exc:
        set_flash(f"Unity JSON export 실패: {exc}")
    return RedirectResponse(f"/data/{table_name}", status_code=303)


@app.post("/build-gdd-from-source")
def build_gdd_from_source() -> RedirectResponse:
    global pending_change
    try:
        pending_change = build_gdd_pending()
    except Exception as exc:
        set_flash(f"GDD 생성 실패: {exc}")
        return RedirectResponse("/", status_code=303)
    if not pending_change.files:
        set_flash(pending_change.message)
        pending_change = None
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/diff", status_code=303)


@app.post("/index")
def index_docs() -> RedirectResponse:
    try:
        count = RagStore(settings).index_documents()
        set_flash(f"인덱싱 완료: {count}개 chunk")
    except Exception as exc:
        set_flash(f"인덱싱 실패: {exc}")
    return RedirectResponse("/", status_code=303)


@app.post("/check")
def check_docs() -> RedirectResponse:
    try:
        report_path = ConsistencyChecker(settings).run()
        rel = Path(report_path).relative_to(PROJECT_ROOT).as_posix()
        set_flash(f"일관성 검사 완료: {rel}")
    except Exception as exc:
        set_flash(f"일관성 검사 실패: {exc}")
    return RedirectResponse("/docs", status_code=303)
