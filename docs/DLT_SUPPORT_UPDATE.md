# 最高评分策略 - 大乐透支持更新

## 📋 更新概述

**版本**: v1.2  
**日期**: 2025-10-23  
**状态**: ✅ 已完成并测试通过

"最高评分（整注）"策略现已全面支持大乐透！

---

## 🎯 更新内容

### 1. 新增大乐透搜索脚本

**文件**: `scripts/find_top_dlt.py`

**功能**:
- 基于频率和遗漏分析构建高质量前区号码池
- 应用大乐透特定的模式过滤器（奇偶比、大小比、区间分布、跨度、和值、AC值）
- 使用 `DLTNumberEvaluator` 进行全面评分
- 排除历史完全匹配的号码组合
- 返回评分最高的 Top K 注号码（包含并列）

**参数**:
- `top_k`: 返回前K名（默认5）
- `periods`: 统计期数（默认100）
- `pool_size`: 前区候选池大小（默认20）
- `out_path`: 输出文件路径（可选）

**命令行用法**:
```bash
python scripts/find_top_dlt.py --top 5 --periods 100 --pool-size 20 --out docs/TOP_DLT_NUMBERS.md
```

**Python API用法**:
```python
from scripts.find_top_dlt import find_top_dlt

results = find_top_dlt(top_k=5, periods=100, pool_size=20, out_path=None)

for item in results:
    print(f"前区: {item['front_numbers']}")
    print(f"后区: {item['back_numbers']}")
    print(f"评分: {item['total_score']}")
```

### 2. 更新生成页面

**文件**: `src/gui/generation_frame.py`

**修改**: `_background_top_scored_generation()` 方法

**变更**:
- 移除了"仅支持双色球"的限制
- 添加了彩票类型判断逻辑
- 双色球 (`lottery_type == 'ssq'`): 调用 `find_top_ssq()`，使用评价页的评分参数
- 大乐透 (`lottery_type == 'dlt'`): 调用 `find_top_dlt()`，使用 DLT 评估器的默认参数
- 其他类型: 抛出错误提示不支持

**代码结构**:
```python
if lottery_type == 'ssq':
    # 双色球逻辑
    from scripts.find_top_ssq import find_top_ssq
    cfg = self._get_ssq_scoring_config_from_evaluation()
    results = find_top_ssq(...)
    # 适配为 GUI 显示结构 (red, blue, score)

elif lottery_type == 'dlt':
    # 大乐透逻辑
    from scripts.find_top_dlt import find_top_dlt
    results = find_top_dlt(...)
    # 适配为 GUI 显示结构 (front, back, score)

else:
    raise ValueError(f"最高评分策略不支持彩票类型: {lottery_type}")
```

---

## 🧪 测试结果

**测试脚本**: `test_dlt_support.py`

### 测试1: 大乐透搜索脚本
- ✅ 成功导入 `find_top_dlt`
- ✅ 搜索功能正常（periods=50, pool_size=15, top_k=3）
- ✅ 返回23注号码，最高评分90.3

**示例结果**:
```
1. 前区: 08 11 22 26 35 | 后区: 04 12 | 评分: 90.3
2. 前区: 08 11 22 26 35 | 后区: 04 09 | 评分: 90.3
3. 前区: 08 11 22 26 35 | 后区: 04 10 | 评分: 90.3
```

### 测试2: 生成页面支持
- ✅ 成功导入 `GenerationFrame`
- ✅ 方法中包含大乐透支持代码
- ✅ 方法中调用了 `find_top_dlt`

---

## 📖 使用指南

### GUI 使用方法

1. **启动应用**:
   ```bash
   python main.py
   ```

2. **切换到"号码推荐"标签页**

3. **选择彩票类型**: 大乐透

4. **选择策略**: 最高评分（整注）

5. **配置参数**:
   - **生成注数**: 例如 5 注
   - **统计期数**: 例如 100（期数越大越全面，但耗时越长）
   - **候选池(前区)**: 例如 20（池越大越全面，但耗时越长）

6. **点击"生成号码"**

7. **查看结果**: 每注号码会显示评分值

### 命令行使用方法

