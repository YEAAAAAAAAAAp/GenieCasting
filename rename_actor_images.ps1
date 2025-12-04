# 배우 이미지 파일명 정리 스크립트
# "20s_손승현", "30s_손승현", "50s_손승현" 형식을 "손승현" 폴더로 통합

$datasetPath = "dataset"

# 연령대 접두사를 가진 폴더 찾기
$agePrefixFolders = Get-ChildItem -Path $datasetPath -Directory | Where-Object { 
    $_.Name -match '^\d+s_' 
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "배우 이미지 파일명 정리 시작" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

if ($agePrefixFolders.Count -eq 0) {
    Write-Host "연령대 접두사가 있는 폴더를 찾을 수 없습니다." -ForegroundColor Yellow
    Write-Host "패턴: 20s_이름, 30s_이름, 50s_이름" -ForegroundColor Yellow
    exit
}

Write-Host "발견된 폴더 ($($agePrefixFolders.Count)개):" -ForegroundColor Green
$agePrefixFolders | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor White }
Write-Host ""

foreach ($folder in $agePrefixFolders) {
    $oldName = $folder.Name
    # "20s_손승현" -> "손승현" 추출
    $newName = $oldName -replace '^\d+s_', ''
    
    Write-Host "처리 중: $oldName -> $newName" -ForegroundColor Yellow
    
    $targetFolder = Join-Path $datasetPath $newName
    
    # 타겟 폴더가 이미 존재하는지 확인
    if (Test-Path $targetFolder) {
        Write-Host "  ✓ 기존 폴더 발견: $newName" -ForegroundColor Green
        
        # 파일 통합
        $sourceFiles = Get-ChildItem -Path $folder.FullName -File
        $fileCount = 0
        
        foreach ($file in $sourceFiles) {
            $targetFile = Join-Path $targetFolder $file.Name
            
            # 파일이 이미 존재하면 번호 증가
            if (Test-Path $targetFile) {
                $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
                $extension = $file.Extension
                $counter = 1
                
                # 사용 가능한 번호 찾기
                do {
                    $number = ($counter).ToString("000")
                    $targetFile = Join-Path $targetFolder "$number$extension"
                    $counter++
                } while (Test-Path $targetFile)
            }
            
            Copy-Item -Path $file.FullName -Destination $targetFile -Force
            $fileCount++
        }
        
        Write-Host "  ✓ 파일 $fileCount 개 통합 완료" -ForegroundColor Green
        
        # 임베딩 폴더도 처리
        $embeddingSource = Join-Path "dataset\embeddings" $oldName
        $embeddingTarget = Join-Path "dataset\embeddings" $newName
        
        if (Test-Path $embeddingSource) {
            if (Test-Path $embeddingTarget) {
                # 임베딩 파일 통합
                $embeddingFiles = Get-ChildItem -Path $embeddingSource -File
                foreach ($file in $embeddingFiles) {
                    $targetFile = Join-Path $embeddingTarget $file.Name
                    
                    if (Test-Path $targetFile) {
                        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
                        $extension = $file.Extension
                        $counter = 1
                        
                        do {
                            $number = ($counter).ToString("000")
                            $targetFile = Join-Path $embeddingTarget "$number$extension"
                            $counter++
                        } while (Test-Path $targetFile)
                    }
                    
                    Copy-Item -Path $file.FullName -Destination $targetFile -Force
                }
                Write-Host "  ✓ 임베딩 파일 통합 완료" -ForegroundColor Green
            } else {
                Rename-Item -Path $embeddingSource -NewName $newName
                Write-Host "  ✓ 임베딩 폴더 이름 변경 완료" -ForegroundColor Green
            }
        }
        
        # 원본 폴더 삭제
        Remove-Item -Path $folder.FullName -Recurse -Force
        Write-Host "  ✓ 원본 폴더 삭제 완료" -ForegroundColor Green
    } else {
        # 타겟 폴더가 없으면 단순 이름 변경
        Rename-Item -Path $folder.FullName -NewName $newName
        Write-Host "  ✓ 폴더 이름 변경 완료" -ForegroundColor Green
        
        # 임베딩 폴더도 이름 변경
        $embeddingSource = Join-Path "dataset\embeddings" $oldName
        if (Test-Path $embeddingSource) {
            $embeddingTarget = Join-Path "dataset\embeddings" $newName
            Rename-Item -Path $embeddingSource -NewName $newName
            Write-Host "  ✓ 임베딩 폴더 이름 변경 완료" -ForegroundColor Green
        }
    }
    
    Write-Host ""
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "모든 작업이 완료되었습니다!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "1. python backend/scripts/build_actor_index_insightface.py --dataset-dir dataset" -ForegroundColor White
Write-Host "2. 백엔드 재시작" -ForegroundColor White
