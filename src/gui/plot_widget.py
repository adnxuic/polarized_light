#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘图部件模块

实现多种可视化模式：
- 数据表格显示
- 庞加莱球面显示  
- 动画模式（S2/S3极坐标动画）
- 参量趋势图（S1, S2, S3随时间变化）
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QTabWidget, QLabel, QSizePolicy,
    QPushButton, QSlider, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D

# 优化中文字体配置
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.autolayout'] = True


class PlotWidget(QWidget):
    """绘图部件"""
    
    def __init__(self):
        super().__init__()
        self.current_data = None
        self.current_mode = "数据模式"
        self.animation = None
        self.animation_index = 0
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 数据表格标签页
        self.create_data_table_tab()
        
        # 图表标签页
        self.create_plot_tab()
        
        layout.addWidget(self.tab_widget)
        
    def create_data_table_tab(self):
        """创建数据表格标签页"""
        table_widget = QWidget()
        layout = QVBoxLayout(table_widget)
        
        # 标题
        title_label = QLabel("斯托克斯参数数据表格")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 表格
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.data_table)
        
        self.tab_widget.addTab(table_widget, "数据表格")
        
    def create_plot_tab(self):
        """创建图表标签页"""
        plot_widget = QWidget()
        layout = QVBoxLayout(plot_widget)
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout.addWidget(self.canvas)
        
        # 动画控制面板
        self.create_animation_controls(layout)
        
        self.tab_widget.addTab(plot_widget, "图表显示")
        
    def create_animation_controls(self, parent_layout):
        """创建动画控制面板"""
        self.control_widget = QWidget()
        control_layout = QHBoxLayout(self.control_widget)
        
        # 播放/暂停按钮
        self.play_button = QPushButton("播放")
        self.play_button.clicked.connect(self.toggle_animation)
        self.play_button.setEnabled(False)
        
        # 重置按钮
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_animation)
        self.reset_button.setEnabled(False)
        
        # 进度滑块
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.valueChanged.connect(self.on_progress_changed)
        
        # 进度标签
        self.progress_label = QLabel("0/0")
        
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.reset_button)
        control_layout.addWidget(QLabel("进度:"))
        control_layout.addWidget(self.progress_slider)
        control_layout.addWidget(self.progress_label)
        control_layout.addStretch()
        
        # 默认隐藏动画控制面板
        self.control_widget.setVisible(False)
        parent_layout.addWidget(self.control_widget)
        
    def update_plot(self, mode: str, data: pd.DataFrame, animation_settings: dict = None):
        """更新图表显示"""
        self.current_data = data
        self.current_mode = mode
        
        # 清除之前的图表
        self.figure.clear()
        
        # 根据模式显示不同内容
        if mode == "数据模式":
            self.show_data_table(data)
            self.tab_widget.setCurrentIndex(0)  # 切换到数据表格标签页
            self.disable_animation_controls()  # 禁用动画控制
        else:
            self.tab_widget.setCurrentIndex(1)  # 切换到图表标签页
            
            if mode == "庞加莱球模式":
                self.plot_poincare_sphere(data)
                self.disable_animation_controls()  # 禁用动画控制
            elif mode == "动画模式":
                self.plot_animation_mode(data, animation_settings)
                # 动画模式会在plot_animation_mode内部启用控制
            elif mode == "参量S1模式":
                self.plot_parameter_trend(data, 'S1')
                self.disable_animation_controls()  # 禁用动画控制
            elif mode == "参量S2模式":
                self.plot_parameter_trend(data, 'S2')
                self.disable_animation_controls()  # 禁用动画控制
            elif mode == "参量S3模式":
                self.plot_parameter_trend(data, 'S3')
                self.disable_animation_controls()  # 禁用动画控制
                
        self.canvas.draw()
        
    def show_data_table(self, data: pd.DataFrame):
        """显示数据表格"""
        if data is None or data.empty:
            self.data_table.clear()
            return
            
        # 设置表格尺寸
        self.data_table.setRowCount(len(data))
        self.data_table.setColumnCount(len(data.columns))
        self.data_table.setHorizontalHeaderLabels(data.columns.tolist())
        
        # 填充数据
        for i, row in data.iterrows():
            for j, value in enumerate(row):
                if isinstance(value, (int, float)):
                    item = QTableWidgetItem(f"{value:.6f}")
                else:
                    item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.data_table.setItem(i, j, item)
                
        # 调整列宽
        self.data_table.resizeColumnsToContents()
        
    def plot_poincare_sphere(self, data: pd.DataFrame):
        """绘制庞加莱球"""
        if data is None or data.empty:
            return
            
        # 创建3D子图
        ax = self.figure.add_subplot(111, projection='3d')
        
        # 获取斯托克斯参数
        S0 = data['S0'].values
        S1 = data['S1'].values
        S2 = data['S2'].values
        S3 = data['S3'].values
        
        # 归一化斯托克斯参数（投影到庞加莱球面）
        S1_norm = S1 / S0
        S2_norm = S2 / S0  
        S3_norm = S3 / S0
        
        # 绘制庞加莱球面
        u = np.linspace(0, 2 * np.pi, 50)
        v = np.linspace(0, np.pi, 50)
        x_sphere = np.outer(np.cos(u), np.sin(v))
        y_sphere = np.outer(np.sin(u), np.sin(v))
        z_sphere = np.outer(np.ones(np.size(u)), np.cos(v))
        
        ax.plot_surface(x_sphere, y_sphere, z_sphere, alpha=0.1, color='lightblue')
        
        # 绘制坐标轴
        ax.plot([-1.2, 1.2], [0, 0], [0, 0], 'k-', alpha=0.3)
        ax.plot([0, 0], [-1.2, 1.2], [0, 0], 'k-', alpha=0.3)
        ax.plot([0, 0], [0, 0], [-1.2, 1.2], 'k-', alpha=0.3)
        
        # 绘制斯托克斯参数点
        scatter = ax.scatter(S1_norm, S2_norm, S3_norm, 
                           c=range(len(S1_norm)), cmap='viridis', 
                           s=30, alpha=0.7)
        
        # 设置标签和标题
        ax.set_xlabel('S1/S0 (水平-垂直线偏振)')
        ax.set_ylabel('S2/S0 (±45°线偏振)')
        ax.set_zlabel('S3/S0 (右-左圆偏振)')
        ax.set_title('庞加莱球面上的偏振状态')
        
        # 设置坐标轴范围
        ax.set_xlim([-1.2, 1.2])
        ax.set_ylim([-1.2, 1.2])
        ax.set_zlim([-1.2, 1.2])
        
        # 添加颜色条
        cbar = self.figure.colorbar(scatter, ax=ax, shrink=0.8)
        cbar.set_label('数据点序号')
        
    def plot_animation_mode(self, data: pd.DataFrame, animation_settings: dict = None):
        """绘制动画模式（S1/S2极坐标）"""
        if data is None or data.empty:
            return
            
        # 获取动画设置，默认不显示轨迹
        if animation_settings is None:
            animation_settings = {'show_trail': False}
        
        show_trail = animation_settings.get('show_trail', False)
            
        # 创建极坐标子图
        ax = self.figure.add_subplot(111, projection='polar')
        
        # 获取数据
        S1 = data['S1'].values
        S2 = data['S2'].values
        
        # 转换为极坐标
        r = np.sqrt(S1**2 + S2**2)
        theta = np.arctan2(S2, S1)
        
        # 根据设置决定是否绘制静态轨迹
        if show_trail:
            ax.plot(theta, r, 'b-', alpha=0.3, linewidth=1, label='轨迹')
        
        # 绘制数据点
        scatter = ax.scatter(theta, r, c=range(len(theta)), 
                           cmap='viridis', s=20, alpha=0.7)
        
        # 初始化动画点
        self.animation_point, = ax.plot([], [], 'ro', markersize=8, label='当前点')
        
        ax.set_title('S1-S2 极坐标动画')
        ax.legend()
        
        # 存储动画数据
        self.animation_theta = theta
        self.animation_r = r
        self.current_ax = ax  # 保存当前坐标轴
        
        # 设置动画控制
        self.setup_animation_controls(len(data))
        
        # 重置动画状态
        self.animation = None
        self.animation_index = 0
        
    def plot_parameter_trend(self, data: pd.DataFrame, parameter: str):
        """绘制参数趋势图"""
        if data is None or data.empty:
            return
            
        ax = self.figure.add_subplot(111)
        
        # 获取数据
        x = data['No'].values if 'No' in data.columns else range(len(data))
        
        if parameter in data.columns:
            y = data[parameter].values
        else:
            ax.text(0.5, 0.5, f'参数 {parameter} 不存在', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            return
            
        # 绘制趋势线
        ax.plot(x, y, 'b-', linewidth=2, label=f'{parameter} 趋势')
        ax.scatter(x, y, c='red', s=30, alpha=0.7, zorder=5)
        
        # 添加统计信息
        mean_val = np.mean(y)
        std_val = np.std(y)
        ax.axhline(y=mean_val, color='green', linestyle='--', alpha=0.7, 
                  label=f'平均值: {mean_val:.4f}')
        ax.axhline(y=mean_val + std_val, color='orange', linestyle=':', alpha=0.7,
                  label=f'平均值+标准差: {mean_val + std_val:.4f}')
        ax.axhline(y=mean_val - std_val, color='orange', linestyle=':', alpha=0.7,
                  label=f'平均值-标准差: {mean_val - std_val:.4f}')
        
        # 设置标签和标题
        ax.set_xlabel('数据点索引')
        ax.set_ylabel(f'{parameter} 值')
        ax.set_title(f'{parameter} 参数随时间变化')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 添加数值统计文本
        stats_text = f'统计信息:\n'
        stats_text += f'数据点数: {len(y)}\n'
        stats_text += f'最小值: {np.min(y):.6f}\n'
        stats_text += f'最大值: {np.max(y):.6f}\n'
        stats_text += f'平均值: {mean_val:.6f}\n'
        stats_text += f'标准差: {std_val:.6f}'
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', fontsize=9,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
               
    def setup_animation_controls(self, total_frames: int):
        """设置动画控制面板 - 仅设置控制，不自动播放"""
        self.total_frames = total_frames
        self.animation_index = 0
        
        # 启用并显示动画控制面板
        self.enable_animation_controls()
        self.progress_slider.setRange(0, total_frames - 1)
        self.progress_slider.setValue(0)
        self.update_progress_label()
        
        # 确保播放按钮显示为"播放"状态，不自动开始
        
    def start_animation(self):
        """启动动画 - 仅在用户点击播放时调用"""
        # 检查是否有动画数据
        if not hasattr(self, 'animation_theta') or not hasattr(self, 'animation_r'):
            return
            
        theta = self.animation_theta
        r = self.animation_r
                
        def animate(frame):
            # 检查frame是否在有效范围内
            if frame < len(theta):
                self.animation_point.set_data([theta[frame]], [r[frame]])
                self.animation_index = frame
                # 防止递归调用progress_slider的valueChanged信号
                self.progress_slider.blockSignals(True)
                self.progress_slider.setValue(frame)
                self.progress_slider.blockSignals(False)
                self.update_progress_label()
                return self.animation_point,
            else:
                # 动画结束时停止并重置按钮状态
                if self.animation:
                    self.animation.event_source.stop()
                self.play_button.setText("播放")
                return self.animation_point,
            
        # 停止之前的动画
        if self.animation:
            self.animation.event_source.stop()
            
        # 创建新动画 - 确保不循环播放，不自动开始
        self.animation = FuncAnimation(
            self.figure, animate, 
            frames=len(theta),
            interval=100, 
            blit=False, 
            repeat=False  # 明确禁用循环播放
        )
        
        # 刷新画布
        self.canvas.draw()
        
    def toggle_animation(self):
        """切换动画播放/暂停 - 完全手动控制"""
        if self.play_button.text() == "播放":
            # 检查是否有动画数据
            if not hasattr(self, 'animation_theta') or not hasattr(self, 'animation_r'):
                return
                
            # 如果动画已结束，从头开始
            if self.animation_index >= len(self.animation_theta):
                self.animation_index = 0
                self.progress_slider.setValue(0)
                
            # 启动动画
            self.start_animation()
            self.play_button.setText("暂停")
        else:
            # 暂停动画
            if self.animation:
                self.animation.event_source.stop()
            self.play_button.setText("播放")
            
    def reset_animation(self):
        """重置动画"""
        # 停止当前动画
        if self.animation:
            self.animation.event_source.stop()
            self.animation = None
            
        # 重置状态
        self.animation_index = 0
        self.progress_slider.setValue(0)
        self.update_progress_label()
        self.play_button.setText("播放")
        
        # 重置动画点到起始位置
        if (hasattr(self, 'animation_theta') and hasattr(self, 'animation_r') 
            and hasattr(self, 'animation_point')):
            if len(self.animation_theta) > 0:
                self.animation_point.set_data([self.animation_theta[0]], [self.animation_r[0]])
                self.canvas.draw()
        
    def on_progress_changed(self, value):
        """处理进度变化 - 用户手动控制滑块时停止动画"""
        # 如果动画正在播放，停止它
        if self.animation and self.play_button.text() == "暂停":
            self.animation.event_source.stop()
            self.play_button.setText("播放")
            
        self.animation_index = value
        self.update_progress_label()
        
        # 更新动画点位置
        if (hasattr(self, 'animation_theta') and hasattr(self, 'animation_r') 
            and hasattr(self, 'animation_point')):
            if 0 <= value < len(self.animation_theta):
                self.animation_point.set_data([self.animation_theta[value]], [self.animation_r[value]])
                self.canvas.draw()
        
    def update_progress_label(self):
        """更新进度标签"""
        if hasattr(self, 'total_frames'):
            self.progress_label.setText(f"{self.animation_index + 1}/{self.total_frames}")
        else:
            self.progress_label.setText("0/0")
            
    def disable_animation_controls(self):
        """禁用并隐藏动画控制面板"""
        self.play_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.progress_slider.setEnabled(False)
        self.progress_label.setText("0/0")
        self.control_widget.setVisible(False)
        
    def enable_animation_controls(self):
        """启用并显示动画控制面板"""
        self.play_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.progress_slider.setEnabled(True)
        self.control_widget.setVisible(True)
        
    def clear_plot(self):
        """清除图表"""
        self.figure.clear()
        self.canvas.draw()
        
        # 清除数据表格
        self.data_table.clear()
        self.data_table.setRowCount(0)
        self.data_table.setColumnCount(0)
        
        # 禁用并隐藏动画控制
        self.disable_animation_controls()
        
    def has_plot(self) -> bool:
        """检查是否有图表"""
        return self.current_data is not None
        
    def save_plot(self, file_path: str) -> bool:
        """保存图表"""
        try:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"保存图表失败: {e}")
            return False 