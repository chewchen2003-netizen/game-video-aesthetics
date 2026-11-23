# 游戏视频美学评价标准与构图验证

本项目包括游戏视频美学评价标准、构图算子代码，以及50条真实游戏视频的构图验证结果。

## 📖 先看交付说明

### [阅读完整交付说明 →](https://chewchen2003-netizen.github.io/game-video-aesthetics/report.html)

说明文档按六部分组织：分类标准与算子表、真实样本验证、训练数据调整、数据缺口与补充、AI使用说明、难点与不足。

也可以[直接在 GitHub 中阅读](REPORT.md)。

**本轮优化：** [构图 Rubric v2.2.0（可读版）](https://chewchen2003-netizen.github.io/game-video-aesthetics/rubrics/composition_rubric_v2.html) · [规则 JSON](rubrics/composition_rubric.json) · [版本与使用说明](rubrics/README.md)。已完成[三条非原50样本试跑](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/rubric-trial3/index.html)，机标使用v2.1.1；当前v2.2.0为事后复核后的修订，尚未复跑。页面附内容识别、分割、测量、逐点证据及复核批注；独立人工验证待完成。下方50条仍为旧版结果。

## 查看评价标准与验证结果

|想看什么|入口|
|---|---|
|完整分类标准与算子表|[打开标签树](https://chewchen2003-netizen.github.io/game-video-aesthetics/game-tag-tree.html)，点击节点查看右侧的定义、影响条件、计算过程、Prompt、人工判档依据和成本|
|50条构图视频及机标结果|[打开审核页](https://chewchen2003-netizen.github.io/game-video-aesthetics/composition-machine50-review.html)，查看视频、时间码截帧、判断依据，并批注、挑选样本|
|逐条结果与整体分布|[结果表](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/构图-50条结果表.html) · [分布图](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/构图-结果分布.svg) · [下载CSV](data/results/composition-results.csv)|
|分档参照与误判分析|[查看案例](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/构图-分档示例与误判分析.html)，包含3例高、3例中、1例低及人工复核意见|

**第一部分的完整标准在标签树及各节点右侧面板中。** 本轮完成样本验证的维度是构图，原机标为高20条、中29条、低1条。其他维度的完成情况见说明文档。

最终评价采用低、中、高；无法判断、不适用单列。不输出数值美学分数，也不对各因素做简单平均。原机标与人工复核意见分开保存。

审核页批注保存在当前浏览器，可导出、导入备份。更换设备或访问域名后，需要自行导入已有批注。

## 下载项目

```sh
git clone https://github.com/chewchen2003-netizen/game-video-aesthetics.git
cd game-video-aesthetics
```

也可以点击仓库的 **Code → Download ZIP**。

|下载内容|位置|
|---|---|
|最新说明文档、两个网页、代码、结果表、保存的测量与网页预览素材|本仓库的 `main` 分支|
|含原始50条视频的完整交付包|[Releases](https://github.com/chewchen2003-netizen/game-video-aesthetics/releases/tag/v1.0.0)|

网页使用压缩视频预览。重新测量原始样本时，将完整包中的 `raw-inputs/videos/` 放在项目根目录下。

## 本地查看与结果回放

需要 Python 3.10+。以下操作使用Python标准库，无需模型、API密钥或额外安装依赖。

**打开两个网页：**

```sh
python3 scripts/serve.py --port 8000 --open
```

浏览器访问 <http://127.0.0.1:8000/>，从首页进入说明文档、标签树或审核页。

**检查文件与固定结果：**

```sh
python3 scripts/check_delivery.py
python3 -m unittest discover -s tests -p 'test_result_validation.py'
```

**回放已保存的测量与预测：**

```sh
python3 scripts/run_pipeline.py --mode replay --run-dir runs/replay
```

结果写入 `runs/replay/`。回放会解压保存的测量、校验输出并汇总分布，不会重新调用模型。

## 重新运行构图算子

流程为：主体与阶段指定 → 4FPS抽帧及时间码 → 视觉测量 → 测量质量检查 → 视觉模型综合判断 → 输出校验。

<details>
<summary><strong>展开依赖安装、测量和推理命令</strong></summary>

### 1. 安装依赖

建议 Python 3.12，另需安装 `ffmpeg`、`ffprobe`。第三方依赖与模型的许可说明见 [COPYRIGHT.md](COPYRIGHT.md)。

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-cv.txt
```

### 2. 抽帧并计算视觉测量

以R01为例；去掉 `--ids R01` 可处理全部50条。

```sh
python scripts/run_pipeline.py --mode measure --ids R01 --raw-dir raw-inputs/videos
```

每条20秒视频按4FPS抽取80帧，保存片内及原会话时间码。首次运行会下载模型权重，计算设备可使用CUDA、Apple MPS或CPU。

只需抽帧时，将 `--mode measure` 改为 `--mode prepare`。没有原始片段时，可用 `--use-preview` 替代 `--raw-dir raw-inputs/videos` 演示；压缩预览的测量结果可能与原始视频不同。

### 3. 运行视觉综合判断

需要已登录的Codex CLI和所指定模型的访问权限，推理会产生费用。默认模型为 `gpt-6.1-sol`，可通过 `--model` 指定实际可用模型。

```sh
python scripts/run_pipeline.py --mode review --ids R01 --model gpt-6.1-sol
```

程序读取测量、序列图、测量QA图与冻结Prompt，校验结构和证据引用，将新结果保存到 `runs/reproduction/`，不覆盖原50条机标。

### 4. 运行检查

```sh
python -m unittest discover -s tests
```

### 运行边界

- 主体与阶段指定沿用 `data/assignments/` 中的RGB观察结果，该环节含人工参与。
- 相对深度由RGB模型估计，没有使用引擎深度、法线、相机位姿或事件流。
- 推理Prompt不提供人工答案，输出校验会拒绝有额外工具调用的推理记录。这是工作流隔离，不是文件系统安全隔离。
- 模型输出可能变化；历史JSON中的 `score: null` 是兼容字段，不代表提供数值美学分数。

</details>

## 文件目录

|位置|内容|
|---|---|
|[REPORT.md](REPORT.md)|完整交付说明|
|[docs/](docs/)|可本地运行的说明文档、标签树、审核页及预览素材|
|[data/standards/](data/standards/)|完整标签树源码、结构化导出，以及实际50条运行使用的冻结算子契约|
|[data/results/](data/results/)|固定预测、CSV、分布、人工复核意见、用量与耗时记录|
|[data/sources/](data/sources/)|抽样方案、原会话、时间段、来源与SHA256|
|[data/assignments/](data/assignments/)|主体与片段阶段指定|
|[data/measurements/](data/measurements/)|原始测量、质量检查后测量及摘要，以gzip保存|
|[src/](src/)|构图测量、数学计算、Prompt构建与输出校验代码|
|[scripts/](scripts/)|网页服务、流程运行、交付检查与打包脚本|
|[tests/](tests/)|几何计算与输出校验测试|
|`raw-inputs/videos/`|完整Release包中的原始视频|
|`runs/`|本地回放或重新运行产生的结果，不提交到Git|
