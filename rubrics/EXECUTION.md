# 构图 Rubric 执行方法

规则源为 `composition_rubric.json`。这条入口与历史50条的旧入口分开，不改写历史结果。

## 三条试跑

使用原100条中未进入旧50条、且排除先前已展示1–11号后的三条样本，原样本号为79、67、17。随机种子2026112303，跨游戏与早／中／晚时段抽取；不是按预期档位挑选。

1. 每条20秒，按4FPS保留80个带时间码的RGB样本。模型实际输入为80张160×90序列缩略帧及第20、60帧较大参考图（768×432），不是80张原始720p图。分割覆盖图按640×360排列；缩略图无法支持的细节应标记证据不足。
2. 第一次GPT-6.1 Sol调用只做主体、陪体、环境及阶段识别和定位。定位框只是分割提示。原始返回值保留；阶段终点规范为下一阶段起点，末段止于20秒。人物切换期间不跨缺席阶段插值。
3. 运行YOLO11n-seg、MobileSAM、YOLO11n-pose、Depth-Anything-V2-Small。分割／姿态按4FPS，深度按1FPS；逐帧保存原始测量及覆盖图。
4. 第二次GPT-6.1 Sol调用同时接收80帧RGB、抽样覆盖图、对应测量、对象阶段记录和展开后的冻结Rubric。必须审查所给覆盖图的每个对象；拒绝的分割对应统计不能作为依据。未提供覆盖图的帧虽然保存了测量，但不声称已经过VLM审查。
5. 每阶段逐项记录42个检查点，再按整体条件判档。数值只作证据，不执行数值美学阈值或平均。
6. 校验检查点完整性、指标关联、证据ID、时间范围、事件引用、mask审查覆盖及状态／档位一致性。结构校验不能替代人工复核或证明判档正确。

内容识别和判档通过本机已登录的Codex CLI请求 `gpt-6.1-sol`；不宣称是已建立的公共API调用，也不独立认证实际后端型号。保存原始请求、响应、图片清单／哈希／尺寸、规则快照、墙钟耗时和可获得用量。原始CLI日志保存在运行目录；公开页面附实际请求文本和结构化原始响应。

## 运行

需要已登录的Codex CLI、Python、Pillow；CV阶段还需要 `requirements-cv.txt` 及模型文件。可用 `CODEX_BIN` 指定CLI路径。以下命令均在仓库根目录执行。

```sh
python scripts/prepare_rubric_trial.py --run-dir runs/new-trial
python scripts/run_rubric_trial.py --run-dir runs/new-trial --phase identify
GAME_EVAL_MODELS_DIR=/path/to/models HF_HUB_OFFLINE=1 python scripts/run_rubric_trial.py --run-dir runs/new-trial --phase measure
python scripts/run_rubric_trial.py --run-dir runs/new-trial --phase judge
python scripts/render_rubric_trial.py --run-dir runs/new-trial
```

输入目录需先具备 `selection.json`、`config.json` 以及各条 `inputs/T01` 等目录内的 `frames.json`、带编号和时间码的 `input-1.jpg`、`input-2.jpg` 与原始采样帧。代码不会从旧人工答案或旧预测构造输入。运行目录默认不入Git；公开试跑材料放在 `docs/results/rubric-trial3/`。

`--ids T01` 可分条执行识别或判档。测量可用 `GAME_EVAL_SAMPLE_IDS=T01` 指定样本。已有有效输出可恢复使用；未校验的判档输出不会自动当作成功。修改规则需使用新运行目录。

## 验证尚未完成的部分

三条用于检查链路与证据可核查性，不保证覆盖高、中、低。独立人工一致率、典型误判统计及同批前后对照须在正式复跑和独立人工复核后补充；不能用本次结构检查替代。
