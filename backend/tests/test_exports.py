from datetime import UTC, datetime
from io import BytesIO

from docx import Document
from openpyxl import load_workbook

from app.services.exports import create_docx, create_xlsx


def test_exports_contain_result_data() -> None:
    results = [
        {
            "study_group_name": "ИВТ-1",
            "vk_user_id": 123,
            "first_name": "Иван",
            "last_name": "Иванов",
            "responded": True,
            "text": "Готово",
            "attachments": [],
            "responded_at": datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
            "is_late": False,
        }
    ]

    workbook = load_workbook(BytesIO(create_xlsx("Опрос", results)))
    document = Document(BytesIO(create_docx("Опрос", results)))

    assert workbook.active["C3"].value == "Иванов Иван"
    assert document.tables[0].cell(1, 2).text == "Иванов Иван"
