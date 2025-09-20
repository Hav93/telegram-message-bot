# GitHub Actions 自动构建设置指南

## 🔧 设置步骤

### 1. 设置Docker Hub Secrets

要启用GitHub Actions自动构建，需要在GitHub仓库中设置Docker Hub凭据：

1. **进入仓库设置**
   - 打开您的GitHub仓库
   - 点击 `Settings` 标签页
   - 在左侧菜单中选择 `Secrets and variables` → `Actions`

2. **添加Docker Hub凭据**
   点击 `New repository secret` 按钮，添加以下两个secrets：
   
   - **Name**: `DOCKER_USERNAME`  
     **Value**: `hav93` (您的Docker Hub用户名)
   
   - **Name**: `DOCKER_PASSWORD`  
     **Value**: 您的Docker Hub访问令牌

### 2. 获取Docker Hub访问令牌

1. 登录 [Docker Hub](https://hub.docker.com/)
2. 点击右上角头像 → `Account Settings`
3. 选择 `Security` 标签页
4. 点击 `New Access Token`
5. 输入令牌名称（如：`github-actions`）
6. 选择权限：`Read, Write, Delete`
7. 点击 `Generate` 并复制生成的令牌

### 3. 测试自动构建

设置完成后，可以通过以下方式触发构建：

1. **自动触发**: 推送代码到main分支
2. **手动触发**: 
   - 进入仓库的 `Actions` 标签页
   - 选择 `Simple Docker Build` 工作流
   - 点击 `Run workflow` 按钮

## 🚨 故障排除

### 常见错误和解决方案

1. **认证失败**
   ```
   Error: buildx failed with: ERROR: failed to solve: failed to authorize
   ```
   **解决**: 检查DOCKER_USERNAME和DOCKER_PASSWORD是否正确设置

2. **权限不足**
   ```
   Error: denied: requested access to the resource is denied
   ```
   **解决**: 确保Docker Hub访问令牌有写入权限

3. **Dockerfile不存在**
   ```
   Error: failed to solve: failed to read dockerfile
   ```
   **解决**: 确保项目根目录存在Dockerfile文件

## 📊 构建状态

设置完成后，您可以在README中添加构建状态徽章：

```markdown
[![Docker Build](https://github.com/Hav93/telegram-message-bot/actions/workflows/docker-simple.yml/badge.svg)](https://github.com/Hav93/telegram-message-bot/actions/workflows/docker-simple.yml)
```

## 🎯 预期结果

配置成功后，每次推送到main分支时：
- ✅ 自动构建Docker镜像
- ✅ 推送到Docker Hub
- ✅ 更新latest和v3.6标签
- ✅ 在Actions页面显示构建状态
