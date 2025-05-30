#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块

实现应用程序的主界面，包括：
- 菜单栏（导入/导出功能）
- 左侧文件列表面板
- 右侧模式选择面板
- 中央绘图工作区
"""

import os
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QMenuBar, QMenu, QStatusBar, QMessageBox,
    QFileDialog, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QAction, QIcon, QDragEnterEvent, QDropEvent

from .left_panel import LeftPanel
from .right_panel import RightPanel  
from .plot_widget import PlotWidget
from component.StokesParameters import StokesParameters


class DataProcessor(QThread):
    """数据处理线程"""
    finished = Signal(bool, str)  # 处理完成信号(成功/失败, 消息)
    progress = Signal(int)  # 进度信号
    
    def __init__(self, file_path: str, stokes_converter: StokesParameters):
        super().__init__()
        self.file_path = file_path
        self.stokes_converter = stokes_converter
        
    def run(self):
        """在后台线程中处理数据"""
        try:
            self.progress.emit(25)
            
            # 加载数据
            success = self.stokes_converter.load_data(self.file_path)
            if not success:
                # 检查是否为编码问题
                if self._is_encoding_error():
                    self.finished.emit(False, 
                        "文件编码问题：无法识别文件编码格式。\n\n"
                        "解决方案：\n"
                        "1. 尝试用记事本打开文件，另存为UTF-8编码\n"
                        "2. 检查文件是否为纯文本格式\n"
                        "3. 确认文件不是二进制格式\n"
                        "4. 支持的编码格式：UTF-8, GBK, GB2312, Latin-1")
                else:
                    self.finished.emit(False, "数据文件加载失败：文件格式或内容错误")
                return
                
            self.progress.emit(50)
            
            # 转换为斯托克斯参数
            results = self.stokes_converter.convert_to_stokes()
            if results is None:
                self.finished.emit(False, "斯托克斯参数转换失败")
                return
                
            self.progress.emit(100)
            self.finished.emit(True, f"成功处理 {len(results)} 个数据点")
            
        except Exception as e:
            self.finished.emit(False, f"处理过程中发生错误: {str(e)}")
            
    def _is_encoding_error(self) -> bool:
        """检查是否为编码错误"""
        try:
            with open(self.file_path, 'rb') as f:
                raw_data = f.read(100)  # 只读取前100字节检查
            
            # 检查常见的编码错误标志
            if b'\xff\xfe' in raw_data or b'\xfe\xff' in raw_data:
                return True  # UTF-16 BOM
            if b'\xff' in raw_data[:1]:
                return True  # 可能的二进制文件
            
            return False
        except:
            return True


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.stokes_converter = StokesParameters()
        self.current_file_path = None
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("偏振光参数转换器 v1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # 启用拖拽功能
        self.setAcceptDrops(True)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建中央部件
        self.create_central_widget()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 导出数据动作
        export_stokes_action = QAction("导出斯托克斯参数(&S)", self)
        export_stokes_action.setShortcut("Ctrl+S")
        export_stokes_action.setStatusTip("导出斯托克斯参数到CSV文件")
        export_stokes_action.triggered.connect(self.export_stokes_data)
        file_menu.addAction(export_stokes_action)
        
        export_plot_action = QAction("导出图表(&P)", self)
        export_plot_action.setShortcut("Ctrl+P")
        export_plot_action.setStatusTip("导出当前图表为图片")
        export_plot_action.triggered.connect(self.export_plot)
        file_menu.addAction(export_plot_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于偏振光参数转换器")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def create_central_widget(self):
        """创建中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建分割器
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧面板（文件列表）
        self.left_panel = LeftPanel()
        self.left_panel.setFixedWidth(250)
        
        # 创建中央分割器（绘图区域和右侧面板）
        center_splitter = QSplitter(Qt.Horizontal)
        
        # 创建绘图部件
        self.plot_widget = PlotWidget()
        
        # 创建右侧面板（模式选择）
        self.right_panel = RightPanel()
        self.right_panel.setFixedWidth(200)
        
        # 添加到分割器
        center_splitter.addWidget(self.plot_widget)
        center_splitter.addWidget(self.right_panel)
        center_splitter.setSizes([800, 200])
        
        main_splitter.addWidget(self.left_panel)
        main_splitter.addWidget(center_splitter)
        main_splitter.setSizes([250, 1000])
        
        main_layout.addWidget(main_splitter)
        
    def setup_connections(self):
        """设置信号连接"""
        # 左侧面板文件选择和导入
        self.left_panel.file_selected.connect(self.on_file_selected)
        self.left_panel.files_imported.connect(self.on_files_imported)
        
        # 右侧面板模式切换
        self.right_panel.mode_changed.connect(self.on_mode_changed)
        
        # 右侧面板动画设置变化
        self.right_panel.animation_settings_changed.connect(self.on_animation_settings_changed)
        
    def on_files_imported(self, file_paths: list):
        """处理文件导入事件"""
        count = len(file_paths)
        self.status_bar.showMessage(f"成功导入 {count} 个文件")
        
    def on_file_selected(self, file_path: str):
        """处理文件选择事件"""
        if not file_path or not os.path.exists(file_path):
            self.status_bar.showMessage("文件不存在或无法访问")
            return
            
        self.current_file_path = file_path
        
        # 在后台线程中处理数据
        self.process_data_file(file_path)
        
    def process_data_file(self, file_path: str):
        """在后台处理数据文件"""
        self.status_bar.showMessage(f"正在处理文件: {os.path.basename(file_path)}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 创建处理线程
        self.data_processor = DataProcessor(file_path, self.stokes_converter)
        self.data_processor.finished.connect(self.on_data_processed)
        self.data_processor.progress.connect(self.progress_bar.setValue)
        self.data_processor.start()
        
    def on_data_processed(self, success: bool, message: str):
        """处理数据完成回调"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_bar.showMessage(message)
            # 触发图表更新
            current_mode = self.right_panel.get_current_mode()
            self.update_plot(current_mode)
        else:
            self.status_bar.showMessage(f"处理失败: {message}")
            
            # 如果是编码问题，显示详细的帮助信息
            if "文件编码问题" in message:
                self.show_encoding_help(message)
            else:
                QMessageBox.warning(self, "处理失败", message)
                
    def on_mode_changed(self, mode: str):
        """处理显示模式切换"""
        self.update_plot(mode)
        
    def on_animation_settings_changed(self, settings: dict):
        """处理动画设置变化"""
        # 如果当前是动画模式，需要更新显示
        current_mode = self.right_panel.get_current_mode()
        if current_mode == "动画模式":
            self.update_plot(current_mode, settings)
        
    def update_plot(self, mode: str, animation_settings: dict = None):
        """更新图表显示"""
        if self.stokes_converter.stokes_results is None:
            self.plot_widget.clear_plot()
            return
            
        # 获取动画设置，如果没有提供则从右侧面板获取
        if animation_settings is None:
            animation_settings = self.right_panel.get_animation_settings()
            
        self.plot_widget.update_plot(mode, self.stokes_converter.stokes_results, animation_settings)
        self.status_bar.showMessage(f"当前模式: {mode}")
        
    def export_stokes_data(self):
        """导出斯托克斯参数数据"""
        if self.stokes_converter.stokes_results is None:
            QMessageBox.warning(self, "导出失败", "没有可导出的数据")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存斯托克斯参数数据",
            "stokes_results.csv",
            "CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if file_path:
            success = self.stokes_converter.save_results(file_path, include_properties=True)
            if success:
                self.status_bar.showMessage(f"数据已保存到: {file_path}")
                QMessageBox.information(self, "导出成功", f"数据已保存到:\n{file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "保存文件时发生错误")
                
    def export_plot(self):
        """导出当前图表"""
        if not self.plot_widget.has_plot():
            QMessageBox.warning(self, "导出失败", "没有可导出的图表")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存图表",
            "plot.png",
            "PNG图片 (*.png);;JPEG图片 (*.jpg);;PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        
        if file_path:
            success = self.plot_widget.save_plot(file_path)
            if success:
                self.status_bar.showMessage(f"图表已保存到: {file_path}")
                QMessageBox.information(self, "导出成功", f"图表已保存到:\n{file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "保存图表时发生错误")
                
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于偏振光参数转换器",
            """
            <h3>偏振光参数转换器 v1.0</h3>
            <p>用于将偏振分析仪导出的光学参数转换为斯托克斯参数的工具。</p>
            
            <p><b>主要功能：</b></p>
            <ul>
            <li>导入偏振分析仪数据文件</li>
            <li>转换为斯托克斯参数 (S0, S1, S2, S3)</li>
            <li>多种可视化模式显示</li>
            <li>数据表格查看</li>
            <li>庞加莱球面显示</li>
            <li>参数动画和趋势分析</li>
            </ul>

            <p>直接从偏振分析仪导出数据文件不能直接导入，需要先打开复制，然后粘贴到一个新的txt文件中。</p>
            """
        )
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            # 检查是否包含支持的文件类型
            urls = event.mimeData().urls()
            valid_files = []
            
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    if file_ext in ['.txt', '.csv', '.dat']:
                        valid_files.append(file_path)
            
            if valid_files:
                event.acceptProposedAction()
                self.status_bar.showMessage(f"准备导入 {len(valid_files)} 个数据文件")
            else:
                event.ignore()
                self.status_bar.showMessage("只支持 .txt, .csv, .dat 格式的数据文件")
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self.status_bar.showMessage("就绪")
        
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid_files = []
            invalid_files = []
            
            # 分析拖入的文件
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_ext = os.path.splitext(file_path)[1].lower()
                    
                    if file_ext in ['.txt', '.csv', '.dat']:
                        if os.path.exists(file_path):
                            valid_files.append(file_path)
                        else:
                            invalid_files.append(f"{os.path.basename(file_path)} (文件不存在)")
                    else:
                        invalid_files.append(f"{os.path.basename(file_path)} (格式不支持)")
            
            # 处理有效文件
            if valid_files:
                # 将文件添加到左侧面板
                imported_files = self.left_panel.get_imported_files()
                new_files = []
                
                for file_path in valid_files:
                    if file_path not in imported_files:
                        new_files.append(file_path)
                        self.left_panel.imported_files.append(file_path)
                
                if new_files:
                    self.left_panel.update_file_list()
                    self.left_panel.files_imported.emit(new_files)
                    
                    # 显示成功消息
                    count = len(new_files)
                    duplicate_count = len(valid_files) - len(new_files)
                    
                    if duplicate_count > 0:
                        message = f"成功导入 {count} 个新文件，{duplicate_count} 个文件已存在"
                    else:
                        message = f"成功导入 {count} 个文件"
                        
                    self.status_bar.showMessage(message)
                    
                    # 如果有无效文件，显示警告
                    if invalid_files:
                        QMessageBox.warning(
                            self,
                            "部分文件导入失败",
                            f"以下文件无法导入：\n" + "\n".join(invalid_files[:5]) + 
                            (f"\n... 还有 {len(invalid_files)-5} 个文件" if len(invalid_files) > 5 else "")
                        )
                else:
                    self.status_bar.showMessage("所有文件已经在列表中")
                    
            else:
                # 没有有效文件
                if invalid_files:
                    QMessageBox.warning(
                        self,
                        "导入失败",
                        f"无法导入文件：\n" + "\n".join(invalid_files[:5]) + 
                        (f"\n... 还有 {len(invalid_files)-5} 个文件" if len(invalid_files) > 5 else "") +
                        "\n\n支持的格式：.txt, .csv, .dat"
                    )
                else:
                    self.status_bar.showMessage("没有找到支持的数据文件")
            
            event.acceptProposedAction()
        else:
            event.ignore()
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 可以在这里添加保存设置等操作
        event.accept()
        
    def show_encoding_help(self, error_message: str):
        """显示编码问题的详细帮助"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("文件编码问题")
        msg_box.setText("文件编码识别失败")
        msg_box.setDetailedText(error_message)
        
        # 添加自定义按钮
        convert_button = msg_box.addButton("尝试转换编码", QMessageBox.ActionRole)
        retry_button = msg_box.addButton("重新选择文件", QMessageBox.ActionRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.RejectRole)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == convert_button:
            self.try_convert_file_encoding()
        elif msg_box.clickedButton() == retry_button:
            self.left_panel.import_files()
            
    def try_convert_file_encoding(self):
        """尝试转换文件编码"""
        if not self.current_file_path:
            return
            
        try:
            # 尝试不同编码读取文件
            encodings_to_try = ['gbk', 'gb2312', 'latin-1', 'cp1252']
            
            for encoding in encodings_to_try:
                try:
                    with open(self.current_file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    
                    # 成功读取，询问是否保存为UTF-8
                    reply = QMessageBox.question(
                        self,
                        "编码转换",
                        f"成功使用 {encoding} 编码读取文件。\n"
                        f"是否将文件转换为UTF-8编码并保存？\n\n"
                        f"原文件将被备份为 .bak 格式。",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        # 备份原文件
                        import shutil
                        backup_path = self.current_file_path + '.bak'
                        shutil.copy2(self.current_file_path, backup_path)
                        
                        # 保存为UTF-8编码
                        with open(self.current_file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        QMessageBox.information(
                            self,
                            "转换成功", 
                            f"文件已成功转换为UTF-8编码。\n"
                            f"原文件已备份为：{backup_path}\n\n"
                            f"现在可以重新加载文件。"
                        )
                        
                        # 重新处理文件
                        self.process_data_file(self.current_file_path)
                        return
                    else:
                        return
                        
                except UnicodeDecodeError:
                    continue
                    
            # 所有编码都失败
            QMessageBox.critical(
                self,
                "转换失败",
                "无法识别文件编码格式。\n\n"
                "请尝试以下解决方案：\n"
                "1. 使用文本编辑器手动转换为UTF-8编码\n"
                "2. 检查文件是否为纯文本格式\n"
                "3. 确认文件不是损坏的二进制文件"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "转换错误",
                f"文件编码转换过程中发生错误：\n{str(e)}"
            ) 