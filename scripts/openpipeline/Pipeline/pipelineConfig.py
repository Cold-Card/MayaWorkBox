# -*- coding: utf-8 -*-

import json
import os


class OpenPipelineConfig(object):

    def __init__(self, config_file=None):
        self.config = {}
        self.config_file_path = config_file or os.path.join(
            os.path.dirname(__file__),
            '.openpipeline_config.json'
        )
        self.load()

    def _normalize_path(self, value):
        if not value:
            return ''
        return value.replace('\\', '/')

    def _ensure_defaults(self):
        self.config.setdefault('work_path', '')
        self.config.setdefault('projects', [])
        self.config.setdefault('library_folder', 'lib')
        self.config.setdefault('last_project', '')
        self.config.setdefault('last_assetType', '')
        self.config.setdefault('last_asset', '')
        self.config.setdefault('last_task', '')
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

    def get_work_path(self):
        return self._normalize_path(self.config.get('work_path', ''))

    def set_work_path(self, path):
        self.config['work_path'] = self._normalize_path(path)
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

    def get_last_select_task(self):
        return self.config.get('last_task', '')

    def set_last_select_task(self, task_name):
        self.config['last_task'] = task_name
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


__all__ = ['OpenPipelineConfig']
