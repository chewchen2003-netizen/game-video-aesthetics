# 构图 Rubric v2.0.0

本轮讨论确认的VLM判档规则，冻结用于验证。**尚未完成独立人工复核或同批复跑，不代表标准已经得到验证。**

- [完整规则 JSON](composition_rubric.json)：唯一关联指标、42个检查点、四个评价因素、整体判档逻辑及证据要求。
- [冻结记录](composition_rubric.lock.json)：版本与SHA256。
- [可读版](https://chewchen2003-netizen.github.io/game-video-aesthetics/rubrics/composition_rubric_v2.html)：从同一JSON生成。

## 固定内容

评价采用低、中、高，无法判断与不适用单列。基本呈现对应中档；高档还需要有上下文依据的关系、处境、感受或含义。每个检查点只关联一个指标。前三个因素检查呈现结果，构图手法记录识别与效果证据，不独立加分。没有数值权重或平均分。

判档模型计划使用GPT-6.1 Sol，原因是用户没有Gemini API。每次执行需另外记录请求模型与服务返回的可获得模型信息。

## 校验与生成可读版

```sh
python3 scripts/check_composition_rubric.py
python3 scripts/render_composition_rubric.py
```

原始JSON的哈希由lock核验。规则需要修改时创建新版本和对应记录；不通过重写旧lock来掩盖同版本变化。

## 与旧结果的关系

原50条预测及原执行契约保留。旧入口 `scripts/run_pipeline.py --mode review` **仍然使用旧契约** `data/standards/composition-frozen-contracts.json`，不会因新增本文件就自动成为v2评测。

本次只固定标准，不运行VLM。新版输入封装、逐点输出结构、独立人工复核和同批复跑需在后续接入；未完成前不能报告v2准确率或改进幅度。
