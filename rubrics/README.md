# 构图 Rubric v2.0.1

本轮讨论确认的VLM判档规则，冻结用于验证。**尚未完成独立人工复核或同批复跑，不代表标准已经得到验证。**

- [精简组织版 JSON（推荐阅读）](composition_rubric.compact.json)：218行；每个指标、每个检查点各占一行，共用证据要求统一定义，无规则信息损失。
- [冻结展开原版](composition_rubric.json)：1015行，保存当前版本的展开内容与SHA256；历史版本由Git记录追溯。
- [冻结记录](composition_rubric.lock.json)：版本与SHA256。
- [可读版](https://chewchen2003-netizen.github.io/game-video-aesthetics/rubrics/composition_rubric_v2.html)：从同一JSON生成。

## 精简版怎样组织？

- 角色、定义、通用规则各集中一处。
- 每个指标的一行中保留定义与合理例外。
- 低、中、高分别组织；每个a/b/c检查点的一行中保留编号、唯一指标和完整条件。
- 42处重复的证据清单，改为按档位共用 `_checkpoint_evidence_defaults`；程序展开时恢复到各检查点。
- 整体判档、输出要求和运行记录仍完整保留。

精简版只是同一规则的存储表示，不是删节版。`src/rubric_format.py` 的 `expand_rubric()` 可恢复完整对象；校验要求展开后的JSON对象与冻结原版完全相等，而非只比较条数。默认值必须由程序展开，不能直接省略证据要求或假定模型自行理解引用。

```python
import json
from src.rubric_format import expand_rubric

with open("rubrics/composition_rubric.compact.json") as f:
    rubric = expand_rubric(json.load(f))
```

这是规则加载示例，并未切换旧评测入口或启动新版推理。规则版本为2.0.1；存储格式另有版本与[精简版校验记录](composition_rubric.compact.lock.json)。

## 固定内容

评价采用低、中、高，无法判断与不适用单列。基本呈现对应中档；高档还需要有上下文依据的关系、处境、感受或含义。每个检查点只关联一个指标。前三个因素检查呈现结果，构图手法记录识别与效果证据，不独立加分。没有数值权重或平均分。

判档模型计划使用GPT-6.1 Sol。每次执行需另外记录请求模型与服务返回的可获得模型信息。

## 校验与生成可读版

```sh
python3 scripts/check_composition_rubric.py
python3 scripts/build_compact_rubric.py
python3 scripts/render_composition_rubric.py
python3 -m unittest discover -s tests -p 'test_rubric_format.py'
```

原始JSON的哈希由lock核验。规则需要修改时创建新版本和对应记录；不通过重写旧lock来掩盖同版本变化。

## 与旧结果的关系

原50条预测及原执行契约保留。旧入口 `scripts/run_pipeline.py --mode review` **仍然使用旧契约** `data/standards/composition-frozen-contracts.json`，不会因新增本文件就自动成为v2评测。

本次只固定标准，不运行VLM。新版输入封装、逐点输出结构、独立人工复核和同批复跑需在后续接入；未完成前不能报告v2准确率或改进幅度。
