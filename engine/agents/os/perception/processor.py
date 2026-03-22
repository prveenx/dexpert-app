# FILE: /os/perception/processor.py
import sys
import re

# 🚀 COMPREHENSIVE INTERACTIVE ROLES
INTERACTIVE_ROLES = {
    'BTN', 'EDIT', 'CHK', 'TAB', 'TABI', 'LINK', 'LNK', 'ITEM', 'SEL', 'CBO', 
    'LIST', 'MENU', 'TREE', 'TABLE', 'TBL', 'ROW', 'CELL', 'SPLIT', 
    'DRP', 'SRCH', 'MSG', 'INP', 'RAD', 'SLD', 'SPN'
}

sys.setrecursionlimit(10000)

class SpatialSorter:
    @staticmethod
    def sort_children(nodes):
        if not nodes: return[]
        if len(nodes) == 1: return nodes
        
        for n in nodes:
            bbox = n.get('bbox', [0, 0, 0, 0])
            n['_left'] = bbox[0]
            n['_right'] = bbox[0] + bbox[2]
            n['_top'] = bbox[1]
            n['_bottom'] = bbox[1] + bbox[3]
        
        columns = SpatialSorter._detect_columns(nodes)
        
        if len(columns) > 1:
            sorted_nodes = []
            columns.sort(key=lambda col: min(n['_left'] for n in col))
            for col_nodes in columns:
                col_nodes.sort(key=lambda n: (n['_top'], n['_left']))
                sorted_nodes.extend(col_nodes)
            return sorted_nodes
        else:
            nodes.sort(key=lambda n: (n['_top'], n['_left']))
            return nodes
    
    @staticmethod
    def _detect_columns(nodes):
        sorted_by_x = sorted(nodes, key=lambda n: n['_left'])
        columns =[]
        for node in sorted_by_x:
            placed = False
            for col in columns:
                if SpatialSorter._overlaps_x_with_column(node, col):
                    col.append(node)
                    placed = True
                    break
            if not placed:
                if any(SpatialSorter._has_y_overlap(node, col) for col in columns):
                    columns.append([node])
                else:
                    added_to_existing = False
                    for col in columns:
                        if node['_left'] < max(n['_right'] for n in col) and node['_right'] > min(n['_left'] for n in col):
                            col.append(node)
                            added_to_existing = True
                            break
                    if not added_to_existing:
                        columns.append([node])
        return columns
    
    @staticmethod
    def _overlaps_x_with_column(node, column):
        for col_node in column:
            if node['_left'] < col_node['_right'] and node['_right'] > col_node['_left']:
                return True
        return False
    
    @staticmethod
    def _has_y_overlap(node, column):
        for col_node in column:
            if node['_top'] < col_node['_bottom'] and node['_bottom'] > col_node['_top']:
                return True
        return False


