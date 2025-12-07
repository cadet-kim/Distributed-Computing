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

        // 이전 달 날짜
        for (let i = firstDay; i > 0; i--) {
            li += `<li class="inactive">${prevLastDate - i + 1}</li>`;
        }

        // 현재 달 날짜
        for (let i = 1; i <= lastDate; i++) {
            const today = new Date();
            const isToday =
                i === today.getDate() &&
                currMonth === today.getMonth() &&
                currYear === today.getFullYear()
                    ? "active"
                    : "";

            li += `<li class="${isToday}">${i}</li>`;
        }

        // 다음 달 날짜
        for (let i = lastDay; i < 6; i++) {
            li += `<li class="inactive">${i - lastDay + 1}</li>`;
        }

        currentDate.innerText = `${months[currMonth]} ${currYear}`;
        daysTag.innerHTML = li;
    }

    // 처음 렌더링
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
});





