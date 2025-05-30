#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
右侧面板模块

实现显示模式选择功能，包括：
- 数据模式
- 庞加莱球模式  
- 动画模式
- 参量S1模式
- 参量S2模式
- 参量S3模式
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QRadioButton, 
    QGroupBox, QButtonGroup, QSlider, QSpinBox,
    QHBoxLayout, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class RightPanel(QWidget):
    """右侧模式选择面板"""
    
    mode_changed = Signal(str)  # 模式切换信号
    animation_settings_changed = Signal(dict)  # 动画设置变化信号
    
    def __init__(self):
        super().__init__()
        self.current_mode = "数据模式"
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 创建显示模式选择组
        self.create_mode_selection(layout)
        
        # 创建动画控制组
        self.create_animation_controls(layout)
        
        # 添加弹性空间
        layout.addStretch()
        
    def create_mode_selection(self, parent_layout):
        """创建显示模式选择组"""
        group_box = QGroupBox("显示模式")
        layout = QVBoxLayout(group_box)
        
        # 标题
        title_label = QLabel("选择显示模式:")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 创建按钮组
        self.mode_button_group = QButtonGroup()
        
        # 模式选项
        modes = [
            ("数据模式", "显示完整的数据表格"),
            ("庞加莱球模式", "在庞加莱球面上显示斯托克斯参数点"),
            ("动画模式", "显示S1和S2在极坐标系中的动画变化"),
            ("参量S1模式", "显示S1参数随时间的变化趋势"),
            ("参量S2模式", "显示S2参数随时间的变化趋势"),
            ("参量S3模式", "显示S3参数随时间的变化趋势")
        ]
        
        for i, (mode_name, tooltip) in enumerate(modes):
            radio_button = QRadioButton(mode_name)
            radio_button.setToolTip(tooltip)
            
            # 设置样式
            radio_button.setStyleSheet("""
                QRadioButton {
                    padding: 5px;
                    font-size: 11px;
                }
                QRadioButton::indicator {
                    width: 12px;
                    height: 12px;
                }
            """)
            
            self.mode_button_group.addButton(radio_button, i)
            layout.addWidget(radio_button)
            
            # 默认选中第一个
            if i == 0:
                radio_button.setChecked(True)
                
        # 连接信号
        self.mode_button_group.buttonClicked.connect(self.on_mode_changed)
        
        parent_layout.addWidget(group_box)
        
    def create_animation_controls(self, parent_layout):
        """创建动画控制组"""
        group_box = QGroupBox("动画设置")
        layout = QVBoxLayout(group_box)
        
        # 标题
        title_label = QLabel("动画参数:")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 播放速度控制
        speed_layout = QHBoxLayout()
        speed_label = QLabel("播放速度:")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.setToolTip("调整动画播放速度 (1-100)")
        
        self.speed_value_label = QLabel("50")
        self.speed_value_label.setMinimumWidth(30)
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)
        layout.addLayout(speed_layout)
        
        # 帧数控制
        frame_layout = QHBoxLayout()
        frame_label = QLabel("显示帧数:")
        self.frame_spinbox = QSpinBox()
        self.frame_spinbox.setRange(10, 1000)
        self.frame_spinbox.setValue(100)
        self.frame_spinbox.setToolTip("设置动画显示的数据点数量")
        
        frame_layout.addWidget(frame_label)
        frame_layout.addWidget(self.frame_spinbox)
        layout.addLayout(frame_layout)
        
        # 显示轨迹复选框
        self.show_trail_checkbox = QCheckBox("显示轨迹")
        self.show_trail_checkbox.setChecked(False)
        self.show_trail_checkbox.setToolTip("显示参数变化的历史轨迹")
        layout.addWidget(self.show_trail_checkbox)
        
        # 连接信号
        self.speed_slider.valueChanged.connect(self.on_animation_settings_changed)
        self.frame_spinbox.valueChanged.connect(self.on_animation_settings_changed)
        self.show_trail_checkbox.toggled.connect(self.on_animation_settings_changed)
        
        # 速度标签更新
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_value_label.setText(str(v))
        )
        
        parent_layout.addWidget(group_box)
        
    def on_mode_changed(self, button):
        """处理模式切换"""
        mode_name = button.text()
        self.current_mode = mode_name
        self.mode_changed.emit(mode_name)
        
        # 根据模式启用/禁用动画控制
        is_animation_mode = mode_name == "动画模式"
        self.speed_slider.setEnabled(is_animation_mode)
        self.frame_spinbox.setEnabled(is_animation_mode)
        self.show_trail_checkbox.setEnabled(is_animation_mode)
        
    def on_animation_settings_changed(self):
        """处理动画设置变化"""
        settings = {
            'speed': self.speed_slider.value(),
            'frames': self.frame_spinbox.value(),
            'show_trail': self.show_trail_checkbox.isChecked()
        }
        self.animation_settings_changed.emit(settings)
        
    def get_current_mode(self) -> str:
        """获取当前选中的模式"""
        return self.current_mode
        
    def get_animation_settings(self) -> dict:
        """获取动画设置"""
        return {
            'speed': self.speed_slider.value(),
            'frames': self.frame_spinbox.value(),
            'show_trail': self.show_trail_checkbox.isChecked()
        }
        
    def set_mode(self, mode_name: str):
        """程序化设置模式"""
        for button in self.mode_button_group.buttons():
            if button.text() == mode_name:
                button.setChecked(True)
                self.on_mode_changed(button)
                break 