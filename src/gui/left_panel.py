#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
左侧面板模块

实现数据文件列表显示和选择功能
"""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QGroupBox, QPushButton, QFileDialog,
    QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
import os


class LeftPanel(QWidget):
    """左侧文件列表面板"""
    
    file_selected = Signal(str)  # 文件选择信号
    files_imported = Signal(list)  # 文件导入信号
    
    def __init__(self):
        super().__init__()
        self.imported_files = []  # 存储已导入的文件路径
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 创建分组框
        group_box = QGroupBox("数据文件")
        group_layout = QVBoxLayout(group_box)
        
        # 标题标签
        title_label = QLabel("数据文件管理:")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # 按钮容器
        button_layout = QHBoxLayout()
        
        # 导入文件按钮
        self.import_btn = QPushButton("导入文件")
        self.import_btn.setToolTip("选择并导入数据文件（支持 .txt, .csv 格式）")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """)
        self.import_btn.clicked.connect(self.import_files)
        
        # 清除列表按钮
        self.clear_btn = QPushButton("清除列表")
        self.clear_btn.setToolTip("清除所有已导入的文件")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #a71e2a;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_files)
        self.clear_btn.setEnabled(False)  # 初始状态禁用
        
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setToolTip("双击选择数据文件进行处理")
        
        # 设置列表样式
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f0f0f0;
                min-height: 200px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e6f3ff;
            }
        """)
        
        # 连接信号
        self.file_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.file_list.currentRowChanged.connect(self.on_selection_changed)
        
        # 状态标签
        self.status_label = QLabel("请点击\"导入文件\"按钮选择数据文件\n或直接拖拽文件到程序窗口")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666; 
                font-style: italic;
                padding: 8px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)  # 启用自动换行
        self.status_label.setMinimumHeight(40)  # 设置最小高度
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # 添加到布局
        group_layout.addWidget(title_label)
        group_layout.addLayout(button_layout)
        group_layout.addWidget(self.file_list)
        group_layout.addWidget(self.status_label)
        
        layout.addWidget(group_box)
        layout.addStretch()  # 添加弹性空间
        
    def import_files(self):
        """导入数据文件"""
        # 打开文件选择对话框
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择数据文件",
            "",
            "数据文件 (*.txt *.csv);;文本文件 (*.txt);;CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if file_paths:
            # 添加新文件到列表（避免重复）
            new_files = []
            for file_path in file_paths:
                if file_path not in self.imported_files:
                    self.imported_files.append(file_path)
                    new_files.append(file_path)
            
            if new_files:
                self.update_file_list()
                self.files_imported.emit(new_files)
                
                # 显示导入成功消息
                count = len(new_files)
                QMessageBox.information(
                    self,
                    "导入成功",
                    f"成功导入 {count} 个文件"
                )
            else:
                QMessageBox.information(
                    self,
                    "提示",
                    "所选文件已经在列表中"
                )
    
    def clear_files(self):
        """清除所有文件"""
        if self.imported_files:
            reply = QMessageBox.question(
                self,
                "确认清除",
                "确定要清除所有已导入的文件吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.imported_files.clear()
                self.update_file_list()
                
    def update_file_list(self):
        """更新文件列表显示"""
        self.file_list.clear()
        
        if not self.imported_files:
            self.status_label.setText("请点击\"导入文件\"按钮选择数据文件\n或直接拖拽文件到程序窗口")
            self.status_label.setVisible(True)
            self.clear_btn.setEnabled(False)
            return
            
        # 隐藏状态标签
        self.status_label.setVisible(False)
        self.clear_btn.setEnabled(True)
        
        # 添加文件到列表
        for file_path in self.imported_files:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setData(Qt.UserRole, file_path)  # 存储完整路径
            item.setToolTip(f"文件: {file_name}\n路径: {file_path}\n双击选择此文件")
            
            # 根据文件扩展名设置不同的显示
            if file_name.endswith('.txt'):
                display_text = f"📄 {file_name}"
            elif file_name.endswith('.csv'):
                display_text = f"📊 {file_name}"
            else:
                display_text = f"📋 {file_name}"
                
            item.setText(display_text)
            self.file_list.addItem(item)
            
        # 更新状态
        count = len(self.imported_files)
        self.status_label.setText(f"已导入 {count} 个数据文件\n请双击文件显示图表或切换数据文件")
        self.status_label.setVisible(True)
        
    def on_item_double_clicked(self, item: QListWidgetItem):
        """处理项目双击事件"""
        if item:
            file_path = item.data(Qt.UserRole)
            if file_path and os.path.exists(file_path):
                self.file_selected.emit(file_path)
            else:
                QMessageBox.warning(
                    self,
                    "文件错误",
                    f"文件不存在或无法访问：\n{file_path}"
                )
                
    def on_selection_changed(self, current_row: int):
        """处理选择变化事件"""
        if current_row >= 0:
            item = self.file_list.item(current_row)
            if item:
                file_path = item.data(Qt.UserRole)
                # 可以在这里添加预览功能
                
    def get_selected_file(self) -> str:
        """获取当前选中的文件路径"""
        current_item = self.file_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole) or ""
        return ""
        
    def select_file(self, file_path: str):
        """程序化选择文件"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item and item.data(Qt.UserRole) == file_path:
                self.file_list.setCurrentItem(item)
                break
                
    def get_imported_files(self) -> List[str]:
        """获取所有已导入的文件路径"""
        return self.imported_files.copy()
        
    def remove_file(self, file_path: str):
        """移除指定文件"""
        if file_path in self.imported_files:
            self.imported_files.remove(file_path)
            self.update_file_list() 