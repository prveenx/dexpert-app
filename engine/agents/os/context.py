import logging

log = logging.getLogger(__name__)

class OSContext:
    """
    Transforms the deep JSON tree into the dense textual prompt for the OS Agent.
    Implements the spatial clustering logic from Dexpert Labs.
    """
    def __init__(self):
        self.node_map = {} # Maps standard ax_id (int) -> {runtime_id, bbox, role}
        self.node_count = 0
        
        self.ACTION_ROLES = ['BTN', 'TXT', 'LBL', 'CHK', 'RAD', 'LNK', 'EDT', 'LST', 'CBO', 'TAB', 'TBL', 'PAN', 'WIN']

    def format_tree(self, root_node: dict) -> str:
        self.node_map.clear()
        self.node_count = 0
        lines =[]
        self._process_node(root_node, lines, depth=0)
        return "\n".join(lines)

    def _process_node(self, node: dict, output_lines: list, depth: int = 0):
        if not node: return
        
        role = node.get('role', 'UNK')
        name = node.get('name', '').strip()
        value = node.get('value', '')
        states = node.get('states',[])
        
        is_scrollable = node.get('is_scrollable', False)
        
        # Determine if interactive (needs an ax_id)
        assign_id = role in self.ACTION_ROLES or is_scrollable
        if role == 'TXT' and len(name) > 30: 
            assign_id = True
            
        node_id_str = ""
        if assign_id:
            self.node_count += 1
            node_id_str = f" "
            self.node_map = {
                "runtime_id": node.get('id', ''),
                "bbox": node.get('bbox',),
                "role": role,
                "name": name
            }

        indent = "  " * depth
        
        # Build representation string
        display_str = ""
        if role in self.ACTION_ROLES:
            display_str = f' "{name}"' if value else f' "{name}"'
        else:
            if value and value != name:
                display_str = f' "{name}" | Val: "{value}"'
            elif name:
                display_str = f' "{name}"'

        state_str = " " + " ".join(states) if states else ""
        if is_scrollable: state_str += ""

        # Skip empty structural panes
        if role in self.ACTION_ROLES and not assign_id and not display_str and not node.get('children'):
            return

        line = f"{indent}{node_id_str}{role}{display_str}{state_str}"
        output_lines.append(line)

        # Process children
        for child in node.get('children',[]):
            self._process_node(child, output_lines, depth + 1)