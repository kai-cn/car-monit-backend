# 为 POM 升级验证创建临时本地工作树。
# 思路：从远端 origin/<branch> 建 detached worktree，避免影响用户当前工作树；
# 修改、提交后通过 push HEAD:<branch> 回写原分支。重复执行会跳过已存在目录。
$ErrorActionPreference = 'Continue'
$root = 'D:\work\IdeaProjects\_pom-upgrade'
New-Item -ItemType Directory -Force -Path $root | Out-Null

$specs = @(
  @{ Repo='D:\work\IdeaProjects\car-monit-api'; Branch='master' },
  @{ Repo='D:\work\IdeaProjects\car-monit-api'; Branch='car-monit-api-java-V3' },
  @{ Repo='D:\work\IdeaProjects\car-monit-api'; Branch='car-monit-api-java-fix' },
  @{ Repo='D:\work\IdeaProjects\car-monit-api'; Branch='car-monit-api-jdk17' },
  @{ Repo='D:\work\IdeaProjects\car-monit-api'; Branch='car-monit-api-jdk21' },
  @{ Repo='D:\work\IdeaProjects\car-monit-api'; Branch='car-monit-api-jdk25' },
  @{ Repo='D:\work\IdeaProjects\car-monit-api'; Branch='feature/springboot3' },
  @{ Repo='D:\work\IdeaProjects\car-monit-api'; Branch='feature/springboot3-jdk17' },
  @{ Repo='D:\work\IdeaProjects\car-monit-api'; Branch='feature-dbupgrade' },
  @{ Repo='D:\work\IdeaProjects\car-monit-backend-new'; Branch='master' },
  @{ Repo='D:\work\IdeaProjects\car-monit-backend-new'; Branch='car-monit-backend-java-V3' },
  @{ Repo='D:\work\IdeaProjects\car-monit-backend-new'; Branch='car-monit-backend-jdk17' },
  @{ Repo='D:\work\IdeaProjects\car-monit-backend-new'; Branch='car-monit-backend-jdk21' },
  @{ Repo='D:\work\IdeaProjects\car-monit-backend-new'; Branch='car-monit-backend-jdk25' },
  @{ Repo='D:\work\IdeaProjects\car-monit-backend-new'; Branch='feat/backend-full-parity' },
  @{ Repo='D:\work\IdeaProjects\car-monit-backend-new'; Branch='feature-dbupgrade' }
)

git -C 'D:\work\IdeaProjects\car-monit-api' fetch origin --prune 2>$null
git -C 'D:\work\IdeaProjects\car-monit-backend-new' fetch origin --prune 2>$null

foreach ($s in $specs) {
  $name = ($s.Branch -replace '[\\/]', '_')
  $repoKind = if ($s.Repo -like '*backend*') { 'bk' } else { 'api' }
  $path = Join-Path $root "${repoKind}__$name"
  if (Test-Path $path) { Write-Output "SKIP $path"; continue }
  $ref = "refs/remotes/origin/$($s.Branch)"
  git -C $s.Repo worktree add --detach $path $ref 2>&1 | Select-Object -Last 1
  Write-Output "ADDED $path <- $ref"
}