class SemanticProcessor:
    @staticmethod
    def process(node):
        """The Master Pipeline: Native UI + Electron + Data Compression"""
        # 0. Global Text Sanitization & Icon Mapping
        SemanticProcessor.clean_all_text(node)
        SemanticProcessor.resolve_unknown_types(node)
        
        # 1. Early Pruning 
        SemanticProcessor.remove_ghosts(node)
        
        # 2. Geometric & Spatial Awareness
        SemanticProcessor.assign_zones(node)

        # 3. 🚀 THE STABILIZATION LOOP: Deep Recursive Structural Fixes
        for _ in range(3):
            SemanticProcessor.unwrap_useless_containers(node)
            SemanticProcessor.resolve_nested_redundancy(node)
            SemanticProcessor.flatten_zones(node)
            SemanticProcessor.collapse_singletons(node)
        
        # 4. Component Cleanups
        SemanticProcessor.flatten_interactive_children(node)
        
        # 5. Data Density Compression
        SemanticProcessor.cluster_leaves(node) 
        SemanticProcessor.merge_list_items(node)
        
        # 6. Final Cleanup
        SemanticProcessor.remove_ghosts(node) 
        SemanticProcessor.clean_empty_groups(node)
        SemanticProcessor.collapse_singletons(node)

    @staticmethod
    def clean_all_text(node):
        def sanitize(text):
            if not isinstance(text, str): return text
            bad_chars =['\u200e', '\u200f', '\u202a', '\u202b', '\u202c', '\u202d', '\u202e', '\u200b', '\ufeff']
            for char in bad_chars: text = text.replace(char, '')

            has_pua = bool(re.search(r'[\ue000-\uf8ff]', text))
            if has_pua:
                cleaned = re.sub(r'[\ue000-\uf8ff]', '', text).strip()
                while cleaned and cleaned[0] in '|-: ': cleaned = cleaned[1:].strip()
                while cleaned and cleaned[-1] in '|-: ': cleaned = cleaned[:-1].strip()
                if not cleaned: return "[ICON]"
                return cleaned

            return text.strip()

        if 'name' in node: node['name'] = sanitize(node['name'])
        if 'value' in node: node['value'] = sanitize(node['value'])
        for child in node.get('children',[]): SemanticProcessor.clean_all_text(child)

    @staticmethod
    def resolve_unknown_types(node):
        if node.get('role') in['UNK', 'GRP', 'CUST']:
            loc = (node.get('localized_role') or '').lower()
            if loc:
                role_map = {
                    'button': 'BTN', 'push button': 'BTN', 'link': 'LNK', 'hyperlink': 'LNK',
                    'text': 'TXT', 'label': 'TXT', 'static text': 'TXT', 'image': 'IMG', 'icon': 'IMG',
                    'edit': 'EDIT', 'textbox': 'EDIT', 'document': 'EDIT', 'heading': 'HEAD',
                    'list': 'LIST', 'list item': 'ITEM', 'pane': 'PANE', 'combo box': 'SEL',
                    'drop down': 'SEL', 'radio button': 'RAD', 'check box': 'CHK'
                }
                if loc in role_map: node['role'] = role_map[loc]
        
        for child in node.get('children',[]):
            SemanticProcessor.resolve_unknown_types(child)

    @staticmethod
    def remove_ghosts(node):
        """Vaporizes empty interactive containers that serve no purpose."""
        if not node.get('children'): return
        for child in node['children']: SemanticProcessor.remove_ghosts(child)
            
        cleaned = []
        for child in node['children']:
            role = child.get('role')
            name = child.get('name', '').strip()
            val = str(child.get('value') or "").strip()
            children_count = len(child.get('children',[]))
            states = child.get('states',[])
            
            if role in INTERACTIVE_ROLES and not name and not val and children_count == 0:
                # Retain elements if they hold an active actionable state
                if any(s in ['[FOCUSED]', '[EXPANDED]', '[COLLAPSED]', '[HAS_MENU]', '[SELECTED]', '[ON]', '[OFF]'] for s in states):
                    if not name: child['name'] = "Action"
                    cleaned.append(child)
                else:
                    continue 
            else:
                cleaned.append(child)
                
        node['children'] = cleaned

    @staticmethod
    def assign_zones(node, root_bbox=None):
        if not root_bbox: root_bbox = node.get('bbox')
        if not root_bbox or root_bbox[2] == 0 or root_bbox[3] == 0:
            for child in node.get('children',[]): SemanticProcessor.assign_zones(child, root_bbox)
            return

        role = node.get('role')
        nx, ny, nw, nh = node.get('bbox',[0, 0, 0, 0])
        rx, ry, rw, rh = root_bbox

        if role in ['PANE', 'GRP', 'ZONE'] and not node.get('name') and nw > 0 and nh > 0:
            area_ratio = (nw * nh) / (rw * rh)
            if 0.05 < area_ratio < 0.95: 
                cx, cy = nx + (nw / 2), ny + (nh / 2)
                rel_x, rel_y = (cx - rx) / rw, (cy - ry) / rh
                
                assigned = False
                if rel_x < 0.35 and nh > rh * 0.6: node['name'] = "Left Sidebar"; assigned = True
                elif rel_x > 0.65 and nh > rh * 0.6: node['name'] = "Right Panel"; assigned = True
                elif rel_y < 0.25 and nw > rw * 0.6: node['name'] = "Top Navigation Bar"; assigned = True
                elif rel_y > 0.8 and nw > rw * 0.6: node['name'] = "Bottom Action Bar"; assigned = True
                elif 0.35 <= rel_x <= 0.65 and nh > rh * 0.5: node['name'] = "Main Content Area"; assigned = True
                if assigned: node['role'] = "ZONE"

        for child in node.get('children',[]): SemanticProcessor.assign_zones(child, root_bbox)

    @staticmethod
    def flatten_zones(node):
        if not node.get('children'): return
        for child in node['children']: SemanticProcessor.flatten_zones(child)
            
        new_children = []
        for child in node['children']:
            if node.get('role') == 'ZONE' and child.get('role') == 'ZONE':
                if node.get('name') == child.get('name') or not child.get('name'):
                    new_children.extend(child.get('children', []))
                    continue
            new_children.append(child)
                
        node['children'] = new_children

    @staticmethod
    def unwrap_useless_containers(node):
        if not node.get('children'): return
        for child in node['children']: SemanticProcessor.unwrap_useless_containers(child)
            
        new_children = []
        for child in node['children']:
            role = child.get('role', 'UNK')
            name = child.get('name', '').strip()
            val = str(child.get('value') or '').strip()
            is_scrollable = child.get('is_scrollable', False)
            is_wrapper = role in['PANE', 'GRP', 'WIN', 'DOC', 'CUST', 'UNK', 'ZONE']
            
            if role in ['BTN', 'ITEM', 'LNK'] and not name and not val:
                is_wrapper = True
                
            children_count = len(child.get('children',[]))
            
            if is_wrapper and not is_scrollable:
                if children_count == 1:
                    sub = child['children'][0]
                    sub_name = sub.get('name', '').strip()
                    if not name or name == sub_name or name in sub_name:
                        new_children.append(sub)
                        continue
                    elif sub.get('role') in['IMG', 'TXT', 'UNK']:
                        sub['name'] = f"{name} {sub_name}".strip()
                        new_children.append(sub)
                        continue
                
                elif children_count > 1 and not name and not val:
                    if role in ['BTN', 'ITEM', 'LNK']:
                        new_children.extend(child.get('children',[]))
                        continue

            new_children.append(child)
        node['children'] = new_children

    @staticmethod
    def resolve_nested_redundancy(node):
        if not node.get('children'): return
        new_children =[]
        for child in node['children']:
            SemanticProcessor.resolve_nested_redundancy(child)
            if len(child.get('children', [])) == 1:
                sub = child['children'][0]
                c_name = child.get('name', '').strip()
                s_name = sub.get('name', '').strip()
                if child.get('role') in['PANE', 'GRP', 'CUST', 'ZONE', 'ITEM', 'WIN', 'DOC'] and not child.get('is_scrollable'):
                    if c_name == s_name or not c_name or c_name in s_name:
                        new_children.append(sub)
                        continue
            new_children.append(child)
        node['children'] = new_children

    @staticmethod
    def collapse_singletons(node):
        if not node.get('children'): return
        for child in node['children']: SemanticProcessor.collapse_singletons(child)
            
        if len(node['children']) == 1:
            child = node['children'][0]
            p_name = (node.get('name') or "").strip()
            c_name = (child.get('name') or "").strip()
            p_role = node.get('role', 'UNK')
            c_role = child.get('role', 'UNK')
            
            p_is_shell = p_role in['PANE', 'GRP', 'UNK', 'ZONE', 'CUST', 'DOC', 'WIN', 'HEAD']
            
            if p_role in['BTN', 'ITEM', 'LNK'] and not p_name and not node.get('value'):
                p_is_shell = True
                
            names_match = not p_name or p_name == c_name or c_name in p_name or p_name in c_name
            
            if names_match and not node.get('is_scrollable'):
                new_role = c_role if p_is_shell else p_role
                if c_role in INTERACTIVE_ROLES and p_is_shell: new_role = c_role
                elif p_role in INTERACTIVE_ROLES and not p_is_shell: new_role = p_role
                elif c_role in INTERACTIVE_ROLES: new_role = c_role

                node['role'] = new_role
                node['name'] = c_name if len(c_name) > len(p_name) else p_name
                node['value'] = child.get('value') or node.get('value')
                node['children'] = child.get('children',[])
                
                # Safely merge and resolve opposing states
                merged_states = list(set(node.get('states', []) + child.get('states', [])))
                if '[ON]' in merged_states and '[OFF]' in merged_states: merged_states.remove('[OFF]')
                if '[EXPANDED]' in merged_states and '[COLLAPSED]' in merged_states: merged_states.remove('[COLLAPSED]')
                node['states'] = merged_states
                
                if child.get('is_scrollable'): node['is_scrollable'] = True
                if child.get('bbox',[0, 0, 0, 0])[2] > 0: node['bbox'] = child.get('bbox')

    @staticmethod
    def flatten_interactive_children(node):
        if not node.get('children'): return
        for child in node['children']: SemanticProcessor.flatten_interactive_children(child)
            
        role = node.get('role')
        if role in INTERACTIVE_ROLES:
            new_children = []
            for child in node.get('children',[]):
                if child.get('role') in ['TXT', 'IMG', 'UNK']:
                    c_name = child.get('name', '').strip()
                    n_name = node.get('name', '').strip()
                    
                    if c_name and c_name not in n_name:
                        if c_name == "[ICON]" and n_name:
                            pass 
                        else:
                            node['name'] = f"{n_name} | {c_name}".strip(" | ")
                else:
                    new_children.append(child)
            node['children'] = new_children

    @staticmethod
    def cluster_leaves(node):
        if not node.get('children'): return
        for child in node['children']: SemanticProcessor.cluster_leaves(child)
            
        if node.get('role') in['TREE', 'LIST', 'TBL', 'TABLE', 'GRID', 'TASKBAR', 'ROW', 'CBO', 'SEL', 'DAT', 'ZONE']:
            return
            
        new_children =[]
        cluster_buffer =[]
        
        def flush_buffer():
            if not cluster_buffer: return
            if len(cluster_buffer) == 1:
                new_children.append(cluster_buffer[0])
            else:
                texts =[]
                for n in cluster_buffer:
                    name = n.get('name', '')
                    val = n.get('value')
                    if n.get('role') == 'IMG': texts.append(name if name else "[IMG]")
                    elif name: texts.append(name)
                    elif val: texts.append(val)
                
                unique_texts = list(dict.fromkeys(texts))
                if "[ICON]" in unique_texts and len(unique_texts) > 1:
                    unique_texts.remove("[ICON]")

                merged_text = " | ".join(unique_texts)
                
                if merged_text and len(merged_text) < 500:
                    base = cluster_buffer[0]
                    base['name'] = merged_text
                    base['role'] = 'TXT' 
                    base['children'] =[]
                    new_children.append(base)
                else:
                    new_children.extend(cluster_buffer)
            cluster_buffer.clear()

        for child in node['children']:
            if child.get('role') in['TXT', 'IMG', 'UNK', 'GRP'] and not child.get('children'):
                cluster_buffer.append(child)
            else:
                flush_buffer()
                new_children.append(child)
                
        flush_buffer()
        node['children'] = new_children

    @staticmethod
    def merge_list_items(node):
        if not node.get('children'): return
        for child in node['children']: SemanticProcessor.merge_list_items(child)
            
        role = node.get('role')
        if role in ['ITEM', 'ROW', 'LISTI']:
            texts =[]
            if node.get('name'): texts.append(node['name'])
            
            def extract_text(n):
                n_name = (n.get('name') or '').strip()
                n_val = str(n.get('value') or '').strip()
                if n_name and n_name not in texts: texts.append(n_name)
                if n_val and n_val not in texts: texts.append(n_val)
                for c in n.get('children',[]): extract_text(c)
            
            interactable_children = []
            for child in node['children']:
                c_role = child.get('role')
                c_states = child.get('states', [])
                
                if c_role not in INTERACTIVE_ROLES or c_role in['TXT', 'ITEM']:
                    extract_text(child)
                elif c_role in['INP', 'EDIT'] and not child.get('children') and '[FOCUSED]' not in c_states:
                    extract_text(child)
                else:
                    extract_text(child)
                    interactable_children.append(child)
            
            ignored =["name", "date modified", "type", "size", "status", "column header", "[ICON]", "read", "delivered", "sent", "received"]
            clean_texts =[]
            for t in texts:
                if t.lower() not in ignored and not any(t in existing for existing in clean_texts):
                    clean_texts.append(t)
                    
            if clean_texts:
                node['name'] = " | ".join(clean_texts)
            
            node['children'] = interactable_children

    @staticmethod
    def clean_empty_groups(node):
        if 'children' in node:
            for child in node['children']: SemanticProcessor.clean_empty_groups(child)
            node['children'] = [c for c in node['children'] if SemanticProcessor.is_useful(c)]

    @staticmethod
    def is_useful(node):
        if len(node.get('children',[])) > 0: return True
        has_text = len((node.get('name') or "").strip()) > 0
        has_value = node.get('value') is not None and len(str(node.get('value')).strip()) > 0
        has_meaningful_state = any(s in ['[ON]', '[OFF]', '[CHECKED]', '[SELECTED]', '[FOCUSED]', '[DISABLED]'] for s in node.get('states',[]))
        return has_text or has_value or node.get('role') in INTERACTIVE_ROLES or node.get('is_scrollable', False) or has_meaningful_state


