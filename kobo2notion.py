#!/usr/bin/env python3

import os
import shutil
import sqlite3
import time
from datetime import datetime
import logging

import requests
import yaml


# Define constants
NODELTA_DATE = '1970-01-01 00:00:00'
PAGES_URL = 'https://api.notion.com/v1/pages'
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# Define custom colors
class ColorFormatter(logging.Formatter):
    """Color formatter for log entries."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'

    FORMATS = {
        logging.INFO: GREEN,
        logging.ERROR: RED
    }

    def format(self, record):
        log_color = self.FORMATS.get(record.levelno, '')  # Get color for log level
        reset_color = self.RESET if log_color else ''  # Reset color if needed
        formatted_message = super().format(record)
        return f"{log_color}{formatted_message}{reset_color}"

class Item:
    """Represents a database record."""
    def __init__(self, values):
        self.volumeid = values[0]
        self.type = values[1]
        self.text = values[2]
        self.annotation = values[3]
        self.extraannotationdata = values[4]
        self.datecreated = values[5] if values[5] is not None else NODELTA_DATE
        self.datemodified = values[6] if values[6] is not None else NODELTA_DATE
        self.booktitle = values[7]
        self.title = values[8]
        self.author = values[9]

    def to_dict(self):
        """Converts item to a dictionary."""
        return {
            'volumeid': self.volumeid,
            'type': self.type,
            'text': self.text,
            'annotation': self.annotation,
            'extraannotationdata': self.extraannotationdata,
            'datecreated': self.datecreated,
            'datemodified': self.datemodified,
            'booktitle': self.booktitle,
            'title': self.title,
            'author': self.author
        }


def initiate_logger():
    """Initiate logger."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Create a handler and set formatter
    handler = logging.StreamHandler()
    formatter = ColorFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def copy_database(database_path, database_cache):
    """Copy database from e-reading device to cache folder."""
    if os.path.exists(database_path):
        logging.info('Retrieving database from e-reader')
        if os.path.exists(database_cache):
            os.remove(database_cache)
        shutil.copy(database_path, database_cache)
    else:
        logging.error('Database not found, is your e-reader connected?')
        exit()


def convert_date(date_str):
    """Converts date string to a standardized format."""
    try:
        date_obj = datetime.fromisoformat(date_str)
    except ValueError:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            raise ValueError('Invalid date format')
    standardized_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
    return standardized_date


def create_notion_page(parent_page_id, title_content, main_content, source_content):
    """Creates a Notion page."""
    data = {
        'parent': {'page_id': parent_page_id},
        'icon': {'emoji': icon},
        'properties': {'title': [{'text': {'content': title_content}}]},
        'children': []
    }

    # Split main_content into blocks of 2000 characters each
    content_blocks = [main_content[i:i+2000] for i in range(0, len(main_content), 2000)]

    # Add each maint_content content block as a separate paragraph object
    for block in content_blocks:
        paragraph_data = {
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{'type': 'text', 'text': {'content': block}}]
            }
        }
        data['children'].append(paragraph_data)
    
    # Add source content as a separate paragraph object
    paragraph_data = {
        'object': 'block',
        'type': 'paragraph',
        'paragraph': {
            'rich_text': [{'type': 'text', 'text': {'content': source_content}, 'annotations': {'italic': True}}]
        }
    }
    data['children'].append(paragraph_data)

    while True:
        response = requests.post(PAGES_URL, headers=HEADERS, json=data)
        if response.status_code == 200:
            logging.info(f'Created "{title_content}"')
            break
        else:
            logging.error(f'{response.status_code}: {response.text}')
            logging.info('Retrying in 1 minute')
            time.sleep(60)  # Wait for one minute before retrying


def parse_database(database_cache):
    """Parses database and returns items."""
    query_items = (
        'SELECT Bookmark.VolumeID, Bookmark.Type, Bookmark.Text, Bookmark.Annotation, '
        'Bookmark.ExtraAnnotationData, Bookmark.DateCreated, Bookmark.DateModified, '
        'content.BookTitle, content.Title, content.Attribution '
        'FROM Bookmark INNER JOIN content '
        'ON Bookmark.VolumeID = content.ContentID;'
    )

    logging.info('Parsing database')
    try:
        with sqlite3.connect(database_cache) as conn:
            cursor = conn.cursor()
            cursor.execute(query_items)
            data = cursor.fetchall()
    except Exception as exc:
        logging.error('Unexpected error reading your KoboReader.sqlite file:', exc)
        return []

    items = [Item(d) for d in data]
    return [item.to_dict() for item in items]


def export_kobo_items(database_cache, delta_date):
    """Exports Kobo items to Notion."""
    latest_date = None
    kobo_items = parse_database(database_cache)

    for kobo_item in kobo_items:
        record_type = kobo_item['type'].capitalize()
        title = kobo_item['title']
        date_created = convert_date(kobo_item['datecreated'])
        date_modified = convert_date(kobo_item['datemodified'])
        main_content = kobo_item['text']
        author = kobo_item['author']

        title_content = f'{record_type}: {title}'
        source_content = f'Source: {title}, {author}'

        if delta_date is None or date_created > delta_date or date_modified > delta_date:
            create_notion_page(parent_page, title_content, main_content, source_content)

            if latest_date is None or date_created > latest_date:
                latest_date = date_created
            if date_modified > latest_date:
                latest_date = date_modified

    if latest_date:
        config['kobo2notion']['delta_date'] = latest_date
        with open(os.path.join(SCRIPT_DIR, 'config.yaml'), 'w') as config_file:
            yaml.safe_dump(config, config_file, default_style='"')


# Load configuration
with open(os.path.join(SCRIPT_DIR, 'config.yaml'), 'r') as config_file:
    config = yaml.safe_load(config_file)
    database_path = os.path.join(SCRIPT_DIR, config['kobo']['database_path'])
    database_cache = os.path.join(SCRIPT_DIR, config['kobo']['database_cache'])
    integration_token = config['notion']['integration_token']
    parent_page = config['notion']['parent_page']
    icon = config['notion']['icon']
    delta_date = str(config['kobo2notion']['delta_date']).strip()
    if delta_date == '':
        delta_date = NODELTA_DATE
    delta_date = convert_date(delta_date)
     
# Define headers for Notion API requests
HEADERS = {
    'Authorization': f'Bearer {integration_token}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

initiate_logger()
copy_database(database_path, database_cache)
export_kobo_items(database_cache, delta_date)
logging.info('Process finished')
