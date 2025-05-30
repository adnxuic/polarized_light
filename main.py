#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
偏振光参数转换GUI应用程序主入口

该程序提供图形用户界面，用于：
- 导入偏振分析仪数据文件
- 转换为斯托克斯参数
- 多种可视化模式显示结果
- 导出处理结果
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MainWindow


def main():
    """主函数"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("偏振光参数转换器")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("偏振光实验室")
    
    # 创建主窗口
    main_window = MainWindow()
    main_window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
