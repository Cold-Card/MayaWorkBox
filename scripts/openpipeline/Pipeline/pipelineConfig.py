# -*- coding: utf-8 -*-

import json
import os


class OpenPipelineConfig(object):
    """轻量级配置管理器，兼容现有 UI 代码的调用方式。"""

    def __init__(self, config_file=None):
        self.config = {}
        self.config_file_path = config_file or os.path.join(
            os.path.dirname(__file__),
            '.py_openpipeline_config.json'
        )
        self.load()

    def _normalize_path(self, value):
        if not value:
            return ''
        return value.replace('\\', '/')

    def _ensure_defaults(self):
        self.config.setdefault('project_root_path', '')
        self.config.setdefault('projects', [])
        self.config.setdefault('asset_types', [])
        self.config.setdefault('library_folder', 'lib')
        self.config.setdefault('last_project', '')
        self.config.setdefault('last_assetType', '')
        self.config.setdefault('last_asset', '')
        self.config.setdefault('last_subtype', '')
        self.config.setdefault('fbx_export', ['Geo_grp', 'root_jnt'])
        return self.config

    def load(self):
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    self.config = data
            except Exception:
                self.config = {}

        self._ensure_defaults()
        self.save()
        return self.config

    def save(self):
        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as fh:
                json.dump(self.config, fh, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    def get_config_file_path(self):
        return self.config_file_path

    def get_project_root_path(self):
        return self._normalize_path(self.config.get('project_root_path', ''))

    def set_project_root_path(self, path):
        self.config['project_root_path'] = self._normalize_path(path)
        return self.save()

    def get_last_project(self):
        return self._normalize_path(self.config.get('last_project', ''))

    def set_last_project(self, path):
        self.config['last_project'] = self._normalize_path(path)
        return self.save()

    def get_last_select_type(self):
        return self.config.get('last_assetType', '')

    def set_last_select_type(self, asset_type):
        self.config['last_assetType'] = asset_type
        return self.save()

    def get_last_select_asset(self):
        return self.config.get('last_asset', '')

    def set_last_select_asset(self, asset_name):
        self.config['last_asset'] = asset_name
        return self.save()

    def get_last_select_subtype(self):
        return self.config.get('last_subtype', '')

    def set_last_select_subtype(self, subtype_name):
        self.config['last_subtype'] = subtype_name
        return self.save()

    def get_projects(self):
        projects = self.config.get('projects', [])
        if not isinstance(projects, list):
            return []
        return projects

    def add_project_path(self, project_path):
        project_path = self._normalize_path(project_path)
        projects = self.get_projects()
        if project_path not in projects:
            projects.append(project_path)
        self.config['projects'] = projects
        return self.save()

    def get_library_folder(self):
        return self.config.get('library_folder', 'lib')

    def set_library_folder(self, folder_name):
        self.config['library_folder'] = folder_name or 'lib'
        return self.save()

    def get_fbx_export_info(self):
        value = self.config.get('fbx_export', ['Geo_grp', 'root_jnt'])
        if not isinstance(value, list):
            value = [str(value)]
        return value

    def set_fbx_export_info(self, fbx_export):
        self.config['fbx_export'] = list(fbx_export or ['Geo_grp', 'root_jnt'])
        return self.save()


__all__ = ['OpenPipelineConfig']
