from jsonize import xml_document_to_dict, Transformation
from pathlib import Path
from json import dumps
import re


def text_cleanup(text: str) -> str:
    """
    A simple text cleanup function that strips all new line characters and
    substitutes consecutive white space characters by a single one.
    :param text: Input text to be cleaned.
    :return: The cleaned version of the text
    """
    text.replace('\n', '')
    return re.sub(r'\s{2,}', ' ', text)


result = xml_document_to_dict(xml_document=Path('./input.xml'),
                              jsonize_map_document=Path('./example_jsonize_mapping.json'),
                              transformations=[Transformation('text_cleanup', text_cleanup)])

with Path('./output.json').open('w') as result_file:
    result_file.write(dumps(result))
