import os
import xml.etree.ElementTree as ET
from datetime import datetime

from .vars import logger
from .vars import DIRECTORY_NAME, PROJECT_FILENAME, WATCH_FILENAME
from .vars import project_file_path, watch_file_path


def build_project(data: dict, path):
    files = [
        os.path.join(path, PROJECT_FILENAME),
        os.path.join(path, WATCH_FILENAME)
    ]
    os.mkdir(path)

    for file in files:
        with open(file, 'w') as f:
            pass

    build_project_file(data, files[0])
    build_watch_file(files[1])


def build_project_file(data: dict, file):
    squirrel = ET.Element('squirrel', name=f"{data.get('name', '')}")

    path = ET.SubElement(squirrel, 'path', src=f'{os.path.dirname(file)}')

    description = ET.SubElement(squirrel, 'description')
    description.text = data.get('description', '')

    due_date = ET.SubElement(squirrel, 'due-date')
    due_date.text = data.get('due', '').strftime('%d/%m/%Y')

    goal = ET.SubElement(squirrel, 'goal')
    goal.text = str(data.get('goal', 0))

    project_type = ET.SubElement(squirrel, 'project-type')
    p_type = data.get('project_type', 'text')
    project_type.text = p_type if p_type is not None else 'text'

    tree = ET.ElementTree(squirrel)
    ET.indent(tree)
    tree.write(file, encoding='utf-8', xml_declaration=True)


def build_watch_file(file):
    squirrel = ET.Element('squirrel')
    comment = ET.Comment(
        'This is file generation by squirrel. Modify it at your own risk.')
    squirrel.insert(1, comment)
    tree = ET.ElementTree(squirrel)
    ET.indent(tree)
    tree.write(file, encoding='utf-8', xml_declaration=True)


def update_project_file(data: dict):
    path = project_file_path
    tree = parse(path)
    squirrel = tree.getroot()

    if (name := data.get('name')) is not None:
        squirrel.set('name', name)

    if (desc := data.get('description')) is not None:
        try:
            squirrel.find('description').text = desc
        except AttributeError as e:
            logger.error('[bold red blink]description[/] element was not found in the xml file'
                         ' try initializing the project again', extra={'markup': True})

    if (goal := data.get('goal')) is not None:
        try:
            squirrel.find('goal').text = str(goal)
        except AttributeError as e:
            logger.error('goal element was not found in the xml file'
                         ' try initializing the project again')

    if (due := data.get('due')) is not None:
        try:
            squirrel.find('due-date').text = due
        except AttributeError as e:
            logger.error('due-date element was not found in the xml file'
                         'try init project again')

    if (project_type := data.get('project_type')) is not None:
        try:
            squirrel.find('project-type').text = project_type
        except AttributeError as e:
            logger.error('[bold red blink]project-type[/] element was not found in the xml file'
                         ' try initializing the project again', extra={'markup': True})

    tree.write(path, encoding='utf-8', xml_declaration=True)


def get_data_from_project_file(basedir=''):
    path = os.path.join(basedir, project_file_path)
    tree = parse(path)
    squirrel = tree.getroot()

    data = {
        'name': squirrel.attrib['name'],
        'path': squirrel.find('path').attrib['src'],
        'description': squirrel.find('description').text,
        'goal': squirrel.find('goal').text,
        'due-date': squirrel.find('due-date').text,
        'project-type': squirrel.find('project-type').text
    }
    return data


def get_watches_data():
    """returns all watches tag data with -1 being the key of the last watches"""
    path = watch_file_path
    tree = parse(path)
    squirrel = tree.getroot()

    data = {}
    data['-1'] = (str(0), str(0))
    if len(squirrel) > 1:
        for watches in squirrel.findall('watches'):
            date = watches.attrib['date']
            data[date] = (watches.attrib['prev_count'],
                          get_watches_last_count(watches))
        data['-1'] = data[date]
    return data


def get_watches_last_count(watches):
    if len(watches) == 0:
        return 0
    else:
        try:
            return watches[-1].text
        except AttributeError:
            return 0


def get_watches_entry(date):
    """retuns the watches tag of the passed date and root element; defaults to (None, root)"""
    path = watch_file_path
    tree = parse(path)
    squirrel = tree.getroot()

    for watches in squirrel.findall('watches'):
        try:
            if watches.attrib['date'] == date.strftime('%d/%m/%Y'):
                return watches, squirrel
        except AttributeError:
            pass
        except KeyError:
            pass
    return None, squirrel


def add_watch_entry(total, dt: datetime):
    """Add a watch tag to the watches tag of that date"""
    path = watch_file_path

    watches_date, root = get_watches_entry(dt.date())
    if watches_date is not None:
        try:
            if watches_date[-1].text != str(total):
                watch = ET.SubElement(watches_date, 'watch', datetime=str(dt))
                watch.text = str(total)
            else:
                return False
        except KeyError:
            pass
    elif root is not None:
        try:
            prev_count = root[-1][-1].text
        except (IndexError, AttributeError):
            prev_count = str(0)

        watches = ET.SubElement(root,
                                'watches',
                                prev_count=prev_count,
                                date=dt.date().strftime('%d/%m/%Y'))
        watch = ET.SubElement(watches, 'watch', datetime=str(dt))
        watch.text = str(total)
    else:
        return False

    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    return True


def parse(path):
    parser_save_comments = ET.XMLParser(
        target=ET.TreeBuilder(insert_comments=True))
    return ET.parse(path, parser_save_comments)