class Printer:
    def __init__(self):
        self.node_count = 0
        self.output_lines =[]
        self.elements_map = {} 
        self.ACTION_ROLES = INTERACTIVE_ROLES

    def process_tree(self, node, depth=0, parent_role=None):
        role = node.get('role', 'UNK')
        
        if 'children' in node and role not in['LIST', 'TREE', 'CBO', 'SEL', 'TBL', 'TABLE']:
            node['children'] = SpatialSorter.sort_children(node['children'])

        name = node.get('name', '').strip()
        value = node.get('value')
        states = list(set(node.get('states',[])))
        is_scrollable = node.get('is_scrollable', False)
        
        assign_id = role in self.ACTION_ROLES or is_scrollable
        if role == 'TXT' and len(name) > 20: assign_id = True
        if parent_role in['LIST', 'TREE', 'ROW', 'MENU', 'CBO', 'SEL', 'TABI'] and name: assign_id = True
        
        node_id = ""
        if assign_id:
            self.node_count += 1
            node['assigned_id'] = self.node_count
            node_id = f"[{self.node_count}] "
            self.elements_map[self.node_count] = {
                "id": self.node_count, "role": role, "name": name, "bbox": node.get('bbox', [0, 0, 0, 0])
            }
        
        if parent_role == 'TABLE':
            is_coord = re.match(r'^[A-Z]+\d+$', name)
            display_str = f' "{value}"' if value else f' "{name}"'
            self.output_lines.append(f"{node_id}{display_str}".strip())
            return
            
        indent = "  " * depth

        # 🚀 HIGH-VISIBILITY STATE MAPPING & SORTING FOR LLMs
        if is_scrollable and '[SCROLLABLE]' not in states: states.append('[SCROLLABLE]')
        mapped_states =[]
        for s in states:
            if role in ['CHK', 'RAD']:
                if s == '[ON]': mapped_states.append('[CHECKED]')
                elif s == '[OFF]': mapped_states.append('[UNCHECKED]')
                else: mapped_states.append(s)
            elif role in ['BTN', 'ITEM']:
                if s == '[ON]': mapped_states.append('[TOGGLED_ON]')
                elif s == '[OFF]': mapped_states.append('[TOGGLED_OFF]')
                else: mapped_states.append(s)
            else:
                mapped_states.append(s)

        # Ensure FOCUSED and DISABLED are always at the absolute front
        state_priority = {
            '[FOCUSED]': 1, '[DISABLED]': 2, '[CHECKED]': 3, '[UNCHECKED]': 3,
            '[TOGGLED_ON]': 3, '[TOGGLED_OFF]': 3, '[SELECTED]': 3,
            '[EXPANDED]': 4, '[COLLAPSED]': 4, '[HAS_MENU]': 5, '[SCROLLABLE]': 6
        }
        mapped_states = list(set(mapped_states))
        mapped_states.sort(key=lambda x: state_priority.get(x, 10))
        
        state_str = "".join(f" {s}" for s in mapped_states)
        
        display_str = ""
        
        if role in ['INP', 'EDIT', 'DOC']:
            clean_value = (value or "").strip()
            content_tag = " [FILLED]" if clean_value else " [EMPTY]"
            if clean_value:
                lines =[l.strip() for l in clean_value.splitlines() if l.strip()]
                first_preview = " | ".join(lines[:2])
                last_preview = " | ".join(lines[-2:])
                meta = f"({len(lines)} lines, {len(clean_value)} chars){'[TRUNCATED]' if '[TRUNCATED' in (value or '') else ''}"
                val_str = f'Start: "{first_preview[:80]}" ... End: "{last_preview[:80]}"' if len(lines) > 2 else f'Val: "{clean_value[:150]}"'
                display_str = f'{content_tag} "{name}" {meta} | {val_str}' if name else f'{content_tag} {meta} | {val_str}'
            else:
                display_str = f'{content_tag} "{name}" | Val: ""' if name else f'{content_tag} | Val: ""'
        else:
            if value and name and name not in value: display_str = f' "{name}" | Val: "{value}"'
            elif value: display_str = f' "{value}"'
            elif name: display_str = f' "{name}"'
        
        if role in ['GRP', 'PANE', 'UNK'] and not name and node.get('children'): role = "ZONE"
        
        if role in['PANE', 'GRP', 'UNK', 'WIN', 'ZONE', 'CUST', 'DOC'] and not assign_id and not display_str and not state_str:
            for child in node.get('children',[]): self.process_tree(child, depth, parent_role=role)
            return
        
        # Format Example: "  [1] EDIT [FOCUSED] [EMPTY] "Search Box""
        self.output_lines.append(f"{indent}{node_id}{role}{state_str}{display_str}")

        if self._is_tabular(node):
            self._render_tabular_children(node, depth + 1)
        else:
            for child in node.get('children',[]):
                self.process_tree(child, depth + 1, parent_role=role)
                
    def _is_tabular(self, node):
        role = node.get('role', 'UNK')
        if role not in['DAT', 'TABLE', 'GRID', 'TBL']: return False
        
        for child in node.get('children', []):
            if child.get('role') in ['ITEM', 'ROW'] and len(child.get('children', [])) > 0:
                return False

        leaves =[]
        def get_leaves(n):
            if SemanticProcessor.is_useful(n) and not n.get('children'): leaves.append(n)
            for c in n.get('children',[]): get_leaves(c)
        get_leaves(node)

        if len(leaves) < 6: return False

        x_centers = [c.get('bbox', [0, 0, 0, 0])[0] + (c.get('bbox', [0, 0, 0, 0])[2] / 2) for c in leaves]
        if not x_centers: return False
        
        x_centers.sort()
        columns = 1
        last_x = x_centers[0]
        
        for x in x_centers[1:]:
            if x - last_x > 40:
                columns += 1
                last_x = x
        
        if columns < 2: return False
        return True

    def _render_tabular_children(self, node, depth):
        flat_cells =[]
        def extract_cells(n):
            if SemanticProcessor.is_useful(n) and (n.get('role') not in['PANE', 'GRP', 'DAT', 'TABLE', 'GRID', 'TBL'] or n.get('name')):
                flat_cells.append(n)
            for c in n.get('children',[]): extract_cells(c)
        
        for c in node.get('children',[]): extract_cells(c)
            
        valid_cells = [c for c in flat_cells if c.get('bbox',[0, 0, 0, 0])[2] > 0 and c.get('bbox',[0, 0, 0, 0])[3] > 0]
        if not valid_cells: return
            
        for c in valid_cells:
            bbox = c.get('bbox')
            c['_cx'] = bbox[0] + (bbox[2] / 2)
            c['_cy'] = bbox[1] + (bbox[3] / 2)
            
        valid_cells.sort(key=lambda c: c['_cy'])
        
        rows, current_row, current_y = [],[], None
        
        for c in valid_cells:
            y, h = c['_cy'], c.get('bbox')[3]
            if current_y is None or abs(y - current_y) <= (h / 3):
                current_row.append(c)
                current_y = y if current_y is None else (current_y + y) / 2
            else:
                rows.append(current_row)
                current_row, current_y = [c], y
                
        if current_row: rows.append(current_row)
            
        known_x_centers = sorted(list(set(round(c['_cx'] / 10) * 10 for c in valid_cells)))
        columns =[]
        for x in known_x_centers:
            if not columns or x - columns[-1] > 20: columns.append(x)

        indent = "  " * depth
        MAX_ROWS, MAX_COLS = 25, 15
        
        for r_idx, row in enumerate(rows):
            if r_idx >= MAX_ROWS:
                self.output_lines.append(f"{indent}...[Table Truncated] ...")
                break
            
            aligned_row = [""] * len(columns)
            for cell in row:
                col_idx = min(range(len(columns)), key=lambda i: abs(columns[i] - cell['_cx']))
                aligned_row[col_idx] = cell
                
            cells_text =[]
            for c_idx, cell in enumerate(aligned_row):
                if c_idx >= MAX_COLS:
                    cells_text.append("...")
                    break
                if not cell:
                    cells_text.append(" - ")
                    continue
                    
                old_lines = self.output_lines
                self.output_lines = []
                temp_cell = cell.copy()
                temp_cell['children'] =[]
                self.process_tree(temp_cell, depth=0, parent_role='TABLE')
                cell_str = self.output_lines[0].strip() if self.output_lines else str(cell.get('name', ''))
                self.output_lines = old_lines
                
                if len(cell_str) > 60: cell_str = cell_str[:57] + "..."
                cells_text.append(cell_str)
                    
            self.output_lines.append(f"{indent}| " + " | ".join(cells_text) + " |")

    def get_output(self):
        return "\n".join(self.output_lines)