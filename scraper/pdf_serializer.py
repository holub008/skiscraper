import os
import subprocess

from configs import Configs

config = Configs()
RACE_DB = config.get_as_string("RACE_DB")
PDF_TO_TEXT = config.get_as_string("PDF_TO_TEXT")
DATA_DIR = os.path.join(config.SCRAPERTOP, "data/")
###############################################
# utilities to serialize pdf data
# todo merge this into UnstructuredRaceResults
##############################################

def write_pdf_and_text(race_info, pdf_content, race_id):
    """
    save a pdf and text file to the local fs
    todo chuck the text blob into a unstructured_race_results table (probably still want local copies though)
    :param race_info: metadata about the race (RaceInfo)
    :param pdf_content: pdf blob (str)
    :param race_id: the race_id associated with the race
    :return: path to the written text file
    """

    """
    the workhorse- writes the pdf to disk, converts it to a txt, writes txt to disk

    :param race_info: race metdata (RaceInfo)
    :param pdf_content: a blob representing (hopefully) a pdf (str)
    :return: the path to the written text (str)
    """

    fpath = os.path.join(DATA_DIR,"pdf/", race_info.season)
    path_fname = os.path.join(fpath, race_info.get_cleansed_name())
    path_fname_ext = "%s.pdf" % (path_fname, )

    txt_path = os.path.join(DATA_DIR, "text/", race_info.season)
    txt_dest = os.path.join(txt_path, race_info.get_cleansed_name())
    txt_dest_ext = "%s.txt" % (txt_dest, )

    # build the data dest dirs, if not there
    if not os.path.exists(fpath):
        os.makedirs(fpath)
    if not os.path.exists(txt_path):
        os.makedirs(txt_path)

    # write the data to a pdf
    pdf_file = open(path_fname_ext,'wb')
    pdf_file.write(pdf_content)
    pdf_file.close()

    # todo check return value of pdftotext
    handle = subprocess.Popen([PDF_TO_TEXT, path_fname_ext, txt_dest_ext], stdout = subprocess.PIPE)
    handle.wait() # block until file is written

    return txt_dest_ext
