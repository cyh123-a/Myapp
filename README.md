# 股票涨跌幅实时显示 App

一款基于 Python/Kivy 开发的 Android 股票涨跌幅实时显示应用，支持在一加 Ace 5 等 Android 手机上运行。

## 功能特性

- **实时股票数据**: 支持显示 1-3 只股票的实时涨跌幅
- **双数据源**: 首选腾讯财经 API，备选新浪财经 API，自动故障切换
- **颜色标识**: 红色表示上涨，绿色表示下跌（符合 A 股习惯）
- **交易时间控制**: 默认仅工作日 9:15-11:35、12:55-15:30 显示
- **全天显示模式**: 可勾选"全天显示"忽略交易时间限制
- **自定义刷新间隔**: 默认 10 秒刷新一次（可修改，最小 5 秒）
- **黑屏暂停**: 手机黑屏时自动暂停刷新以节省电量
- **设置面板**: 应用内设置界面，无需修改代码即可配置

## 项目结构

```
stock-display-app/
├── main.py                    # Kivy 应用主程序
├── buildozer.spec             # Buildozer 打包配置
├── requirements.txt           # Python 依赖包
├── .github/
│   └── workflows/
│       └── build.yml          # GitHub Actions 自动构建配置
└── README.md                  # 说明文档
```

## 快速开始

### 方法一：GitHub Actions 在线打包（推荐）

1. **创建 GitHub 仓库**
   - 将本项目代码推送到 GitHub 新仓库

2. **触发构建**
   - 进入仓库的 Actions 标签页
   - 点击 "Build Android App" 工作流
   - 点击 "Run workflow" 按钮

3. **下载 APK**
   - 构建完成后（约 10-20 分钟），在 Actions 页面的 Artifacts 中下载 APK 文件
   - 安装到手机上即可使用

### 方法二：本地构建 APK

1. **安装依赖**
   ```bash
   pip install buildozer cython==3.0.10
   ```

2. **初始化 Buildozer**
   ```bash
   buildozer init
   ```

3. **编辑 buildozer.spec**
   - 根据需要修改包名、版本等配置

4. **构建 APK**
   ```bash
   # Debug 版本
   buildozer android debug
   
   # Release 版本（需要签名配置）
   buildozer android release
   ```

5. **安装到手机**
   - 构建完成后，APK 文件在 `dist/` 目录下
   - 通过 USB 传输到手机安装

### 方法三：直接在手机上运行（Termux）

1. 在手机上安装 Termux（F-Droid 版本）
2. 安装 Python: `pkg install python`
3. 安装依赖: `pip install kivy requests`
4. 运行: `python main.py`

## 股票代码说明

| 股票名称 | 代码格式 | 说明 |
|---------|---------|------|
| 上证指数 | sh000001 | 上海证券交易所综合指数 |
| 深证成指 | sz399001 | 深圳证券交易所成份指数 |
| 贵州茅台 | sh600519 | 上海证券交易所 |
| 平安银行 | sz000001 | 深圳证券交易所 |
| 比亚迪 | sz002594 | 深圳证券交易所 |

**代码格式规则:**
- 沪市（上海）股票: 前缀 `sh` + 6位代码（如 sh600519）
- 深市（深圳）股票: 前缀 `sz` + 6位代码（如 sz000001）

## API 数据源

### 腾讯财经 API（首选）
- 接口: `https://qt.gtimg.cn/q=股票代码`
- 优点: 稳定、无需特殊请求头
- 返回: GBK 编码的文本数据

### 新浪财经 API（备选）
- 接口: `http://hq.sinajs.cn/list=股票代码`
- 要求: 需设置 Referer 请求头
- 注意: 部分网络环境可能被限制

## 设置说明

应用内设置界面包含以下选项:

| 设置项 | 说明 | 默认值 |
|-------|------|--------|
| 股票代码 | 多只股票用逗号分隔 | sh600519,sz000001,sh000001 |
| 数据源 | tencent 或 sina | tencent |
| 刷新间隔 | 秒数，最小 5 秒 | 10 |
| 仅交易时间显示 | 勾选后仅交易时间显示 | 勾选 |
| 全天显示 | 勾选后忽略交易时间，一直刷新 | 未勾选 |
| 黑屏暂停刷新 | 勾选后黑屏时暂停刷新 | 勾选 |

## 注意事项

1. **网络权限**: 应用需要互联网权限才能获取股票数据
2. **后台运行**: 建议将应用加入电池优化白名单，防止系统杀死后台进程
3. **屏幕常亮**: 如需长时间显示，建议在手机设置中开启"保持屏幕常亮"
4. **数据延迟**: 免费 API 数据可能有 3-30 秒延迟，非实时 Level-2 数据
5. **构建环境**: GitHub Actions 构建需要足够的磁盘空间（约 5-10GB）

## 技术栈

- **语言**: Python 3.11
- **框架**: Kivy 2.3.0
- **打包工具**: Buildozer / python-for-android
- **CI/CD**: GitHub Actions
- **数据源**: 腾讯财经 API / 新浪财经 API

## 许可证

MIT License
