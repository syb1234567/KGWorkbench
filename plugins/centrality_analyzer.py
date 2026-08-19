from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
import networkx as nx
from networkx.exception import PowerIterationFailedConvergence
import scipy

class CentralityPlugin(QObject):
    """中心性分析插件：提供多种中心性指标的统计功能。"""
    def __init__(self, graph_manager):
        super().__init__()
        self.name = "Centrality Analysis Plugin"
        # 获取完整图数据并构建 NetworkX 图
        self.graph_data = graph_manager.get_graph_data()
        self._build_graph()

    def _build_graph(self):
        """将原始数据转换为 NetworkX 无向图结构"""
        self.G = nx.Graph()
        for node in self.graph_data['nodes']:
            self.G.add_node(node['name'], type=node['type'])
        for edge in self.graph_data['edges']:
            self.G.add_edge(
                edge['source'],
                edge['target'],
                relation_type=edge.get('relation_type', None)
            )

    def _degree_centrality(self):
        dc = nx.degree_centrality(self.G)
        categorized = {'方剂': [], '药材': [], '治法': [], '证型': []}
        for n, score in dc.items():
            t = self.G.nodes[n].get('type', '')
            if t in categorized:
                categorized[t].append((n, round(score, 4)))
        display_names = {
            '方剂': 'Formula',
            '药材': 'Medicinal Material',
            '治法': 'Therapeutic Method',
            '证型': 'Syndrome Pattern',
        }
        rows = []
        for t, items in categorized.items():
            for node, sc in sorted(items, key=lambda x: x[1], reverse=True)[:5]:
                rows.append((display_names.get(t, t), node, sc))
        return rows

    def _betweenness_centrality(self):
        weight_map = {'组成包含': 1.0, '治法': 0.8, '禁忌': -1.0, '归属经络': 0.5}
        WG = nx.Graph()
        for u, v, data in self.G.edges(data=True):
            w = weight_map.get(data.get('relation_type'), 0.5)
            WG.add_edge(u, v, weight=w)
        bc = nx.betweenness_centrality(WG, weight='weight')
        threshold = sorted(bc.values(), reverse=True)[len(bc) // 10]
        rows = [(n, round(s, 4)) for n, s in bc.items() if s >= threshold]
        rows.sort(key=lambda x: x[1], reverse=True)
        return rows

    def _closeness_centrality(self):
        comp = max(nx.connected_components(self.G), key=len)
        sub = self.G.subgraph(comp)
        cc = nx.closeness_centrality(sub)
        rows = [(n, round(s, 4)) for n, s in cc.items()]
        rows.sort(key=lambda x: x[1], reverse=True)
        return rows[:10]

    def _eigenvector_centrality(self):
        try:
            ev = nx.eigenvector_centrality(self.G, max_iter=1000, tol=1e-6)
        except PowerIterationFailedConvergence as e:
            QMessageBox.warning(None, self.name, f"Eigenvector centrality did not converge: {e}")
            return []
        rows = sorted(ev.items(), key=lambda x: x[1], reverse=True)[:10]
        return [(n, round(s, 4)) for n, s in rows]

    def _pagerank(self):
        """PageRank Top10：兼容无 scipy 环境的快速实现"""
        # 先尝试标准 PageRank（依赖 scipy）
        try:
            pr = nx.pagerank(self.G, max_iter=1000, tol=1e-6)
        except PowerIterationFailedConvergence as e:
            QMessageBox.warning(None, self.name, f"PageRank did not converge: {e}")
            return []
        except ImportError:
            # scipy 未安装，使用 numpy 实现的 pagerank_numpy 作为备选
            try:
                pr = nx.pagerank_numpy(self.G)
            except Exception as err:
                QMessageBox.warning(None, self.name, "PageRank calculation failed. Please install scipy and try again.")
                return []
        except Exception as e:
            QMessageBox.warning(None, self.name, f"PageRank calculation error: {e}")
            return []
        rows = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:10]
        return [(n, round(s, 4)) for n, s in rows]

    def _clustering_coefficient(self):
        cc = nx.clustering(self.G)
        rows = sorted(cc.items(), key=lambda x: x[1], reverse=True)[:10]
        return [(n, round(s, 4)) for n, s in rows]

    def run(self):
        """插件入口：弹出功能选择菜单。"""
        dlg = QDialog()
        dlg.setWindowTitle(self.name)
        layout = QVBoxLayout(dlg)

        features = [
            ("Degree Centrality", lambda: self._show_degree(dlg)),
            ("Betweenness Centrality", lambda: self._show_betweenness(dlg)),
            ("Closeness Centrality", lambda: self._show_closeness(dlg)),
            ("Eigenvector Centrality", lambda: self._show_eigenvector(dlg)),
            ("PageRank", lambda: self._show_pagerank(dlg)),
            ("Clustering Coefficient", lambda: self._show_clustering(dlg)),
        ]
        for label, handler in features:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        dlg.exec_()

    def _show_degree(self, parent):
        rows = self._degree_centrality()
        self._show_table("Degree Centrality Top 5 by Category", ["Category", "Node", "Score"], rows, parent)

    def _show_betweenness(self, parent):
        rows = self._betweenness_centrality()
        self._show_table("Betweenness Centrality Key Bridges", ["Node", "Score"], rows, parent)

    def _show_closeness(self, parent):
        rows = self._closeness_centrality()
        self._show_table("Closeness Centrality Top 10", ["Node", "Score"], rows, parent)

    def _show_eigenvector(self, parent):
        rows = self._eigenvector_centrality()
        self._show_table("Eigenvector Centrality Top 10", ["Node", "Score"], rows, parent)

    def _show_pagerank(self, parent):
        rows = self._pagerank()
        self._show_table("PageRank Top 10", ["Node", "Score"], rows, parent)

    def _show_clustering(self, parent):
        rows = self._clustering_coefficient()
        self._show_table("Clustering Coefficient Top 10", ["Node", "Coefficient"], rows, parent)

    def _show_table(self, title, headers, data_rows, parent):
        """通用表格展示函数"""
        if not data_rows:
            QMessageBox.information(parent, title, "No data to display.")
            return
        dlg = QDialog(parent)
        dlg.setWindowTitle(title)
        dlg.resize(500, 400)
        table = QTableWidget(len(data_rows), len(headers), dlg)
        table.setHorizontalHeaderLabels(headers)
        for i_row, row in enumerate(data_rows):
            for j_col, val in enumerate(row):
                table.setItem(i_row, j_col, QTableWidgetItem(str(val)))
        layout = QVBoxLayout(dlg)
        layout.addWidget(table)
        dlg.exec_()


# 入口类
class Plugin(CentralityPlugin):
    def __init__(self, graph_manager):
        super().__init__(graph_manager)
