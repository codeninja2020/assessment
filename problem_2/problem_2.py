"""
Problem 2: Given an employee name, return every employee who reports to them,
directly or indirectly, all the way down to the leaf level.

implemented BFS for flat table of all reports, and DFS for indented tree and Graphviz chart.

"""

from collections import defaultdict, deque

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Org Hierarchy Explorer", page_icon="💼", layout="wide")


SAMPLE_ROWS = [
    ("Alice", None),            # CEO
    ("Bob", "Alice"),           # VP Engineering
    ("Carol", "Alice"),         # VP Sales
    ("Dave", "Bob"),            # Eng Manager A
    ("Erin", "Bob"),            # Eng Manager B
    ("Frank", "Carol"),         # Sales Manager
    ("Grace", "Dave"),          # Dev
    ("Heidi", "Dave"),          # Dev
    ("Ivan", "Erin"),           # Dev
    ("Judy", "Erin"),           # Dev
    ("Karl", "Frank"),          # Sales Rep
    ("Liam", "Frank"),          # Sales Rep
    ("Mia", "Grace"),           # Intern
    ("Nate", "Karl"),           # Sales Rep (junior)
    ]


def build_hierarchy(df: pd.DataFrame):

    """
    Build a manager -> [direct reports] adjacency list from an
    (Employee, Manager) dataframe. Returns (children_map, all_names, cycle_members).
    """

    children = defaultdict(list) # manager -> list of direct reports
    all_names = set() # all unique employee and manager names
    manager_of = {} # employee -> manager mapping 

    for _, row in df.iterrows():
        employee = str(row["Employee"]).strip()  #define employee to handle potential NaN values
        manager_raw = row["Manager"] # define manager_raw to handle potential NaN values
        manager = None if pd.isna(manager_raw) else str(manager_raw).strip() #handle potential NaN values for manager
        if not employee:
            continue
        all_names.add(employee)
        if manager:
            all_names.add(manager)
            children[manager].append(employee)
            manager_of[employee] = manager

    cycle_members = detect_cycle_members(children, all_names)
    return children, all_names, cycle_members


def detect_cycle_members(children, all_names):
    """
    Detect any employees involved in a reporting cycle (bad data), using
    iterative DFS with a recursion-stack set so we never spin on bad input.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {name: WHITE for name in all_names}
    cyclic = set()

    for start in all_names:
        if color[start] != WHITE:
            continue
        stack = [(start, iter(children.get(start, [])))]
        color[start] = GRAY
        while stack:
            node, it = stack[-1]
            advanced = False
            for nxt in it:
                if color[nxt] == GRAY:
                    cyclic.add(nxt)
                    cyclic.add(node)
                elif color[nxt] == WHITE:
                    color[nxt] = GRAY
                    stack.append((nxt, iter(children.get(nxt, []))))
                    advanced = True
                    break
            if not advanced:
                color[node] = BLACK
                stack.pop()
    return cyclic


def all_subordinates(start: str, children: dict):
    """
    BFS from `start`, collecting every descendant down to the leaves.
    Returns (ordered_list_of_names, depth_map).
    """
    visited = {start}
    depth = {start: 0}
    order = []
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for child in children.get(node, []):
            if child in visited:
                continue  # guard against a cyclic edge in bad data
            visited.add(child)
            depth[child] = depth[node] + 1
            order.append(child)
            queue.append(child)
    return order, depth


def preorder_tree(start: str, children: dict):
    """
    DFS preorder traversal used only to render a nested indented tree
    (parents immediately followed by their own subtree), as opposed to the
    BFS order used for the flat table.
    """
    visited = {start}
    lines = []

    def walk(node, lvl):
        for child in sorted(children.get(node, [])):
            if child in visited:
                continue
            visited.add(child)
            lines.append((child, lvl))
            walk(child, lvl + 1)

    walk(start, 0)
    return lines


def build_dot(start: str, children: dict, descendants: set) -> str:
    lines = ["digraph G {", '  rankdir="TB";', '  node [shape=box, style=filled, fillcolor="#EAF2FF"];']
    lines.append(f'  "{start}" [fillcolor="#FFD54F"];')
    seen_edges = set()

    def walk(node):
        for child in children.get(node, []):
            if child not in descendants and child != start:
                continue
            edge = (node, child)
            if edge in seen_edges:
                continue
            seen_edges.add(edge)
            lines.append(f'  "{node}" -> "{child}";')
            walk(child)

    walk(start)
    lines.append("}")
    return "\n".join(lines)


# User Interface 

st.title("💼 Org Hierarchy Explorer")
st.caption(
    "Enter an employee's name to see everyone who reports to them, "
    "directly or indirectly, down to the leaf level."
)

with st.sidebar:
    st.header("Data source")
    uploaded = st.file_uploader(
        "Upload a CSV with columns 'Employee' and 'Manager'",
        type="csv",
    )
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        missing = {"Employee", "Manager"} - set(df.columns)
        if missing:
            st.error(f"CSV is missing required column(s): {', '.join(missing)}")
            st.stop()
    else:
        df = pd.DataFrame(SAMPLE_ROWS, columns=["Employee", "Manager"])
        st.info("Using built-in sample org data. Upload your own CSV to replace it.")

    with st.expander("Show raw data"):
        st.dataframe(df, use_container_width=True, hide_index=True)

children_map, all_names, cyclic = build_hierarchy(df)

if cyclic:
    st.warning(
        "The hierarchy data contains a cycle involving: "
        + ", ".join(sorted(cyclic))
        + ". Traversal below still terminates safely, but results for "
        "anyone in that cycle may not reflect a true tree."
    )

name = st.selectbox(
    "Employee name",
    options=sorted(all_names),
    index=None,
    placeholder="Start typing a name...",
)

if name:
    if name not in all_names:
        st.error(f"'{name}' was not found in the hierarchy.")
    else:
        reports, depth = all_subordinates(name, children_map)

        st.subheader(f"Reports to {name}: {len(reports)} total")

        if not reports:
            st.write("This employee has no subordinates (leaf of the hierarchy).")
        else:
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("**Flat list**")
                result_df = pd.DataFrame(
                    {
                        "Employee": reports,
                        "Levels below": [depth[r] for r in reports],
                    }
                ).sort_values(["Levels below", "Employee"]).reset_index(drop=True)
                st.dataframe(result_df, use_container_width=True, hide_index=True)

            with col2:
                st.markdown("**Indented tree**")
                tree_lines = [
                    "  " * lvl + f"- {child}" for child, lvl in preorder_tree(name, children_map)
                ]
                st.text("\n".join(tree_lines))

            st.markdown("**Org chart (subtree)**")
            try:
                st.graphviz_chart(build_dot(name, children_map, set(reports)))
            except Exception as e:
                st.caption(f"(Graph rendering unavailable: {e})")
