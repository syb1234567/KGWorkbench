from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLineEdit, QLabel, QComboBox,
    QListWidgetItem, QFrame, QDialog
)
from PyQt5.QtGui import QColor

class SearchDialog(QDialog):
    """知识图谱搜索对话框"""
    node_selected = pyqtSignal(str)  # 节点选择信号

    def __init__(self, graph_manager, parent=None):
        super().__init__(parent)
        self.graph_manager = graph_manager
        self.parent_window = parent
        self.setWindowTitle("Knowledge Graph Search")
        self.setModal(False)
        self.resize(400, 600)
        self.init_ui()

    def init_ui(self):
        """初始化搜索界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 搜索标题
        title_label = QLabel("Knowledge Graph Search")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2196F3;
                padding: 5px 0;
            }
        """)
        layout.addWidget(title_label)

        # 搜索输入框区域
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        search_layout = QVBoxLayout(search_container)

        # 搜索类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("Search Type:")
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["All", "Nodes Only", "Relationships Only"])
        self.search_type_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-width: 100px;
            }
        """)

        type_layout.addWidget(type_label)
        type_layout.addWidget(self.search_type_combo)
        type_layout.addStretch()
        search_layout.addLayout(type_layout)

        # 搜索输入框
        input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search keywords...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                font-size: 14px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        self.search_input.returnPressed.connect(self.perform_search)

        self.search_button = QPushButton("Search")
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.search_button.clicked.connect(self.perform_search)

        input_layout.addWidget(self.search_input)
        input_layout.addWidget(self.search_button)
        search_layout.addLayout(input_layout)

        layout.addWidget(search_container)

        # 搜索结果显示区域
        results_label = QLabel("Search Results")
        results_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding: 10px 0 5px 0;
            }
        """)
        layout.addWidget(results_label)

        # 结果统计
        self.results_stats = QLabel("Ready to search")
        self.results_stats.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                padding: 0 0 5px 0;
            }
        """)
        layout.addWidget(self.results_stats)

        # 结果列表
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.results_list.itemClicked.connect(self.on_result_clicked)
        self.results_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        layout.addWidget(self.results_list)

        # 底部操作按钮
        buttons_layout = QHBoxLayout()

        self.clear_button = QPushButton("Clear")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.clear_button.clicked.connect(self.clear_search)

        self.locate_button = QPushButton("Locate in Graph")
        self.locate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.locate_button.clicked.connect(self.locate_selected_node)
        self.locate_button.setEnabled(False)

        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        close_button.clicked.connect(self.close)

        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.locate_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_button)
        layout.addLayout(buttons_layout)

    def perform_search(self):
        """执行搜索 - 添加UI保护"""
        query = self.search_input.text().strip()
        if not query:
            self.results_stats.setText("Please enter a search keyword.")
            return

        # 禁用搜索按钮防止重复点击
        self.search_button.setEnabled(False)
        self.search_button.setText("Searching...")

        try:
            print(f"开始执行搜索: {query}")
            search_type = self.search_type_combo.currentIndex()

            # 检查图管理器和图对象
            if not hasattr(self, 'graph_manager') or self.graph_manager is None:
                self.results_stats.setText("Graph manager is not initialized.")
                return

            if not hasattr(self.graph_manager, 'graph') or self.graph_manager.graph is None:
                self.results_stats.setText("Graph data is not loaded.")
                return

            print(f"图中有 {self.graph_manager.graph.number_of_nodes()} 个节点")
            print(f"图中有 {self.graph_manager.graph.number_of_edges()} 条边")

            results = self.search_knowledge_graph(query, search_type)

            print(f"搜索完成，结果数量: {len(results)}")
            self.display_results(results, query)

        except Exception as e:
            print(f"搜索过程中出错: {e}")
            import traceback
            traceback.print_exc()
            self.results_stats.setText(f"Search failed: {str(e)}")

        finally:
            # 恢复搜索按钮
            self.search_button.setEnabled(True)
            self.search_button.setText("Search")

    def search_knowledge_graph(self, query, search_type=0):
        """搜索知识图谱"""
        results = []
        query_lower = query.lower()

        # 搜索节点
        if search_type in [0, 1]:
            for node, data in self.graph_manager.graph.nodes(data=True):
                score = 0
                match_info = []

                # 节点名称匹配
                if query_lower in node.lower():
                    score += 10
                    match_info.append(f"Node name: {node}")

                # 节点类型匹配
                node_type = data.get('type', '')
                if query_lower in node_type.lower():
                    score += 5
                    match_info.append(f"Type: {node_type}")

                # 属性匹配 - 修复部分：添加类型检查
                attributes = data.get('attributes', {})

                # 确保 attributes 是字典类型
                if isinstance(attributes, dict):
                    for key, value in attributes.items():
                        if query_lower in str(key).lower() or query_lower in str(value).lower():
                            score += 3
                            match_info.append(f"Attribute: {key}={value}")
                else:
                    # 如果 attributes 不是字典，尝试作为单个值处理
                    if attributes and query_lower in str(attributes).lower():
                        score += 3
                        match_info.append(f"Attribute value: {attributes}")

                if score > 0:
                    # 获取节点连接信息
                    try:
                        connected = self.graph_manager.get_connected_nodes(node)
                        connection_info = ""
                        if connected:
                            in_count = len(connected.get('predecessors', []))
                            out_count = len(connected.get('successors', []))
                            connection_info = f"Connections: {in_count} incoming, {out_count} outgoing"
                    except:
                        connection_info = "Failed to retrieve connection information"

                    results.append({
                        'type': 'node',
                        'name': node,
                        'node_type': node_type,
                        'score': score,
                        'match_info': match_info,
                        'connection_info': connection_info,
                        'data': data
                    })

        # 搜索关系
        if search_type in [0, 2]:
            try:
                for source, target, data in self.graph_manager.graph.edges(data=True):
                    score = 0
                    match_info = []

                    relation_type = data.get('relation_type', '') if isinstance(data, dict) else str(data)

                    # 关系类型匹配
                    if query_lower in relation_type.lower():
                        score += 8
                        match_info.append(f"Relationship: {relation_type}")

                    # 源节点和目标节点匹配
                    if query_lower in str(source).lower():
                        score += 5
                        match_info.append(f"Source node: {source}")

                    if query_lower in str(target).lower():
                        score += 5
                        match_info.append(f"Target node: {target}")

                    if score > 0:
                        results.append({
                            'type': 'relationship',
                            'name': f"{source} → {target}",
                            'relation_type': relation_type,
                            'source': source,
                            'target': target,
                            'score': score,
                            'match_info': match_info,
                            'data': data
                        })
            except Exception as e:
                print(f"搜索关系时出错: {e}")
                # 如果边搜索失败，至少保证节点搜索结果可用

        # 按相关性分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def display_results(self, results, query):
        """显示搜索结果"""
        self.results_list.clear()
        self.locate_button.setEnabled(False)

        if not results:
            self.results_stats.setText(f"No results found for '{query}'.")
            return

        self.results_stats.setText(f"Found {len(results)} results for '{query}'.")

        for result in results:
            item = QListWidgetItem()

            if result['type'] == 'node':
                # 节点结果显示
                main_text = f"📊 {result['name']}"
                if result['node_type']:
                    main_text += f" ({result['node_type']})"

                detail_text = ""
                if result['connection_info']:
                    detail_text += result['connection_info']
                if result['match_info']:
                    detail_text += f"\nMatch: {', '.join(result['match_info'][:2])}"

                item.setText(f"{main_text}\n{detail_text}")

            else:  # relationship
                # 关系结果显示
                main_text = f"🔗 {result['source']} → {result['target']}"
                detail_text = f"Relationship: {result['relation_type']}"
                if result['match_info']:
                    detail_text += f"\nMatch: {', '.join(result['match_info'][:2])}"

                item.setText(f"{main_text}\n{detail_text}")

            # 存储结果数据
            item.setData(Qt.UserRole, result)

            # 设置不同类型的背景色
            if result['type'] == 'node':
                item.setBackground(QColor(240, 248, 255))  # 淡蓝色
            else:
                item.setBackground(QColor(255, 248, 240))  # 淡橙色

            self.results_list.addItem(item)

    def on_result_clicked(self, item):
        """单击结果项"""
        self.locate_button.setEnabled(True)

    def on_result_double_clicked(self, item):
        """双击结果项 - 自动定位"""
        self.locate_selected_node()

    def locate_selected_node(self):
        """在图中定位选中的节点"""
        current_item = self.results_list.currentItem()
        if not current_item:
            return

        result_data = current_item.data(Qt.UserRole)
        if not result_data:
            return

        if result_data['type'] == 'node':
            node_name = result_data['name']
            self.highlight_node_in_graph(node_name)
            # 发射信号通知主窗口选中了节点
            self.node_selected.emit(node_name)

        elif result_data['type'] == 'relationship':
            # 对于关系，我们高亮显示源节点和目标节点
            source = result_data['source']
            target = result_data['target']
            self.highlight_relationship_in_graph(source, target)

    def highlight_node_in_graph(self, node_name):
        """在图中高亮显示节点（稳健版：安全注入 + 宽松匹配 + 回调提示）"""
        view = getattr(self.parent_window, "graph_view", None)
        if view is None:
            print("[highlight] ❌ parent_window.graph_view 不存在")
            return
        print(f"[highlight] ▶ 请求定位节点: {node_name!r}")
        try:
            import json
            # 用 json.dumps 生成安全的 JS 字面量，避免引号/反斜杠导致脚本错误
            node_js = json.dumps(str(node_name))

            js_code = (
                """
    (function () {
        if (!window.network || !network.body || !network.body.data) return "no-network";
        var nodes = network.body.data.nodes;
        if (!nodes || typeof nodes.getIds !== "function") return "no-nodes";

        // 目标关键字（统一小写）
        var needle = String(NAME).toLowerCase();

        // 将富文本 label/title 转为纯文本再比较
        function html2text(s){
            var d = document.createElement('div');
            d.innerHTML = String(s || '');
            return (d.textContent || d.innerText || '');
        }

        // 在 id / label / title 上做宽松匹配（全等或包含）
        var matchId = null;
        var ids = nodes.getIds();
        for (var i = 0; i < ids.length; i++) {
            var id = ids[i];
            var item = nodes.get(id) || {};
            var idStr = String(id).toLowerCase();
            var label = item.label != null ? html2text(item.label).trim().toLowerCase() : "";
            var title = item.title != null ? html2text(item.title).trim().toLowerCase() : "";
            if (idStr === needle || label === needle || title === needle ||
                (label && label.indexOf(needle) >= 0) || (title && title.indexOf(needle) >= 0)) {
                matchId = id; break;
            }
        }
        if (matchId === null) return "not-found";

        try {
            network.selectNodes([matchId]);
            if (typeof network.focus === "function") {
                network.focus(matchId, { scale: 1.25, animation: { duration: 600, easingFunction: "easeInOutQuad" } });
            } else if (typeof network.fit === "function") {
                network.fit({ nodes: [matchId], animation: true });
            }
            setTimeout(function(){ try { network.unselectAll(); } catch(e){} }, 1200);
            return "ok";
        } catch (e) {
            return "error:" + (e && e.message ? e.message : "unknown");
        }
    })();
    """
            ).replace("NAME", node_js)

            page = view.page()

            def _cb(res):
                # —— Python 侧详细调试输出 —— #
                print("[highlight] ◀ JS 回调结果：", res)
                try:
                    if isinstance(res, dict):
                        dbg = res.get("dbg") or []
                        for i, line in enumerate(dbg):
                            print(f"[highlight][JS#{i:02d}] {line}")
                        status = res.get("status")
                        reason = res.get("reason")
                        matched = res.get("matched")
                    else:
                        # 兼容字符串返回
                        dbg, status, reason, matched = [], str(res), None, None
                except Exception as e:
                    print("[highlight] ⚠ 解析 JS 回调异常：", e)
                    dbg, status, reason, matched = [], "parse-error", None, None
                stats = getattr(self, "results_stats", None)
                if stats is not None:
                    if status == "ok":
                        stats.setText(f"Node located (id={matched}, reason={reason}).")
                    elif status in (
                    "no-window", "no-network", "no-network-body", "no-network-data", "no-nodes", "no-getIds",
                    "ids-error", "not-ready"):
                        stats.setText(f"Graph view is not ready or data is unavailable ({status}).")
                    elif status == "not-found":
                        stats.setText("No matching node found. Please check whether id, label, or title matches the search term.")
                    elif status and status.startswith("error"):
                        stats.setText(f"Locate error: {status}")
                    else:
                        stats.setText(f"Locate result: {status}")

            page.runJavaScript(js_code, _cb)

        except Exception as e:
            print("图形高亮失败:", e)

    def highlight_relationship_in_graph(self, source, target):
        """在图中高亮显示关系"""
        if hasattr(self.parent_window, 'graph_view') and hasattr(self.parent_window, 'current_mode'):
            if self.parent_window.current_mode == "graph":
                js_code = f"""
                (function() {{
                    var sourceId = '{source}';
                    var targetId = '{target}';
                    
                    if (typeof network !== 'undefined' && network !== null) {{
                        try {{
                            var nodeIds = nodes.getIds();
                            var validNodes = [];
                            
                            // 检查源节点和目标节点是否存在
                            if (nodeIds.includes(sourceId)) {{
                                validNodes.push(sourceId);
                            }}
                            if (nodeIds.includes(targetId)) {{
                                validNodes.push(targetId);
                            }}
                            
                            if (validNodes.length > 0) {{
                                // 选中相关节点
                                network.selectNodes(validNodes);
                                
                                // 聚焦到这些节点
                                network.fit({{
                                    nodes: validNodes,
                                    animation: true
                                }});
                                
                                // 更新状态
                                updateStatus('Relationship located: {source} -> {target}');
                                
                                // 3秒后取消选择
                                setTimeout(function() {{
                                    if (network) {{
                                        network.unselectAll();
                                    }}
                                }}, 3000);
                                
                                console.log('Relationship located:', sourceId, '->', targetId);
                            }} else {{
                                console.log('Relationship nodes do not exist');
                                updateStatus('Relationship nodes do not exist');
                            }}
                        }} catch(e) {{
                            console.error('Relationship locate failed:', e);
                            updateStatus('Locate failed: ' + e.message);
                        }}
                    }} else {{
                        console.log('Network object is not initialized');
                        updateStatus('Graph view is not ready');
                    }}
                }})();
                """
                try:
                    self.parent_window.graph_view.page().runJavaScript(js_code)
                except Exception as e:
                    print(f"关系高亮失败: {e}")

    def clear_search(self):
        """清空搜索"""
        self.search_input.clear()
        self.results_list.clear()
        self.results_stats.setText("Ready to search")
        self.locate_button.setEnabled(False)


class Plugin(QObject):
    """知识图谱搜索插件"""

    def __init__(self, graph_manager):
        super().__init__()
        self.graph_manager = graph_manager
        self.name = "Knowledge Graph Search Plugin"
        self.search_dialog = None

    def run(self, parent=None):
        """运行插件 - 显示搜索对话框"""
        try:
            # 创建并显示搜索对话框
            self.search_dialog = SearchDialog(self.graph_manager,parent=parent)
            self.search_dialog.show()

            return "Search plugin started and the search window is open."

        except Exception as e:
            return f"Search plugin failed to start: {str(e)}"

