<div align="center">
  <a href="https://github.com/lichman0405/mineru-api.git">
    <img src="/assets/edit_logo.png" alt="Logo" width="150px">
  </a>
  
  <h1 align="center">MinerU PDF 智能解析服务</h1>
  
  <p align="center">
    一个基于 MinerU、FastAPI 和 Celery 构建的强大、可扩展的 PDF 解析 API 服务。
    <br>
    <a href="./README-en.md"><strong>English</strong></a>
    ·
    <a href="https://github.com/lichman0405/mineru-api.git/issues">报告 Bug</a>
    ·
    <a href="https://github.com/lichman0405/mineru-api.git/issues">提出新特性</a>
  </p>
</div>

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi)
![Celery](https://img.shields.io/badge/Celery-3778AF?style=flat&logo=celery)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker)
[![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/YOUR_REPO_NAME.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/issues)
[![GitHub stars](https://img.shields.io/github/stars/lichman0405/mineru-api.git.svg?style=social)](https://github.com/lichman0405/mineru-api.git])

</div>

---

## 📖 关于项目

本项目是一个功能强大的 PDF 文档解析服务。它利用 [MinerU](https://github.com/opendatalab/MinerU) 的核心能力，能够深度解析 PDF 文件，提取文本、表格、图片等元素，并将其转换为结构化的 Markdown 和 JSON 格式。
需要注意，这里的MinerU还暂时没有假如GPU支持。

如果对项目感兴趣，请fork并且star原项目[MinerU](https://github.com/opendatalab/MinerU)

服务采用异步架构，通过 FastAPI 接收请求，使用 Celery 和 Redis 构建分布式任务队列，确保了在高并发和处理大型文件时的稳定性和高性能。整个服务已完全容器化，可通过 Docker Compose 一键部署。

### ✨ 主要功能

* **PDF 到 Markdown**: 将 PDF 内容（包括文本和图片）高质量地转换为 Markdown 格式。
* **PDF 到 JSON**: 提取文档内容并输出为两种结构化的 JSON 格式，便于程序处理。
* **OCR 支持**: 自动检测扫描版 PDF，并调用 OCR 提取文字。
* **异步处理**: 基于 Celery 的任务队列，API 能够立即响应，并在后台处理耗时任务。
* **日志系统**: 同时输出到美化的控制台和持久化的文件，便于调试和追踪。
* **容器化部署**: 使用 Docker 和 Docker Compose，实现一键启动和环境隔离。
* **可扩展架构**: Web 服务与计算任务分离，可以独立扩展 Celery Worker 以应对高负载。

### 🏗️ 系统架构

服务采用经典M-M-W模式，由三个核心容器组成：
1.  **FastAPI Web App**: 作为Master，接收用户上传的 PDF 文件，创建解析任务并推入 Redis 队列，然后立即返回任务 ID。
2.  **Redis**: 作为消息代理（Broker），存储待处理的任务队列，并作为后端（Backend）存储任务结果。
3.  **Celery Worker**: 作为Worker，从 Redis 队列中获取任务，调用 `magic-pdf` 库执行繁重的 PDF 解析工作，并将结果写回 Redis。

## 🚀 快速开始

### 📋 先决条件

在开始之前，请确保您的系统已安装以下软件：
* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/) (通常随 Docker Desktop 一同安装)

### ⚙️ 安装与设置

1.  **克隆仓库**
    ```bash
    git clone https://github.com/lichman0405/mineru-api.git
    cd mineru-api
    ```

2.  **创建数据目录**
    服务需要一个 `data` 目录来存放输入、输出和日志文件。请在项目根目录执行：
    ```bash
    mkdir -p data/input_pdfs data/output data/logs
    ```

3.  **准备测试文件**
    将一个或多个您想要测试的 PDF 文件放入 `./data/input_pdfs/` 目录中。

4.  **构建并启动服务**
    使用 Docker Compose 一键构建并启动所有服务（Web App, Worker, Redis）。
    ```bash
    docker-compose up --build -d
    ```
    `-d` 参数会让服务在后台运行。您可以使用 `docker-compose logs -f` 查看实时日志。

## 🕹️ 使用方法

我们推荐使用项目提供的客户端脚本与服务进行交互。这大大简化了提交、轮询和下载的流程。请在您的本地电脑（而非容器内）运行这些脚本。

### 方式一：测试单个文件（推荐用于调试）

使用 `test_single_file.py` 脚本，可以完成从提交到下载结果的完整流程。

1.  **安装依赖**:
    ```bash
    pip install requests
    ```
2.  **运行脚本**:
    ```bash
    # 将 test.pdf 的处理结果下载到 ./downloaded_results 目录
    python test_single_file.py --file ./data/input_pdfs/test.pdf --download-dir ./downloaded_results
    ```
3.  **查看结果**:
    脚本会自动提交文件、轮询状态，并在任务成功后下载一个包含所有结果的 `.zip` 文件到 `./downloaded_results` 目录。

### 方式二：批量提交任务（推荐用于生产）

使用 `batch_submit.py` 脚本，可以高效地将一个目录下的所有PDF文件提交给服务。

1.  **安装依赖**:
    ```bash
    pip install requests tqdm
    ```
2.  **运行脚本**:
    ```bash
    # 使用10个并发线程，提交指定目录下的所有PDF
    python batch_submit.py --directory ./data/input_pdfs/ --workers 10
    ```
3.  **获取任务ID**:
    脚本运行结束后，会在当前目录生成一个 `submission_log.csv` 文件。此文件包含了每个文件名与对应的 `task_id`。您可以在稍后根据这些 `task_id` 来获取结果。


### API 端点参考

如果您希望自己编写客户端，以下是核心的API端点：

| 方法   | 路径                               | 描述                                     |
| :----- | :--------------------------------- | :--------------------------------------- |
| `POST` | `/process-pdf/`                    | 提交一个PDF文件，返回 `task_id`。          |
| `GET`  | `/tasks/status/{task_id}`          | 查询指定任务的状态和结果（如果已完成）。 |
| `GET`  | `/tasks/result/download/{task_id}` | 下载指定任务所有结果的 `.zip` 压缩包。     |

## 📁 输出结构

当您通过下载API获取到结果的 `.zip` 压缩包并解压后，会看到一个以原PDF文件名命名的专属文件夹，其内部结构如下：

```bash
data/output/
└── my_document/
    ├── my_document.md
    ├── my_document_content_list.json
    ├── my_document_middle.json
    ├── my_document_layout.pdf
    └── images/
        └── ...
```

## 📝 许可证
本项目采用 MIT 许可证。详情请见 LICENSE 文件。

## ✍️ 作者(工程化)
Shibo Li