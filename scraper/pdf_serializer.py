import os
import subprocess

from configs import Configs

config = Configs()
RACE_DB = config.get_as_string("RACE_DB")
PDF_TO_TEXT = config.get_as_string("PDF_TO_TEXT")
DATA_DIR = os.path.join(config.SCRAPERTOP, "data/")
###############################################
# utilities to serialize pdf data
##############################################

def write_pdf_and_text(race_info, pdf_content):
    """
    save a pdf and text file to the local fs
    todo chuck the text blob into a unstructured_race_results table (probably still want local copies though)
    :param race_info: metadata about the race (RaceInfo)
    :param pdf_content: pdf blob (str)
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


def write_race_metadata(race_info, text_path, cnx):
    """
    it is the caller's responsibility to properly close the connection
    :param race_info: race metadata (RaceInfo)
    :param text_path: path to the text blob associated with the results (str)
    :param cnx: a db connection (mysql.connector)
    :return: void
    """
    cursor = cnx.cursor()
    # ensure that the parser found all the race properties
    # if we don't make this entry in the db, the race will simply never be searched
    if race_info.name and race_info.url and race_info.date:
        cursor.execute("INSERT INTO %s (rpath, rname, rdate, ryear, rurl) VALUES('%s','%s','%s','%s','%s')" % (RACE_DB,
        text_path, race_info.get_cleansed_name(), race_info.date, race_info.season, race_info.url))
        cnx.commit()
    else:
        print("Missing necessary race info fields- this entry will not be searched")
        # todo logging
    cnx.close()
