# 游戏视频美学评价标准与构图验证

本交付包括完整标签树、50条构图机标审核网页、说明文档、逐条结果和构图算子原型。**第一部分“分类标准与算子表”的完整内容在标签树及各节点右侧面板中**，不是仅见于本说明。

## 在线阅读

- [项目首页](https://chewchen2003-netizen.github.io/game-video-aesthetics/)
- [完整分类标准与算子表：标签树](https://chewchen2003-netizen.github.io/game-video-aesthetics/game-tag-tree.html)
- [50条构图机标审核：视频、截帧、批注](https://chewchen2003-netizen.github.io/game-video-aesthetics/composition-machine50-review.html)
- [六部分说明文档](docs/report.html)
- [逐条结果表](docs/results/构图-50条结果表.html) · [分布图](docs/results/构图-结果分布.svg) · [分档示例与误判分析](docs/results/构图-分档示例与误判分析.html)

网页批注只保存在当前浏览器，可导出/导入备份，不会写入他人的批注。原来file://页面的批注不会自动迁移到新域名。网页内视频是压缩预览；精确复测使用Release完整包中的原始片段。

## 本地运行

需要Python 3.10+。查看网页、检查交付和回放保存结果不需要模型或API密钥。

```sh
python3 scripts/serve.py --port 8000 --open
python3 scripts/check_delivery.py
python3 scripts/run_pipeline.py --mode replay --run-dir runs/replay
python3 -m unittest discover -s tests -p 'test_result_validation.py'
```

浏览器打开 http://127.0.0.1:8000/ 。replay会解压保存的测量，验证输出结构并重新汇总分布；它不重新推理，也不是新一轮模型测试。

## 重新处理视频

需要ffmpeg/ffprobe，完整CV流程建议Python 3.12。模型权重首次自动下载；GPU可由PyTorch使用CUDA或Apple MPS，CPU也可执行。依赖及第三方模型许可证见COPYRIGHT.md。

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-cv.txt
python scripts/run_pipeline.py --mode prepare --ids R01 --raw-dir raw-inputs/videos
python scripts/run_pipeline.py --mode measure --ids R01 --raw-dir raw-inputs/videos
python -m unittest discover -s tests
```

没有原始片段时可显式使用`--use-preview`替代`--raw-dir`演示，测量不保证与原始运行一致。每条20秒，以4FPS抽取80帧，输出片内时间码和原会话时间码。主体/阶段指定沿用data/assignments中的RGB观察结果，这一步不是全自动识别。

视觉综合判断需要可用的Codex CLI登录和所指定模型的访问权限；会产生推理费用。模型名称默认gpt-6.1-sol，可按实际访问权限指定。该命令不是OpenAI独立API适配器。

```sh
python scripts/run_pipeline.py --mode review --ids R01 --model gpt-6.1-sol
```

review读取测量、序列图、测量QA图和冻结Prompt，校验结构与证据，将新结果写到runs/reproduction，**不覆盖原50条结果**。人工复核意见另存；Prompt不提供人工答案，并拒绝有额外工具调用的推理记录。此为工作流隔离，不是文件系统安全隔离。模型输出可能变化，无法承诺逐字复现。

## 文件索引

|位置|内容|
|---|---|
|docs/game-tag-tree.html|完整可交互标签树，含所有右侧说明|
|data/standards/tag-tree-source.html|完整标签树源文件|
|data/standards/taxonomy-full.json|包含基础信息与全部面板的完整结构化导出|
|data/standards/aesthetic-taxonomy.json|美学评价子树结构化导出|
|data/standards/composition-frozen-contracts.json|实际50条运行使用的历史算子契约，与后续润色版分开保存|
|docs/composition-machine50-review.html|50条视频、截帧、机标证据、独立批注与挑选|
|data/results/|固定预测、CSV、分布、人工讨论、用量与耗时|
|data/measurements/|50条原始/QA后测量与摘要，gzip保存|
|data/sources/|抽样方案、原会话、时间段、来源与SHA256|
|src/|实际构图测量、计算与Prompt构建代码|
|scripts/|运行、检查、网页服务|
|raw-inputs/videos/|仅完整Release包提供的原始50条片段，不重复放入Git历史|

只验证了构图维度。其他维度是评价设计，不能视为已完成模型实测。最终输出为低/中/高，证据不足或不适用单列；不输出数值美学分数，不用简单平均。历史JSON中的score:null为兼容字段。
