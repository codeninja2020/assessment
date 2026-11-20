# Problem 2: Org Hierarchy Explorer

Given an employee's name, the app returns everyone who reports to them, directly or indirectly, down to the leaf level. For the example in the brief, **Harry** returns **Chang, Mary and Alfonse**.

## Run it

Requires Python 3.10 or newer. No other system software is needed.

From the root of the repository:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r problem_2/requirements.txt
streamlit run problem_2/problem_2.py
```

The app opens in your browser at http://localhost:8501.

## Features

- **Search:** pick an employee to see all their subordinates as a table, with how many levels below them each person sits, and as an org chart of their subtree.
- **Edit the hierarchy:** open *Edit hierarchy* to change managers, add employees or delete rows. Results update immediately, and the edited data can be downloaded as a CSV. *Reset to original data* in the sidebar discards edits.
- **Upload your own data:** the sidebar accepts a CSV with `Employee` and `Manager` columns. Leave `Manager` blank for the person at the top.
- **Data checks:** warns about reporting cycles (for example A reports to B and B reports to A), duplicate names and people listed as their own manager. The search always terminates, even on bad data.

## How it works

- The data is turned into a manager → direct reports map.
- A breadth-first search (BFS) from the chosen employee collects every subordinate and their depth.
- A depth-first search (DFS) builds the org chart
