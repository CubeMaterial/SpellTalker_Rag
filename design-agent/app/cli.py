import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="SpellTalker Design Agent",
        description="Local AI + RAG assistant for SpellTalker Markdown design docs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-docs", help="Create initial GDD Markdown templates.")
    subparsers.add_parser("build-gdd-from-source", help="Build GDD drafts from source_docs Markdown files.")
    subparsers.add_parser("index", help="Index Markdown documents into ChromaDB.")
    subparsers.add_parser("chat", help="Start an interactive design planning chat.")
    subparsers.add_parser("check", help="Run consistency checks and write a Markdown report.")
    subparsers.add_parser("snapshot", help="Back up docs_workspace into storage/snapshots.")
    subparsers.add_parser("ui", help="Run the local web UI.")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "init-docs":
        from app.document_manager import DocumentManager

        manager = DocumentManager()
        created = manager.init_docs()
        print(f"Created {len(created)} document template(s).")
        for path in created:
            print(f"- {path}")
        return

    if args.command == "snapshot":
        from app.document_manager import DocumentManager

        manager = DocumentManager()
        snapshot_path = manager.snapshot_docs()
        print(f"Snapshot created: {snapshot_path}")
        return

    if args.command == "build-gdd-from-source":
        from app.source_gdd_builder import SourceGddBuilder

        SourceGddBuilder().run()
        return

    if args.command == "index":
        from app.rag import RagStore

        store = RagStore()
        count = store.index_documents()
        print(f"Indexed {count} chunk(s).")
        return

    if args.command == "chat":
        from app.agent import DesignAgent

        DesignAgent().chat()
        return

    if args.command == "check":
        from app.validators import ConsistencyChecker

        report_path = ConsistencyChecker().run()
        print(f"Consistency report written: {report_path}")
        return

    if args.command == "ui":
        from app.web import run_web

        run_web()
        return
