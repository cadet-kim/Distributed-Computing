const daysTag = document.querySelector(".days"),
      currentDate = document.querySelector(".current-date"),
      prevNextIcon = document.querySelectorAll(".nav button");

let date = new Date(),
    currYear = date.getFullYear(),
    currMonth = date.getMonth();

const months = ["January","February","March","April","May","June","July",
                "August","September","October","November","December"];

function renderCalendar() {
    let firstDay = new Date(currYear, currMonth, 1).getDay(),
        lastDate = new Date(currYear, currMonth + 1, 0).getDate(),
        lastDay = new Date(currYear, currMonth, lastDate).getDay(),
        prevLastDate = new Date(currYear, currMonth, 0).getDate();

    let li = "";

    for (let i = firstDay; i > 0; i--) {
        li += `<li class="inactive">${prevLastDate - i + 1}</li>`;
    }

    for (let i = 1; i <= lastDate; i++) {
        const isToday =
            i === new Date().getDate() &&
            currMonth === new Date().getMonth() &&
            currYear === new Date().getFullYear()
                ? "active"
                : "";
        li += `<li class="${isToday}">${i}</li>`;
    }

    for (let i = lastDay; i < 6; i++) {
        li += `<li class="inactive">${i - lastDay + 1}</li>`;
    }

    currentDate.innerText = `${months[currMonth]} ${currYear}`;
    daysTag.innerHTML = li;
}

renderCalendar();

prevNextIcon.forEach(btn => {
    btn.addEventListener("click", () => {
        currMonth = btn.id === "prev" ? currMonth - 1 : currMonth + 1;
        renderCalendar();
    });
});
