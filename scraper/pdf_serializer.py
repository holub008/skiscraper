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

def write_pdf_and_text(pdf_content, race_id):
    """
    save a pdf and text file to the local fs
    :param pdf_content: pdf blob (str)
    :param race_id: the race_id associated with the race
    :return: the text content of pdf (str)
    """

    fpath = os.path.join(DATA_DIR,"pdf/")
    path_fname = os.path.join(fpath, str(race_id))
    path_fname_ext = "%s.pdf" % (path_fname, )

    txt_path = os.path.join(DATA_DIR, "text/")
    txt_dest = os.path.join(txt_path, str(race_id))
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
    if not handle.returncode == 0:
        print "Warning: PDF to text returned with exit code %d." % (handle.returncode,)

    with file(txt_dest_ext, "r") as text_file:
        return text_file.read()
