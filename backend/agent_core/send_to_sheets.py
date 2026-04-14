import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_sheet() -> gspread.Worksheet:
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE")
    if not creds_file:
        raise EnvironmentError("GOOGLE_CREDENTIALS_FILE не задан в .env")
    creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    client = gspread.authorize(creds)

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise EnvironmentError("GOOGLE_SHEET_ID не задан в .env")

    return client.open_by_key(sheet_id).sheet1


def _find_next_empty_row(sheet: gspread.Worksheet) -> int:
    """
    Ищет первую пустую строку в колонке B (Название ТЗ).
    Строка 1 — заголовок, данные с строки 2.
    """
    col_b = sheet.col_values(2)  # колонка B
    for i, val in enumerate(col_b[1:], start=2):
        if not val.strip():
            return i
    return len(col_b) + 1


def _build_expert_comment(scoring_result: dict) -> str:
    parts = []

    comment = scoring_result.get("expert_comment", "")
    if comment:
        parts.append(comment)

    constraints = scoring_result.get("hard_constraints_triggered", [])
    if constraints:
        parts.append("⚠ НАРУШЕНИЯ: " + "; ".join(constraints))

    defects = scoring_result.get("defects", {})
    all_defects = (
        defects.get("spelling_errors", []) +
        defects.get("vague_formulations", []) +
        defects.get("structural_issues", []) +
        defects.get("missing_elements", []) +
        defects.get("other_issues", [])
    )
    if all_defects:
        parts.append("Замечания: " + " | ".join(all_defects[:3]))

    return "\n".join(parts)


def upload_to_google_sheets(scoring_result: dict) -> dict:
    """
    Записывает результат скоринга в первую пустую строку таблицы (колонки A-M).
    Итоговый балл (колонка L) — формула по весам критериев.

    Args:
        scoring_result: dict от score_document()

    Returns:
        dict со статусом и номером строки
    """
    sheet = _get_sheet()
    scores = scoring_result.get("scores", {})
    row = _find_next_empty_row(sheet)
    row_num = row - 1  # порядковый номер без заголовка

    # Формула итогового балла: E*0.2 + F*0.1 + G*0.15 + H*0.2 + I*0.15 + J*0.1 + K*0.1, умножить на 10
    total_formula = (
        f"=(E{row}*0.2+F{row}*0.1+G{row}*0.15+"
        f"H{row}*0.2+I{row}*0.15+J{row}*0.1+K{row}*0.1)*10"
    )

    # Пишем явно по ячейкам через update чтобы точно попасть в A-M
    cells = {
        f"A{row}": row_num,
        f"B{row}": scoring_result.get("project_name", "Не указано"),
        f"C{row}": scoring_result.get("organization", "Не указано"),
        f"D{row}": "AI Scoring Agent",
        f"E{row}": scores.get("strategic_relevance", 0),
        f"F{row}": scores.get("goals_and_tasks", 0),
        f"G{row}": scores.get("scientific_novelty", 0),
        f"H{row}": scores.get("practical_applicability", 0),
        f"I{row}": scores.get("expected_results", 0),
        f"J{row}": scores.get("socio_economic_effect", 0),
        f"K{row}": scores.get("feasibility", 0),
        f"L{row}": total_formula,
        f"M{row}": _build_expert_comment(scoring_result),
    }

    for cell, value in cells.items():
        sheet.update(cell, [[value]], value_input_option="USER_ENTERED")

    print(f"✅ Записано в строку {row} (запись #{row_num})")
    print(f"   Проект: {scoring_result.get('project_name', '?')}")

    return {
        "status": "success",
        "row": row,
        "row_number": row_num,
        "project_name": scoring_result.get("project_name", "Не указано"),
    }


def upload_batch_to_google_sheets(scoring_results: list) -> list:
    """Батч-загрузка нескольких результатов."""
    return [upload_to_google_sheets(s) for s in scoring_results]