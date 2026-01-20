#!/bin/bash

# 激活 conda 环境
conda activate PPTAS

# 进入后端目录
cd e:\HomeWorkForDaSE\PPTAS\backend

# 安装依赖（如果需要）
echo "安装后端依赖..."
pip install -r requirements.txt

# 启动后端服务器
echo "启动后端服务器..."
python main.py
