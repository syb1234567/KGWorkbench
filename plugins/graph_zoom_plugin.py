# -*- coding: utf-8 -*-
# plugins/graph_zoom_plugin.py

import sys
import os
import platform
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, 
    QInputDialog, QLabel, QSpinBox, QComboBox,
    QCheckBox, QGroupBox, QTextEdit, QSplitter, QRadioButton
)
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import numpy as np
from collections import defaultdict


class FontManager:
    """字体管理器，处理中文字体兼容性问题"""
    
    def __init__(self):
        self.chinese_font = self._get_chinese_font()
        self._configure_matplotlib()
    
    def _get_chinese_font(self):
        """获取可用的中文字体"""
        try:
            # 常见中文字体列表（按优先级排序）
            chinese_fonts = [
                'SimHei',           # 黑体 (Windows)
                'Microsoft YaHei',  # 微软雅黑 (Windows)
                'PingFang SC',      # 苹方 (macOS)
                'STHeiti',          # 华文黑体 (macOS)
                'WenQuanYi Micro Hei',  # 文泉驿微米黑 (Linux)
                'Noto Sans CJK SC',     # 思源黑体 (Linux)
                'DejaVu Sans',      # 回退字体
            ]
            
            # 获取系统所有可用字体
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            # 查找第一个可用的中文字体
            for font in chinese_fonts:
                if font in available_fonts:
                    print(f"使用字体: {font}")
                    return font
            
            # 如果没有找到预定义字体，尝试查找包含CJK的字体
            for font in available_fonts:
                if any(keyword in font.lower() for keyword in ['cjk', 'chinese', 'simhei', 'yahei']):
                    print(f"使用字体: {font}")
                    return font
            
            # 最后的回退选项
            print("警告: 未找到合适的中文字体，使用默认字体")
            return 'DejaVu Sans'
            
        except Exception as e:
            print(f"字体检测失败: {e}")
            return 'DejaVu Sans'
    
    def _configure_matplotlib(self):
        """配置matplotlib的中文显示"""
        try:
            # 设置字体
            plt.rcParams['font.sans-serif'] = [self.chinese_font, 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
            
            # 设置默认字体大小
            plt.rcParams['font.size'] = 10
            plt.rcParams['figure.titlesize'] = 12
            plt.rcParams['axes.titlesize'] = 11
            plt.rcParams['axes.labelsize'] = 10
            plt.rcParams['legend.fontsize'] = 9
            
        except Exception as e:
            print(f"matplotlib字体配置失败: {e}")


class GraphZoomPlugin(QObject):
    """图谱局部放大插件：提供以指定节点为中心的局部图谱放大显示功能。"""
    
    def __init__(self, graph_manager):
        super().__init__()
        self.name = "Local Graph Zoom Tool"
        self.graph_manager = graph_manager
        self.zoom_dialog = None
        self.current_subgraph = None
        self.current_center = None
        self.current_depth = 1
        
        # 初始化字体管理器
        self.font_manager = FontManager()
        
    def run(self):
        """插件入口：弹出局部放大功能界面。"""
        if self.zoom_dialog is None:
            self.zoom_dialog = ZoomDialog(self.graph_manager, self)
        self.zoom_dialog.show()
        self.zoom_dialog.raise_()
        self.zoom_dialog.activateWindow()


class ZoomDialog(QDialog):
    """局部放大对话框"""
    
    def __init__(self, graph_manager, plugin):
        super().__init__()
        self.graph_manager = graph_manager
        self.plugin = plugin
        self.current_graph = None
        self.node_positions = {}
        self.node_colors = {}
        self.directed_edges = set()  # 存储有向边
        self.undirected_edges = set()  # 存储无向边
        
        # 文本常量（便于国际化）
        self.texts = {
            'window_title': 'Local Graph Zoom Tool',
            'control_panel': 'Local Zoom Controls',
            'center_node': 'Center Node:',
            'neighbor_layers': 'Neighbor Layers:',
            'show_labels': 'Show node labels',
            'show_edges': 'Show relationship labels',
            'edge_mode': 'Edge Type Mode:',
            'directed_mode': 'Directed edges',
            'undirected_mode': 'Undirected edges',
            'mixed_mode': 'Mixed mode',
            'zoom_display': 'Zoom In',
            'reset_view': 'Reset View',
            'export_subgraph': 'Export Subgraph',
            'info_panel': 'Local Graph Information',
            'center_details': 'Center Node Details:',
            'neighbor_list': 'Neighbor Node List:',
            'node_name': 'Node Name',
            'node_type': 'Type',
            'distance': 'Distance',
            'relation_type': 'Relationship Type',
            'full_graph_view': 'Full Graph View',
            'local_zoom_view': 'Local Zoom View - Center: {} (Depth: {})',
            'center_node_legend': 'Center Node',
            'layer_neighbor': 'Layer {} Neighbor',
            'select_center_prompt': 'Select a center node to display the local graph.',
            'unknown': 'Unknown',
            'relation': 'Related',
            'warning': 'Warning',
            'error': 'Error',
            'info': 'Information',
            'success': 'Success'
        }
        
        self.setup_ui()
        self.load_graph_data()
        
    def setup_ui(self):
        """设置界面布局"""
        self.setWindowTitle(self.texts['window_title'])
        self.setMinimumSize(1000, 700)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 分割器：左侧图形，右侧信息
        splitter = QSplitter()
        main_layout.addWidget(splitter)
        
        # 左侧：图形显示区域
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        splitter.addWidget(self.canvas)
        
        # 右侧：信息面板
        info_panel = self.create_info_panel()
        splitter.addWidget(info_panel)
        
        # 设置分割器比例
        splitter.setSizes([700, 300])
        
    def create_control_panel(self):
        """创建控制面板"""
        group = QGroupBox(self.texts['control_panel'])
        layout = QHBoxLayout(group)
        
        # 中心节点选择
        layout.addWidget(QLabel(self.texts['center_node']))
        self.center_combo = QComboBox()
        self.center_combo.setMinimumWidth(150)
        self.center_combo.setEditable(True)
        layout.addWidget(self.center_combo)
        
        # 邻居层数选择
        layout.addWidget(QLabel(self.texts['neighbor_layers']))
        self.depth_spinbox = QSpinBox()
        self.depth_spinbox.setRange(1, 5)
        self.depth_spinbox.setValue(1)
        self.depth_spinbox.setToolTip("Select the number of neighbor layers to display (1-5).")
        layout.addWidget(self.depth_spinbox)
        
        # 边类型模式选择
        edge_group = QGroupBox(self.texts['edge_mode'])
        edge_layout = QVBoxLayout(edge_group)
        
        self.directed_radio = QRadioButton(self.texts['directed_mode'])
        self.undirected_radio = QRadioButton(self.texts['undirected_mode'])
        self.mixed_radio = QRadioButton(self.texts['mixed_mode'])
        self.mixed_radio.setChecked(True)  # 默认混合模式
        
        self.directed_radio.setToolTip("Display all edges as directed edges with arrows.")
        self.undirected_radio.setToolTip("Display all edges as undirected edges without arrows.")
        self.mixed_radio.setToolTip("Automatically determine direction from the edge is_directed attribute.")
        
        edge_layout.addWidget(self.mixed_radio)
        edge_layout.addWidget(self.directed_radio)
        edge_layout.addWidget(self.undirected_radio)
        layout.addWidget(edge_group)
        
        # 显示选项
        self.show_labels_cb = QCheckBox(self.texts['show_labels'])
        self.show_labels_cb.setChecked(True)
        layout.addWidget(self.show_labels_cb)
        
        self.show_edges_cb = QCheckBox(self.texts['show_edges'])
        self.show_edges_cb.setChecked(True)
        self.show_edges_cb.setToolTip("Show relationship type labels on edges.")
        layout.addWidget(self.show_edges_cb)
        
        # 操作按钮
        layout.addStretch()
        
        self.zoom_btn = QPushButton(self.texts['zoom_display'])
        self.zoom_btn.clicked.connect(self.perform_zoom)
        layout.addWidget(self.zoom_btn)
        
        self.reset_btn = QPushButton(self.texts['reset_view'])
        self.reset_btn.clicked.connect(self.reset_view)
        layout.addWidget(self.reset_btn)
        
        self.export_btn = QPushButton(self.texts['export_subgraph'])
        self.export_btn.clicked.connect(self.export_subgraph)
        layout.addWidget(self.export_btn)
        
        return group
    
    def create_info_panel(self):
        """创建信息面板"""
        group = QGroupBox(self.texts['info_panel'])
        layout = QVBoxLayout(group)
        
        # 统计信息
        self.stats_label = QLabel(self.texts['select_center_prompt'])
        self.stats_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f0f8ff;
                border: 1px solid #b0d4f1;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.stats_label)
        
        # 节点详情
        layout.addWidget(QLabel(self.texts['center_details']))
        self.center_info = QTextEdit()
        self.center_info.setMaximumHeight(120)
        self.center_info.setReadOnly(True)
        layout.addWidget(self.center_info)
        
        # 邻居节点列表
        layout.addWidget(QLabel(self.texts['neighbor_list']))
        self.neighbor_table = QTableWidget()
        self.neighbor_table.setColumnCount(4)
        self.neighbor_table.setHorizontalHeaderLabels([
            self.texts['node_name'], 
            self.texts['node_type'], 
            self.texts['distance'],
            self.texts['relation_type']
        ])
        layout.addWidget(self.neighbor_table)
        
        return group
    
    def safe_text(self, text, fallback=""):
        """安全的文本处理，避免编码问题"""
        try:
            if isinstance(text, bytes):
                return text.decode('utf-8', errors='replace')
            return str(text) if text is not None else fallback
        except Exception:
            return fallback
    
    def load_graph_data(self):
        """加载图谱数据"""
        try:
            data = self.graph_manager.get_graph_data()
            if not data["nodes"]:
                QMessageBox.warning(self, self.texts['warning'], "The current graph is empty. Local zoom cannot be performed.")
                return
            
            # 构建NetworkX图
            self.current_graph = nx.MultiDiGraph()  # 使用MultiDiGraph支持多重有向边
            self.directed_edges = set()
            self.undirected_edges = set()
            
            # 添加节点
            for node in data["nodes"]:
                node_name = self.safe_text(node["name"])
                node_type = self.safe_text(node.get("type", self.texts['unknown']))
                attributes = node.get("attributes", {})
                
                self.current_graph.add_node(
                    node_name,
                    type=node_type,
                    attributes=attributes
                )
            
            # 添加边 - 修复的关键部分
            for edge in data["edges"]:
                source = self.safe_text(edge["source"])
                target = self.safe_text(edge["target"])
                relation_type = self.safe_text(edge.get("relation_type", self.texts['relation']))
                
                # 检查边的方向性
                is_directed = edge.get("is_directed", True)  # 默认为有向边
                
                if is_directed:
                    # 有向边：只添加一个方向
                    edge_key = self.current_graph.add_edge(
                        source,
                        target,
                        relation_type=relation_type,
                        is_directed=True
                    )
                    self.directed_edges.add((source, target, edge_key))
                else:
                    # 无向边：添加两个方向，但标记为无向
                    edge_key1 = self.current_graph.add_edge(
                        source,
                        target,
                        relation_type=relation_type,
                        is_directed=False
                    )
                    edge_key2 = self.current_graph.add_edge(
                        target,
                        source,
                        relation_type=relation_type,
                        is_directed=False
                    )
                    self.undirected_edges.add((source, target, edge_key1))
                    self.undirected_edges.add((target, source, edge_key2))
            
            # 更新中心节点下拉列表
            self.center_combo.clear()
            node_names = sorted(self.current_graph.nodes())
            self.center_combo.addItems(node_names)
            
            # 显示初始空白状态
            self.show_initial_state()
            
        except Exception as e:
            error_msg = f"Failed to load graph data: {self.safe_text(str(e))}"
            QMessageBox.critical(self, self.texts['error'], error_msg)
    
    def get_edge_style(self):
        """根据用户选择获取边的显示样式"""
        if self.directed_radio.isChecked():
            return "directed"
        elif self.undirected_radio.isChecked():
            return "undirected"
        else:  # mixed_radio
            return "mixed"
    
    def show_initial_state(self):
        """显示初始空白状态"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 显示提示信息
        ax.text(0.5, 0.5, 'Select a center node and click "Zoom In" to view the local graph.', 
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=16,
                fontfamily=self.plugin.font_manager.chinese_font,
                color='gray',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgray', alpha=0.3))
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        self.canvas.draw()
        
        # 更新统计信息
        directed_count = len(self.directed_edges)
        undirected_count = len(self.undirected_edges) // 2  # 无向边计算了两次
        stats_text = f"Graph loaded\nTotal nodes: {len(self.current_graph.nodes())}\n"
        stats_text += f"Directed edges: {directed_count}\nUndirected edges: {undirected_count}\nSelect a center node for local zoom."
        self.update_stats_info(stats_text)
    
    def show_full_graph(self):
        """显示完整图谱"""
        if not self.current_graph:
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        try:
            # 为了布局计算，创建一个简化的图
            simple_graph = nx.Graph()
            for node in self.current_graph.nodes():
                simple_graph.add_node(node)
            
            # 添加去重的边用于布局
            added_edges = set()
            for edge in self.current_graph.edges():
                edge_tuple = tuple(sorted([edge[0], edge[1]]))
                if edge_tuple not in added_edges:
                    simple_graph.add_edge(edge[0], edge[1])
                    added_edges.add(edge_tuple)
            
            # 使用spring布局
            pos = nx.spring_layout(simple_graph, k=5, iterations=100)
            
            # 绘制节点 - 统一使用简单的蓝色
            nx.draw_networkx_nodes(
                simple_graph,
                pos=pos,
                node_color='lightblue',
                node_size=500,
                alpha=0.8,
                ax=ax
            )
            
            # 根据边模式绘制边
            edge_style = self.get_edge_style()
            self.draw_edges_with_style(simple_graph, pos, ax, edge_style)
            
            # 绘制标签
            if self.show_labels_cb.isChecked():
                nx.draw_networkx_labels(
                    simple_graph,
                    pos=pos,
                    font_size=10,
                    font_weight='bold',
                    font_family=self.plugin.font_manager.chinese_font,
                    ax=ax
                )
            
            # 绘制边标签（关系）
            if self.show_edges_cb.isChecked():
                self.draw_edge_labels(pos, ax)
            
            ax.set_title(self.texts['full_graph_view'], 
                        fontsize=14, fontweight='bold',
                        fontfamily=self.plugin.font_manager.chinese_font)
            ax.axis('off')
            
            self.canvas.draw()
            
            # 更新统计信息
            directed_count = len(self.directed_edges)
            undirected_count = len(self.undirected_edges) // 2
            stats_text = f"Full graph\nNodes: {len(self.current_graph.nodes())}\n"
            stats_text += f"Directed edges: {directed_count}\nUndirected edges: {undirected_count}"
            self.update_stats_info(stats_text)
            
        except Exception as e:
            error_msg = f"Failed to draw graph: {self.safe_text(str(e))}"
            QMessageBox.critical(self, self.texts['error'], error_msg)
    
    def draw_edges_with_style(self, graph, pos, ax, edge_style):
        """根据样式绘制边"""
        if edge_style == "directed":
            # 所有边都显示为有向边
            nx.draw_networkx_edges(
                graph, pos=pos, edge_color='gray', alpha=0.6, width=1.5,
                arrows=True, arrowsize=20, arrowstyle='->', ax=ax
            )
        elif edge_style == "undirected":
            # 所有边都显示为无向边
            nx.draw_networkx_edges(
                graph, pos=pos, edge_color='gray', alpha=0.6, width=1.5,
                arrows=False, ax=ax
            )
        else:  # mixed
            # 混合模式：根据边的is_directed属性区分
            directed_edges_simple = []
            undirected_edges_simple = []
            
            processed_edges = set()
            
            for u, v, key in self.current_graph.edges(keys=True):
                edge_data = self.current_graph.edges[u, v, key]
                is_directed = edge_data.get('is_directed', True)
                
                edge_tuple = (u, v)
                reverse_tuple = (v, u)
                
                if is_directed:
                    directed_edges_simple.append(edge_tuple)
                else:
                    # 对于无向边，只添加一次
                    if edge_tuple not in processed_edges and reverse_tuple not in processed_edges:
                        undirected_edges_simple.append(edge_tuple)
                        processed_edges.add(edge_tuple)
                        processed_edges.add(reverse_tuple)
            
            # 绘制有向边
            if directed_edges_simple:
                nx.draw_networkx_edges(
                    graph, pos=pos, edgelist=directed_edges_simple,
                    edge_color='red', alpha=0.7, width=2,
                    arrows=True, arrowsize=20, arrowstyle='->', ax=ax
                )
            
            # 绘制无向边
            if undirected_edges_simple:
                nx.draw_networkx_edges(
                    graph, pos=pos, edgelist=undirected_edges_simple,
                    edge_color='blue', alpha=0.7, width=2,
                    arrows=False, ax=ax
                )
    
    def draw_edge_labels(self, pos, ax):
        """绘制边标签"""
        edge_labels = {}
        processed_edges = set()
        
        for u, v, key in self.current_graph.edges(keys=True):
            edge_data = self.current_graph.edges[u, v, key]
            relation = edge_data.get('relation_type', self.texts['relation'])
            is_directed = edge_data.get('is_directed', True)
            
            if is_directed:
                edge_labels[(u, v)] = self.safe_text(relation)
            else:
                # 对于无向边，只标记一次
                edge_tuple = tuple(sorted([u, v]))
                if edge_tuple not in processed_edges:
                    edge_labels[edge_tuple] = self.safe_text(relation)
                    processed_edges.add(edge_tuple)
        
        if edge_labels:
            nx.draw_networkx_edge_labels(
                self.current_graph, pos=pos, edge_labels=edge_labels,
                font_size=8, font_family=self.plugin.font_manager.chinese_font, ax=ax,
                bbox=dict(boxstyle='round,pad=0.1', facecolor='lightyellow', alpha=0.8),
                rotate=False
            )
    
    def perform_zoom(self):
        """执行局部放大"""
        if not self.current_graph:
            QMessageBox.warning(self, self.texts['warning'], "Please load graph data first.")
            return
        
        center_node = self.safe_text(self.center_combo.currentText().strip())
        if not center_node:
            QMessageBox.warning(self, self.texts['warning'], "Please select a center node.")
            return
        
        if center_node not in self.current_graph.nodes():
            QMessageBox.warning(self, self.texts['warning'], f"Node '{center_node}' does not exist.")
            return
        
        depth = self.depth_spinbox.value()
        
        try:
            # 获取局部子图
            subgraph_nodes = self.get_subgraph_nodes(center_node, depth)
            if len(subgraph_nodes) <= 1:
                QMessageBox.information(self, self.texts['info'], f"Node '{center_node}' does not have enough neighbor nodes.")
                return
                
            subgraph = self.current_graph.subgraph(subgraph_nodes)
            
            # 绘制局部子图
            self.draw_subgraph(subgraph, center_node, depth)
            
            # 更新信息面板
            self.update_info_panel(center_node, subgraph, depth)
            
        except Exception as e:
            import traceback
            error_msg = f"Local zoom failed: {self.safe_text(str(e))}\nDetails:\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, self.texts['error'], f"Local zoom failed: {self.safe_text(str(e))}")
    
    def get_subgraph_nodes(self, center_node, depth):
        """获取指定深度的子图节点"""
        visited = set()
        current_level = {center_node}
        
        for level in range(depth + 1):
            if level == 0:
                visited.update(current_level)
            else:
                next_level = set()
                for node in current_level:
                    try:
                        # 获取所有邻居（不考虑方向）
                        neighbors = set()
                        for neighbor in self.current_graph.successors(node):
                            neighbors.add(neighbor)
                        for neighbor in self.current_graph.predecessors(node):
                            neighbors.add(neighbor)
                        
                        next_level.update(neighbors - visited)
                    except Exception as e:
                        print(f"获取节点 {node} 的邻居时出错: {e}")
                        continue
                
                if not next_level:
                    break
                    
                visited.update(next_level)
                current_level = next_level
        
        return list(visited)
    
    def draw_subgraph(self, subgraph, center_node, depth):
        """绘制局部子图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        try:
            # 为布局创建简化图
            simple_subgraph = nx.Graph()
            for node in subgraph.nodes():
                simple_subgraph.add_node(node)
            
            # 添加去重的边用于布局
            added_edges = set()
            for edge in subgraph.edges():
                edge_tuple = tuple(sorted([edge[0], edge[1]]))
                if edge_tuple not in added_edges:
                    simple_subgraph.add_edge(edge[0], edge[1])
                    added_edges.add(edge_tuple)
            
            # 计算节点到中心的距离
            try:
                distances = nx.single_source_shortest_path_length(simple_subgraph, center_node)
            except:
                distances = {node: 1 if node != center_node else 0 for node in subgraph.nodes()}
            
            # 使用spring布局
            pos = nx.spring_layout(simple_subgraph, k=3, iterations=100)
            
            # 按距离分层绘制节点
            # 定义每层的颜色（更明显的区分）
            layer_colors = {
                0: '#FF0000',  # 中心节点：红色
                1: '#1E90FF',  # 1层邻居：道奇蓝
                2: '#32CD32',  # 2层邻居：绿色
                3: '#FF8C00',  # 3层邻居：橙色
                4: '#9932CC',  # 4层邻居：紫色
                5: '#FF1493'   # 5层邻居：深粉色
            }
            
            for dist in range(depth + 1):
                nodes_at_distance = [n for n, d in distances.items() if d == dist]
                if not nodes_at_distance:
                    continue
                
                if dist == 0:  # 中心节点
                    node_size = 1200
                    node_color = layer_colors[0]
                    alpha = 1.0
                else:
                    node_size = max(800 - dist * 100, 400)
                    # 直接使用层级颜色
                    node_colors = layer_colors.get(dist, '#808080')  # 灰色作为默认色
                    alpha = max(0.9 - dist * 0.1, 0.6)  # 调整透明度范围
                
                # 绘制节点
                node_pos = {n: pos[n] for n in nodes_at_distance}
                if dist == 0:
                    nx.draw_networkx_nodes(
                        simple_subgraph.subgraph(nodes_at_distance),
                        pos=node_pos, node_color=node_color,
                        node_size=node_size, alpha=alpha, ax=ax
                    )
                else:
                    nx.draw_networkx_nodes(
                        simple_subgraph.subgraph(nodes_at_distance),
                        pos=node_pos, node_color=node_colors,
                        node_size=node_size, alpha=alpha, ax=ax
                    )
            
            # 根据边模式绘制边
            edge_style = self.get_edge_style()
            self.draw_subgraph_edges_with_style(subgraph, pos, ax, edge_style)
            
            # 绘制标签
            if self.show_labels_cb.isChecked():
                nx.draw_networkx_labels(
                    simple_subgraph, pos=pos, font_size=12, font_weight='bold',
                    font_family=self.plugin.font_manager.chinese_font, ax=ax
                )
            
            # 绘制边标签
            if self.show_edges_cb.isChecked():
                self.draw_subgraph_edge_labels(subgraph, pos, ax)
            
            title = self.texts['local_zoom_view'].format(center_node, depth)
            ax.set_title(title, fontsize=14, fontweight='bold',
                        fontfamily=self.plugin.font_manager.chinese_font)
            ax.axis('off')
            
            # 添加距离图例
            legend_elements = []
            layer_colors_for_legend = {
                0: '#FF0000',  # 中心节点：红色
                1: '#1E90FF',  # 1层邻居：道奇蓝
                2: '#32CD32',  # 2层邻居：绿色
                3: '#FF8C00',  # 3层邻居：橙色
                4: '#9932CC',  # 4层邻居：紫色
                5: '#FF1493'   # 5层邻居：深粉色
            }
            
            for dist in range(depth + 1):
                if dist == 0:
                    legend_elements.append(mpatches.Patch(
                        color=layer_colors_for_legend[0], 
                        label=self.texts['center_node_legend']
                    ))
                else:
                    color = layer_colors_for_legend.get(dist, '#808080')
                    legend_elements.append(mpatches.Patch(
                        color=color, 
                        label=self.texts['layer_neighbor'].format(dist)
                    ))
            
            legend = ax.legend(handles=legend_elements, loc='upper right')
            for text in legend.get_texts():
                text.set_fontfamily(self.plugin.font_manager.chinese_font)
            
            self.canvas.draw()
            
        except Exception as e:
            error_msg = f"Failed to draw subgraph: {self.safe_text(str(e))}"
            QMessageBox.critical(self, self.texts['error'], error_msg)
    
    def draw_subgraph_edges_with_style(self, subgraph, pos, ax, edge_style):
        """在子图中根据样式绘制边"""
        if edge_style == "directed":
            # 创建有向图用于绘制
            directed_graph = nx.DiGraph()
            for node in subgraph.nodes():
                directed_graph.add_node(node)
            
            # 添加边（避免重复）
            for u, v, key in subgraph.edges(keys=True):
                if not directed_graph.has_edge(u, v):
                    directed_graph.add_edge(u, v)
            
            nx.draw_networkx_edges(
                directed_graph, pos=pos, edge_color='gray', alpha=0.7, width=2.5,
                arrows=True, arrowsize=25, arrowstyle='->', ax=ax
            )
        elif edge_style == "undirected":
            # 创建无向图用于绘制
            undirected_graph = nx.Graph()
            for node in subgraph.nodes():
                undirected_graph.add_node(node)
            
            # 添加边（自动去重）
            for u, v, key in subgraph.edges(keys=True):
                undirected_graph.add_edge(u, v)
            
            nx.draw_networkx_edges(
                undirected_graph, pos=pos, edge_color='gray', alpha=0.7, width=2.5,
                arrows=False, ax=ax
            )
        else:  # mixed
            # 分别处理有向边和无向边
            directed_edges = []
            undirected_edges = []
            processed_undirected = set()
            
            for u, v, key in subgraph.edges(keys=True):
                edge_data = self.current_graph.edges[u, v, key]
                is_directed = edge_data.get('is_directed', True)
                
                if is_directed:
                    directed_edges.append((u, v))
                else:
                    edge_tuple = tuple(sorted([u, v]))
                    if edge_tuple not in processed_undirected:
                        undirected_edges.append((u, v))
                        processed_undirected.add(edge_tuple)
            
            # 绘制有向边
            if directed_edges:
                directed_graph = nx.DiGraph()
                directed_graph.add_edges_from(directed_edges)
                nx.draw_networkx_edges(
                    directed_graph, pos=pos, edge_color='red', alpha=0.7, width=2.5,
                    arrows=True, arrowsize=25, arrowstyle='->', ax=ax
                )
            
            # 绘制无向边
            if undirected_edges:
                undirected_graph = nx.Graph()
                undirected_graph.add_edges_from(undirected_edges)
                nx.draw_networkx_edges(
                    undirected_graph, pos=pos, edge_color='blue', alpha=0.7, width=2.5,
                    arrows=False, ax=ax
                )
    
    def draw_subgraph_edge_labels(self, subgraph, pos, ax):
        """绘制子图边标签"""
        edge_labels = {}
        processed_edges = set()
        
        for u, v, key in subgraph.edges(keys=True):
            edge_data = self.current_graph.edges[u, v, key]
            relation = edge_data.get('relation_type', self.texts['relation'])
            is_directed = edge_data.get('is_directed', True)
            
            if is_directed:
                edge_labels[(u, v)] = self.safe_text(relation)
            else:
                edge_tuple = tuple(sorted([u, v]))
                if edge_tuple not in processed_edges:
                    edge_labels[edge_tuple] = self.safe_text(relation)
                    processed_edges.add(edge_tuple)
        
        if edge_labels:
            nx.draw_networkx_edge_labels(
                subgraph, pos=pos, edge_labels=edge_labels, font_size=9,
                font_family=self.plugin.font_manager.chinese_font, ax=ax,
                bbox=dict(boxstyle='round,pad=0.1', facecolor='lightyellow', alpha=0.9),
                rotate=False
            )
    
    def update_info_panel(self, center_node, subgraph, depth):
        """更新信息面板"""
        # 更新统计信息
        node_count = len(subgraph.nodes())
        edge_count = len(subgraph.edges())
        
        # 计算距离分布
        simple_subgraph = subgraph.to_undirected()
        try:
            distances = nx.single_source_shortest_path_length(simple_subgraph, center_node)
        except:
            distances = {node: 1 if node != center_node else 0 for node in subgraph.nodes()}
        
        distance_counts = defaultdict(int)
        for d in distances.values():
            distance_counts[d] += 1
        
        # 统计边类型
        directed_count = 0
        undirected_count = 0
        processed_undirected = set()
        
        for u, v, key in subgraph.edges(keys=True):
            edge_data = self.current_graph.edges[u, v, key]
            is_directed = edge_data.get('is_directed', True)
            
            if is_directed:
                directed_count += 1
            else:
                edge_tuple = tuple(sorted([u, v]))
                if edge_tuple not in processed_undirected:
                    undirected_count += 1
                    processed_undirected.add(edge_tuple)
        
        stats_text = f"Local subgraph statistics\nCenter node: {center_node}\n"
        stats_text += f"Neighbor layers: {depth}\nTotal nodes: {node_count}\n"
        stats_text += f"Directed edges: {directed_count}\nUndirected edges: {undirected_count}\nDistance distribution:\n"
        for dist in sorted(distance_counts.keys()):
            stats_text += f"  Layer {dist}: {distance_counts[dist]} nodes\n"
        
        self.update_stats_info(stats_text)
        
        # 更新中心节点信息
        center_info = f"Node Name: {center_node}\n"
        center_attrs = self.current_graph.nodes[center_node]
        center_info += f"Type: {center_attrs.get('type', self.texts['unknown'])}\n"
        
        # 计算度数信息
        try:
            out_degree = 0
            in_degree = 0
            
            for u, v, key in self.current_graph.out_edges(center_node, keys=True):
                out_degree += 1
            for u, v, key in self.current_graph.in_edges(center_node, keys=True):
                in_degree += 1
            
            center_info += f"Out-degree: {out_degree}\nIn-degree: {in_degree}\n"
        except Exception as e:
            center_info += f"Degree information: calculation error\n"
        
        # 显示出边关系
        try:
            out_relations = []
            for u, v, key in self.current_graph.out_edges(center_node, keys=True):
                if v in subgraph.nodes():
                    edge_data = self.current_graph.edges[u, v, key]
                    relation = self.safe_text(edge_data.get('relation_type', self.texts['relation']))
                    is_directed = edge_data.get('is_directed', True)
                    direction = '→' if is_directed else '—'
                    out_relations.append(f"  {direction} {v} ({relation})")
            
            if out_relations:
                center_info += f"\nOutgoing relationships ({len(out_relations)}):\n"
                center_info += '\n'.join(sorted(out_relations))
        except Exception as e:
            center_info += f"\nOutgoing relationships: failed to retrieve\n"
        
        # 显示入边关系
        try:
            in_relations = []
            for u, v, key in self.current_graph.in_edges(center_node, keys=True):
                if u in subgraph.nodes():
                    edge_data = self.current_graph.edges[u, v, key]
                    relation = self.safe_text(edge_data.get('relation_type', self.texts['relation']))
                    is_directed = edge_data.get('is_directed', True)
                    direction = '←' if is_directed else '—'
                    in_relations.append(f"  {direction} {u} ({relation})")
            
            if in_relations:
                center_info += f"\nIncoming relationships ({len(in_relations)}):\n"
                center_info += '\n'.join(sorted(in_relations))
        except Exception as e:
            center_info += f"\nIncoming relationships: failed to retrieve\n"
        
        # 显示属性
        if center_attrs.get('attributes'):
            center_info += f"\nAttributes:\n"
            for key, value in center_attrs['attributes'].items():
                safe_key = self.safe_text(key)
                safe_value = self.safe_text(value)
                center_info += f"  {safe_key}: {safe_value}\n"
        
        self.center_info.setText(center_info)
        
        # 更新邻居表格
        self.update_neighbor_table(center_node, subgraph, distances)
    
    def update_neighbor_table(self, center_node, subgraph, distances):
        """更新邻居节点表格"""
        neighbors = [n for n in subgraph.nodes() if n != center_node]
        neighbors.sort(key=lambda n: (distances.get(n, 999), n))
        
        self.neighbor_table.setRowCount(len(neighbors))
        
        for i, neighbor in enumerate(neighbors):
            try:
                # 节点名称
                self.neighbor_table.setItem(i, 0, QTableWidgetItem(self.safe_text(neighbor)))
                
                # 节点类型
                node_type = self.current_graph.nodes[neighbor].get('type', self.texts['unknown'])
                self.neighbor_table.setItem(i, 1, QTableWidgetItem(self.safe_text(node_type)))
                
                # 距离
                distance = distances.get(neighbor, 999)
                self.neighbor_table.setItem(i, 2, QTableWidgetItem(str(distance)))
                
                # 关系类型
                relation_text = ""
                if distance == 1:  # 直接邻居
                    relations = []
                    
                    # 检查出边
                    for u, v, key in self.current_graph.out_edges(center_node, keys=True):
                        if v == neighbor:
                            edge_data = self.current_graph.edges[u, v, key]
                            relation = self.safe_text(edge_data.get('relation_type', self.texts['relation']))
                            is_directed = edge_data.get('is_directed', True)
                            direction = '→' if is_directed else '—'
                            relations.append(f"{direction} {relation}")
                    
                    # 检查入边
                    for u, v, key in self.current_graph.in_edges(center_node, keys=True):
                        if u == neighbor:
                            edge_data = self.current_graph.edges[u, v, key]
                            relation = self.safe_text(edge_data.get('relation_type', self.texts['relation']))
                            is_directed = edge_data.get('is_directed', True)
                            direction = '←' if is_directed else '—'
                            relations.append(f"{direction} {relation}")
                    
                    if relations:
                        relation_text = " / ".join(relations)
                    else:
                        relation_text = "Indirect connection"
                else:
                    relation_text = f"Layer {distance} neighbor"
                
                self.neighbor_table.setItem(i, 3, QTableWidgetItem(relation_text))
                
            except Exception as e:
                print(f"更新邻居表格行 {i} 时出错: {e}")
                # 设置默认值
                self.neighbor_table.setItem(i, 0, QTableWidgetItem(self.safe_text(neighbor)))
                self.neighbor_table.setItem(i, 1, QTableWidgetItem("Unknown"))
                self.neighbor_table.setItem(i, 2, QTableWidgetItem("?"))
                self.neighbor_table.setItem(i, 3, QTableWidgetItem("Error"))
        
        self.neighbor_table.resizeColumnsToContents()
    
    def update_stats_info(self, text):
        """更新统计信息标签"""
        self.stats_label.setText(self.safe_text(text))
    
    def generate_color_map(self, node_types):
        """为不同节点类型生成颜色映射"""
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', 
                 '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43']
        
        color_map = {}
        for i, node_type in enumerate(sorted(node_types)):
            color_map[node_type] = colors[i % len(colors)]
        
        return color_map
    
    def reset_view(self):
        """重置视图"""
        self.show_full_graph()
        self.center_info.clear()
        self.neighbor_table.setRowCount(0)
        self.update_stats_info("Reset to full graph view.")
    
    def export_subgraph(self):
        """导出当前子图"""
        center_node = self.safe_text(self.center_combo.currentText().strip())
        depth = self.depth_spinbox.value()
        
        if not center_node or center_node not in self.current_graph.nodes():
            QMessageBox.warning(self, self.texts['warning'], "Please select a valid center node first.")
            return
        
        try:
            # 获取子图
            subgraph_nodes = self.get_subgraph_nodes(center_node, depth)
            subgraph = self.current_graph.subgraph(subgraph_nodes)
            
            # 转换为可保存的格式
            export_data = {
                "center_node": center_node,
                "depth": depth,
                "nodes": [],
                "edges": []
            }
            
            # 添加节点
            for node in subgraph.nodes():
                node_data = {
                    "name": self.safe_text(node),
                    "type": self.safe_text(self.current_graph.nodes[node].get('type', self.texts['unknown'])),
                    "attributes": self.current_graph.nodes[node].get('attributes', {})
                }
                export_data["nodes"].append(node_data)
            
            # 添加边（去重无向边）
            processed_undirected = set()
            for u, v, key in subgraph.edges(keys=True):
                edge_data = self.current_graph.edges[u, v, key]
                is_directed = edge_data.get('is_directed', True)
                
                if is_directed:
                    edge_export = {
                        "source": self.safe_text(u),
                        "target": self.safe_text(v),
                        "relation_type": self.safe_text(edge_data.get('relation_type', self.texts['relation'])),
                        "is_directed": True
                    }
                    export_data["edges"].append(edge_export)
                else:
                    edge_tuple = tuple(sorted([u, v]))
                    if edge_tuple not in processed_undirected:
                        edge_export = {
                            "source": self.safe_text(u),
                            "target": self.safe_text(v),
                            "relation_type": self.safe_text(edge_data.get('relation_type', self.texts['relation'])),
                            "is_directed": False
                        }
                        export_data["edges"].append(edge_export)
                        processed_undirected.add(edge_tuple)
            
            # 保存文件
            from PyQt5.QtWidgets import QFileDialog
            import json
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Subgraph", 
                f"subgraph_{center_node}_{depth}layers.json",
                "JSON Files (*.json)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, self.texts['success'], f"Subgraph exported to: {filename}")
        
        except Exception as e:
            error_msg = f"Failed to export subgraph: {self.safe_text(str(e))}"
            QMessageBox.critical(self, self.texts['error'], error_msg)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.plugin.zoom_dialog = None
        event.accept()


class Plugin(GraphZoomPlugin):
    """Plugin 管理器识别的入口类"""
    pass
