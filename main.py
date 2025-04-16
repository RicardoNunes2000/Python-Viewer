import streamlit as st
import json
import re
from collections import defaultdict

# Initialize session state variables
if 'expanded_keys' not in st.session_state:
    st.session_state.expanded_keys = set()
if 'json_input' not in st.session_state:
    st.session_state['json_input'] = ''
if 'generated_code' not in st.session_state:
    st.session_state['generated_code'] = ''
if 'search_query' not in st.session_state:
    st.session_state['search_query'] = ''
if 'selected_jsonl_index' not in st.session_state:
    st.session_state['selected_jsonl_index'] = 0
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = []
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'path_finder'  # 'path_finder' or 'tree_view'
if 'display_mode' not in st.session_state:
    st.session_state['display_mode'] = 'keys'  # 'keys' or 'values'

# Function to generate Python code for accessing a specific item
def generate_python_code(path):
    """Generate Python code to access a specific JSON path"""
    code = "import json\n\n"
    code += "# Load your JSON data\n"
    code += "data = json.loads(json_string)  # Replace json_string with your JSON data\n\n"
    code += f"# Access the specific path\n"
    code += f"value = {path}\n"
    code += "print(value)"
    return code

# Function to format value previews based on type
def format_value_preview(value, max_length=30):
    if isinstance(value, str):
        return f'"{value[:max_length]}{"..." if len(value) > max_length else ""}"'
    elif isinstance(value, (dict, list)):
        return f"{type(value).__name__} with {len(value)} items"
    else:
        return str(value)

# Function to extract paths from JSON
def extract_paths(json_obj, current_path="data", paths=None):
    """Extract all possible paths from JSON object"""
    if paths is None:
        paths = []
    
    if isinstance(json_obj, dict):
        if not json_obj:  # Handle empty dict
            paths.append((current_path, "{}"))
            return paths
            
        for key, value in json_obj.items():
            new_path = f"{current_path}['{key}']" if isinstance(key, str) else f"{current_path}[{key}]"
            if isinstance(value, (dict, list)):
                extract_paths(value, new_path, paths)
            else:
                preview = format_value_preview(value)
                paths.append((new_path, preview, key, value))
    elif isinstance(json_obj, list):
        if not json_obj:  # Handle empty list
            paths.append((current_path, "[]"))
            return paths
            
        for i, item in enumerate(json_obj):
            new_path = f"{current_path}[{i}]"
            if isinstance(item, (dict, list)):
                extract_paths(item, new_path, paths)
            else:
                preview = format_value_preview(item)
                paths.append((new_path, preview, i, item))
    else:
        # This handles the case where the root is a primitive
        preview = format_value_preview(json_obj)
        paths.append((current_path, preview, None, json_obj))
    
    return paths

# Function to load example JSON
def load_example():
    example_json = {
        "name": "Jane Doe",
        "age": 28,
        "address": {
            "street": "456 Elm St",
            "city": "Othertown",
            "zip": "67890",
            "coordinates": {
                "latitude": 40.7128,
                "longitude": -74.0060
            }
        },
        "pageProps": {
            "allAppsData": [
                {
                    "id": "123",
                    "name": "Sample App",
                    "hostedWithStreamlit": True
                }
            ]
        }
    }
    st.session_state['json_input'] = json.dumps(example_json, indent=4)
    st.session_state['generated_code'] = ''
    st.session_state.expanded_keys.clear()
    st.session_state['selected_jsonl_index'] = 0