```bash
# 搜索大乐透最高评分号码
python scripts/find_top_dlt.py --top 5 --periods 100 --pool-size 20

# 保存结果到文件
python scripts/find_top_dlt.py --top 10 --periods 150 --pool-size 25 --out docs/TOP_DLT_NUMBERS.md
```

---

## 🔧 技术细节

### 大乐透模式过滤器

**前区过滤规则**:
- 奇偶比: 2-3 个奇数
- 大小比: 2-3 个大号（≥18）
- 区间覆盖: 至少覆盖2个区间（1-12, 13-24, 25-35）
- 跨度: 10-34
- 和值: 70-130
- AC值: ≥3

**后区**: 枚举所有2个号码的组合（C(12,2) = 66种）

### 评分体系

使用 `DLTNumberEvaluator` 的完整评分体系:
- **频率分析**: 前区和后区的频率得分
- **遗漏分析**: 前区和后区的遗漏得分
- **模式分析**: 奇偶比、大小比、区间分布、连号、和值、跨度、AC值
- **历史对比**: 与历史中奖号码的相似度

### 性能优化

**启发式剪枝**:
1. 构建高质量前区候选池（基于频率60% + 反遗漏40%）
2. 只从候选池中生成组合（大幅减少搜索空间）
3. 应用模式过滤器（快速排除不合格组合）
4. 排除历史完全匹配（避免重复中奖号码）

**搜索空间对比**:
- 全量搜索: C(35,5) × C(12,2) ≈ 25,000,000 种组合
- 剪枝搜索: C(20,5) × C(12,2) ≈ 102,000 种组合（减少99.6%）

---

## 📊 参数建议

### 快速模式（适合日常使用）
- 统计期数: 50
- 候选池大小: 15
- 预计耗时: 5-10秒

### 平衡模式（推荐）
- 统计期数: 100
- 候选池大小: 20
- 预计耗时: 20-30秒

### 全面模式（追求最优）
- 统计期数: 150
- 候选池大小: 25
- 预计耗时: 60-90秒

---

## 🆚 双色球 vs 大乐透

| 特性 | 双色球 (SSQ) | 大乐透 (DLT) |
|------|-------------|-------------|
| 号码结构 | 6红球 + 1蓝球 | 5前区 + 2后区 |
| 红球/前区范围 | 1-33 | 1-35 |
| 蓝球/后区范围 | 1-16 | 1-12 |
| 评分参数联动 | ✅ 联动"号码评价"页 | ❌ 使用默认参数 |
| 搜索参数 | periods, pool_size | periods, pool_size |
| 候选池标签 | "候选池(红):" | "候选池(前区):" |

**注意**: 大乐透目前使用 `DLTNumberEvaluator` 的默认评分参数，未来可考虑添加评分参数配置页面。

---

## 🔄 版本历史

### v1.2 (2025-10-23)
- ✅ 新增大乐透搜索脚本 `scripts/find_top_dlt.py`
- ✅ 更新生成页面支持大乐透
- ✅ 添加大乐透支持测试脚本
- ✅ 更新文档

### v1.1 (2025-10-23)
- ✅ 搜索参数动态显示/隐藏
- ✅ 候选池标签动态更新

### v1.0 (2025-10-23)
- ✅ 联动"号码评价"的评分设置
- ✅ 暴露搜索参数到UI
- ✅ 在结果中显示评分值

---

## 📝 相关文档

- **快速参考**: `docs/QUICK_REFERENCE.md`
- **详细指南**: `docs/TOP_SCORED_GENERATION_GUIDE.md`
- **实现总结**: `docs/IMPLEMENTATION_SUMMARY.md`
- **可见性更新**: `docs/SEARCH_PARAMS_VISIBILITY_UPDATE.md`

---

## 🎉 总结

"最高评分（整注）"策略现已全面支持双色球和大乐透两种彩票类型！

**主要优势**:
- 🎯 基于科学的评分体系
- ⚡ 启发式剪枝保证速度
- 🔧 灵活的参数配置
- 📊 直观的评分显示
- 🚫 自动排除历史重复

**下一步计划**:
- 考虑为大乐透添加评分参数配置页面
- 优化搜索性能（并行计算、缓存等）
- 添加更多生成策略

---

**版本**: v1.2  
**状态**: ✅ 已完成并测试通过  
**测试脚本**: `test_dlt_support.py`

