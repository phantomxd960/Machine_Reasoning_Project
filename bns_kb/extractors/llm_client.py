"""
LLM Client Interface for Pass 1 / Pass 2 Structured Extraction.
Supports OpenAI API (gpt-4o-mini) when an API key is available.
"""
import os
from typing import Optional, Dict, Any, List
from bns_kb.schemas.components import Pass1ComponentOutput, Component
from bns_kb.schemas.relationships import Pass2RelationshipOutput, Relationship

class LLMExtractorClient:
    """
    OpenAI Structured Output Extractor for BNS statutory provisions.
    """
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def extract_components_pass1(self, section_number: int, section_name: str, raw_text: str) -> Pass1ComponentOutput:
        """
        Extracts legal components using gpt-4o-mini with Pydantic structured output.
        """
        if not self.is_available:
            raise RuntimeError("OpenAI client is not configured or OPENAI_API_KEY is missing.")

        prompt = (
            f"You are a formal legal knowledge engineer. Decompose the following statutory section "
            f"from the Bharatiya Nyaya Sanhita (BNS), 2023 into structured legal components.\n"
            f"Preserve EXACT statutory wording in verbatim_text (do not paraphrase or summarize).\n\n"
            f"Section {section_number}: {section_name}\n"
            f"Statutory Text:\n{raw_text}\n"
        )

        response = self._client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You decompose legal statutes into exact verbatim components with preserved hierarchy."},
                {"role": "user", "content": prompt}
            ],
            response_format=Pass1ComponentOutput
        )
        return response.choices[0].message.parsed

    def extract_relationships_pass2(
        self,
        section_number: int,
        components: List[Component]
    ) -> Pass2RelationshipOutput:
        """
        Discovers typed legal relationships among extracted components.
        """
        if not self.is_available:
            raise RuntimeError("OpenAI client is not configured or OPENAI_API_KEY is missing.")

        comps_summary = "\n".join([f"- [{c.id}] ({c.component_type}): {c.verbatim_text[:100]}" for c in components])
        prompt = (
            f"Analyze the extracted legal components for BNS Section {section_number} and determine "
            f"directed legal relationships (HAS_CHILD, QUALIFIES, EXCEPTION_TO, PROVIDES_ILLUSTRATION_FOR, "
            f"PUNISHES, CROSS_REFERENCES).\n\n"
            f"Components:\n{comps_summary}\n"
        )

        response = self._client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You establish typed legal relations between statutory components."},
                {"role": "user", "content": prompt}
            ],
            response_format=Pass2RelationshipOutput
        )
        return response.choices[0].message.parsed
