# Railway Persistent Volume 설정 가이드

## 🔥 현재 문제

Railway가 재배포할 때마다 모델 파일(408MB)을 처음부터 다운로드하여 5-10분 소요됩니다.
이로 인해 Vercel 요청이 타임아웃되고 사용자는 서비스를 이용할 수 없습니다.

---

## ✅ 해결 방법: Persistent Volume 사용

Railway의 **Persistent Volume**을 마운트하면 재배포 후에도 모델이 유지됩니다.

### **1단계: Railway 대시보드 설정**

1. **Railway 프로젝트** 접속
   ```
   https://railway.app/project/[your-project-id]
   ```

2. **Backend 서비스** 선택
   - GenieCasting backend 클릭

3. **Volumes 탭** 클릭
   - 왼쪽 메뉴에서 "Volumes" 선택

4. **New Volume 생성**
   ```
   Volume Name: models-cache
   Mount Path: /app/models
   Size: 1 GB (기본값)
   ```

5. **Redeploy** 클릭
   - Volume이 마운트되면서 재배포됨

---

### **2단계: 환경 변수 확인**

Railway 환경 변수가 이미 설정되어 있는지 확인:

```bash
HF_HOME=/app/models
TRANSFORMERS_CACHE=/app/models
```

**확인 방법**:
1. Backend 서비스 → Variables 탭
2. 위 환경 변수가 있는지 확인
3. 없으면 추가 후 Redeploy

---

### **3단계: 첫 배포 (10분 대기)**

Volume 설정 후 첫 배포:

1. **Redeploy** 클릭
2. 배포 로그 확인:
   ```
   📥 모델 파일 다운로드 필요 (현재: 0개 유효 ONNX 파일)
   ⏳ HuggingFace Hub에서 AuraFace-v1 모델 다운로드 중...
   Fetching 8 files: 100% ✅
   ✅ 모델 다운로드 완료
   ✅ 모델 파일 검증 완료: 5개 유효 ONNX 파일
   ```
3. **10분 대기** (모델 다운로드)
4. 서비스 정상 작동 확인

---

### **4단계: 재배포 테스트**

Volume이 제대로 작동하는지 확인:

1. **Redeploy** 클릭 (다시 한 번)
2. 배포 로그 확인:
   ```
   ✅ 모델 파일 검증 완료: 5개 유효 ONNX 파일
   ✅ AuraFace-v1 모델 로딩 완료
   ```
3. **다운로드 없이 즉시 로드됨** ✅
4. 서비스 즉시 사용 가능

---

## 📊 설정 전후 비교

| 항목 | Volume 없음 (현재) | Volume 있음 (권장) |
|------|---------------------|---------------------|
| 첫 배포 시간 | 10분 (다운로드) | 10분 (다운로드) |
| 재배포 시간 | 10분 (매번 다운로드) | **1분 (캐시 사용)** ✅ |
| Vercel 타임아웃 | 자주 발생 ❌ | 발생 안함 ✅ |
| 사용자 경험 | 배포 중 서비스 중단 | 즉시 사용 가능 |

---

## 🎯 즉각적인 임시 해결책

**Volume 설정 전에 지금 당장 테스트하려면**:

1. Railway 대시보드 → Backend 서비스
2. **Redeploy** 클릭
3. **10분 대기** (모델 다운로드 완료까지)
4. 배포 완료 후 바로 테스트 진행
   - 이 세션에서는 캐시가 유지됨
   - 다음 배포 전까지는 정상 작동

**단, 다음 배포 시 다시 다운로드됨** (Volume 없으면)

---

## 🔍 Volume 작동 확인 방법

### **Railway 로그 확인**

**Volume 작동 중** (정상):
```
[DEBUG] Loading InsightFace model...
🔮 AuraFace-v1 모델 로딩 중...
✅ 모델 파일 검증 완료: 5개 유효 ONNX 파일
✅ AuraFace-v1 모델 로딩 완료
INFO: Application startup complete.
```

**Volume 미작동** (문제):
```
[DEBUG] Loading InsightFace model...
🔮 AuraFace-v1 모델 로딩 중...
📥 모델 파일 다운로드 필요 (현재: 0개 유효 ONNX 파일)
⏳ HuggingFace Hub에서 AuraFace-v1 모델 다운로드 중...
Fetching 8 files...
```

---

## ⚠️ 주의사항

### **Railway Free 플랜 제한**
- Volume 크기: 최대 1GB
- 모델 크기: ~408MB
- 여유 공간: ~600MB (충분함)

### **Railway Pro 플랜 (권장)**
- Volume 크기: 최대 100GB
- 더 빠른 네트워크 속도
- 더 안정적인 서비스

---

## 🚀 최종 확인 체크리스트

- [ ] Railway Volumes 탭에서 Volume 생성 (`/app/models`)
- [ ] 환경 변수 설정 확인 (`HF_HOME`, `TRANSFORMERS_CACHE`)
- [ ] 첫 배포 후 10분 대기 (모델 다운로드)
- [ ] 배포 로그에서 "모델 파일 검증 완료" 확인
- [ ] 재배포 시 즉시 로드되는지 테스트
- [ ] Vercel에서 API 호출 테스트 (타임아웃 없이 응답)

---

## 📞 도움이 필요하면

1. Railway 배포 로그 전체 복사
2. Vercel 배포 로그 복사
3. 위 로그를 첨부하여 문의

---

**마지막 업데이트**: 2025-12-04  
**문서 작성자**: GitHub Copilot
