import subprocess
import os

def run_git_command(cmd, cwd=None):
    """执行 Git 命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print(f"✅ 成功: {cmd}")
            print(result.stdout)
        else:
            print(f"❌ 失败: {cmd}")
            print(result.stderr)
        return result
    except Exception as e:
        print(f"❌ 异常: {e}")
        return None

# 使用示例：一键同步到 Gitee
def git_sync(project_path, commit_message="自动提交"):
    """一键 Git 同步"""
    os.chdir(project_path)
    
    # 1. 拉取最新代码
    # run_git_command("git pull --rebase")
    
    # 2. 添加所有改动
    run_git_command("git add .")
    
    # 3. 提交
    run_git_command(f'git commit -m "{commit_message}"')
    
    # 4. 推送
    # run_git_command("git push -u origin master")
    run_git_command("git push")
    print("🎉 同步完成！")

# 调用
git_sync("D:/pyAuto", "自动同步：添加新功能")