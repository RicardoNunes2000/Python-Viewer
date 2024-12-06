import streamlit as st
import json

# Initialize session state
if 'expanded_keys' not in st.session_state:
    st.session_state.expanded_keys = set()
if 'json_input' not in st.session_state:
    st.session_state['json_input'] = ''
if 'generated_code' not in st.session_state:
    st.session_state['generated_code'] = ''
if 'selected_jsonl_index' not in st.session_state:
    st.session_state['selected_jsonl_index'] = 0

# Function to generate Python code for accessing a specific item
def generate_python_code(json_obj, keys):
    code = "import json\n\n"
    code += f"data = json.loads('''\n{json.dumps(json_obj, indent=4)}\n''')\n\n"
    access_path = "data"
    for key in keys:
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            access_path += f"[{key}]"
        else:
            access_path += f"['{key}']"
    code += f"value = {access_path}\nprint(value)"
    return code

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
        }
    }
    st.session_state['json_input'] = json.dumps(example_json, indent=4)
    st.session_state['generated_code'] = ''
    st.session_state.expanded_keys.clear()
    st.session_state['selected_jsonl_index'] = 0

# Streamlit app configuration
st.set_page_config(
    page_title="JSON Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styles
st.markdown("""
    <style>
    .json-key { font-weight: bold; color: #2E86C1; }
    .json-value { color: #D35400; }
    .indent { margin-left: 20px; }
    .stButton>button { width: 100%; text-align: left; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 JSON Visualizer")

# Sidebar for JSON input
with st.sidebar:
    st.header("🔧 Input JSON")
    
    if st.button("📝 Load Example JSON"):
        load_example()
    
    json_input = st.text_area(
        "Paste your JSON or JSON Lines (JSONL) here:",
        height=300,
        placeholder='Enter JSON or JSON Lines (JSONL) data here...',
        key='json_input',
    ).strip()

    if st.button("🔄 Clear JSON"):
        st.session_state['json_input'] = ''

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
            st.error("❗ Invalid JSON or JSONL data")
            json_objects = []
            is_jsonl = False

    if is_jsonl and json_objects:
        st.subheader("Select JSON Object")
        selected_index = st.selectbox(
            "Choose an object to display",
            [f"Object {i+1}" for i in range(len(json_objects))],
            index=st.session_state['selected_jsonl_index']
        )
        st.session_state['selected_jsonl_index'] = [f"Object {i+1}" for i in range(len(json_objects))].index(selected_index)
        original_json = json_objects[st.session_state['selected_jsonl_index']]
    elif json_objects:
        original_json = json_objects[0]
    else:
        original_json = None

# Main content area
if original_json:
    st.subheader("📂 JSON Structure")
    
    COLOR_PALETTE = ["#e74c3c", "#27ae60", "#3498db", "#8e44ad", "#f1c40f", "#e67e22", "#16a085"]
    
    def display_json(json_obj, keys=[], level=0):
        # Get color based on the level (wrap around if levels exceed the palette size)
        color = COLOR_PALETTE[level % len(COLOR_PALETTE)]
        indent = "&nbsp;" * 4 * level  # Indentation for nested elements

        if isinstance(json_obj, dict):
            for key, value in json_obj.items():
                new_keys = keys + [key]
                unique_key = "_".join(map(str, new_keys))

                # Render the key as a clickable link
                st.markdown(
                    f"{indent}<span style='color:{color}; cursor:pointer;'>{key}</span>",
                    unsafe_allow_html=True,
                )
                if st.button(f"Click to access '{key}'", key=unique_key):
                    st.session_state['generated_code'] = generate_python_code(original_json, new_keys)
                if isinstance(value, (dict, list)):
                    display_json(value, new_keys, level + 1)

        elif isinstance(json_obj, list):
            for index, item in enumerate(json_obj):
                new_keys = keys + [index]
                unique_key = "_".join(map(str, new_keys))

                # Render the index as a clickable link
                st.markdown(
                    f"{indent}<span style='color:{color}; cursor:pointer;'>[{index}]</span>",
                    unsafe_allow_html=True,
                )
                if st.button(f"Click to access [{index}]", key=unique_key):
                    st.session_state['generated_code'] = generate_python_code(original_json, new_keys)
                if isinstance(item, (dict, list)):
                    display_json(item, new_keys, level + 1)

    # Main content usage
    st.info("🔍 Click on a key or index to generate the Python code for accessing it. Colors indicate nesting level.")
    display_json(original_json)

# Display generated code dynamically
if st.session_state.get('generated_code'):
    st.subheader("📝 Generated Python Code")
    st.code(st.session_state['generated_code'], language='python')
else:
    st.info("⚠️ Please enter JSON data in the sidebar to visualize.")