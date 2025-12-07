document.addEventListener("DOMContentLoaded", function () {
    const daysTag = document.querySelector(".days");
    const currentDate = document.querySelector(".current-date");
    const prevNextIcon = document.querySelectorAll(".nav-btn");

    let date = new Date(),
        currYear = date.getFullYear(),
        currMonth = date.getMonth();

    const months = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ];

    function renderCalendar() {
        let firstDay = new Date(currYear, currMonth, 1).getDay(),
            lastDate = new Date(currYear, currMonth + 1, 0).getDate(),
            lastDay = new Date(currYear, currMonth, lastDate).getDay(),
            prevLastDate = new Date(currYear, currMonth, 0).getDate();

        let li = "";

        // 이전 달
        for (let i = firstDay; i > 0; i--) {
            li += `<li class="inactive">${prevLastDate - i + 1}</li>`;
        }

        // 현재 달 날짜 생성
        for (let i = 1; i <= lastDate; i++) {
            const today = new Date();
            const isToday =
                i === today.getDate() &&
                currMonth === today.getMonth() &&
                currYear === today.getFullYear()
                    ? "active"
                    : "";

            const monthStr = (currMonth + 1).toString().padStart(2, "0");
            const dayStr = i.toString().padStart(2, "0");
            const fullDate = `${currYear}-${monthStr}-${dayStr}`;

            li += `<li class="day ${isToday}" data-date="${fullDate}">${i}</li>`;
        }

        // 다음 달
        for (let i = lastDay; i < 6; i++) {
            li += `<li class="inactive">${i - lastDay + 1}</li>`;
        }

        currentDate.innerText = `${months[currMonth]} ${currYear}`;
        daysTag.innerHTML = li;

        // 🔥 렌더 후 색상 적용
        applyScheduleColors();
    }

    // 일정이 있는 날짜를 색칠하는 함수
    function applyScheduleColors() {
        if (!scheduleData) return; // 데이터 없으면 스킵

        const allDays = document.querySelectorAll(".day");

        allDays.forEach(day => {
            const d = day.dataset.date;

            // 해당 날짜의 일정 목록
            const matched = scheduleData.filter(s => s.date === d);

            if (matched.length > 0) {
                // 여러 개면 마지막 색 or 고정 규칙도 가능
                const color = matched[matched.length - 1].color;

                day.style.background = color;
                day.style.color = "white";
                day.style.borderRadius = "50%";
                day.style.fontWeight = "bold";
            }
        });
    }

    renderCalendar();

    // 월 이동
    prevNextIcon.forEach(btn => {
        btn.addEventListener("click", () => {
            currMonth = btn.id === "prev" ? currMonth - 1 : currMonth + 1;

            if (currMonth < 0) {
                currMonth = 11;
                currYear--;
            } else if (currMonth > 11) {
                currMonth = 0;
                currYear++;
            }

            renderCalendar();
        });
    });

    // 날짜 클릭 → 일정 페이지로 이동
    document.addEventListener("click", function (e) {
        if (e.target.classList.contains("day")) {
            const selectedDate = e.target.dataset.date;
            if (selectedDate) {
                window.location.href = `/schedule/${selectedDate}`;

            }
        }
    });
});










