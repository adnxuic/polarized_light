"""
斯托克斯参数转换模块

该模块用于将偏振分析仪导出的光学参数转换为斯托克斯参数。
斯托克斯参数(S0, S1, S2, S3)完整描述光的偏振状态。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import os


class StokesParameters:
    """
    斯托克斯参数转换类
    
    将偏振分析仪的测量参数(PER, DOP, 方位角等)转换为斯托克斯参数
    """
    
    def __init__(self):
        """初始化斯托克斯参数转换器"""
        self.data = None
        self.stokes_results = None
        
    def load_data(self, file_path: str) -> bool:
        """
        加载偏振分析仪导出的数据文件
        
        Args:
            file_path: 数据文件路径
            
        Returns:
            bool: 加载是否成功
        """
        # 常见的编码格式列表
        encodings = ['utf-8', 'gbk', 'utf-16le', 'gb2312', 'latin-1', 'cp1252', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                print(f"尝试使用 {encoding} 编码读取文件...")
                # 读取数据文件，跳过前两行标题
                self.data = pd.read_csv(file_path, sep='\t', skiprows=2, encoding=encoding)
                print(f"成功加载数据文件: {file_path} (编码: {encoding})")
                print(f"数据行数: {len(self.data)}")
                print(f"数据列: {list(self.data.columns)}")
                return True
            except UnicodeDecodeError:
                print(f"编码 {encoding} 无法解码文件，尝试下一个编码...")
                continue
            except Exception as e:
                print(f"使用编码 {encoding} 读取文件失败: {e}")
                continue
        
        # 如果所有编码都失败，尝试以二进制方式检测文件类型
        try:
            print("尝试自动检测文件编码...")
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                
            # # 检查是否为二进制文件
            # if b'\x00' in raw_data:
            #     print("错误: 文件似乎是二进制文件，不支持此格式")
            #     return False
                
            # 尝试使用chardet进行编码检测（如果可用）
            try:
                import chardet
                detected = chardet.detect(raw_data)
                detected_encoding = detected['encoding']
                confidence = detected['confidence']
                
                if detected_encoding and confidence > 0.7:
                    print(f"检测到编码: {detected_encoding} (置信度: {confidence:.2f})")
                    try:
                        self.data = pd.read_csv(file_path, sep='\t', skiprows=2, encoding=detected_encoding)
                        print(f"成功加载数据文件: {file_path} (编码: {detected_encoding})")
                        print(f"数据行数: {len(self.data)}")
                        return True
                    except Exception as e:
                        print(f"使用检测到的编码 {detected_encoding} 读取失败: {e}")
                        
            except ImportError:
                print("chardet库未安装，无法进行编码检测")
                
        except Exception as e:
            print(f"文件编码检测失败: {e}")
        
        print(f"错误: 无法读取文件 {file_path}，请检查文件格式和编码")
        print("支持的编码格式: UTF-8, GBK, GB2312, Latin-1, CP1252")
        print("请确保文件是文本格式且包含正确的数据列")
        return False
    
    def convert_to_stokes(self) -> Optional[pd.DataFrame]:
        """
        将光学参数转换为斯托克斯参数
        
        斯托克斯参数计算公式:
        - S0 = I (总强度)
        - S1 = I * DOP * cos(2*φ) * cos(2*χ)
        - S2 = I * DOP * sin(2*φ) * cos(2*χ)  
        - S3 = I * DOP * sin(2*χ)
        
        其中：
        - I: 强度
        - DOP: 偏振度 (0-1)
        - φ: 方位角 (弧度)
        - χ: 椭圆度角，通过PER计算
        
        Returns:
            pd.DataFrame: 包含斯托克斯参数的数据框
        """
        if self.data is None:
            print("错误: 未加载数据文件")
            return None
            
        try:
            # 提取需要的参数
            intensity = self.data['Intensity [%]'].values / 100.0  # 归一化到0-1
            dop = self.data['DOP [%]'].values / 100.0  # 转换为0-1范围
            try:
                azimuth_deg = self.data['φ [°]'].values  # 方位角(度)
            except:
                #读取第5列
                azimuth_deg = self.data.iloc[:, 4].values
            per_db = self.data['PER [dB]'].values  # 消光比(dB)
            
            # 转换角度为弧度
            azimuth_rad = np.deg2rad(azimuth_deg)
            
            # 从PER计算椭圆度角
            # PER = 10*log10(a²/b²), 其中a和b是椭圆的长短轴
            per_linear = 10**(per_db / 10.0)  # 将dB转换为线性比值
            ellipticity_angle = 0.5 * np.arctan(2.0 / np.sqrt(per_linear - 1))
            
            # 计算斯托克斯参数
            # S0: 总强度
            S0 = intensity
            
            # S1: 水平-垂直线性偏振分量
            S1 = intensity * dop * np.cos(2 * azimuth_rad) * np.cos(2 * ellipticity_angle)
            
            # S2: 45°-135°线性偏振分量  
            S2 = intensity * dop * np.sin(2 * azimuth_rad) * np.cos(2 * ellipticity_angle)
            
            # S3: 右圆-左圆偏振分量
            S3 = intensity * dop * np.sin(2 * ellipticity_angle)
            
            # 创建结果数据框
            results = pd.DataFrame({
                'No': self.data['No'],
                'S0': S0,
                'S1': S1,
                'S2': S2,
                'S3': S3,
                'DOP_calculated': np.sqrt(S1**2 + S2**2 + S3**2) / S0,  # 验证DOP
                'Azimuth_original [°]': azimuth_deg,
                'PER_original [dB]': per_db,
                'Intensity_original [%]': self.data['Intensity [%]'],
            })
            
            self.stokes_results = results
            print("斯托克斯参数转换完成")
            return results
            
        except Exception as e:
            print(f"斯托克斯参数转换失败: {e}")
            return None
    
    def get_polarization_properties(self) -> Optional[pd.DataFrame]:
        """
        计算偏振特性参数
        
        Returns:
            pd.DataFrame: 包含偏振特性的数据框
        """
        if self.stokes_results is None:
            print("错误: 未计算斯托克斯参数")
            return None
            
        try:
            S0 = self.stokes_results['S0'].values
            S1 = self.stokes_results['S1'].values
            S2 = self.stokes_results['S2'].values
            S3 = self.stokes_results['S3'].values
            
            # 计算偏振度
            dop_calc = np.sqrt(S1**2 + S2**2 + S3**2) / S0
            
            # 计算方位角 (度)
            azimuth_calc = 0.5 * np.rad2deg(np.arctan2(S2, S1))
            
            # 计算椭圆度角 (度)
            ellipticity_calc = 0.5 * np.rad2deg(np.arcsin(S3 / (S0 * dop_calc + 1e-10)))
            
            # 计算椭圆度
            ellipticity_ratio = np.tan(np.deg2rad(ellipticity_calc))
            
            properties = pd.DataFrame({
                'No': self.stokes_results['No'],
                'DOP [%]': dop_calc * 100,
                'Azimuth_calculated [°]': azimuth_calc,
                'Ellipticity_angle [°]': ellipticity_calc,
                'Ellipticity_ratio': ellipticity_ratio,
                'Linear_DOP [%]': np.sqrt(S1**2 + S2**2) / S0 * 100,
                'Circular_DOP [%]': np.abs(S3) / S0 * 100
            })
            
            return properties
            
        except Exception as e:
            print(f"计算偏振特性失败: {e}")
            return None
    
    def save_results(self, output_file: str, include_properties: bool = True) -> bool:
        """
        保存转换结果到文件
        
        Args:
            output_file: 输出文件路径
            include_properties: 是否包含偏振特性
            
        Returns:
            bool: 保存是否成功
        """
        if self.stokes_results is None:
            print("错误: 无转换结果可保存")
            return False
            
        try:
            # 准备保存的数据
            save_data = self.stokes_results.copy()
            
            if include_properties:
                properties = self.get_polarization_properties()
                if properties is not None:
                    # 合并偏振特性数据
                    save_data = save_data.merge(properties, on='No', how='left')
            
            # 保存到CSV文件
            save_data.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"结果已保存到: {output_file}")
            return True
            
        except Exception as e:
            print(f"保存结果失败: {e}")
            return False
    
    def print_summary(self) -> None:
        """打印转换结果摘要"""
        if self.stokes_results is None:
            print("错误: 无转换结果")
            return
            
        print("\n=== 斯托克斯参数转换结果摘要 ===")
        print(f"数据点数量: {len(self.stokes_results)}")
        
        # 统计信息
        print("\n斯托克斯参数统计:")
        for param in ['S0', 'S1', 'S2', 'S3']:
            values = self.stokes_results[param].values
            print(f"{param}: 平均值={np.mean(values):.4f}, "
                  f"标准差={np.std(values):.4f}, "
                  f"范围=[{np.min(values):.4f}, {np.max(values):.4f}]")
        
        # DOP比较
        print(f"\nDOP验证:")
        original_dop = self.data['DOP [%]'].values / 100.0
        calculated_dop = self.stokes_results['DOP_calculated'].values
        dop_diff = np.abs(original_dop - calculated_dop)
        print(f"原始DOP vs 计算DOP的平均差异: {np.mean(dop_diff):.6f}")
        print(f"最大差异: {np.max(dop_diff):.6f}")


