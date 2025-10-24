# 搜索参数可见性优化 - 更新说明

## 📋 问题描述

用户反馈了两个重要的UI问题：

### 问题1：搜索参数对所有策略都显示
**现象**：统计期数和候选池参数一直显示在界面上，即使选择的策略不使用这些参数。

**问题**：
- 这些参数只对"最高评分（整注）"策略有效
- 其他策略（如"统计优选"、"随机生成"等）不使用这些参数
- 一直显示会让用户困惑，以为这些参数对所有策略都生效

### 问题2：候选池标签不随彩票类型变化
**现象**：候选池标签固定显示为"候选池(红):"，即使切换到大乐透。

**问题**：
- 双色球的红球对应大乐透的前区
- 标签应该根据彩票类型动态更新：
  - 双色球 → "候选池(红):"
  - 大乐透 → "候选池(前区):"

---

## ✅ 解决方案

### 解决方案1：动态显示/隐藏搜索参数

**实现思路**：
- 将搜索参数控件（标签和输入框）保存为实例变量
- 默认隐藏这些控件
- 只在选择"最高评分（整注）"策略时显示
- 切换到其他策略时自动隐藏

**关键代码**：

```python
# 1. 保存控件引用（而不是直接grid）
self.periods_label = ttk.Label(config_frame, text="统计期数:")
self.periods_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
self.periods_spinbox = ttk.Spinbox(config_frame, from_=10, to=500, ...)
self.periods_spinbox.grid(row=3, column=1, padx=5, pady=5, sticky="w")

self.pool_size_label = ttk.Label(config_frame, text="候选池(红):")
self.pool_size_label.grid(row=3, column=2, padx=5, pady=5, sticky="w")
self.pool_size_spinbox = ttk.Spinbox(config_frame, from_=10, to=30, ...)
self.pool_size_spinbox.grid(row=3, column=3, padx=5, pady=5, sticky="w")

# 2. 默认隐藏
self._hide_search_params()

# 3. 显示方法
def _show_search_params(self):
    """显示搜索参数控件"""
    self.periods_label.grid()
    self.periods_spinbox.grid()
    self.pool_size_label.grid()
    self.pool_size_spinbox.grid()
    self._update_pool_size_label()

# 4. 隐藏方法
def _hide_search_params(self):
    """隐藏搜索参数控件"""
    self.periods_label.grid_remove()
    self.periods_spinbox.grid_remove()
    self.pool_size_label.grid_remove()
    self.pool_size_spinbox.grid_remove()

# 5. 策略切换时调用
def _on_strategy_change(self, event=None):
    strategy = self.strategy_map.get(self.strategy_var.get())
    if strategy == "top_scored":
        self._update_scoring_info_display()
        self._show_search_params()  # 显示
    else:
        self.scoring_info_label.config(text="")
        self._hide_search_params()  # 隐藏
```

**使用 grid_remove() 的优势**：
- 保留控件的grid配置（位置、对齐等）
- 隐藏后不占用空间
- 再次显示时只需调用 `grid()` 即可恢复原位置
- 比 `grid_forget()` 更适合需要反复显示/隐藏的场景

### 解决方案2：动态更新候选池标签

**实现思路**：
- 根据当前选择的彩票类型，动态更新标签文字
- 在彩票类型切换时自动更新
- 在显示搜索参数时也更新（确保标签正确）

**关键代码**：

```python
def _update_pool_size_label(self):
    """根据彩票类型更新候选池标签文字"""
    lottery_type = self.lottery_type_var.get()
    if lottery_type == 'ssq':
        label_text = "候选池(红):"
    elif lottery_type == 'dlt':
        label_text = "候选池(前区):"
    else:
        label_text = "候选池:"
    self.pool_size_label.config(text=label_text)

def _on_lottery_type_change(self):
    """切换彩票类型时的处理"""
    self.clear_results()
    self._update_pool_size_label()  # 更新标签

def _show_search_params(self):
    """显示搜索参数控件"""
    self.periods_label.grid()
    self.periods_spinbox.grid()
    self.pool_size_label.grid()
    self.pool_size_spinbox.grid()
    self._update_pool_size_label()  # 显示时也更新标签
```

---

## 🎯 效果展示

### 场景1：默认状态（统计优选策略）
```
彩票类型: [双色球 ▼]
生成注数: [5]
生成策略: [统计优选 ▼]

[生成号码]
```
**说明**：搜索参数（统计期数、候选池）不显示 ✅

