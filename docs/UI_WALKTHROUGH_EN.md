# English Interface Walkthrough

This walkthrough is intended for international users and reviewers. It maps the main user-interface elements to their English labels and explains their functions.

## Language Availability

The application now starts in English by default. Users can still switch languages from the toolbar through `Language`.

Domain-specific graph data, such as Chinese medicine formula names, herb names, disease names, and TCM concept labels, remain in their original terminology to preserve the dataset semantics.

## Main Window

| Area | English Label | Function |
| --- | --- | --- |
| Window title | Traditional Chinese Medicine Knowledge Graph | Main application window. |
| Left panel | Graph view | Interactive knowledge graph visualization. |
| Right upper panel | Node Information | Displays and edits the selected node's name, type, attributes, and related images. |
| Right lower panel | Plugin list | Lists loaded plugins. Double-click a plugin to run it. |
| Toolbar statistics | Nodes / Relationships / Types | Displays current graph data counts. |

## Toolbar Menus

| Menu | Item | Function |
| --- | --- | --- |
| File | Import Data | Import node or relationship data from CSV or JSON files. |
| File | Save Data | Save the current graph data. |
| File | Export Data | Export graph data to supported formats. |
| File | Save JSON-LD | Save graph data as JSON-LD. |
| Edit | Add Node | Open the add-node dialog. |
| Edit | Batch Edit Nodes | Open the node table editor. |
| Edit | Batch Edit Relationships | Open the relationship table editor. |
| View | Reset Layout | Restore the main panel layout. |
| View | Fit to Window | Fit the graph view to the visible window. |
| View | Toggle Theme | Theme-switching entry. |
| Language | English / Chinese | Switch interface language. |
| Plugins | Load Plugin | Load plugin files. |
| Plugins | Manage Plugins | Manage loaded plugins. |

## Graph View Controls

| Control | Function |
| --- | --- |
| Save Layout | Save the manually adjusted graph layout. |
| Reset Layout | Reset the graph to a grid layout. |
| Auto Layout | Arrange nodes in a circular layout. |
| Add node prompt | Requests node name, node type, and JSON attributes. |
| Add relationship prompt | Requests the relationship type when linking nodes. |
| Delete confirmations | Confirms node or relationship deletion before applying changes. |

## Data Mode

| Label | Function |
| --- | --- |
| Data Detail Mode | Opens a detailed browsable view of the graph data. |
| Node Statistics | Displays total node count and type distribution. |
| Relationship Statistics | Displays relationship count and relationship type distribution. |
| Relationship Examples | Shows representative graph triples. |
| Export Current View | Exports the current data-mode view. |

## Node Detail Panel

| Field | Function |
| --- | --- |
| Node Name | Read-only selected node identifier. |
| Node Type | Editable selected node type. |
| Node Attributes | Editable JSON attributes. |
| Related Images | Shows linked image resources where available. |
| Save Changes | Saves edits to the selected node. |

## Notes for Manuscript Response

The revised software provides an English localized interface by default and includes this walkthrough as a visual/textual mapping of key UI elements. Chinese graph data values are retained as source data rather than interface language.
