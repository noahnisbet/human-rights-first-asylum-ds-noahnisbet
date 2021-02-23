import os

os.environ["OMP_NUM_THREADS"]= '1'
os.environ["OMP_THREAD_LIMIT"] = '1'
os.environ["MKL_NUM_THREADS"] = '1'
os.environ["NUMEXPR_NUM_THREADS"] = '1'
os.environ["OMP_NUM_THREADS"] = '1'
os.environ["PAPERLESS_AVX2_AVAILABLE"]="false"
os.environ["OCR_THREADS"] = '1'


from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes, convert_from_path
from fastapi import APIRouter, File, UploadFile
import sqlalchemy
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
import PyPDF4
import io
import slate3k as slate
import poppler
from app.BIA_Scraper import BIACase
from typing import List, Tuple, Union, Callable, Dict, Iterator
from collections import defaultdict
from pprint import pprint
from difflib import SequenceMatcher
from datetime import datetime
import bs4
from bs4 import BeautifulSoup, element
import geonamescache
import requests
import pandas as pd
import numpy as np
from pathlib import Path
import re
import os
import spacy
from spacy.tokens.doc import Doc
from spacy.tokens.span import Span
from spacy.tokens.token import Token
nlp = spacy.load('en_core_web_lg')

router = APIRouter()
# print('dir ', os.listdir('..'))
load_dotenv(find_dotenv())
database_url = os.getenv('DATABASE_URL')
# print('test db?',database_url)

engine = sqlalchemy.create_engine(database_url)

@router.post('/insert')
async def create_upload_file(file: bytes = File(...)):
    '''
    This function inserts a PDF and the OCR converted text into a database

    '''
    
    text = []

    ### Converts the bytes object recieved from fastapi
    pages = convert_from_bytes(file,500)
    
    ### Uses pytesseract to convert each page of pdf to txt
    for item in pages:
        text.append(pytesseract.image_to_string(item))

    ### Joins the list to an output string
    string_to_return = " ".join(text)


    return {'Text': string_to_return}

@router.post('/get_fields')
async def create_upload_file(file: bytes = File(...)):
    

    text = []

    ### Converts the bytes object recieved from fastapi
    pages = convert_from_bytes(file,500)
    
    ### Uses pytesseract to convert each page of pdf to txt
    for item in pages:
        text.append(pytesseract.image_to_string(item))

    ### Joins the list to an output string
    string = " ".join(text)


    case = BIACase(string)
    case_data = {}

    remove_pw: Callable[[str], str]
    remove_pw = lambda s: s[:s.find('?secret')]

    case_data['filename'] = remove_pw(f) if 'password' in text else text[:-4]

    app = case.get_application()
    app = [ap for ap, b in app.items() if b]
    case_data['application'] = '; '.join(app) if app else None

    case_data['date'] = case.get_date()

    case_data['country_of_origin'] = case.get_country_of_origin()

    panel = case.get_panel()
    case_data['panel_members'] = '; '.join(panel) if panel else None

    case_data['outcome'] = case.get_outcome()

    pgs = case.get_protected_grounds()
    case_data['protected_grounds'] = '; '.join(pgs) if pgs else None

    based_violence = case.get_based_violence()
    violence = '; '.join([k for k, v in based_violence.items() if v]) \
              if based_violence \
              else None

    keywords = '; '.join(['; '.join(v) for v in based_violence.values()]) \
              if based_violence \
              else None
      
    case_data['based_violence'] = violence
    case_data['keywords'] = keywords

    references = [
    'Matter of AB, 27 I&N Dec. 316 (A.G. 2018)' 
    if case.references_AB27_216() else None,
    'Matter of L-E-A-, 27 I&N Dec. 581 (A.G. 2019)'
    if case.references_LEA27_581() else None
    ]

    case_data['references'] = '; '.join([r for r in references if r])
    case_data['sex_of_applicant'] = case.get_seeker_sex()

    return case_data
