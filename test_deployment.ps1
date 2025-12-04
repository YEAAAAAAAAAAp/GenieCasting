# 배포 환경 최종 테스트 스크립트

Write-Host "=== GenieCasting 배포 환경 테스트 ===" -ForegroundColor Cyan
Write-Host ""

# 1. Railway 백엔드 테스트
Write-Host "[1/4] Railway 백엔드 테스트..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "https://geniecasting-production.up.railway.app/health" -Method Get
    if ($health.status -eq "ok") {
        Write-Host "✅ Health check 성공" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Health check 실패: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/4] 인덱스 상태 확인..." -ForegroundColor Yellow
try {
    $index = Invoke-RestMethod -Uri "https://geniecasting-production.up.railway.app/index-status" -Method Get
    Write-Host "✅ 인덱스 로드됨: $($index.loaded)" -ForegroundColor Green
    Write-Host "✅ 배우 수: $($index.actor_count)" -ForegroundColor Green
    Write-Host "✅ 인덱스 파일 존재: $($index.has_index)" -ForegroundColor Green
} catch {
    Write-Host "❌ 인덱스 상태 확인 실패: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/4] 필수 파일 확인..." -ForegroundColor Yellow
$files = @(
    "backend/app/data/embeddings.npy",
    "backend/app/data/metadata.json",
    "nixpacks.toml",
    "requirements.txt",
    "runtime.txt",
    "frontend/vercel.json"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file - 파일 없음!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "[4/4] 배우 이미지 폴더 확인..." -ForegroundColor Yellow
$actorCount = (Get-ChildItem backend/app/data/actors -Directory).Count
Write-Host "✅ 배우 폴더 수: $actorCount" -ForegroundColor Green

Write-Host ""
Write-Host "=== 모든 테스트 통과! ===" -ForegroundColor Green
Write-Host ""
Write-Host "배포 준비 완료:" -ForegroundColor Cyan
Write-Host "- Railway 백엔드: https://geniecasting-production.up.railway.app" -ForegroundColor White
Write-Host "- Vercel 프론트엔드: https://genie-casting.vercel.app" -ForegroundColor White
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "1. Vercel 대시보드에서 자동 재배포 완료 대기 (약 2-3분)" -ForegroundColor White
Write-Host "2. Railway 대시보드에서 모델 다운로드 확인 (첫 배포 시 타임아웃 가능)" -ForegroundColor White
Write-Host "3. If timeout occurs, click Railway Redeploy button (uses cache)" -ForegroundColor White
Write-Host "4. Visit https://genie-casting.vercel.app and test image upload" -ForegroundColor White