# Streamlit app configuration
st.set_page_config(
    page_title="Advanced JSON Explorer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styles
st.markdown("""
    <style>
    .json-key { font-weight: bold; color: #2E86C1; }
    .json-value { color: #D35400; }
    .toggle-box { cursor: pointer; color: #3498db; }
    .search-result { padding: 8px; border: 1px solid #e0e0e0; margin: 4px 0; border-radius: 4px; }
    .search-result:hover { background-color: #f0f0f0; }
    .path-display { font-family: monospace; color: #2c3e50; }
    .value-preview { color: #7f8c8d; font-style: italic; }
    .view-toggle { display: flex; justify-content: center; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; }
    </style>
""", unsafe_allow_html=True)

# App title
st.title("🔍 Advanced JSON Explorer")

# Sidebar for JSON input
with st.sidebar:
    st.header("📄 Input JSON")
    
    if st.button("📝 Load Example JSON"):
        load_example()
    
    json_input = st.text_area(
        "Paste your JSON or JSON Lines (JSONL) here:",
        height=250,
        placeholder='Enter JSON or JSON Lines (JSONL) data here...',
        key='json_input',
    ).strip()

    if st.button("🔄 Clear JSON"):
        st.session_state['json_input'] = ''
        st.session_state['generated_code'] = ''
        st.session_state['search_results'] = []
        st.session_state.expanded_keys.clear()

    # Parse JSON or JSONL
    try:
        if json_input:
            parsed_json = json.loads(json_input)
            is_jsonl = False
            json_objects = [parsed_json]
        else:
            json_objects = []
            is_jsonl = False
    except json.JSONDecodeError:
        try:
            json_objects = [json.loads(line) for line in json_input.splitlines() if line.strip()]
            is_jsonl = True
        except json.JSONDecodeError:
            st.error("❌ Invalid JSON or JSONL data")
            json_objects = []
            is_jsonl = False

    if is_jsonl and json_objects:
        st.subheader("JSONL Navigator")
        selected_index = st.selectbox(
            "Choose an object to display",
            [f"Object {i+1}" for i in range(len(json_objects))],
            index=st.session_state['selected_jsonl_index']
        )
        st.session_state['selected_jsonl_index'] = [f"Object {i+1}" for i in range(len(json_objects))].index(selected_index)
        current_json = json_objects[st.session_state['selected_jsonl_index']]
    elif json_objects:
        current_json = json_objects[0]
    else:
        current_json = None

# Main content area
if current_json:
    # Create tabs for different views
    tab1, tab2 = st.tabs(["🔎 Path Finder", "🌲 Tree Explorer"])
    
    # Extract all paths from JSON
    all_paths = extract_paths(current_json)
    
    # Path Finder View
    with tab1:
        # Search functionality
        col_search, col_mode = st.columns([3, 1])
        
        with col_search:
            search_query = st.text_input("Search for keys or values:", 
                                        placeholder="Type part of a key or value...",
                                        help="Search within the JSON structure")
        
        with col_mode:
            display_mode = st.selectbox(
                "Display mode:",
                ["Show Keys", "Show Values"],
                index=0 if st.session_state['display_mode'] == 'keys' else 1
            )
            st.session_state['display_mode'] = 'keys' if display_mode == "Show Keys" else 'values'
            
        # Filter paths based on search query
        if search_query:
            if st.session_state['display_mode'] == 'keys':
                # Search in keys
                search_results = [
                    path for path in all_paths 
                    if search_query.lower() in path[0].lower()
                ]
            else:
                # Search in values
                search_results = [
                    path for path in all_paths 
                    if isinstance(path[3], (str, int, float, bool)) and 
                    search_query.lower() in str(path[3]).lower()
                ]
            st.session_state['search_results'] = search_results
        else:
            st.session_state['search_results'] = all_paths[:100]  # Limit to first 100 paths if no search
        
        # Display search results
        if st.session_state['search_results']:
            results_count = len(st.session_state['search_results'])
            st.write(f"Found {results_count} paths" + 
                    (f" (showing first 100)" if results_count > 100 and not search_query else ""))
            
            # Group results if in value mode
            if st.session_state['display_mode'] == 'values':
                # Create value-based groups
                value_groups = defaultdict(list)
                for path_info in st.session_state['search_results'][:100]:
                    if len(path_info) >= 4:  # Make sure we have value data
                        value = str(path_info[3])
                        # Truncate very long values for grouping
                        if len(value) > 50:
                            value = value[:47] + "..."
                        value_groups[value].append(path_info)
                
                # Display grouped by value
                for value, paths in value_groups.items():
                    with st.expander(f"Value: {value} ({len(paths)} occurrences)"):
                        for i, path_info in enumerate(paths):
                            path, preview = path_info[0], path_info[1]
                            # Create unique key for each button
                            key = f"value_path_{i}_{hash(path)}"
                            
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"<div class='path-display'>{path}</div>", unsafe_allow_html=True)
                            with col2:
                                if st.button("Get Path", key=key):
                                    st.session_state['generated_code'] = generate_python_code(path)
            else:
                # Show paths in a scrollable container (key mode)
                with st.container():
                    for i, path_info in enumerate(st.session_state['search_results'][:100]):
                        path, preview = path_info[0], path_info[1]
                        # Create unique key for each button
                        key = f"path_{i}_{hash(path)}"
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"""
                            <div class="search-result">
                                <div class="path-display">{path}</div>
                                <div class="value-preview">Value: {preview}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button("Get Path", key=key):
                                st.session_state['generated_code'] = generate_python_code(path)
        else:
            st.info("No paths found matching your search.")
    
    # Tree Explorer View
    with tab2:
        # Option to expand all or collapse all
        col_expand, col_collapse, col_mode = st.columns(3)
        
        with col_expand:
            if st.button("🔽 Expand All"):
                # Extract all unique prefixes from paths for expanding
                for path, _, _, _ in all_paths:
                    parts = re.findall(r"\['([^']+)'\]|\[(\d+)\]", path)
                    current = []
                    for part in parts:
                        part = next(p for p in part if p)  # Get the non-empty part
                        current.append(part)
                        st.session_state.expanded_keys.add('_'.join(current))
        
        with col_collapse:
            if st.button("🔼 Collapse All"):
                st.session_state.expanded_keys.clear()
        
        with col_mode:
            tree_display_mode = st.selectbox(
                "Tree display:",
                ["Show Keys", "Show Values"],
                index=0 if st.session_state['display_mode'] == 'keys' else 1,
                key="tree_display_mode"
            )
            st.session_state['display_mode'] = 'keys' if tree_display_mode == "Show Keys" else 'values'
        
        # Function to recursively display JSON with expand/collapse controls
        def display_collapsible_json(json_obj, path=None, level=0):
            path = path or []
            path_key = '_'.join(map(str, path))
            
            if isinstance(json_obj, dict):
                if not json_obj:  # Empty dict
                    st.write("{}")
                    return
                
                for key, value in json_obj.items():
                    new_path = path + [key]
                    new_path_key = '_'.join(map(str, new_path))
                    
                    # Determine if this node should be expanded
                    is_expanded = new_path_key in st.session_state.expanded_keys
                    
                    # Render toggle control + key/value
                    if isinstance(value, (dict, list)):
                        expander_icon = "🔽" if is_expanded else "▶️"
                        
                        # Create a clickable row with key/value name and toggle icon
                        col1, col2, col3 = st.columns([0.05, 0.75, 0.2])
                        
                        with col1:
                            if st.button(expander_icon, key=f"toggle_{new_path_key}"):
                                if is_expanded:
                                    st.session_state.expanded_keys.remove(new_path_key)
                                else:
                                    st.session_state.expanded_keys.add(new_path_key)
                                st.rerun()
                        
                        with col2:
                            type_indicator = "{...}" if isinstance(value, dict) else "[...]"
                            if st.session_state['display_mode'] == 'keys':
                                # Display key name
                                st.markdown(f"<span style='color:#2E86C1; margin-left: {level*20}px;'><b>{key}</b></span> <span style='color:#7f8c8d;'>{type_indicator}</span>", unsafe_allow_html=True)
                            else:
                                # Display value summary
                                item_count = len(value)
                                st.markdown(f"<span style='color:#2E86C1; margin-left: {level*20}px;'><b>{key}</b></span>: <span style='color:#D35400;'>{type(value).__name__} with {item_count} items</span>", unsafe_allow_html=True)
                        
                        with col3:
                            # Generate path to this key
                            path_str = "data"
                            for p in new_path:
                                if isinstance(p, int) or (isinstance(p, str) and p.isdigit()):
                                    path_str += f"[{p}]"
                                else:
                                    path_str += f"['{p}']"
                            
                            if st.button("Get Path", key=f"path_{new_path_key}"):
                                st.session_state['generated_code'] = generate_python_code(path_str)
                        
                        # Show contents if expanded
                        if is_expanded:
                            display_collapsible_json(value, new_path, level + 1)
                    else:
                        # Render leaf node (no children)
                        col1, col2, col3 = st.columns([0.05, 0.75, 0.2])
                        
                        with col1:
                            st.write("  ")  # Empty space for alignment
                            
                        with col2:
                            # Format value display based on type
                            if isinstance(value, str):
                                value_display = f'"{value[:50]}{"..." if len(value) > 50 else ""}"'
                            else:
                                value_display = str(value)
                            
                            if st.session_state['display_mode'] == 'keys':
                                st.markdown(f"<span style='color:#2E86C1; margin-left: {level*20}px;'><b>{key}</b></span>: <span style='color:#D35400;'>{value_display}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='color:#2E86C1; margin-left: {level*20}px;'><b>{key}</b></span>: <span style='color:#D35400;'>{value_display}</span>", unsafe_allow_html=True)
                        
                        with col3:
                            # Generate path to this key
                            path_str = "data"
                            for p in new_path:
                                if isinstance(p, int) or (isinstance(p, str) and p.isdigit()):
                                    path_str += f"[{p}]"
                                else:
                                    path_str += f"['{p}']"
                                    
                            if st.button("Get Path", key=f"path_{new_path_key}"):
                                st.session_state['generated_code'] = generate_python_code(path_str)
            
            elif isinstance(json_obj, list):
                if not json_obj:  # Empty list
                    st.write("[]")
                    return
                    
                for i, item in enumerate(json_obj):
                    new_path = path + [i]
                    new_path_key = '_'.join(map(str, new_path))
                    
                    # Determine if this node should be expanded
                    is_expanded = new_path_key in st.session_state.expanded_keys
                    
                    # Render toggle control + index
                    if isinstance(item, (dict, list)):
                        expander_icon = "🔽" if is_expanded else "▶️"
                        
                        col1, col2, col3 = st.columns([0.05, 0.75, 0.2])
                        
                        with col1:
                            if st.button(expander_icon, key=f"toggle_{new_path_key}"):
                                if is_expanded:
                                    st.session_state.expanded_keys.remove(new_path_key)
                                else:
                                    st.session_state.expanded_keys.add(new_path_key)
                                st.rerun()
                        
                        with col2:
                            type_indicator = "{...}" if isinstance(item, dict) else "[...]"
                            if st.session_state['display_mode'] == 'keys':
                                st.markdown(f"<span style='color:#2E86C1; margin-left: {level*20}px;'><b>[{i}]</b></span> <span style='color:#7f8c8d;'>{type_indicator}</span>", unsafe_allow_html=True)
                            else:
                                item_count = len(item)
                                st.markdown(f"<span style='color:#2E86C1; margin-left: {level*20}px;'><b>[{i}]</b></span>: <span style='color:#D35400;'>{type(item).__name__} with {item_count} items</span>", unsafe_allow_html=True)
                        
                        with col3:
                            # Generate path to this index
                            path_str = "data"
                            for p in new_path:
                                if isinstance(p, int) or (isinstance(p, str) and p.isdigit()):
                                    path_str += f"[{p}]"
                                else:
                                    path_str += f"['{p}']"
                                    
                            if st.button("Get Path", key=f"path_{new_path_key}"):
                                st.session_state['generated_code'] = generate_python_code(path_str)
                        
                        # Show contents if expanded
                        if is_expanded:
                            display_collapsible_json(item, new_path, level + 1)
                    else:
                        # Render leaf node (no children)
                        col1, col2, col3 = st.columns([0.05, 0.75, 0.2])
                        
                        with col1:
                            st.write("  ")  # Empty space for alignment
                            
                        with col2:
                            # Format value display based on type
                            if isinstance(item, str):
                                value_display = f'"{item[:50]}{"..." if len(item) > 50 else ""}"'
                            else:
                                value_display = str(item)
                                
                            st.markdown(f"<span style='color:#2E86C1; margin-left: {level*20}px;'><b>[{i}]</b></span>: <span style='color:#D35400;'>{value_display}</span>", unsafe_allow_html=True)
                        
                        with col3:
                            # Generate path to this index
                            path_str = "data"
                            for p in new_path:
                                if isinstance(p, int) or (isinstance(p, str) and p.isdigit()):
                                    path_str += f"[{p}]"
                                else:
                                    path_str += f"['{p}']"
                                    
                            if st.button("Get Path", key=f"path_{new_path_key}"):
                                st.session_state['generated_code'] = generate_python_code(path_str)
        
        # Display the collapsible JSON structure
        display_collapsible_json(current_json)

# Display generated code
if st.session_state.get('generated_code'):
    st.subheader("📝 Generated Python Code")
    st.code(st.session_state['generated_code'], language='python')
    
    # Copy button for the generated code
    if st.button("📋 Copy Code to Clipboard"):
        st.info("Code copied to clipboard! (Note: This is a UI simulation - in a real app, JavaScript would handle the copy operation)")
else:
    st.info("⚠️ Enter JSON data and select a path to generate access code.")