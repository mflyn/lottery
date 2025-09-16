import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from typing import Dict
import pandas as pd

class DataVisualizer:
    """数据可视化类"""
    
    def __init__(self):
        plt.style.use('seaborn')
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 支持中文显示
        plt.rcParams['axes.unicode_minus'] = False
        
    def plot_trend_chart(self, data: pd.DataFrame, title: str = "号码走势图"):
        """绘制走势图"""
        plt.figure(figsize=(15, 8))
        
        # 前区号码走势
        for col in data.columns:
            if col.startswith('front_'):
                plt.plot(data.index, data[col], marker='o', label=f'前区{col.split("_")[1]}')
                
        plt.title(title)
        plt.xlabel('期号')
        plt.ylabel('号码')
        plt.grid(True)
        plt.legend()
        
        return plt.gcf()
    
    def plot_frequency_distribution(self, data: Dict[int, int], title: str = "号码频率分布图"):
        """绘制频率分布图"""
        plt.figure(figsize=(12, 6))
        
        numbers = list(data.keys())
        frequencies = list(data.values())
        
        sns.barplot(x=numbers, y=frequencies)
        plt.title(title)
        plt.xlabel('号码')
        plt.ylabel('出现频率')
        
        return plt.gcf()
    
    def plot_number_correlation(self, correlation_matrix: pd.DataFrame, title: str = "号码关联分析图"):
        """绘制号码关联图"""
        plt.figure(figsize=(10, 10))
        
        # 创建关联网络图
        G = nx.Graph()
        
        # 添加节点和边
        for i in correlation_matrix.index:
            for j in correlation_matrix.columns:
                if i != j and correlation_matrix.loc[i, j] > 0.5:  # 设置关联阈值
                    G.add_edge(i, j, weight=correlation_matrix.loc[i, j])
        
        # 绘制网络图
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=500, font_size=10, font_weight='bold')
        
        plt.title(title)
        return plt.gcf()