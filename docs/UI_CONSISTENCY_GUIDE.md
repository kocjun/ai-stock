# KoolSecret UI Consistency Guide

이 문서는 레시피 추천 페이지에 적용된 **상단 띠지(band)** 레이아웃과 **Empty State** 패턴을 다른 화면에도 쉽게 확장하기 위한 실무 지침입니다. 내일부터 진행할 페이지 수정 시 아래 절차를 따라 주세요.

---

## 1. 상단 띠지(Band) 재사용하기

### 공통 개념
- `Layout`은 `Outlet`에 `setBannerContent`를 전달합니다. 페이지에서 `useOutletContext()`로 이 함수를 호출하면 헤더 바로 아래 띠지 영역에 원하는 UI를 주입할 수 있습니다.
- 띠지 영역은 기존 **게스트 경고**가 표시되던 위치입니다. `setBannerContent`가 `null`이면 게스트 경고가 나타나고, 콘텐츠가 주입되면 게스트 경고는 숨겨집니다.

### 적용 절차
1. 페이지 컴포넌트 상단에서 `useOutletContext`를 import 합니다.
   ```jsx
   import { useOutletContext } from 'react-router-dom';
   ```
2. 컴포넌트 내부에서 컨텍스트를 받아 `setBannerContent`를 획득합니다.
   ```jsx
   const { setBannerContent } = useOutletContext() || {};
   ```
3. 띠지에 렌더링할 JSX를 별도 함수나 `useMemo`로 정의합니다.  
   - 좌측: eyebrow + 제목 + 설명  
   - 우측: 탭 또는 CTA 버튼 묶음 (`tab-group`, `band-buttons`, `btn btn-primary` 등 공용 클래스를 사용)
4. `useEffect`에서 `setBannerContent(bandElement)`를 호출하고, 언마운트 시 `null`로 복원합니다.
   ```jsx
   useEffect(() => {
     if (!setBannerContent) return;
     setBannerContent(bandElement);
     return () => setBannerContent(null);
   }, [bandElement, setBannerContent]);
   ```
5. 별도 섹션으로 띠지를 만들 필요가 없습니다. Layout이 자동으로 헤더 아래 영역에 삽입합니다.

### 스타일 참고
- `frontend/src/styles/theme.css`의 `.band-content`, `.band-text`, `.band-actions`, `.tab-group`, `.band-buttons` 클래스를 그대로 사용하면 색상/간격이 일관됩니다.

---

## 2. Empty State 패턴 재사용하기

### 공통 개념
- Empty State 컨테이너는 `.empty-state-wrapper` + `.empty-state` 두 레이어로 구성되어, 화면 높이의 70% 이상을 차지하며 중앙 정렬됩니다.
- 배경은 사이트 색상과 맞춘 연한 블루/시안 그라데이션, 텍스트는 `var(--color-brand-700)`과 `var(--color-gray-500)`를 사용합니다.

### 적용 절차
1. 조건부 렌더링에서 데이터가 없을 때 아래 구조를 그대로 사용합니다.
   ```jsx
   {isEmpty && (
     <div className="empty-state-wrapper">
       <div className="empty-state">
         <h3>상태 제목</h3>
         <p>사용자에게 안내할 메시지…</p>
         <div className="btn-group">
           <Button variant="secondary">보조 액션</Button>
           <Button variant="primary">주요 액션</Button>
         </div>
       </div>
     </div>
   )}
   ```
2. h3/p/버튼 그룹은 필요에 따라 수정하되, 클래스를 유지해 색상/타이포가 일관되게 적용되도록 합니다.
3. 섹션 전체 스크롤을 줄이고 싶다면 Empty State 렌더링 위치를 페이지의 가장 바깥 컨테이너 바로 아래에 배치합니다.

### 스타일 참고
- 관련 클래스는 `frontend/src/styles/theme.css` 738행 부근에 정의되어 있습니다.

---

## 3. 버튼 & 카드 일관성

- 버튼: `btn btn-primary`, `btn btn-secondary`, `btn btn-outline`, `btn btn-ghost` 네 가지 외의 클래스를 새로 만들지 않습니다.
- 카드: 내용에 따라 `card`, `card-data`, `card-media`, `card-form`을 사용합니다. 내용 분류가 애매하면 우선 `card-data`를 기본으로 사용하세요.

---

## 4. 작업 순서 제안

1. 페이지 상단에 띠지가 필요한 경우 먼저 `setBannerContent`를 적용해 탭/CTA를 정렬합니다.
2. 데이터가 비어있을 수 있는 섹션에는 Empty State 레이아웃을 추가합니다.
3. 버튼/카드 색상이 기존 팔레트에 맞는지 확인하고 필요 시 공용 클래스만 사용하도록 정리합니다.

이 지침을 따라 주시면 레시피 추천 페이지와 다른 화면이 동일한 구조/톤을 유지하게 됩니다. 추가적인 변형이 필요하면 동일 문서에 기록을 이어가 주세요.
