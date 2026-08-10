# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import xml.etree.ElementTree as ET

from openpipeline.asset_info import PROJECTS_XML


def get_projects_xml_path(cfg):
    root_path = cfg.get_project_root_path() if cfg else ''
    if not root_path:
        return ''
    return os.path.join(root_path, PROJECTS_XML)


def ensure_projects_xml(cfg):
    xml_path = get_projects_xml_path(cfg)
    if not xml_path:
        return ''
    root_path = os.path.dirname(xml_path)
    if root_path and not os.path.exists(root_path):
        os.makedirs(root_path, exist_ok=True)
    if not os.path.exists(xml_path):
        root = ET.Element('projects')
        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    return xml_path


def load_projects_from_xml(cfg):
    xml_path = get_projects_xml_path(cfg)
    if not xml_path or not os.path.exists(xml_path):
        return {}
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        projects = {}
        for project in root.findall('project'):
            name_elem = project.find('name')
            path_elem = project.find('path')
            if name_elem is None or path_elem is None:
                continue
            name = (name_elem.text or '').strip()
            path = (path_elem.text or '').strip()
            if name and path:
                projects[name] = path.replace('\\', '/')
        return projects
    except Exception:
        return {}


def add_project_to_xml(cfg, name, path, libraryfolder='lib'):
    xml_path = ensure_projects_xml(cfg)
    if not xml_path:
        return False
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception:
        root = ET.Element('projects')
        tree = ET.ElementTree(root)

    for project in root.findall('project'):
        name_elem = project.find('name')
        if name_elem is not None and name_elem.text == name:
            return True

    project_elem = ET.SubElement(root, 'project')
    ET.SubElement(project_elem, 'name').text = name
    ET.SubElement(project_elem, 'path').text = path.replace('\\', '/')
    ET.SubElement(project_elem, 'libraryfolder').text = libraryfolder or 'lib'
    tree._setroot(root)
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    return True


def open_folder_in_explorer(path):
    # 1. 判断是否为文件，如果是则提取所在目录
    if os.path.isfile(path):
        target = os.path.dirname(path)
        # 如果传的是 "file.txt" 这种不带路径的纯文件名，dirname返回空，改为当前目录
        if not target:
            target = '.'  # 或 os.getcwd()
    else:
        target = path
    target = os.path.abspath(target)
    target = target.replace('\\', '/')

    if sys.platform.startswith('win'):
        os.startfile(target)
    elif sys.platform.startswith('darwin'):
        subprocess.Popen(['open', target])
    else:
        subprocess.Popen(['xdg-open', target])
    return True


def open_file_in_explorer(path):
    return open_folder_in_explorer(path)


__all__ = [
    'load_projects_from_xml',
    'get_projects_xml_path',
    'ensure_projects_xml',
    'add_project_to_xml',
    'open_folder_in_explorer',
    'open_file_in_explorer',
]
