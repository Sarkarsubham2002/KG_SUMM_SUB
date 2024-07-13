from hashlib import md5
from xml.etree import ElementTree as ET
import requests
from kg_summarizer.config import CACHE_DIR

import logging
from logging.handlers import RotatingFileHandler
import os
import pathlib


def append_to_file(message):
    log_file_path = (
        pathlib.Path(__file__).parents[1].joinpath("logs/kg_summarizer_manual.log")
    )
    try:
        with open(log_file_path, "a") as file:
            file.write(message + "\n")
    except Exception as e:
        print("An error occurred:", str(e))


class LoggingUtil(object):
    """Logging utility controlling format and setting initial logging level"""

    @staticmethod
    def init_logging(
        name, level=logging.INFO, format_sel="medium", log_file_level=None
    ):
        log_file_path = (
            pathlib.Path(__file__).parents[1].joinpath("logs/kg_summarizer.log")
        )
        # get a logger
        logger = logging.getLogger(__name__)

        # returns a new logger if its not the root
        if not logger.parent.name == "root":
            return logger

        # define the output types
        format_types = {
            "short": "[%(name)s.%(funcName)s] : %(message)s",
            "medium": "[%(name)s.%(funcName)s] - %(asctime)-15s: %(message)s",
            "long": "[%(name)s.%(funcName)s] - %(asctime)-15s %(filename)s %(levelname)s: %(message)s",
        }[format_sel]

        # create a stream handler (default to console)
        stream_handler = logging.StreamHandler()

        # create a formatter
        formatter = logging.Formatter(format_types)

        # set the formatter on the console stream
        stream_handler.setFormatter(formatter)

        # get the name of this logger
        logger = logging.getLogger(name)

        # set the logging level
        logger.setLevel(level)

        # if there was a file path passed in use it
        if log_file_path is not None:
            # create a rotating file handler, 50mb max per file with a max number of 2 files
            file_handler = RotatingFileHandler(
                filename=log_file_path, maxBytes=50000000, backupCount=2
            )

            # set the formatter
            file_handler.setFormatter(formatter)

            # if a log level for the file was passed in use it
            if log_file_level is not None:
                level = log_file_level

            # set the log level
            file_handler.setLevel(level)

            # add the handler to the logger
            logger.addHandler(file_handler)

        # add the console handler to the logger
        logger.addHandler(stream_handler)

        # return to the caller
        return logger


def cached_get_pubmed_abstract(pubmed_id, n_retry=5):
    pubmed_cache_dir = CACHE_DIR / "pubmed_abstracts"
    pubmed_cache_dir.mkdir(parents=True, exist_ok=True)

    pubmed_id_num = pubmed_id.split(":")[1]
    pubmed_cache_file = pubmed_cache_dir / f"{pubmed_id_num}.txt"
    if pubmed_cache_file.exists():
        with open(pubmed_cache_file, "r", encoding="utf-8") as file:
            abstract = file.read()
    else:
        abstract = get_pubmed_abstract(pubmed_id, n_retry=n_retry)
        if abstract is not None:
            with open(pubmed_cache_file, "w", encoding="utf-8") as file:
                file.write(abstract)

    return abstract


def get_pubmed_abstract(pubmed_id, n_retry=5):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": str(pubmed_id),
        "retmode": "xml",
        "rettype": "abstract",
    }

    for itry in range(n_retry):
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            # print(response.content)
            xml_root = ET.fromstring(response.content)
            abstract_elements = xml_root.findall(".//AbstractText")
            abstract_parts = []
            for element in abstract_elements:
                label = element.get("Label")
                text = element.text
                if text:
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
            abstract_text = " ".join(abstract_parts)
            if abstract_text:
                return abstract_text.strip()

    return None


def post_query(url, query_dict):
    try:
        resp = requests.post(url, json=query_dict, timeout=600)
    except requests.exceptions.ReadTimeout:
        print("Request timed out!")
        logging.warning("Request timed out!")
        return "Error", -1
    except requests.exceptions.ConnectionError:
        print("Request had connection error")
        logging.warning("Request had connection error!")
        return "Error", -1
    if resp.status_code != 200:
        raise ValueError("Node normalizer sent", resp.status_code)

    return resp


def normalize_list(l):
    d = {"curies": l}
    URL = "https://nodenormalization-sri.renci.org/1.3/get_normalized_nodes"
    x = post_query(URL, d)
    j = x.json()
    result_d = {}
    for k in j.keys():
        if j[k] == None:
            continue
        idx = j[k]["id"]["identifier"]
        label = j[k]["id"].get("label", "")
        result_d[k] = (idx, label)
    return result_d


def unique_name_from_str(string: str, last_idx: int = 12) -> str:
    """
    Generates a unique id name
    refs:
    - md5: https://stackoverflow.com/questions/22974499/generate-id-from-string-in-python
    - sha3: https://stackoverflow.com/questions/47601592/safest-way-to-generate-a-unique-hash
    (- guid/uiid: https://stackoverflow.com/questions/534839/how-to-create-a-guid-uuid-in-python?noredirect=1&lq=1)
    """
    m = md5()
    string = string.encode("utf-8")
    m.update(string)
    unqiue_name: str = str(int(m.hexdigest(), 16))[0:last_idx]
    return unqiue_name
