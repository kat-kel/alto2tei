from src.sru_data import SRU_API
from lxml import etree
from testing_data.unimarc_data1 import sru_answer


unimarc_test_data = 'testing_data/unimarc_data1.xml'
correct_response = sru_answer


def test_parse_unimarc():
    with open(unimarc_test_data) as r:
        response = etree.parse(r)
        sru_data = SRU_API("ark:/12148/test").clean(response, True)
    assert sru_data == correct_response


if __name__ == "__main__":
    test_parse_unimarc()