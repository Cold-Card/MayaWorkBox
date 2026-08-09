# -*- coding: utf-8 -*-
import maya.cmds as cmds
import re


class LogicCompiler:

    IGNORE_NODE_TYPES = [
        'renderLayer', 'displayLayer', 'objectSet', 
        'shadingEngine', 'materialInfo', 'groupId',
        'renderLayerManager', 'lightLinker', 'partition',
        'hyperLayout', 'hyperView', 'script', 'nodeGraphEditorInfo'
    ]
    
    IGNORE_NAME_PREFIXES = [
        'default', 'lambert1', 'particleCloud1', 
        'initial', 'layerManager', 'lightLinker1',
        'renderPartition', 'shaderPartition'
    ]
    
    DEFAULT_VALUE_TOLERANCE = 1e-6

    def __init__(self):
        self._var_map = {}
        self._processed_connections = set()
        self._connected_attrs = set()
    
    def _normalize_to_list(self, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    def validate_network(self, sources, targets, intermediates):
        sources = self._normalize_to_list(sources)
        targets = self._normalize_to_list(targets)
        
        valid_scope = set(sources + targets + intermediates)
        missing_dependencies = set()

        for node in intermediates:
            connected_nodes = cmds.listConnections(node) or []

            for linked_node in connected_nodes:
                try:
                    if cmds.nodeType(linked_node) in self.IGNORE_NODE_TYPES:
                        continue
                except:
                    continue

                is_ignored_name = any(linked_node.startswith(prefix) for prefix in self.IGNORE_NAME_PREFIXES)
                if is_ignored_name:
                    continue

                if linked_node not in valid_scope:
                    missing_dependencies.add(linked_node)

        return list(missing_dependencies)

    def compile(self, sources, targets, intermediates):
        sources = self._normalize_to_list(sources)
        targets = self._normalize_to_list(targets)
        
        self._var_map = {}
        self._processed_connections = set()
        self._connected_attrs = set()
        
        self._collect_connected_attributes(sources + targets + intermediates)
        
        for i, src in enumerate(sources):
            var_name = f"source_{i}" if len(sources) > 1 else "source"
            self._var_map[src] = var_name
            
        for i, tgt in enumerate(targets):
            var_name = f"target_{i}" if len(targets) > 1 else "target"
            self._var_map[tgt] = var_name
        
        lines = []
        
        lines.append("import maya.cmds as cmds")
        lines.append("")
        
        func_params = self._generate_function_params(sources, targets)
        lines.append(f"def build_connection_logic({func_params}):")
        
        self._generate_docstring(lines, sources, targets)
        
        self._add_line(lines, "cmds.undoInfo(openChunk=True)")
        self._add_line(lines, "try:")

        for node in intermediates:
            safe_name = self._sanitize_node_name(node)
            self._var_map[node] = f"{safe_name}_var"

        self._add_line(lines, "# 1. Create Intermediate Nodes", indent_level=2)
        prefix_var = "source" if len(sources) == 1 else "source_0"
        for node in intermediates:
            node_type = cmds.nodeType(node)
            var_name = self._var_map[node]
            safe_node_name = self._sanitize_node_name(node)
            self._add_line(lines, f"{var_name} = cmds.createNode('{node_type}', name=f'{{{prefix_var}}}_{safe_node_name}_gen')", indent_level=2)

        lines.append("")
        
        self._add_line(lines, "# 2. Set Attributes (Skip Default Values)", indent_level=2)
        self._compile_attributes(lines, intermediates)

        lines.append("")
        
        self._add_line(lines, "# 3. Connect Attributes (Including Message Type)", indent_level=2)
        self._compile_connections(lines, sources, targets, intermediates)

        lines.append("")
        
        if len(sources) == 1 and len(targets) == 1:
            self._add_line(lines, "print(f'Success: Logic connected from {source} to {target}')", indent_level=2)
        else:
            self._add_line(lines, f"print(f'Success: Logic connected ({len(sources)} sources -> {len(targets)} targets)')", indent_level=2)
        
        self._add_line(lines, "finally:")
        self._add_line(lines, "cmds.undoInfo(closeChunk=True)", indent_level=2)
        
        return "\n".join(lines)

    def _collect_connected_attributes(self, nodes):
        for node in nodes:
            connections = cmds.listConnections(node, connections=True, plugs=True, destination=True) or []
            for i in range(0, len(connections), 2):
                dst_plug = connections[i + 1] if i + 1 < len(connections) else None
                if dst_plug:
                    self._connected_attrs.add(dst_plug)
                    parts = dst_plug.split('.')
                    if len(parts) > 1:
                        node_name = parts[0]
                        attr_parts = parts[1:]
                        for j in range(len(attr_parts)):
                            partial_attr = '.'.join([node_name] + attr_parts[:j+1])
                            self._connected_attrs.add(partial_attr)

    def _generate_function_params(self, sources, targets):
        params = []
        
        if len(sources) == 1:
            params.append("source")
        else:
            for i in range(len(sources)):
                params.append(f"source_{i}")
        
        if len(targets) == 1:
            params.append("target")
        else:
            for i in range(len(targets)):
                params.append(f"target_{i}")
        
        return ", ".join(params)

    def _generate_docstring(self, lines, sources, targets):
        lines.append('    """')
        lines.append(f'    Auto-generated logic network')
        lines.append(f'    Sources: {", ".join(sources)}')
        lines.append(f'    Targets: {", ".join(targets)}')
        lines.append('    ')
        lines.append('    Args:')
        
        if len(sources) == 1:
            lines.append(f'        source: 驱动端节点 (原: {sources[0]})')
        else:
            for i, src in enumerate(sources):
                lines.append(f'        source_{i}: 驱动端节点 {i+1} (原: {src})')
        
        if len(targets) == 1:
            lines.append(f'        target: 被驱动端节点 (原: {targets[0]})')
        else:
            for i, tgt in enumerate(targets):
                lines.append(f'        target_{i}: 被驱动端节点 {i+1} (原: {tgt})')
        
        lines.append('    """')

    def _compile_attributes(self, lines, nodes):
        for node in nodes:
            var_name = self._var_map[node]
            node_type = cmds.nodeType(node)
            all_attrs = self._get_settable_attributes(node)
            
            for attr in all_attrs:
                full_attr = f"{node}.{attr}"
                
                try:
                    if self._is_attr_connected(node, attr):
                        continue
                    
                    attr_type = cmds.getAttr(full_attr, type=True)
                    val = cmds.getAttr(full_attr)
                    
                    is_critical_attr = (node_type == 'unitConversion' and attr == 'conversionFactor')
                    if not is_critical_attr and self._is_default_value(node, attr, val, attr_type):
                        continue
                    
                    code = self._generate_setattr_code(var_name, attr, attr_type, val)
                    if code:
                        self._add_line(lines, code, indent_level=2)
                        
                except Exception:
                    continue

    def _is_attr_connected(self, node, attr):
        full_attr = f"{node}.{attr}"
        
        if full_attr in self._connected_attrs:
            return True
        
        try:
            if cmds.connectionInfo(full_attr, isDestination=True):
                return True
        except:
            pass
        
        try:
            base_attr = attr.split('[')[0]
            children = cmds.attributeQuery(base_attr, node=node, listChildren=True) or []
            for child in children:
                child_full = f"{node}.{child}"
                if child_full in self._connected_attrs:
                    return True
                if cmds.connectionInfo(child_full, isDestination=True):
                    return True
        except:
            pass
        
        return False

    def _is_default_value(self, node, attr, current_value, attr_type):
        try:
            base_attr = attr.split('[')[0]
            
            default = cmds.attributeQuery(base_attr, node=node, listDefault=True)
            
            if default is None:
                return False
            
            return self._values_equal(current_value, default, attr_type)
            
        except:
            return False

    def _values_equal(self, val1, val2, attr_type):
        if isinstance(val1, (list, tuple)) and isinstance(val2, (list, tuple)):
            if len(val1) != len(val2):
                return False
            flat1 = self._flatten(val1)
            flat2 = self._flatten(val2)
            if len(flat1) != len(flat2):
                return False
            for v1, v2 in zip(flat1, flat2):
                if not self._values_equal(v1, v2, attr_type):
                    return False
            return True
        
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return abs(val1 - val2) < self.DEFAULT_VALUE_TOLERANCE
        
        return val1 == val2

    def _flatten(self, lst):
        result = []
        for item in lst:
            if isinstance(item, (list, tuple)):
                result.extend(self._flatten(item))
            else:
                result.append(item)
        return result

    def _get_settable_attributes(self, node):
        result = set()
        
        basic_attrs = cmds.listAttr(node, keyable=True, write=True) or []
        
        user_attrs = cmds.listAttr(node, userDefined=True) or []
        
        special_attrs = cmds.listAttr(node, string="inputMatrix") or []
        special_attrs += cmds.listAttr(node, string="operation") or []
        special_attrs += cmds.listAttr(node, string="input*") or []
        
        node_type = cmds.nodeType(node)
        if node_type == 'unitConversion':
            result.add('conversionFactor')
        
        all_base_attrs = set(basic_attrs + user_attrs + special_attrs)
        
        for attr in all_base_attrs:
            if '.' in attr:
                continue
            
            if node_type == 'unitConversion' and attr == 'conversionFactor':
                continue
                
            try:
                self._process_attribute(node, attr, result)
            except:
                result.add(attr)
        
        return list(result)

    def _process_attribute(self, node, attr, result):
        base_attr = attr.split('[')[0]
        full_attr = f"{node}.{attr}"
        
        try:
            is_multi = cmds.attributeQuery(base_attr, node=node, multi=True)
        except:
            is_multi = False
        
        if is_multi:
            try:
                indices = cmds.getAttr(f"{node}.{base_attr}", multiIndices=True) or []
                for idx in indices:
                    indexed_attr = f"{base_attr}[{idx}]"
                    self._process_single_or_compound(node, indexed_attr, result)
            except:
                pass
        else:
            self._process_single_or_compound(node, attr, result)

    def _process_single_or_compound(self, node, attr, result):
        base_attr = attr.split('[')[0]
        
        try:
            children = cmds.attributeQuery(base_attr, node=node, listChildren=True)
        except:
            children = None
        
        if children:
            for child in children:
                if '[' in attr:
                    child_attr = f"{attr}.{child}"
                else:
                    child_attr = child
                result.add(child_attr)
        else:
            result.add(attr)

    def _generate_setattr_code(self, var_name, attr, attr_type, val):
        if attr_type == 'matrix':
            val_str = ", ".join([str(v) for v in val])
            return f"cmds.setAttr(f'{{{var_name}}}.{attr}', {val_str}, type='matrix')"

        if attr_type in ('double3', 'float3', 'short3', 'long3'):
            if isinstance(val, list) and len(val) == 1 and len(val[0]) == 3:
                v1, v2, v3 = val[0]
                return f"cmds.setAttr(f'{{{var_name}}}.{attr}', {v1}, {v2}, {v3}, type='{attr_type}')"

        if attr_type in ('double2', 'float2', 'short2', 'long2'):
            if isinstance(val, list) and len(val) == 1 and len(val[0]) == 2:
                v1, v2 = val[0]
                return f"cmds.setAttr(f'{{{var_name}}}.{attr}', {v1}, {v2}, type='{attr_type}')"

        if attr_type == 'enum':
            return f"cmds.setAttr(f'{{{var_name}}}.{attr}', {val})"

        if attr_type == 'string':
            if val:
                escaped_val = val.replace("\\", "\\\\").replace("'", "\\'")
                return f"cmds.setAttr(f'{{{var_name}}}.{attr}', '{escaped_val}', type='string')"
            return None

        if attr_type == 'bool':
            return f"cmds.setAttr(f'{{{var_name}}}.{attr}', {val})"

        if isinstance(val, (int, float)):
            return f"cmds.setAttr(f'{{{var_name}}}.{attr}', {val})"

        if attr_type in ('double', 'float', 'long', 'short'):
            return f"cmds.setAttr(f'{{{var_name}}}.{attr}', {val})"

        return None

    def _compile_connections(self, lines, sources, targets, intermediates):
        all_relevant_nodes = set(intermediates + sources + targets)
        check_list = sources + intermediates

        for node in check_list:
            connections = cmds.listConnections(
                node, 
                connections=True, 
                plugs=True, 
                source=False, 
                destination=True,
                skipConversionNodes=False
            ) or []
            
            for i in range(0, len(connections), 2):
                src_plug_real = connections[i]
                dst_plug_real = connections[i + 1]
                
                conn_pair = (src_plug_real, dst_plug_real)
                if conn_pair in self._processed_connections:
                    continue
                self._processed_connections.add(conn_pair)
                
                dst_node_real = dst_plug_real.split('.')[0]
                src_node_real = src_plug_real.split('.')[0]

                if dst_node_real in all_relevant_nodes:
                    src_var = self._var_map.get(src_node_real)
                    dst_var = self._var_map.get(dst_node_real)
                    if not src_var or not dst_var: 
                        continue

                    src_plug_code = src_plug_real.replace(src_node_real, f"{{{src_var}}}")
                    dst_plug_code = dst_plug_real.replace(dst_node_real, f"{{{dst_var}}}")
                    
                    try:
                        attr_type = cmds.getAttr(src_plug_real, type=True)
                        if attr_type == 'message':
                            self._add_line(lines, f"# Message connection", indent_level=2)
                    except:
                        pass
                    
                    self._add_line(lines, f"cmds.connectAttr(f'{src_plug_code}', f'{dst_plug_code}', force=True)", indent_level=2)

    @staticmethod
    def _sanitize_node_name(node_name):
        clean_name = node_name.split(':')[-1].split('|')[-1]
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', clean_name)
        if clean_name and clean_name[0].isdigit():
            clean_name = '_' + clean_name
        return clean_name

    @staticmethod
    def _add_line(lines, code, indent_level=1):
        lines.append("    " * indent_level + code)
