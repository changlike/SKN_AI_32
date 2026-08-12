"""PDF 문서와 게시글을 ChromaDB에 일괄 색인하는 관리 명령입니다."""
from django.core.management.base import BaseCommand, CommandError
from rag.service import RagService


class Command(BaseCommand):
    help = "docs PDF와 게시글을 OpenAI 임베딩으로 변환하여 ChromaDB에 색인합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="변경 여부와 관계없이 모든 벡터를 다시 생성합니다.",
        )
        parser.add_argument(
            "--source",
            choices=["all", "documents", "boards"],
            default="all",
            help="색인할 데이터 범위를 선택합니다.",
        )

    def handle(self, *args, **options):
        try:
            service = RagService()
            source = options["source"]
            force = options["force"]
            if source == "documents":
                result = {"documents": service.sync_documents(force=force)}
            elif source == "boards":
                result = {"boards": service.sync_boards(force=force)}
            else:
                result = service.sync_all(force=force)
            self.stdout.write(self.style.SUCCESS(f"RAG 색인 완료: {result}"))
        except Exception as exc:
            raise CommandError(str(exc)) from exc
