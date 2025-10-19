// 샘플 데이터
const SAMPLE_DATA = [
  { id:1, role:'mentor', name:'김민수', major:'컴퓨터공학', year:'4학년', mode:'online',
    available:'주말 오후', available_text:'토/일 14-18시', categories:['프로그래밍'],
    tags:['알고리즘','Python'], intro:'알고리즘/코테 대비 경험 풍부' },
  { id:2, role:'mentor', name:'박수영', major:'수학', year:'3학년', mode:'offline',
    available:'평일 저녁', available_text:'월/수 19-21시', categories:['수학'],
    tags:['해석학','선형대수'], intro:'개념+예제로 쉽게 설명합니다' },
  { id:3, role:'mentor', name:'이정훈', major:'군사학', year:'졸업생', mode:'offline',
    available:'주말 오전', available_text:'토 10-12시', categories:['군사학'],
    tags:['전술','발표'], intro:'전술평가/발표 구조 피드백 전문' },
];

// 카드 렌더링 함수
function renderCard(m){
  const badge = m.role==='mentor' ? 'success' : 'secondary';
  const roleLabel = m.role==='mentor' ? '멘토' : '멘티';
  return `
  <div class="col-12 col-md-6 col-lg-4">
    <div class="card card-mentor h-100">
      <div class="card-body">
        <div class="d-flex justify-content-between mb-2">
          <div>
            <h5>${m.name}</h5>
            <div class="small text-muted">${m.major} · ${m.year}</div>
          </div>
          <span class="badge bg-${badge}">${roleLabel}</span>
        </div>
        <p>${m.intro}</p>
        <div class="mb-2">${m.tags.map(t=>`<span class="badge bg-light text-dark border me-1">#${t}</span>`).join('')}</div>
        <button class="btn btn-sm btn-primary">매칭 요청</button>
      </div>
      <div class="card-footer small text-muted">가능: ${m.available_text}</div>
    </div>
  </div>`;
}

// mentors.html 초기화
function initMentorPage(){
  const params = new URLSearchParams(location.search);
  const category = params.get('category');
  if(category) document.getElementById('subtitle').textContent = `카테고리: ${category}`;

  let items = SAMPLE_DATA;
  if(category) items = items.filter(x => x.categories.includes(category));

  const list = document.getElementById('list');
  const empty = document.getElementById('empty');

  if(items.length===0){
    list.innerHTML = '';
    empty.classList.remove('d-none');
    return;
  }
  list.innerHTML = items.map(renderCard).join('');
  empty.classList.add('d-none');
}
