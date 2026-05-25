"""Build a fully wired :class:`~grader_agent.pipeline.GradingPipeline` for Flask."""

from __future__ import annotations

from grader_agent.llm.clients import make_openai_transcription_client, make_openrouter_chat_client
from grader_agent.pipeline import GradingPipeline
from grader_agent.services.code_notebook_extraction import CodeNotebookExtractionService
from grader_agent.services.content_validation import ContentValidationService
from grader_agent.services.feedback import FeedbackService
from grader_agent.services.grading import GradingService
from grader_agent.services.output_validation import OutputValidationService
from grader_agent.services.pdf_extraction import PDFExtractionService
from grader_agent.services.research import RubricResearchService
from grader_agent.services.rubric_validation import RubricValidationService
from grader_agent.services.transcription import TranscriptionService
from grader_agent.settings import GraderPaths, openai_api_key, openrouter_api_key


def create_grading_pipeline() -> GradingPipeline:
    """Instantiate services with OpenRouter (chat) and OpenAI (Whisper) clients."""
    chat = make_openrouter_chat_client(api_key=openrouter_api_key())
    whisper = make_openai_transcription_client(api_key=openai_api_key())
    paths = GraderPaths.from_env()
    paths.ensure_directories()
    return GradingPipeline(
        transcription_service=TranscriptionService(whisper),
        pdf_extraction_service=PDFExtractionService(),
        code_notebook_extraction_service=CodeNotebookExtractionService(),
        content_validation=ContentValidationService(chat),
        rubric_validation=RubricValidationService(),
        grading=GradingService(chat),
        output_validation=OutputValidationService(),
        feedback=FeedbackService(chat),
        research=RubricResearchService(chat, paths=paths),
    )
