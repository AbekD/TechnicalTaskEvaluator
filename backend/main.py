
from services.inputer_data_tz import convert_file_to_text
from agent_core import *
from agent_core.scoringAimodule import score_document
from test_doc import *
from agent_core.send_to_sheets import upload_to_google_sheets

a = convert_file_to_text("test_doc/ТЗ Цифровой полигон.docx")
print(a)
s = score_document(a)
print(s)
upload_to_google_sheets(s)