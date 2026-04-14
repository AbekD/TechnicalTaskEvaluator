import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
from .promt import PROMT_TO_SCORING

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

WEIGHTS = {
    "strategic_relevance": 0.20,
    "goals_and_tasks": 0.10,
    "scientific_novelty": 0.15,
    "practical_applicability": 0.20,
    "expected_results": 0.15,
    "socio_economic_effect": 0.10,
    "feasibility": 0.10,
}


def _clean_json_response(text: str) -> str:
    """Strip markdown code fences if model wraps response in them."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _recalculate_total(scores: dict) -> float:
    """Recalculate weighted total from scores dict as a safety check."""
    total = sum(scores.get(k, 0) * w for k, w in WEIGHTS.items())
    return round(total * 10, 2)


def score_document(text: str) -> dict:
    """
    Send TZ text to Gemini scoring model and return structured result.

    Args:
        text: Raw text content of the technical specification document.

    Returns:
        Parsed scoring result as a Python dict.

    Raises:
        ValueError: If the model returns unparseable JSON.
    """
    model_name = os.getenv("GEMINI_SCORING_MODEL", "gemini-2.5-pro")
    model = genai.GenerativeModel(model_name)

    full_prompt = f"{PROMT_TO_SCORING}\n\n--- ТЕКСТ ТЗ ---\n{text}\n--- КОНЕЦ ТЕКСТА ---"

    response = model.generate_content(full_prompt)
    raw = _clean_json_response(response.text)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Scoring model returned invalid JSON: {e}\nRaw response:\n{raw}")

    # Safety: recalculate total from scores to catch model arithmetic errors
    if "scores" in result:
        result["total_weighted_score"] = _recalculate_total(result["scores"])

    return result


def score_document_to_file(text: str, output_path: str) -> dict:
    """
    Score a document and save the result as a JSON file.

    Args:
        text: Raw text of the TZ document.
        output_path: Path where the JSON result will be saved.

    Returns:
        The scoring result dict.
    """
    result = score_document(text)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def build_chat_context(scoring_result: dict) -> str:
    """
    Convert scoring result into a compact context string for the chat agent.
    This is what Agent 2 (chat) receives as its initial knowledge about the TZ.

    Args:
        scoring_result: Dict returned by score_document().

    Returns:
        Formatted string summarizing the scoring for the chat agent.
    """
    scores = scoring_result.get("scores", {})
    defects = scoring_result.get("defects", {})
    reasoning = scoring_result.get("category_reasoning", {})
    constraints = scoring_result.get("hard_constraints_triggered", [])

    lines = [
        f"=== РЕЗУЛЬТАТ СКОРИНГА ТЗ ===",
        f"Проект: {scoring_result.get('project_name', 'Не указано')}",
        f"Организация: {scoring_result.get('organization', 'Не указано')}",
        f"Итоговый балл: {scoring_result.get('total_weighted_score', 0)}/100",
        "",
        "--- ОЦЕНКИ ПО КРИТЕРИЯМ ---",
        f"Стратегическая релевантность (×0.20): {scores.get('strategic_relevance', 0)}/10 — {reasoning.get('strategic_relevance', '')}",
        f"Цель и задачи (×0.10):                {scores.get('goals_and_tasks', 0)}/10 — {reasoning.get('goals_and_tasks', '')}",
        f"Научная новизна (×0.15):               {scores.get('scientific_novelty', 0)}/10 — {reasoning.get('scientific_novelty', '')}",
        f"Практическая применимость (×0.20):     {scores.get('practical_applicability', 0)}/10 — {reasoning.get('practical_applicability', '')}",
        f"Ожидаемые результаты (×0.15):          {scores.get('expected_results', 0)}/10 — {reasoning.get('expected_results', '')}",
        f"Соц-экономический эффект (×0.10):      {scores.get('socio_economic_effect', 0)}/10 — {reasoning.get('socio_economic_effect', '')}",
        f"Реализуемость (×0.10):                 {scores.get('feasibility', 0)}/10 — {reasoning.get('feasibility', '')}",
    ]

    if constraints:
        lines += ["", "--- НАРУШЕНЫ ЖЁСТКИЕ УСЛОВИЯ ---"]
        lines += [f"⚠ {c}" for c in constraints]

    all_defects = (\
        defects.get("spelling_errors", [])
        + defects.get("vague_formulations", [])
        + defects.get("structural_issues", [])
        + defects.get("missing_elements", [])
        + defects.get("other_issues", [])
    )
    if all_defects:
        lines += ["", "--- ВЫЯВЛЕННЫЕ НЕДОСТАТКИ ---"]
        lines += [f"• {d}" for d in all_defects]

    lines += [
        "",
        "--- ОБЩИЙ ВЫВОД ЭКСПЕРТА ---",
        scoring_result.get("expert_comment", ""),
    ]

    return "\n".join(lines)
