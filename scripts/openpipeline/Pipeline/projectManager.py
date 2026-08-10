# -*- coding: utf-8 -*-

import base64
import json
import os
import re
import shutil
import time

try:
    import maya.cmds as cmds
except ImportError:  # pragma: no cover
    cmds = None


class ProjectManager(object):
    """管理单个项目下的资产、子类型和版本文件。"""

    def __init__(self, project_root, project_name, library_folder='lib'):
        self.project_root = project_root.replace('\\', '/') if project_root else ''
        self.project_name = project_name or os.path.basename(self.project_root.rstrip('/'))
        self.library_folder = library_folder or 'lib'

    def _normalize(self, value):
        return value.replace('\\', '/') if value else ''

    def _ensure_dir(self, path):
        if path and not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    def get_asset_dir(self, asset_type, asset_name):
        return self._normalize(os.path.join(self.project_root, self.library_folder, asset_type, asset_name))

    def list_assets(self, asset_type):
        asset_type_dir = os.path.join(self.project_root, self.library_folder, asset_type)
        if not os.path.exists(asset_type_dir):
            return []
        assets = []
        for name in sorted(os.listdir(asset_type_dir)):
            path = os.path.join(asset_type_dir, name)
            if os.path.isdir(path):
                assets.append(name)
        return assets

    def create_asset(self, asset_type, asset_name):
        if not asset_type or not asset_name:
            return False
        asset_dir = self.get_asset_dir(asset_type, asset_name)
        if os.path.exists(asset_dir):
            return False
        self._ensure_dir(os.path.dirname(asset_dir))
        self._ensure_dir(asset_dir)
        self._ensure_dir(os.path.join(asset_dir, 'components'))
        return True

    def list_subtypes(self, asset_type, asset_name):
        asset_dir = self.get_asset_dir(asset_type, asset_name)
        subtype_dir = os.path.join(asset_dir, 'components')
        if not os.path.exists(subtype_dir):
            return []
        subtypes = []
        for name in sorted(os.listdir(subtype_dir),reverse=True):
            path = os.path.join(subtype_dir, name)
            if os.path.isdir(path):
                subtypes.append(name)
        return subtypes

    def create_subtype(self, asset_type, asset_name, subtype_name):
        asset_dir = self.get_asset_dir(asset_type, asset_name)
        subtype_path = os.path.join(asset_dir, 'components', subtype_name)
        if os.path.exists(subtype_path):
            return False
        self._ensure_dir(os.path.dirname(subtype_path))
        self._ensure_dir(subtype_path)
        self._ensure_dir(os.path.join(subtype_path, 'master'))
        self._ensure_dir(os.path.join(subtype_path, 'notes'))
        self._ensure_dir(os.path.join(subtype_path, 'workshop'))
        return True

    def rename_subtype(self, asset_type, asset_name, subtype_name, new_name):
        old_path = os.path.join(self.get_asset_dir(asset_type, asset_name), 'components', subtype_name)
        new_path = os.path.join(self.get_asset_dir(asset_type, asset_name), 'components', new_name)
        if not os.path.exists(old_path) or os.path.exists(new_path):
            return False, u'子类型不存在或新名称已存在'
        os.rename(old_path, new_path)
        return True, u'子类型已重命名为 {}'.format(new_name)

    def _get_subtype_dir(self, asset_type, asset_name, subtype_name):
        return os.path.join(self.get_asset_dir(asset_type, asset_name), 'components', subtype_name)

    def get_workshop_versions(self, asset_type, asset_name, subtype_name):
        workshop_dir = os.path.join(self._get_subtype_dir(asset_type, asset_name, subtype_name), 'workshop')
        if not os.path.exists(workshop_dir):
            return []
        versions = []
        for name in sorted(os.listdir(workshop_dir),reverse=True):
            path = os.path.join(workshop_dir, name)
            if os.path.isfile(path):
                versions.append(name)
        return versions

    def get_latest_workshop(self, asset_type, asset_name, subtype_name):
        versions = self.get_workshop_versions(asset_type, asset_name, subtype_name)
        if not versions:
            return None
        workshop_dir = os.path.join(self._get_subtype_dir(asset_type, asset_name, subtype_name), 'workshop')
        latest_path = None
        latest_time = None
        for version in versions:
            path = os.path.join(workshop_dir, version)
            if not os.path.exists(path):
                continue
            stamp = os.path.getmtime(path)
            if latest_time is None or stamp > latest_time:
                latest_time = stamp
                latest_path = path
        return latest_path

    def _get_notes_json_path(self, subtype_dir):
        notes_dir = os.path.join(subtype_dir, 'notes')
        if not os.path.exists(notes_dir):
            os.makedirs(notes_dir, exist_ok=True)
        return os.path.join(notes_dir, 'notes.json')

    def _load_notes_json(self, subtype_dir):
        note_json = self._get_notes_json_path(subtype_dir)
        if os.path.exists(note_json):
            try:
                with open(note_json, 'r', encoding='utf-8') as fh:
                    return json.load(fh)
            except Exception:
                return {}
        return {}

    def _save_notes_json(self, subtype_dir, data):
        note_json = self._get_notes_json_path(subtype_dir)
        try:
            with open(note_json, 'w', encoding='utf-8') as fh:
                json.dump(data, fh, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    def delete_note_entry(self, asset_type, asset_name, subtype_name, version_filename):
        subtype_dir = self._get_subtype_dir(asset_type, asset_name, subtype_name)
        notes_data = self._load_notes_json(subtype_dir)
        if version_filename in notes_data:
            notes_data.pop(version_filename, None)
            return self._save_notes_json(subtype_dir, notes_data)
        return False

    def _format_note_entry(self, filename, metadata):
        if not metadata:
            return ''

        lines = []
        for key in ['Version', 'Time', 'Maya', 'Note']:
            if key in metadata:
                lines.append(u"{}: {}".format(key, metadata[key]))
        return u"\n".join(lines)

    def get_notes(self, asset_type, asset_name, subtype_name, version_filename=None):
        subtype_dir = self._get_subtype_dir(asset_type, asset_name, subtype_name)
        if not os.path.exists(subtype_dir):
            return ''

        notes_data = self._load_notes_json(subtype_dir)
        if not notes_data:
            return ''

        if version_filename:
            if version_filename in notes_data:
                return self._format_note_entry(version_filename, notes_data[version_filename])
            return ''

        entries = []
        for filename in sorted(notes_data.keys(),reverse=True):
            entries.append(self._format_note_entry(filename, notes_data[filename]))
        return u"\n\n".join(entries)

    def write_note_info(self, task_dir, version_filename, info='', workshop=True):
        if not task_dir or not version_filename:
            return False
        if not os.path.exists(task_dir):
            os.makedirs(task_dir, exist_ok=True)

        subtype_dir = task_dir
        notes_data = self._load_notes_json(subtype_dir)
        version_index = ''
        match = re.search(r'workshop_(\d{3})', version_filename, re.IGNORECASE)
        if match:
            version_index = match.group(1)

        metadata = {
            'Version': version_index,
            'Time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'Maya': cmds.about(version=True) if cmds is not None else '',
            'Note': info or ''
        }

        notes_data[version_filename] = metadata
        return self._save_notes_json(subtype_dir, notes_data)

    def _get_scene_file_type(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.mb':
            return 'mayaBinary'
        return 'mayaAscii'

    def _get_next_version_index(self, asset_type, asset_name, subtype_name):
        workshop_dir = os.path.join(
            self._get_subtype_dir(asset_type, asset_name, subtype_name),
            'workshop'
        )
        if not os.path.exists(workshop_dir):
            return 1

        highest = 0
        pattern = re.compile(r'^{}_{}_workshop_(\d{{3}})\.ma$'.format(
            re.escape(asset_name), re.escape(subtype_name)
        ), re.IGNORECASE)
        for filename in os.listdir(workshop_dir):
            match = pattern.match(filename)
            if match:
                try:
                    index = int(match.group(1))
                    if index > highest:
                        highest = index
                except ValueError:
                    pass
        return highest + 1

    def _get_version_filename_for_scene(self, asset_type, asset_name, subtype_name, notes=None):
        index = self._get_next_version_index(asset_type, asset_name, subtype_name)
        return '{}_{}_workshop_{:03d}.ma'.format(
            asset_name, subtype_name, index
        )

    def save_version(self, asset_type, asset_name, subtype_name, notes=None):
        subtype_dir = self._get_subtype_dir(asset_type, asset_name, subtype_name)
        workshop_dir = os.path.join(subtype_dir, 'workshop')
        self._ensure_dir(workshop_dir)

        version_filename = self._get_version_filename_for_scene(asset_type, asset_name, subtype_name, notes)
        version_path = os.path.join(workshop_dir, version_filename)
        if cmds is not None:
            try:
                cmds.file(rename=version_path)
                cmds.file(save=True, type=self._get_scene_file_type(version_path))
                if notes:
                    self.write_note_info(subtype_dir, version_filename, notes, workshop=True)
                return True
            except Exception:
                pass

        with open(version_path, 'wb') as fh:
            fh.write(b'placeholder')
        if notes:
            self.write_note_info(subtype_dir, version_filename, notes, workshop=True)
        return True

    def save_master(self, asset_type, asset_name, subtype_name):
        subtype_dir = self._get_subtype_dir(asset_type, asset_name, subtype_name)
        master_dir = os.path.join(subtype_dir, 'master')
        self._ensure_dir(master_dir)

        master_path = os.path.join(master_dir, asset_name + '_' + subtype_name + '.ma')
        if cmds is not None:
            try:
                cmds.file(rename=master_path)
                cmds.file(save=True, type='mayaAscii')
                return True
            except Exception:
                pass
        with open(master_path, 'wb') as fh:
            fh.write(b'placeholder')
        return True

    def get_master_file(self, asset_type, asset_name, subtype_name):
        master_path = os.path.join(self._get_subtype_dir(asset_type, asset_name, subtype_name), 'master', asset_name + '_' + subtype_name + '.ma')
        if os.path.exists(master_path):
            return master_path
        return None

    def set_master(self, asset_type, asset_name, subtype_name, version_filename):
        subtype_dir = self._get_subtype_dir(asset_type, asset_name, subtype_name)
        workshop_dir = os.path.join(subtype_dir, 'workshop')
        source_path = os.path.join(workshop_dir, version_filename)
        if not os.path.exists(source_path):
            return False
        master_path = os.path.join(subtype_dir, 'master', asset_name + '_' + subtype_name + '.ma')
        shutil.copy2(source_path, master_path)
        return True

    def take_snapshot(self, asset_type, asset_name, subtype_name=None):
        asset_dir = self.get_asset_dir(asset_type, asset_name)
        self._ensure_dir(asset_dir)
        if subtype_name:
            image_path = os.path.join(self._get_subtype_dir(asset_type, asset_name, subtype_name), 'preview.png')
        else:
            image_path = os.path.join(asset_dir, 'preview.png')

        if cmds is not None:

            try:
                w = int(cmds.getAttr('defaultResolution.width'))
                h = int(cmds.getAttr('defaultResolution.height'))
            except Exception:
                w, h = 1280, 720

            try:
                frame = int(cmds.currentTime(query=True))
            except Exception:
                frame = 1

            cmds.playblast(completeFilename=image_path,
                                format='image', viewer=False,
                                showOrnaments=False, widthHeight=[w, h], percent=100, quality=100,
                                offScreen=True,frame=frame)

            if os.path.exists(image_path):
                return image_path

        return image_path


__all__ = ['ProjectManager']