### 场景2：切换到"最高评分（整注）"策略（双色球）
```
彩票类型: [双色球 ▼]
生成注数: [5]
生成策略: [最高评分（整注） ▼]
统计期数: [100]  候选池(红): [18]

当前评分参数: 蓝球频率权重=0.30, 蓝球遗漏权重=0.30, ...

[生成号码]
```
**说明**：
- 搜索参数显示 ✅
- 候选池标签显示"候选池(红):" ✅
- 评分参数提示显示 ✅

### 场景3：保持策略，切换到大乐透
```
彩票类型: [大乐透 ▼]
生成注数: [5]
生成策略: [最高评分（整注） ▼]
统计期数: [100]  候选池(前区): [18]

当前评分参数: 蓝球频率权重=0.30, 蓝球遗漏权重=0.30, ...

[生成号码]
```
**说明**：
- 搜索参数仍然显示 ✅
- 候选池标签更新为"候选池(前区):" ✅

### 场景4：切换回其他策略
```
彩票类型: [大乐透 ▼]
生成注数: [5]
生成策略: [随机生成 ▼]

[生成号码]
```
**说明**：
- 搜索参数隐藏 ✅
- 评分参数提示隐藏 ✅

---

## 🧪 测试验证

### 自动化测试
```bash
echo "2" | python test_search_params_visibility.py
```

**测试结果**：
```
测试1：检查控件是否正确创建
  ✅ 所有搜索参数控件已创建

测试2：检查方法是否存在
  ✅ 所有新增方法已实现

测试3：测试候选池标签更新
  ✅ 双色球: 候选池(红):
  ✅ 大乐透: 候选池(前区):

测试4：测试显示/隐藏功能
  ✅ _show_search_params() 调用成功
  ✅ _hide_search_params() 调用成功

所有程序化测试通过 ✅
```

### 手动测试
```bash
python test_search_params_visibility.py
# 选择 1 进行GUI测试
```

**测试步骤**：
1. 观察默认状态（统计优选策略）→ 搜索参数应隐藏
2. 切换到"最高评分（整注）"→ 搜索参数应显示
3. 切换彩票类型到大乐透 → 候选池标签应更新
4. 切换回其他策略 → 搜索参数应隐藏

---

## 📁 修改的文件

### src/gui/generation_frame.py

**修改内容**：

1. **控件创建部分（第62-76行）**
   - 将控件保存为实例变量
   - 默认调用 `_hide_search_params()` 隐藏

2. **新增方法**：
   - `_show_search_params()` - 显示搜索参数
   - `_hide_search_params()` - 隐藏搜索参数
   - `_update_pool_size_label()` - 更新候选池标签

3. **修改方法**：
   - `_on_lottery_type_change()` - 新增标签更新调用
   - `_on_strategy_change()` - 新增显示/隐藏调用

---

## 💡 设计考虑

### 为什么使用 grid_remove() 而不是 grid_forget()？

| 方法 | 效果 | 适用场景 |
|------|------|----------|
| `grid_forget()` | 完全移除grid配置 | 不再需要显示的控件 |
| `grid_remove()` | 隐藏但保留配置 | 需要反复显示/隐藏的控件 |

**选择 grid_remove() 的原因**：
- 保留位置、对齐等配置
- 再次显示时只需 `grid()` 即可
- 性能更好（不需要重新配置）
- 代码更简洁

### 为什么在两处调用 _update_pool_size_label()？

1. **在 _on_lottery_type_change() 中调用**
   - 用户切换彩票类型时更新
   - 无论搜索参数是否显示都更新

2. **在 _show_search_params() 中调用**
   - 显示搜索参数时确保标签正确
   - 防止标签与当前彩票类型不匹配

**好处**：
- 确保标签始终与彩票类型一致
- 避免用户看到错误的标签文字

---

## 🎓 用户体验改进

### 改进前
- ❌ 搜索参数一直显示，让用户误以为对所有策略都生效
- ❌ 候选池标签固定，大乐透时显示"红球"不合适
- ❌ 界面信息冗余，不够简洁

### 改进后
- ✅ 搜索参数只在需要时显示，界面更简洁
- ✅ 候选池标签动态更新，术语准确
- ✅ 用户不会被无关参数困扰
- ✅ 界面更智能，自动适应当前选择

---

## 📚 相关文档

- [快速参考](./QUICK_REFERENCE.md)
- [详细使用指南](./TOP_SCORED_GENERATION_GUIDE.md)
- [实现总结](./IMPLEMENTATION_SUMMARY.md)

---

**更新日期**：2025-10-23  
**版本**：v1.1  
**状态**：✅ 已完成并测试通过

