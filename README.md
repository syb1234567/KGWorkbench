# KGWorkbench

**A Templated, Evidence-Linked Workbench for Reproducible Domain Knowledge Graph Construction**

KGWorkbench is an open-source, plugin-based desktop application for building, curating, and exporting domain-specific knowledge graphs (KGs). It unifies data cleaning, interactive graph editing, network analytics, multimodal evidence binding, and semantic export within a single local-first environment, eliminating the need to switch between spreadsheets, notebooks, and standalone visualization tools.

KGWorkbench was developed and validated on Traditional Chinese Medicine (TCM) datasets, but its plugin architecture and export formats generalise to any domain requiring structured, evidence-linked knowledge curation.

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Reproducing the Manuscript Examples](#reproducing-the-manuscript-examples)
6. [Data Schema](#data-schema)
7. [Built-in Plugins](#built-in-plugins)
8. [Export Formats](#export-formats)
9. [Plugin Development Guide](#plugin-development-guide)
10. [FAQ and Troubleshooting](#faq-and-troubleshooting)

---

## Features

- **Template-based data cleaning** — regex/lookup mapping, name normalisation, deduplication, and isolated-node removal, each producing a human-readable impact summary
- **Interactive graph editing** — add, edit, and delete nodes and edges with full undo/redo (deque-based snapshot stack)
- **Dual-mode visualisation** — switch between a force-directed Graph Mode (Vis.js) and a statistical Table Mode at any time
- **Multimodal evidence binding** — attach PNG/JPG images and PDF documents directly to nodes and edges as first-class provenance
- **Built-in network analytics** — degree, betweenness, closeness, eigenvector centrality, PageRank, clustering coefficients, community detection (Louvain), and shortest-path queries
- **Multi-format export** — JSON, CSV, GraphML, RDF/OWL, and JSON-LD
- **Plugin ecosystem** — dynamically loaded Python plugins; new analysis or curation capabilities can be added without modifying core code
- **Cross-graph merging** — fuzzy-matching-based entity alignment across multiple KG files with configurable similarity thresholds

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.8 or higher |
| Operating system | Windows 10/11, Ubuntu 20.04+, macOS 11+ |

### Python dependencies

```text
PyQt5>=5.15.11
PyQtWebEngine>=5.15.7
pandas>=2.2.3
chardet>=5.2.0
networkx>=3.4.2
rdflib>=7.1.3
scipy>=1.15.2
python-louvain>=0.16
matplotlib>=3.0
numpy>=1.15
PyMuPDF
```

A `requirements.txt` file with pinned versions is included in the repository root.

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/syb1234567/KGWorkbench.git
cd KGWorkbench
```

### Step 2 — (Recommended) Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Launch the application

```bash
python ui/main_window.py
```

The KGWorkbench main window should appear within a few seconds.

---

### Platform-specific notes

**Windows**
No additional steps are required. PyQt5 wheels for Windows are distributed via PyPI and install automatically.

**Ubuntu / Debian Linux**
If the Qt platform plugin is not found, install the following system packages before running `pip install`:

```bash
sudo apt-get install python3-pyqt5 libqt5gui5 libqt5widgets5
```

**macOS**
On Apple Silicon (M1/M2/M3) Macs, use Python 3.9 or higher. If `PyMuPDF` fails to install, try:

```bash
pip install pymupdf --no-binary pymupdf
```

---

## Quick Start

The repository ships with a sample TCM dataset at `graph_data.json`. This dataset contains approximately 160 nodes and 280 edges spanning five domain node types — Formula (方剂), Herb (药材), Treatment Method (药理), Disease (疾病), and TCM Concept (中医概念) — connected by more than 20 relation types. It is sufficient to exercise every plugin and export format described in this document.

**To load the sample dataset:**

1. Launch the application: `python ui/main_window.py`
2. Click **File → Open**
3. Navigate to `graph_data.json` and click **Open**
4. The graph renders immediately in Graph Mode

**To switch to Table Mode:**

Click the **Table Mode** toggle in the control panel (top right). The view switches to a statistical dashboard showing node counts by type, edge counts by relation type, and summary statistics.

**To switch back to Graph Mode:**

Click the **Graph Mode** toggle.

---

## Reproducing the Manuscript Examples

All figures in the manuscript are generated from `/graph_data.json`. The steps below reproduce each figure exactly.

### Figure 2 — Interactive node creation

1. Load `graph_data.json` as described in Quick Start
2. Click **Edit → Add Node** (step A1 in the manuscript)
3. In the dialog that appears, fill in:
   - **Node Name**: any string, e.g. `TestHerb`
   - **Node Type**: any string, e.g. `药材`
   - **Node Attributes**: a valid JSON object, e.g. `{"origin": "Sichuan"}`
4. Click **Confirm** (step A3)
5. The new node appears in the graph view

> Note: node creation is a manual primitive. Duplicate detection and deduplication are handled by the Data Cleaning Plugin (see Built-in Plugins).

### Figure 3 — Multi-format data export

1. Load `graph_data.json`
2. Click **File → Export Data** (step A4)
3. In the system file dialog (step A5), choose a destination folder
4. Select a format from the dropdown (step A6): JSON, CSV, GraphML, RDF, or OWL
5. Click **Save**; the file is written to the selected directory

Repeat for each format to obtain all five output files shown in the manuscript figure.

### Figure 4 — Dual-mode visualisation

1. Load `graph_data.json`
2. Click the **Table Mode** toggle (step A7)
3. The dashboard (step A8) shows:
   - Node statistics panel (counts per type)
   - Relationship statistics panel (counts per relation type)
   - Node type distribution breakdown

---

## Data Schema

KGWorkbench accepts two input formats: **JSON** (native) and **CSV** (tabular, with interactive schema mapping).

### JSON format

The native format is a single JSON object with two top-level keys:

```json
{
  "nodes": [...],
  "edges": [...]
}
```

**Node object:**

```json
{
  "name": "白虎汤",
  "type": "方剂",
  "attributes": {"source": "伤寒论"},
  "resources": [
    {"path": "/absolute/or/relative/path/to/image.png", "type": "Image"},
    {"path": "/path/to/document.pdf", "type": "PDF"}
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Unique node identifier within the graph |
| `type` | string | yes | Node category label (user-defined) |
| `attributes` | object | no | Arbitrary key-value metadata; must be a JSON object or `{}` |
| `resources` | array | no | List of evidence bindings; each item has `path` (string) and `type` (`"Image"` or `"PDF"`) |

**Edge object:**

```json
{
  "source": "白虎汤",
  "target": "清热救燥",
  "relation_type": "治法",
  "resources": []
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | string | yes | `name` of the source node |
| `target` | string | yes | `name` of the target node |
| `relation_type` | string | yes | Label for the directed relationship |
| `resources` | array | no | Evidence bindings (same format as node resources) |

### CSV format

When loading a CSV file, an interactive schema mapping dialog prompts you to map your column names to the internal schema. At minimum, map:

- One column → **Source Node Name**
- One column → **Target Node Name**
- One column → **Relation Type**
- Optionally: columns for node type, attributes

Unmapped columns are ignored.

---

## Built-in Plugins

Plugins are loaded automatically from the `plugins/` directory at startup. The following seven plugins ship with KGWorkbench.

### Interface Layer Plugins

These three plugins are always active and integrate directly with the main graph view.

**Graph Navigator**
Displays a minimap-style overview panel with real-time viewport synchronisation. Click and drag inside the minimap to pan the main view. Conflict prevention logic ensures smooth interaction during concurrent drag operations.

**Local Zoom Tool**
Opens a secondary visualisation window showing the neighbourhood of a selected node. Configure:
- **Depth**: 1–5 hops from the selected node
- **Edge mode**: directed, undirected, or mixed
Layers are colour-coded by hop distance (matplotlib).

**KG Search**
Searches across node names, node types, node attributes, and edge relation types using string-containment fuzzy matching. Results are displayed in a categorised panel; single-click highlights the node in the main view, double-click centres the viewport on it.

---

### Analysis and Curation Plugins

These four plugins operate directly on the loaded graph instance and are accessed from the **Plugins** menu.

**Centrality Analysis Plugin**
Calculates six centrality metrics for every node: degree centrality, betweenness centrality, closeness centrality, eigenvector centrality, PageRank, and clustering coefficient. Results are ranked by node type and displayed in a sortable table. All metrics are computed via NetworkX algorithms.

**Data Cleaning Plugin**
Provides five automated cleaning operations, each producing a human-readable impact summary (number of nodes/edges affected):

| Operation | Description |
|---|---|
| Remove empty properties | Deletes node/edge attributes whose value is `null`, `""`, or `{}` |
| Name normalisation | Strips leading/trailing whitespace; normalises case |
| Isolated node deletion | Removes nodes with no incoming or outgoing edges |
| Edge deduplication | Removes duplicate edges (same source, target, and relation type) |
| Node deduplication | Merges nodes with identical names or high attribute similarity (template-driven) |

> Duplicate detection is an explicit, auditable batch step rather than a silent check at insertion time, allowing curators to review and approve all merges before they are committed.

**Multimodal Data Integration Plugin**
Binds external evidence files to nodes or edges. Supported modalities in the current release:

- **Raster images** (PNG, JPG): useful for attaching photographs of specimens, diagrams, or scanned figures
- **PDF documents**: useful for attaching classical texts, clinical guideline excerpts, or supporting publications

Resource bindings are stored in the `resources` attribute of the node or edge. Thumbnail previews use MD5-based caching to avoid recomputation; PDF previews are rendered via PyMuPDF.

**Graph Analysis Tool**
Provides three analysis functions:
- **Degree statistics**: computes node degree on an undirected projection of the loaded graph and displays the results in a table
- **Community detection**: applies the Louvain algorithm (via `python-louvain`) to the undirected projection of the graph
- **Shortest path**: computes the shortest path between two nodes on the undirected projection of the graph

---

## Export Formats

Access all export options via **File → Export Data**.

| Format | Extension | Intended consumer |
|---|---|---|
| JSON | `.json` | Programmatic post-processing; round-trip back into KGWorkbench |
| CSV | `.csv` | Spreadsheet-based human review (node table + edge table) |
| GraphML | `.graphml` | Dedicated graph tools: Gephi, Cytoscape |
| RDF/OWL | `.rdf` / `.owl` | Triple stores (Apache Jena, GraphDB); SPARQL querying; OWL reasoners |
| JSON-LD | `.jsonld` | Web publication; JavaScript applications; Linked Data pipelines |

> CSV is a tabular representation and does not preserve nested attributes faithfully. It is recommended for inspection and reporting rather than as a primary persistence format.

---

## Plugin Development Guide

KGWorkbench loads any Python module in the `plugins/` directory that contains a class named `Plugin`. The class must implement the following interface:

```python
class Plugin:
    # Required class attributes
    name: str          # Display name shown in the Plugins menu
    description: str   # One-line description shown in the plugin panel

    def __init__(self, graph_manager):
        """
        Called once when the plugin is loaded.

        Parameters
        ----------
        graph_manager : GraphDataManager
            The live graph instance. Access the underlying NetworkX DiGraph
            via graph_manager.graph.
        """
        self.graph_manager = graph_manager

    def run(self):
        """
        Called when the user activates the plugin from the menu.
        Perform analysis or curation here and display results
        (e.g. open a QDialog or print to the log panel).
        """
        raise NotImplementedError
```

### Minimal example: Node Count Plugin

Save the following as `plugins/node_count_plugin.py`:

```python
from PyQt5.QtWidgets import QMessageBox

class Plugin:
    name = "Node Count"
    description = "Displays the total number of nodes in the current graph."

    def __init__(self, graph_manager):
        self.gm = graph_manager

    def run(self):
        n = self.gm.graph.number_of_nodes()
        QMessageBox.information(None, "Node Count", f"The graph contains {n} nodes.")
```

Restart KGWorkbench (or use **Plugins → Reload Plugins**) to see **Node Count** appear in the Plugins menu.

### Available GraphDataManager methods

| Method | Description |
|---|---|
| `graph` | The underlying `networkx.DiGraph` instance |
| `add_node(name, type, attributes)` | Add a node; returns the updated graph |
| `delete_node(name)` | Remove a node and all its incident edges |
| `add_relationship(source, target, relation_type)` | Add a directed relationship |
| `delete_relationship(source, target)` | Remove a relationship |
| `undo()` | Revert to the previous snapshot |
| `redo()` | Re-apply the next snapshot |
| `get_all_nodes()` | Return a list of all node attribute dicts |
| `get_all_relationships()` | Return a list of all relationship records |

---

## FAQ and Troubleshooting

**Q: The application window does not appear after running `python ui/main_window.py`.**
A: Verify that PyQt5 is installed correctly: `python -c "from PyQt5.QtWidgets import QApplication; print('OK')"`. On Linux, ensure that a Qt platform plugin is available (see Platform-specific notes above).

**Q: I get `ModuleNotFoundError: No module named 'fitz'` when loading a PDF.**
A: `fitz` is the Python binding for PyMuPDF. Install it with: `pip install PyMuPDF`.

**Q: I get `ModuleNotFoundError: No module named 'community'` when running the Graph Analysis Tool.**
A: Install the Louvain package: `pip install python-louvain`.

**Q: My CSV file loads but all nodes show type `Unknown`.**
A: In the schema mapping dialog, make sure you assign a column to **Node Type**. If your CSV does not contain a type column, you can assign a constant value after import using the Data Cleaning Plugin's name normalisation feature.

**Q: Resource paths in `graph_data.json` are absolute Windows paths and do not resolve on my machine.**
A: The sample file contains one node (`麻黄汤`) with an absolute path resource for demonstration purposes. This is expected; the image will not render on your machine unless you update the path. All other nodes in the sample dataset have no resource bindings and load without issue.

**Q: The graph renders very slowly with large datasets.**
A: KGWorkbench holds the full graph in memory (NetworkX DiGraph). For very large graphs (> ~50,000 nodes), consider filtering or sampling the dataset before loading. Out-of-core execution is planned for a future release.

**Q: Can I use KGWorkbench with a non-TCM dataset?**
A: Yes. The node types, relation types, and attribute keys are entirely user-defined. Any domain dataset formatted according to the JSON schema above (or mappable from CSV) can be loaded and curated.

---

## License

MIT License. See `LICENSE` for details.

## Contact

For questions or bug reports, please open an issue on GitHub or contact:
shenyb25@mails.tsinghua.edu.cn

## Citation

If you use KGWorkbench in your research, please cite:

> Shen, Y., Qian, Z., et al. KGWorkbench: A Templated, Evidence-Linked Workbench for Reproducible Domain Knowledge Graph Construction. *SoftwareX*, 2026.
