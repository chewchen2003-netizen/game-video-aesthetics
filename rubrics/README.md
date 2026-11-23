# 构图 Rubric v2.1.1

本轮讨论确认的VLM判档规则，冻结用于验证。**尚未完成独立人工复核或同批复跑，不代表标准已经得到验证。**

- [构图规则 JSON](composition_rubric.json)：唯一规则文件，采用逐条紧凑格式；每个指标、检查点各占一行，共用证据要求统一定义。
- [冻结记录](composition_rubric.lock.json)：版本与SHA256。
- [可读版](https://chewchen2003-netizen.github.io/game-video-aesthetics/rubrics/composition_rubric_v2.html)：从同一JSON生成。

## 信息怎样组织？

- 角色、定义、通用规则各集中一处。
- 每个指标的一行中保留定义与合理例外。
- 低、中、高分别组织；每个a/b/c检查点的一行中保留编号、唯一指标和完整条件。
- 42处重复的证据清单，改为按档位共用 `_checkpoint_evidence_defaults`；程序展开时恢复到各检查点。
- 整体判档、输出要求和运行记录仍完整保留。

不另存千行展开文件。`load_rubric()` 加载这份规则时，在内存中把共同证据要求恢复到各检查点；提供给模型前应完成此步骤，不能省略证据要求或假定模型自行理解引用。文件SHA256及完整加载内容的校验值统一保存在lock中；本次整理前后已验证内容一致。

```python
from src.rubric_format import load_rubric

rubric = load_rubric("rubrics/composition_rubric.json")
```

这是规则加载示例，并未切换旧评测入口或启动新版推理。规则版本为2.1.1，整理文件不改变判档条件。

## 固定内容

评价采用低、中、高，无法判断与不适用单列。基本呈现对应中档；高档还需要有上下文依据的关系、处境、感受或含义。每个检查点只关联一个指标。前三个因素检查呈现结果，构图手法记录识别与效果证据，不独立加分。没有数值权重或平均分。

判档模型计划使用GPT-6.1 Sol。每次执行需另外记录请求模型与服务返回的可获得模型信息。

## 校验与生成可读版

```sh
python3 scripts/check_composition_rubric.py
python3 scripts/render_composition_rubric.py
python3 -m unittest discover -s tests -p 'test_rubric_format.py'
```

原始JSON的哈希由lock核验。规则需要修改时创建新版本和对应记录；不通过重写旧lock来掩盖同版本变化。

## 与旧结果的关系

原50条预测及原执行契约保留。旧入口 `scripts/run_pipeline.py --mode review` **仍然使用旧契约** `data/standards/composition-frozen-contracts.json`，不会因新增本文件就自动成为v2评测。

本次只固定标准，不运行VLM。新版输入封装、逐点输出结构、独立人工复核和同批复跑需在后续接入；未完成前不能报告v2准确率或改进幅度。
