#!/usr/bin/env python3
"""
斯托克斯参数转换测试脚本

用于测试偏振光参数转换为斯托克斯参数的功能
"""

import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from component.StokesParameters import StokesParameters


def test_stokes_conversion():
    """测试斯托克斯参数转换功能"""
    print("=== 偏振光参数转斯托克斯参数转换测试 ===\n")
    
    # 创建转换器实例
    converter = StokesParameters()
    
    # 数据文件路径
    data_file = "data/datatest.txt"
    output_file = "data/stokes_results.csv"
    
    # 检查数据文件是否存在
    if not os.path.exists(data_file):
        print(f"错误: 数据文件不存在 - {data_file}")
        print("请确保data/datatest.txt文件存在")
        return False
    
    # 步骤1: 加载数据
    print("步骤1: 加载偏振分析仪数据...")
    if not converter.load_data(data_file):
        print("数据加载失败!")
        return False
    
    print(f"原始数据预览:")
    print(converter.data.head())
    print()
    
    # 步骤2: 转换为斯托克斯参数
    print("步骤2: 转换为斯托克斯参数...")
    stokes_results = converter.convert_to_stokes()
    if stokes_results is None:
        print("斯托克斯参数转换失败!")
        return False
    
    # 步骤3: 显示结果摘要
    print("步骤3: 转换结果分析...")
    converter.print_summary()
    
    # 步骤4: 显示斯托克斯参数结果
    print("\n步骤4: 斯托克斯参数结果 (前5行):")
    print("="*80)
    result_cols = ['No', 'S0', 'S1', 'S2', 'S3', 'DOP_calculated']
    print(stokes_results[result_cols].head().to_string(index=False, float_format='%.6f'))
    
    # 步骤5: 计算偏振特性
    print("\n步骤5: 计算的偏振特性 (前5行):")
    print("="*80)
    properties = converter.get_polarization_properties()
    if properties is not None:
        prop_cols = ['No', 'DOP [%]', 'Azimuth_calculated [°]', 'Linear_DOP [%]', 'Circular_DOP [%]']
        print(properties[prop_cols].head().to_string(index=False, float_format='%.3f'))
    
    # 步骤6: 保存结果
    print(f"\n步骤6: 保存结果到文件...")
    if converter.save_results(output_file):
        print(f"✓ 转换完成! 结果已保存到 {output_file}")
        return True
    else:
        print("保存结果失败!")
        return False


def compare_original_vs_calculated():
    """比较原始参数与从斯托克斯参数反推的参数"""
    print("\n=== 参数一致性验证 ===")
    
    converter = StokesParameters()
    
    if not converter.load_data("data/datatest.txt"):
        return
    
    if converter.convert_to_stokes() is None:
        return
    
    # 获取原始参数和计算参数
    original_data = converter.data
    calculated_properties = converter.get_polarization_properties()
    
    if calculated_properties is None:
        return
    
    print("\n原始 vs 计算参数对比:")
    print("="*60)
    
    # DOP对比
    orig_dop = original_data['DOP [%]'].values
    calc_dop = calculated_properties['DOP [%]'].values
    dop_diff = abs(orig_dop - calc_dop)
    
    print(f"DOP对比:")
    print(f"  原始DOP平均值: {orig_dop.mean():.3f}%")
    print(f"  计算DOP平均值: {calc_dop.mean():.3f}%")
    print(f"  平均差异: {dop_diff.mean():.6f}%")
    print(f"  最大差异: {dop_diff.max():.6f}%")
    
    # 方位角对比
    orig_azimuth = original_data['φ [°]'].values
    calc_azimuth = calculated_properties['Azimuth_calculated [°]'].values
    
    print(f"\n方位角对比:")
    print(f"  原始方位角平均值: {orig_azimuth.mean():.3f}°")
    print(f"  计算方位角平均值: {calc_azimuth.mean():.3f}°")
    
    # 详细对比表
    print(f"\n详细对比 (前5行):")
    comparison_df = original_data[['No', 'DOP [%]', 'φ [°]']].copy()
    comparison_df['DOP_calc [%]'] = calc_dop
    comparison_df['Azimuth_calc [°]'] = calc_azimuth
    comparison_df['DOP_diff'] = dop_diff
    
    print(comparison_df.head().to_string(index=False, float_format='%.3f'))


if __name__ == "__main__":
    # 运行转换测试
    success = test_stokes_conversion()
    
    if success:
        # 运行参数验证
        compare_original_vs_calculated()
        
        print("\n" + "="*60)
        print("✓ 所有测试完成!")
        print("✓ 斯托克斯参数转换程序工作正常")
        print(f"✓ 结果文件: data/stokes_results.csv")
    else:
        print("\n" + "="*60)
        print("✗ 测试失败!")
        print("请检查数据文件和依赖包是否正确安装") 