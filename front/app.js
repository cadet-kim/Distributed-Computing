// 샘플 데이터 제거 (빈 배열)
const SAMPLE_DATA = [];

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
      </div>
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
