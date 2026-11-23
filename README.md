# 游戏视频美学评价标准与构图验证

项目包含美学评价框架、构图运行流程和样本验证。以下按整理日期区分两个版本；**11月24日是在11月23日同一批50条视频上复跑与复核的更新。**

## 2026年11月24日｜本轮更新

**[阅读11月24日报告](https://chewchen2003-netizen.github.io/game-video-aesthetics/report.html)** · [GitHub文字版](REPORT.md)

本轮依旧采用构图维度作为真实样本验证。

模型选用说明：由于暂无 Gemini API 资源，本轮采用 GPT-6.1 Sol 作为视觉语言模型（VLM）替代方案。

构图 Rubric v2.3.0：50题机标为 **27高、20中、3低**；人工复核25题，一致14题，**一致率56%**。

|内容|入口|
|---|---|
|构图 Rubric|[可读版](https://chewchen2003-netizen.github.io/game-video-aesthetics/rubrics/composition_rubric_v2.html) · [规则JSON](rubrics/composition_rubric.json)|
|主体提取、分割、测量到判档的全过程|[流程说明](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/composition-workflow.html) · [50题审核页](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/composition-v23-review/index.html)|
|两轮50题前后对照|[逐题来源、截取时间、原片哈希与判档对照](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/composition-two-round-comparison.html)|
|高、中、低典型案例|[R49高／R01中／R13低：机器过程与人工comments](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/composition-v23-selected-cases.html)|
|人工复核一致率与典型误判|[一致率、11题分歧及批注、典型问题与归因](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/composition-v23-human25-agreement.html)|
|其他维度 Rubric 草案|[色彩、光影、镜头、人声、音效的模型输入与验证方法](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/other-dimensions-methods.html)|

两轮素材逐题一致，抽帧及模型输入不同。本轮采用2FPS基础采样、局部4FPS补帧，复用既有CV缓存并重新核验。人工复核提出的规则修订意见单独记录，尚未应用到冻结规则；其他维度为方法草案，尚未实测。

## 2026年11月23日｜前轮历史版本

**[阅读11月23日报告](https://chewchen2003-netizen.github.io/game-video-aesthetics/report-history-20261123.html)**

包括分类标准与算子设计、首轮50题验证、训练数据调整、数据缺口、AI使用说明及不足。前轮机标为 **20高、29中、1低**，保留原始结果供对照。

|内容|入口|
|---|---|
|分类标准与算子表|[标签树与各维度说明](https://chewchen2003-netizen.github.io/game-video-aesthetics/game-tag-tree.html)|
|前轮50题审核|[视频、截图与原机标](https://chewchen2003-netizen.github.io/game-video-aesthetics/composition-machine50-review.html)|
|前轮结果与分布|[结果表](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/构图-50条结果表.html) · [分布图](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/构图-结果分布.svg) · [CSV](data/results/composition-results.csv)|
|前轮案例与误判分析|[历史案例](https://chewchen2003-netizen.github.io/game-video-aesthetics/results/构图-分档示例与误判分析.html)|

## 下载与本地查看

```sh
git clone https://github.com/chewchen2003-netizen/game-video-aesthetics.git
cd game-video-aesthetics
python3 scripts/serve.py --port 8000 --open
```

- 仓库 `main` 分支包含上述两个日期的材料，也可通过 **Code → Download ZIP** 下载。
- [原始50条视频完整包](https://github.com/chewchen2003-netizen/game-video-aesthetics/releases/tag/v1.0.0)为前轮交付包；11月24日新增材料见当前仓库。
- 安装、测量、回放、测试及目录说明见 [本地运行说明](RUNNING.md)。

审核页批注保存在当前浏览器，跨设备或域名需导出、导入。固定机标与人工意见分别保存。
